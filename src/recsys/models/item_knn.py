"""
Item-based Collaborative Filtering using k-Nearest Neighbors and Adjusted Cosine similarity.
"""

from typing import Dict, List, Optional, Set, Tuple
import numpy as np
import pandas as pd
from src.recsys.models.base import BaseRecommender


class ItemKNNRecommender(BaseRecommender):
    """
    Item-based Collaborative Filtering Recommender.
    Uses Adjusted Cosine similarity (subtracting user means):
        s(i, j) = sum_u (r_ui - mu_u)(r_uj - mu_u) / (sqrt(sum (r_ui - mu_u)^2) * sqrt(sum (r_uj - mu_u)^2))
    Prediction:
        r_hat(u, i) = sum_j s(i, j) * r_uj / sum_j |s(i, j)|
    Fallback chain when neighbours are insufficient: item mean -> user mean -> global mean.
    """

    def __init__(self, k: int = 20, min_overlap: int = 2) -> None:
        super().__init__()
        self.k: int = int(k)
        self.min_overlap: int = int(min_overlap)

        self.user_ratings: Dict[int, Dict[int, float]] = {}
        self.item_users: Dict[int, Dict[int, float]] = {}
        self.item_users_sets: Dict[int, Set[int]] = {}
        self.sim_cache: Dict[Tuple[int, int], float] = {}

    def fit(self, train_ratings: pd.DataFrame) -> "ItemKNNRecommender":
        self._init_base_statistics(train_ratings)

        self.user_ratings = {}
        self.item_users = {}
        self.item_users_sets = {}
        self.sim_cache = {}

        for _, row in train_ratings.iterrows():
            u = int(row["user_id"])
            i = int(row["item_id"])
            r = float(row["rating"])

            if u not in self.user_ratings:
                self.user_ratings[u] = {}
            self.user_ratings[u][i] = r

            if i not in self.item_users:
                self.item_users[i] = {}
            self.item_users[i][u] = r

        # Precompute user sets per item to accelerate overlap checking
        self.item_users_sets = {i: set(users.keys()) for i, users in self.item_users.items()}

        self.is_fitted = True
        return self

    def compute_similarity(self, i1: int, i2: int) -> float:
        if i1 == i2:
            return 1.0

        pair_key = (min(i1, i2), max(i1, i2))
        if pair_key in self.sim_cache:
            return self.sim_cache[pair_key]

        users1 = self.item_users.get(i1)
        users2 = self.item_users.get(i2)
        if not users1 or not users2:
            self.sim_cache[pair_key] = 0.0
            return 0.0

        # Rapid pruning: if either item has fewer raters than min_overlap, intersection cannot meet threshold
        if len(users1) < self.min_overlap or len(users2) < self.min_overlap:
            self.sim_cache[pair_key] = 0.0
            return 0.0

        set1 = self.item_users_sets.get(i1, set())
        set2 = self.item_users_sets.get(i2, set())
        common = set1.intersection(set2)
        if len(common) < self.min_overlap:
            self.sim_cache[pair_key] = 0.0
            return 0.0

        diff1 = np.array([users1[u] - self.user_means[u] for u in common], dtype=np.float64)
        diff2 = np.array([users2[u] - self.user_means[u] for u in common], dtype=np.float64)

        numerator = np.sum(diff1 * diff2)
        denom = np.sqrt(np.sum(diff1**2)) * np.sqrt(np.sum(diff2**2))

        if denom <= 1e-9:
            sim = 0.0
        else:
            sim = float(numerator / denom)

        self.sim_cache[pair_key] = sim
        return sim

    def predict(self, user_id: int, item_id: int) -> float:
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before predict.")

        if user_id not in self.user_ratings or item_id not in self.item_users:
            return float(np.clip(self._fallback_prediction(user_id, item_id), 1.0, 5.0))

        user_items = self.user_ratings[user_id]
        neighbors: List[Tuple[float, float]] = []

        for j, r_uj in user_items.items():
            if j == item_id:
                continue
            sim = self.compute_similarity(item_id, j)
            if sim > 0.0:
                neighbors.append((sim, r_uj))

        if not neighbors:
            return float(np.clip(self._fallback_prediction(user_id, item_id), 1.0, 5.0))

        neighbors.sort(key=lambda x: -x[0])
        top_k = neighbors[: self.k]

        sim_sum = sum(sim for sim, _ in top_k)
        if sim_sum <= 1e-9:
            return float(np.clip(self._fallback_prediction(user_id, item_id), 1.0, 5.0))

        weighted_sum = sum(sim * r_uj for sim, r_uj in top_k)
        pred = weighted_sum / sim_sum
        return float(np.clip(pred, 1.0, 5.0))

    def recommend(
        self,
        user_id: int,
        n: int = 10,
        exclude_seen: bool = True,
    ) -> List[Tuple[int, float]]:
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before recommend.")

        if user_id not in self.user_ratings:
            return super().recommend(user_id, n, exclude_seen)

        seen = self.user_seen_items.get(user_id, set()) if exclude_seen else set()
        candidates = [item for item in self.all_items if item not in seen]

        if not candidates:
            return []

        user_items = self.user_ratings[user_id]
        if not user_items:
            return super().recommend(user_id, n, exclude_seen)

        # Inverted index candidate pruning:
        # Identify candidate items that share at least 1 rater with the user's rated items.
        # Any candidate item with 0 co-raters has 0 overlap with all user items (sim=0),
        # so its neighbors list is guaranteed empty, directly yielding the fallback prediction.
        candidates_with_co_raters: Set[int] = set()
        for j in user_items:
            for v in self.item_users.get(j, {}):
                candidates_with_co_raters.update(self.user_ratings.get(v, {}).keys())
        candidates_with_co_raters.difference_update(seen)

        scores: List[Tuple[int, float]] = []

        for item in candidates:
            if item in candidates_with_co_raters:
                neighbors: List[Tuple[float, float]] = []
                for j, r_uj in user_items.items():
                    sim = self.compute_similarity(item, j)
                    if sim > 0.0:
                        neighbors.append((sim, r_uj))

                if not neighbors:
                    pred = self._fallback_prediction(user_id, item)
                else:
                    neighbors.sort(key=lambda x: -x[0])
                    top_k = neighbors[: self.k]
                    sim_sum = sum(s for s, _ in top_k)
                    if sim_sum <= 1e-9:
                        pred = self._fallback_prediction(user_id, item)
                    else:
                        weighted_sum = sum(s * r_uj for s, r_uj in top_k)
                        pred = weighted_sum / sim_sum
            else:
                pred = self._fallback_prediction(user_id, item)

            scores.append((item, float(np.clip(pred, 1.0, 5.0))))

        scores.sort(key=lambda x: (-x[1], x[0]))
        return scores[:n]
