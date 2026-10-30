"""
Bayesian Damped Popularity Baseline for MovieRec Version 2 (MovieLens 1M).
Shrinks item average ratings toward the global mean based on rating volume.
"""

from typing import Dict, List, Optional, Set, Tuple
import numpy as np
import pandas as pd

from .base import BaseRecommender


class PopularityBaseline(BaseRecommender):
    """
    Damped Popularity Recommender.
    
    Item score formula:
        score_i = (sum(r_ui) + damping * global_mean) / (count_i + damping)
        
    Args:
        damping: Regularization constant shrinkage toward the global mean (default 50.0).
        min_ratings: Minimum ratings required for recommendation eligibility.
    """

    def __init__(self, damping: float = 50.0, min_ratings: int = 1):
        super().__init__()
        self.damping = float(damping)
        self.min_ratings = int(min_ratings)
        self.damped_scores: Dict[int, float] = {}
        self.item_counts: Dict[int, int] = {}
        self.item_raw_sums: Dict[int, float] = {}
        self.ranked_items: List[Tuple[int, float]] = []

    def fit(self, train_df: pd.DataFrame) -> "PopularityBaseline":
        self.global_mean = float(train_df["rating"].mean())
        self.all_users = sorted(train_df["user_id"].unique().tolist())
        self.all_items = sorted(train_df["movie_id"].unique().tolist())

        # Build user seen items
        self.user_seen_items = {}
        for uid, grp in train_df.groupby("user_id"):
            self.user_seen_items[int(uid)] = set(grp["movie_id"].tolist())

        # Group by movie_id
        grouped = train_df.groupby("movie_id")["rating"].agg(["sum", "count"])
        self.damped_scores = {}
        self.item_counts = {}
        self.item_raw_sums = {}

        for item_id, row in grouped.iterrows():
            item_id = int(item_id)
            cnt = int(row["count"])
            sm = float(row["sum"])
            self.item_counts[item_id] = cnt
            self.item_raw_sums[item_id] = sm

            # Bayesian damped mean
            score = (sm + self.damping * self.global_mean) / (cnt + self.damping)
            score = float(np.clip(score, 1.0, 5.0))
            self.damped_scores[item_id] = score

        # Pre-sort all candidate items: descending by score, tie-break by item_id ascending
        candidates = [
            (i, self.damped_scores[i])
            for i in self.all_items
            if self.item_counts.get(i, 0) >= self.min_ratings
        ]
        candidates.sort(key=lambda x: (-x[1], x[0]))
        self.ranked_items = candidates
        self.is_fitted = True
        return self

    def predict(self, user_id: Optional[int], item_id: int) -> float:
        if not self.is_fitted:
            raise RuntimeError("Model is not fitted.")
        return self.damped_scores.get(item_id, self.global_mean)

    def recommend(
        self,
        user_id: int,
        n: int = 10,
        exclude_seen: bool = True,
    ) -> List[Tuple[int, float]]:
        if not self.is_fitted:
            raise RuntimeError("Model is not fitted.")
        if n <= 0:
            return []

        seen = self.user_seen_items.get(user_id, set()) if exclude_seen else set()
        recs = []
        for item_id, score in self.ranked_items:
            if item_id in seen:
                continue
            recs.append((item_id, score))
            if len(recs) >= n:
                break
        return recs
