"""
Recommendation service layer for MovieLens 100K collaborative filtering system.
Encapsulates model inference, online folding-in for new user profiles,
cold-start fallback logic, movie search, item similarity, and explanation generation.
"""

import json
import os
import re
from typing import Dict, List, Optional, Set, Tuple
import numpy as np
import pandas as pd

from src.recsys.data import load_ratings, load_movies, get_default_data_dir, GENRE_COLUMNS
from src.recsys.split import chronological_split
from src.recsys.models.svd import TruncatedSVDRecommender
from src.recsys.models.popularity import PopularityBaseline


class RecommenderService:
    """
    Production-grade inference and recommendation service.
    
    Attributes:
        min_ratings_for_personalization (int): Minimum ratings threshold to trigger
            personalized SVD recommendations. Below this, popularity cold-start is used.
    """

    def __init__(
        self,
        data_dir: Optional[str] = None,
        artifacts_dir: Optional[str] = None,
        min_ratings_for_personalization: int = 3,
        auto_fit: bool = True,
    ):
        self.data_dir = data_dir or get_default_data_dir()
        self.artifacts_dir = artifacts_dir
        self.min_ratings_for_personalization = min_ratings_for_personalization

        # Data structures
        self.movies_df: pd.DataFrame = pd.DataFrame()
        self.movie_metadata: Dict[int, dict] = {}
        self.all_genres: List[str] = [g for g in GENRE_COLUMNS if g != "unknown"]

        # Models
        self.svd_model: Optional[TruncatedSVDRecommender] = None
        self.popularity_model: Optional[PopularityBaseline] = None

        # Normalized item latent vectors for cosine similarity (n_items, n_factors)
        self.item_factors_normalized: Optional[np.ndarray] = None
        self.item_factor_idx_map: Dict[int, int] = {}

        if auto_fit:
            self._initialize()

    def _initialize(self) -> None:
        """Load metadata and either load cached artifacts or fit models."""
        self._load_metadata()

        if self.artifacts_dir and self._artifacts_exist(self.artifacts_dir):
            try:
                self.load_artifacts(self.artifacts_dir)
                return
            except Exception:
                # If artifact loading fails, fall back to fitting from raw data
                pass

        self._fit_models()

        if self.artifacts_dir:
            try:
                self.save_artifacts(self.artifacts_dir)
            except Exception:
                pass

    def _artifacts_exist(self, directory: str) -> bool:
        """Check if all required project artifact files exist."""
        svd_path = os.path.join(directory, "svd_artifacts.npz")
        pop_path = os.path.join(directory, "popularity_artifacts.json")
        return os.path.exists(svd_path) and os.path.exists(pop_path)

    def _load_metadata(self) -> None:
        """Load and index movie metadata from MovieLens u.item."""
        self.movies_df = load_movies(self.data_dir)

        # Parse metadata into fast lookup dict
        for _, row in self.movies_df.iterrows():
            item_id = int(row["item_id"])
            title = str(row["title"])

            # Extract release year from title e.g. "Toy Story (1995)"
            year_match = re.search(r"\((\d{4})\)", title)
            if year_match:
                year = int(year_match.group(1))
            else:
                # Fallback to release_date if title regex fails
                rel_date = str(row.get("release_date", ""))
                parts = rel_date.split("-")
                year = int(parts[-1]) if len(parts) == 3 and parts[-1].isdigit() else None

            # Genres
            genres = [g for g in self.all_genres if row.get(g, 0) == 1]

            self.movie_metadata[item_id] = {
                "item_id": item_id,
                "title": title,
                "year": year,
                "genres": genres,
                "imdb_url": str(row.get("imdb_url", "")),
                "avg_rating": 0.0,
                "rating_count": 0,
            }

        # Compute historical training rating statistics for movie metadata
        ratings = load_ratings(self.data_dir)
        splits = chronological_split(ratings, train_frac=0.60, val_frac=0.20, random_state=42)
        train_val = pd.concat([splits.train, splits.val], ignore_index=True)
        stats = train_val.groupby("item_id")["rating"].agg(["count", "mean"]).to_dict(orient="index")
        for item_id, st in stats.items():
            if item_id in self.movie_metadata:
                self.movie_metadata[item_id]["rating_count"] = int(st["count"])
                self.movie_metadata[item_id]["avg_rating"] = float(round(st["mean"], 2))

    def _fit_models(self) -> None:
        """Fit SVD and Popularity baseline on Train + Validation splits."""
        ratings = load_ratings(self.data_dir)
        splits = chronological_split(ratings, train_frac=0.60, val_frac=0.20, random_state=42)
        train_val = pd.concat([splits.train, splits.val], ignore_index=True)

        # 1. Fit winning SVD model (n_factors=20)
        self.svd_model = TruncatedSVDRecommender(n_factors=20, random_state=42).fit(train_val)

        # 2. Fit winning Popularity Baseline (damping=50.0, min_ratings=1)
        self.popularity_model = PopularityBaseline(damping=50.0, min_ratings=1).fit(train_val)

        # 3. Compute normalized item latent factors for similarity
        self._compute_normalized_factors()

    def _compute_normalized_factors(self) -> None:
        """Compute normalized right singular vectors (item factors) for cosine similarity."""
        if self.svd_model is None or self.svd_model.Vt is None:
            return

        V = self.svd_model.Vt.T  # (n_items, n_factors)
        norms = np.linalg.norm(V, axis=1, keepdims=True)
        norms[norms == 0.0] = 1e-9
        self.item_factors_normalized = V / norms
        self.item_factor_idx_map = {item: idx for idx, item in enumerate(self.svd_model.all_items)}

    # --------------------------------------------------------------------------
    # Public Service API
    # --------------------------------------------------------------------------

    def search_movies(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search movies by title query (case-insensitive substring match).
        Results are ordered by popularity (rating count) descending.
        """
        if not query or not query.strip():
            return []

        q = query.strip().lower()
        matches = []
        for meta in self.movie_metadata.values():
            if q in meta["title"].lower():
                matches.append(meta)

        matches.sort(key=lambda m: (-m["rating_count"], m["title"]))
        return matches[:limit]

    def get_movie_info(self, item_id: int) -> Dict:
        """Retrieve metadata for a specific movie ID."""
        if item_id not in self.movie_metadata:
            raise ValueError(f"Movie ID {item_id} not found in catalog.")
        return dict(self.movie_metadata[item_id])

    def recommend_for_user(
        self,
        user_id: int,
        n: int = 10,
        filter_genres: Optional[List[str]] = None,
    ) -> List[Dict]:
        """
        Generate recommendations for a known training user ID using SVD.
        
        Args:
            user_id: Existing user ID from training data.
            n: Number of recommendations to return.
            filter_genres: Optional list of genre names to filter candidate items.
        """
        if not isinstance(user_id, int):
            raise ValueError(f"user_id must be an integer, got {type(user_id)}.")
        if n <= 0:
            raise ValueError(f"n must be a positive integer, got {n}.")
        if self.svd_model is None or not self.svd_model.is_fitted:
            raise RuntimeError("Recommender model is not fitted.")
        if user_id not in self.svd_model.user_seen_items:
            raise ValueError(f"Unknown user ID: {user_id}. User not found in training dataset.")

        # If genre filtering is active, retrieve extra candidates to filter
        candidate_count = len(self.svd_model.all_items) if filter_genres else n
        raw_recs = self.svd_model.recommend(user_id, n=candidate_count, exclude_seen=True)

        user_seen = self.svd_model.user_seen_items.get(user_id, set())
        results = []

        for item_id, score in raw_recs:
            meta = self.movie_metadata.get(item_id, {})
            item_genres = meta.get("genres", [])

            if filter_genres and not any(g in item_genres for g in filter_genres):
                continue

            explanation = self._explain_recommendation(item_id, user_seen, is_cold_start=False)

            results.append({
                "item_id": item_id,
                "title": meta.get("title", f"Movie {item_id}"),
                "year": meta.get("year"),
                "genres": item_genres,
                "predicted_rating": round(float(score), 2),
                "avg_rating": meta.get("avg_rating", 0.0),
                "rating_count": meta.get("rating_count", 0),
                "explanation": explanation,
                "is_cold_start": False,
                "strategy": "svd_personalized",
            })

            if len(results) >= n:
                break

        return results

    def recommend_for_profile(
        self,
        ratings: Dict[int, float],
        n: int = 10,
        filter_genres: Optional[List[str]] = None,
    ) -> List[Dict]:
        """
        Generate recommendations for a new interactive user profile.
        
        If len(ratings) < min_ratings_for_personalization, transparently triggers
        the Popularity Baseline with is_cold_start=True.
        Otherwise, folds the user into the latent SVD space using right singular vectors.
        
        Args:
            ratings: Dict mapping movie item_id -> rating (1.0 to 5.0).
            n: Number of recommendations to return.
            filter_genres: Optional list of genre names to filter candidate items.
        """
        # Input validation
        if not ratings:
            raise ValueError("User profile cannot be empty. Please provide at least one rating.")
        if n <= 0:
            raise ValueError(f"n must be a positive integer, got {n}.")

        for item_id, r in ratings.items():
            if item_id not in self.movie_metadata:
                raise ValueError(f"Unknown movie ID in profile: {item_id}.")
            if not isinstance(r, (int, float)) or not (1.0 <= float(r) <= 5.0):
                raise ValueError(f"Invalid rating {r} for movie {item_id}. Ratings must be between 1.0 and 5.0.")

        seen_items = set(ratings.keys())
        is_cold_start = len(ratings) < self.min_ratings_for_personalization

        if is_cold_start:
            return self._recommend_popularity(seen_items, n, filter_genres)
        else:
            return self._recommend_svd_folding(ratings, n, filter_genres)

    def _recommend_popularity(
        self,
        seen_items: Set[int],
        n: int,
        filter_genres: Optional[List[str]],
    ) -> List[Dict]:
        """Generate cold-start recommendations using Popularity Baseline."""
        if self.popularity_model is None:
            raise RuntimeError("Popularity baseline is not fitted.")

        candidates = [i for i in self.popularity_model.all_items if i not in seen_items]
        candidate_scores = []

        for item_id in candidates:
            meta = self.movie_metadata.get(item_id, {})
            item_genres = meta.get("genres", [])

            if filter_genres and not any(g in item_genres for g in filter_genres):
                continue

            score = self.popularity_model.predict(user_id=None, item_id=item_id)
            candidate_scores.append((item_id, score))

        candidate_scores.sort(key=lambda x: (-x[1], x[0]))
        top_candidates = candidate_scores[:n]

        results = []
        for item_id, score in top_candidates:
            meta = self.movie_metadata.get(item_id, {})
            results.append({
                "item_id": item_id,
                "title": meta.get("title", f"Movie {item_id}"),
                "year": meta.get("year"),
                "genres": meta.get("genres", []),
                "predicted_rating": round(float(score), 2),
                "avg_rating": meta.get("avg_rating", 0.0),
                "rating_count": meta.get("rating_count", 0),
                "explanation": f"Recommended from Popularity Baseline ({meta.get('rating_count', 0)} ratings, avg {meta.get('avg_rating', 0.0)} stars) due to cold-start profile (< {self.min_ratings_for_personalization} ratings).",
                "is_cold_start": True,
                "strategy": "popularity_cold_start",
            })

        return results

    def _recommend_svd_folding(
        self,
        ratings: Dict[int, float],
        n: int,
        filter_genres: Optional[List[str]],
    ) -> List[Dict]:
        """Fold user ratings into SVD latent space using right singular vectors."""
        if self.svd_model is None or self.svd_model.Vt is None:
            raise RuntimeError("SVD model is not fitted.")

        seen_items = set(ratings.keys())
        user_mean = float(np.mean(list(ratings.values())))

        # Construct centered rating vector x across all catalog items
        V = self.svd_model.Vt.T  # (n_items, n_factors)
        x = np.zeros(len(self.svd_model.all_items), dtype=np.float64)

        for item_id, r in ratings.items():
            if item_id in self.svd_model.item2idx:
                idx = self.svd_model.item2idx[item_id]
                x[idx] = float(r) - user_mean

        # Folding-in projection: residual = (x @ V) @ Vt
        # user latent factors p = x @ V
        p = x @ V
        pred_residual = p @ self.svd_model.Vt
        pred_ratings = user_mean + pred_residual
        pred_ratings = np.clip(pred_ratings, 1.0, 5.0)

        # Score and filter candidates
        candidate_scores = []
        for item_id in self.svd_model.all_items:
            if item_id in seen_items:
                continue

            meta = self.movie_metadata.get(item_id, {})
            item_genres = meta.get("genres", [])

            if filter_genres and not any(g in item_genres for g in filter_genres):
                continue

            idx = self.svd_model.item2idx[item_id]
            candidate_scores.append((item_id, float(pred_ratings[idx])))

        candidate_scores.sort(key=lambda s: (-s[1], s[0]))
        top_candidates = candidate_scores[:n]

        results = []
        for item_id, score in top_candidates:
            meta = self.movie_metadata.get(item_id, {})
            explanation = self._explain_recommendation(item_id, seen_items, is_cold_start=False, profile_ratings=ratings)

            results.append({
                "item_id": item_id,
                "title": meta.get("title", f"Movie {item_id}"),
                "year": meta.get("year"),
                "genres": meta.get("genres", []),
                "predicted_rating": round(float(score), 2),
                "avg_rating": meta.get("avg_rating", 0.0),
                "rating_count": meta.get("rating_count", 0),
                "explanation": explanation,
                "is_cold_start": False,
                "strategy": "svd_personalized",
            })

        return results

    def _explain_recommendation(
        self,
        target_item: int,
        user_seen_items: Set[int],
        is_cold_start: bool,
        profile_ratings: Optional[Dict[int, float]] = None,
    ) -> str:
        """
        Generate grounded explanation based strictly on real model signals
        (cosine similarity in SVD item factor space to user's rated movies).
        """
        if is_cold_start or not user_seen_items or self.item_factors_normalized is None:
            meta = self.movie_metadata.get(target_item, {})
            return f"Recommended by popularity baseline ({meta.get('rating_count', 0)} ratings, avg {meta.get('avg_rating', 0.0)} stars)."

        if target_item not in self.item_factor_idx_map:
            return "Recommended based on overall collaborative filtering preferences."

        target_idx = self.item_factor_idx_map[target_item]
        target_vec = self.item_factors_normalized[target_idx]

        best_item = None
        best_sim = -1.0

        for seen_id in user_seen_items:
            # Focus on positively rated items if rating values are provided
            if profile_ratings and profile_ratings.get(seen_id, 0.0) < 3.0:
                continue

            if seen_id in self.item_factor_idx_map:
                seen_idx = self.item_factor_idx_map[seen_id]
                sim = float(target_vec @ self.item_factors_normalized[seen_idx])
                if sim > best_sim:
                    best_sim = sim
                    best_item = seen_id

        if best_item and best_sim > 0.10:
            best_meta = self.movie_metadata.get(best_item, {})
            rating_str = f" ({profile_ratings[best_item]} stars)" if profile_ratings and best_item in profile_ratings else ""
            return f"Recommended because you rated '{best_meta.get('title', f'Movie {best_item}')}'{rating_str} (similarity: {best_sim:.2f})."

        return "Recommended based on your overall latent factor preference profile."

    def similar_movies(self, item_id: int, n: int = 10) -> List[Dict]:
        """
        Find top-n most similar movies to item_id using cosine similarity
        in the fitted 20-dimensional SVD item latent factor space.
        """
        if item_id not in self.movie_metadata:
            raise ValueError(f"Movie ID {item_id} not found in catalog.")
        if n <= 0:
            raise ValueError(f"n must be a positive integer, got {n}.")
        if self.item_factors_normalized is None or item_id not in self.item_factor_idx_map:
            raise RuntimeError("Model item factors not initialized.")

        target_idx = self.item_factor_idx_map[item_id]
        target_vec = self.item_factors_normalized[target_idx]

        # Compute cosine similarities to all items
        sims = self.item_factors_normalized @ target_vec
        sorted_indices = np.argsort(-sims)

        results = []
        for idx in sorted_indices:
            other_id = self.svd_model.all_items[idx]
            if other_id == item_id:
                continue

            meta = self.movie_metadata.get(other_id, {})
            results.append({
                "item_id": other_id,
                "title": meta.get("title", f"Movie {other_id}"),
                "year": meta.get("year"),
                "genres": meta.get("genres", []),
                "similarity": round(float(sims[idx]), 4),
                "avg_rating": meta.get("avg_rating", 0.0),
                "rating_count": meta.get("rating_count", 0),
            })

            if len(results) >= n:
                break

        return results

    # --------------------------------------------------------------------------
    # Artifact Persistence
    # --------------------------------------------------------------------------

    def save_artifacts(self, directory: str) -> None:
        """Serialize project-produced model artifacts to disk."""
        os.makedirs(directory, exist_ok=True)
        if self.svd_model is None or not self.svd_model.is_fitted:
            raise RuntimeError("Cannot save un-fitted model artifacts.")

        users = np.array(list(self.svd_model.user2idx.keys()), dtype=np.int64)
        items = np.array(self.svd_model.all_items, dtype=np.int64)
        user_means_arr = np.array([self.svd_model.user_means[u] for u in users], dtype=np.float64)

        # 1. SVD Artifacts
        svd_path = os.path.join(directory, "svd_artifacts.npz")
        np.savez_compressed(
            svd_path,
            U=self.svd_model.U,
            sigma=self.svd_model.sigma,
            Vt=self.svd_model.Vt,
            users=users,
            items=items,
            user_means=user_means_arr,
            global_mean=np.array(self.svd_model.global_mean),
            n_factors=np.array(self.svd_model.n_factors),
        )

        # 2. Popularity Artifacts
        pop_path = os.path.join(directory, "popularity_artifacts.json")
        pop_data = {
            "damping": self.popularity_model.damping,
            "min_ratings": self.popularity_model.min_ratings,
            "global_mean": self.popularity_model.global_mean,
            "damped_scores": {int(k): float(v) for k, v in self.popularity_model.damped_scores.items()},
        }
        with open(pop_path, "w") as f:
            json.dump(pop_data, f)

    def load_artifacts(self, directory: str) -> None:
        """Load project-produced model artifacts from disk."""
        svd_path = os.path.join(directory, "svd_artifacts.npz")
        pop_path = os.path.join(directory, "popularity_artifacts.json")

        if not os.path.exists(svd_path) or not os.path.exists(pop_path):
            raise FileNotFoundError(f"Artifacts missing in {directory}.")

        # 1. Load SVD
        data = np.load(svd_path)
        self.svd_model = TruncatedSVDRecommender(n_factors=int(data["n_factors"]), random_state=42)
        self.svd_model.U = data["U"]
        self.svd_model.sigma = data["sigma"]
        self.svd_model.Vt = data["Vt"]
        users = data["users"].tolist()
        items = data["items"].tolist()
        self.svd_model.all_items = items
        self.svd_model.user2idx = {u: idx for idx, u in enumerate(users)}
        self.svd_model.idx2user = {idx: u for idx, u in enumerate(users)}
        self.svd_model.item2idx = {i: idx for idx, i in enumerate(items)}
        self.svd_model.idx2item = {idx: i for idx, i in enumerate(items)}
        self.svd_model.user_means = dict(zip(users, data["user_means"].tolist()))
        self.svd_model.global_mean = float(data["global_mean"])
        self.svd_model.is_fitted = True

        # Load historical ratings to restore user_seen_items
        ratings = load_ratings(self.data_dir)
        splits = chronological_split(ratings, train_frac=0.60, val_frac=0.20, random_state=42)
        train_val = pd.concat([splits.train, splits.val], ignore_index=True)
        self.svd_model.user_seen_items = train_val.groupby("user_id")["item_id"].apply(set).to_dict()

        # 2. Load Popularity
        with open(pop_path, "r") as f:
            pop_data = json.load(f)
        self.popularity_model = PopularityBaseline(
            damping=float(pop_data["damping"]),
            min_ratings=int(pop_data["min_ratings"]),
        )
        self.popularity_model.global_mean = float(pop_data["global_mean"])
        self.popularity_model.damped_scores = {int(k): float(v) for k, v in pop_data["damped_scores"].items()}
        self.popularity_model.all_items = self.svd_model.all_items
        self.popularity_model.is_fitted = True

        # 3. Normalized factors
        self._compute_normalized_factors()
