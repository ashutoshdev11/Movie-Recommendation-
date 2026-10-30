"""
Recommendation and Catalog Service for MovieRec Version 2.
Loads exclusively V2 artifacts (SVD-1M and Popularity-1M) and handles online folding-in.
"""

import json
import os
from typing import Dict, List, Optional, Set, Tuple
import numpy as np
import pandas as pd

from app.ml.models.svd import TruncatedSVDRecommender
from app.ml.models.popularity import PopularityBaseline

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARTIFACTS_DIR = os.path.join(BASE_DIR, "artifacts")
DATA_DIR = os.path.join(BASE_DIR, "data", "processed")


class V2RecommenderService:
    """Production service for ML-1M catalog lookup, similarity, and online recommendation."""

    def __init__(self):
        self.movies_df: pd.DataFrame = pd.DataFrame()
        self.movie_metadata: Dict[int, dict] = {}
        self.all_genres: List[str] = []
        self.svd_model: Optional[TruncatedSVDRecommender] = None
        self.popularity_model: Optional[PopularityBaseline] = None

        # Normalized item latent factor vectors for cosine similarity (n_items, 30)
        self.item_factors_normalized: Optional[np.ndarray] = None
        self.item_factor_idx_map: Dict[int, int] = {}

        self._initialize()

    def _initialize(self) -> None:
        """Load metadata and V2 model artifacts."""
        # 1. Load movies metadata
        movies_path = os.path.join(DATA_DIR, "movies_metadata.csv.gz")
        if os.path.exists(movies_path):
            self.movies_df = pd.read_csv(movies_path, compression="gzip")
            # Build fast lookup dict
            for _, row in self.movies_df.iterrows():
                mid = int(row["movie_id"])
                # Extract genres from string repr
                raw_genres = row["genres"]
                if isinstance(raw_genres, str) and raw_genres.startswith("["):
                    import ast
                    genres = ast.literal_eval(raw_genres)
                elif isinstance(raw_genres, list):
                    genres = raw_genres
                else:
                    genres = []

                year = int(row["year"]) if pd.notnull(row["year"]) else None
                self.movie_metadata[mid] = {
                    "movie_id": mid,
                    "title": str(row["title"]),
                    "year": year,
                    "genres": genres,
                    "avg_rating": 0.0,
                    "rating_count": 0,
                }

        # 2. Load SVD Model
        svd_path = os.path.join(ARTIFACTS_DIR, "svd_1m_artifacts.npz")
        if os.path.exists(svd_path):
            self.svd_model = TruncatedSVDRecommender.load_artifacts(svd_path)
            self._compute_normalized_factors()

        # 3. Load Popularity Model
        pop_path = os.path.join(ARTIFACTS_DIR, "popularity_1m_artifacts.json")
        if os.path.exists(pop_path):
            with open(pop_path, "r", encoding="utf-8") as f:
                pop_data = json.load(f)
            self.popularity_model = PopularityBaseline(
                damping=pop_data.get("damping", 50.0),
                min_ratings=pop_data.get("min_ratings", 1),
            )
            self.popularity_model.global_mean = pop_data.get("global_mean", 3.58)
            self.popularity_model.damped_scores = {int(k): float(v) for k, v in pop_data.get("damped_scores", {}).items()}
            self.popularity_model.item_counts = {int(k): int(v) for k, v in pop_data.get("item_counts", {}).items()}
            self.popularity_model.all_items = sorted(list(self.popularity_model.damped_scores.keys()))
            self.popularity_model.ranked_items = sorted(
                [(i, self.popularity_model.damped_scores[i]) for i in self.popularity_model.all_items],
                key=lambda x: (-x[1], x[0]),
            )
            self.popularity_model.is_fitted = True

            # Update movie_metadata with rating counts and scores
            for mid, cnt in self.popularity_model.item_counts.items():
                if mid in self.movie_metadata:
                    self.movie_metadata[mid]["rating_count"] = cnt
                    self.movie_metadata[mid]["avg_rating"] = self.popularity_model.damped_scores.get(mid, 3.5)

    def _compute_normalized_factors(self) -> None:
        """Compute unit-norm item singular vectors for fast cosine similarity."""
        if self.svd_model is None or self.svd_model.Vt is None:
            return
        V = self.svd_model.Vt.T  # (n_items, k)
        norms = np.linalg.norm(V, axis=1, keepdims=True)
        norms[norms == 0.0] = 1e-9
        self.item_factors_normalized = V / norms
        self.item_factor_idx_map = {item: idx for idx, item in enumerate(self.svd_model.all_items)}

    # --------------------------------------------------------------------------
    # Catalog Lookup & Exploration APIs
    # --------------------------------------------------------------------------

    def get_movie(self, movie_id: int) -> Optional[dict]:
        """Fetch metadata for a single movie ID."""
        return self.movie_metadata.get(movie_id)

    def search_movies(
        self,
        query: Optional[str] = None,
        genre: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[dict], int]:
        """
        Search catalog by query and/or genre with pagination.
        Ordered by rating count (popularity) descending.
        """
        matches = list(self.movie_metadata.values())

        if query and query.strip():
            q = query.strip().lower()
            matches = [m for m in matches if q in m["title"].lower()]

        if genre and genre.strip():
            g = genre.strip()
            matches = [m for m in matches if g in m["genres"]]

        matches.sort(key=lambda m: (-m["rating_count"], m["title"]))
        total = len(matches)
        paginated = matches[offset : offset + limit]
        return paginated, total

    def get_trending(self, limit: int = 12) -> List[dict]:
        """Return top trending movies by historical interaction volume."""
        all_movies = list(self.movie_metadata.values())
        all_movies.sort(key=lambda m: (-m["rating_count"], m["title"]))
        return all_movies[:limit]

    def get_top_rated(self, limit: int = 12, min_ratings: int = 50) -> List[dict]:
        """Return top critically-acclaimed movies by Bayesian damped rating."""
        qualified = [m for m in self.movie_metadata.values() if m["rating_count"] >= min_ratings]
        qualified.sort(key=lambda m: (-m["avg_rating"], -m["rating_count"]))
        return qualified[:limit]

    def get_similar_movies(self, movie_id: int, n: int = 10) -> List[dict]:
        """Compute top-N similar movies using cosine similarity in 30D SVD item latent space."""
        if self.item_factors_normalized is None or movie_id not in self.item_factor_idx_map:
            # Fallback to genre-based matching if movie not in latent space
            return self._similar_by_genre(movie_id, n=n)

        target_idx = self.item_factor_idx_map[movie_id]
        target_vec = self.item_factors_normalized[target_idx]

        sims = np.dot(self.item_factors_normalized, target_vec)
        sorted_indices = np.argsort(-sims)

        results = []
        for idx in sorted_indices:
            other_id = self.svd_model.all_items[idx]
            if other_id == movie_id:
                continue

            meta = self.movie_metadata.get(other_id)
            if meta:
                item_dict = dict(meta)
                item_dict["similarity"] = round(float(sims[idx]), 4)
                results.append(item_dict)

            if len(results) >= n:
                break
        return results

    def _similar_by_genre(self, movie_id: int, n: int = 10) -> List[dict]:
        """Fallback genre similarity."""
        target = self.movie_metadata.get(movie_id)
        if not target:
            return []
        target_genres = set(target.get("genres", []))
        candidates = []
        for mid, meta in self.movie_metadata.items():
            if mid == movie_id:
                continue
            common = len(target_genres.intersection(meta.get("genres", [])))
            if common > 0:
                candidates.append((common, meta))
        candidates.sort(key=lambda c: (-c[0], -c[1]["rating_count"]))
        return [c[1] for c in candidates[:n]]

    # --------------------------------------------------------------------------
    # Personalized Recommendations from Saved User Ratings
    # --------------------------------------------------------------------------

    def recommend_for_user_ratings(
        self,
        ratings: Dict[int, float],
        n: int = 10,
    ) -> Dict:
        """
        Generate recommendations for a user based on their saved rating interactions.
        
        Protocol:
            - If len(ratings) < 3: Uses PopularityBaseline (cold-start fallback).
            - If len(ratings) >= 3: Uses TruncatedSVD profile folding-in.
            - Excludes already-rated movies.
        """
        seen_items = set(ratings.keys())
        is_cold_start = len(ratings) < 3

        if is_cold_start:
            # Popularity Baseline Fallback
            raw_recs = []
            if self.popularity_model:
                for item_id, score in self.popularity_model.ranked_items:
                    if item_id in seen_items:
                        continue
                    raw_recs.append((item_id, score))
                    if len(raw_recs) >= n:
                        break
            strategy = "popularity_cold_start"
            explanation_prefix = "Recommended based on community popularity (< 3 ratings in your profile)."
        else:
            # Personalized SVD Folding-In
            if self.svd_model:
                raw_recs = self.svd_model.fold_in_profile(ratings, n=n)
            else:
                raw_recs = []
            strategy = "svd_personalized_folding"
            explanation_prefix = "Personalized recommendation: folded into 30-dimensional SVD latent space."

        # Build recommendation items
        items = []
        for rank, (movie_id, score) in enumerate(raw_recs, start=1):
            meta = self.movie_metadata.get(movie_id, {})
            items.append({
                "rank": rank,
                "movie_id": movie_id,
                "title": meta.get("title", f"Movie {movie_id}"),
                "year": meta.get("year"),
                "genres": meta.get("genres", []),
                "predicted_rating": round(float(score), 2),
                "avg_rating": meta.get("avg_rating", 0.0),
                "rating_count": meta.get("rating_count", 0),
                "strategy": strategy,
                "is_cold_start": is_cold_start,
                "explanation": f"{explanation_prefix} Predicted score: {score:.1f} stars.",
                "poster_url": f"/api/v1/posters/fallback/{movie_id}",
            })

        return {
            "strategy": strategy,
            "is_cold_start": is_cold_start,
            "count": len(items),
            "items": items,
        }


# Global singleton instance
recommender_service = V2RecommenderService()
