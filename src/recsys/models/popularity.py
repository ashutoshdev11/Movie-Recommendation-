"""
Popularity baseline recommender with damped mean ratings and global prior.
"""

from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from src.recsys.models.base import BaseRecommender


class PopularityBaseline(BaseRecommender):
    """
    Popularity Baseline Recommender.
    Scores each movie using Bayesian / damped mean rating:
        score(i) = (sum(r_ui) + m * global_mean) / (count(i) + m)
    If count(i) < min_ratings, falls back to global_mean.
    """

    def __init__(self, damping: float = 10.0, min_ratings: int = 5) -> None:
        super().__init__()
        self.damping: float = float(damping)
        self.min_ratings: int = int(min_ratings)
        self.damped_scores: Dict[int, float] = {}

    def fit(self, train_ratings: pd.DataFrame) -> "PopularityBaseline":
        self._init_base_statistics(train_ratings)

        grouped = train_ratings.groupby("item_id")["rating"]
        item_sums = grouped.sum().to_dict()
        item_counts = grouped.count().to_dict()

        self.damped_scores = {}
        for item_id in self.all_items:
            count = item_counts.get(item_id, 0)
            if count >= self.min_ratings:
                total_sum = item_sums.get(item_id, 0.0)
                damped_mean = (total_sum + self.damping * self.global_mean) / (count + self.damping)
            else:
                damped_mean = self.global_mean

            # Clip bounded
            self.damped_scores[item_id] = float(np.clip(damped_mean, 1.0, 5.0))

        self.is_fitted = True
        return self

    def predict(self, user_id: int, item_id: int) -> float:
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before predict.")

        if item_id in self.damped_scores:
            return self.damped_scores[item_id]
        # Unknown item fallback
        return float(np.clip(self.global_mean, 1.0, 5.0))

    def recommend(
        self,
        user_id: int,
        n: int = 10,
        exclude_seen: bool = True,
    ) -> List[Tuple[int, float]]:
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before recommend.")

        seen = self.user_seen_items.get(user_id, set()) if exclude_seen else set()
        candidates = [item for item in self.all_items if item not in seen]

        scores = [(item, self.damped_scores[item]) for item in candidates]
        scores.sort(key=lambda x: (-x[1], x[0]))
        return scores[:n]
