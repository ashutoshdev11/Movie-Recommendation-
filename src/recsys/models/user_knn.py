"""
User-based Collaborative Filtering using k-Nearest Neighbors and Pearson correlation.
"""

from typing import Dict, List, Optional, Set, Tuple
import numpy as np
import pandas as pd
from src.recsys.models.base import BaseRecommender


class UserKNNRecommender(BaseRecommender):
    """
    User-based Collaborative Filtering Recommender.
    Computes Pearson correlation over mean-centred ratings on co-rated items:
        r_hat(u, i) = mean_u + sum_v s(u, v) * (r_vi - mean_v) / sum_v |s(u, v)|
    Fallback chain when neighbours are insufficient: item mean -> user mean -> global mean.
    """

    def __init__(self, k: int = 20, min_overlap: int = 2) -> None:
        super().__init__()
        self.k: int = int(k)
        self.min_overlap: int = int(min_overlap)

        # Mapping: user_id -> dict of {item_id: rating}
        self.user_ratings: Dict[int, Dict[int, float]] = {}
        # Mapping: item_id -> dict of {user_id: rating}
        self.item_users: Dict[int, Dict[int, float]] = {}
        # Precomputed pairwise similarities cache: (u1, u2) -> similarity
        self.sim_cache: Dict[Tuple[int, int], float] = {}

    def fit(self, train_ratings: pd.DataFrame) -> "UserKNNRecommender":
        self._init_base_statistics(train_ratings)

        self.user_ratings = {}
        self.item_users = {}
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

        self.is_fitted = True
        return self

    def compute_similarity(self, u1: int, u2: int) -> float:
        if u1 == u2:
            return 1.0

        pair_key = (min(u1, u2), max(u1, u2))
        if pair_key in self.sim_cache:
            return self.sim_cache[pair_key]

        items1 = self.user_ratings.get(u1, {})
        items2 = self.user_ratings.get(u2, {})

        common = set(items1.keys()).intersection(items2.keys())
        if len(common) < self.min_overlap:
            self.sim_cache[pair_key] = 0.0
            return 0.0

        mu1 = self.user_means[u1]
        mu2 = self.user_means[u2]

        diff1 = np.array([items1[i] - mu1 for i in common], dtype=np.float64)
        diff2 = np.array([items2[i] - mu2 for i in common], dtype=np.float64)

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

        raters = self.item_users[item_id]
        neighbors: List[Tuple[float, float, float]] = []

        for v, r_vi in raters.items():
            if v == user_id:
                continue
            sim = self.compute_similarity(user_id, v)
            if sim > 0.0:
                neighbors.append((sim, r_vi, self.user_means[v]))

        if not neighbors:
            return float(np.clip(self._fallback_prediction(user_id, item_id), 1.0, 5.0))

        neighbors.sort(key=lambda x: -x[0])
        top_k = neighbors[: self.k]

        sim_sum = sum(sim for sim, _, _ in top_k)
        if sim_sum <= 1e-9:
            return float(np.clip(self._fallback_prediction(user_id, item_id), 1.0, 5.0))

        weighted_delta = sum(sim * (r_vi - mu_v) for sim, r_vi, mu_v in top_k)
        pred = self.user_means[user_id] + (weighted_delta / sim_sum)
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

        # Precompute similarities to all co-raters once for user_id
        # Candidate neighbors are users who co-rated at least one item with user_id
        my_items = set(self.user_ratings[user_id].keys())
        potential_neighbors = set()
        for i in my_items:
            potential_neighbors.update(self.item_users.get(i, {}).keys())
        potential_neighbors.discard(user_id)

        # Precompute positive similarities
        positive_neighbors = []
        for v in potential_neighbors:
            sim = self.compute_similarity(user_id, v)
            if sim > 0.0:
                positive_neighbors.append((v, sim, self.user_means[v]))

        scores: List[Tuple[int, float]] = []
        if not positive_neighbors:
            for item in candidates:
                scores.append((item, float(np.clip(self._fallback_prediction(user_id, item), 1.0, 5.0))))
        else:
            for item in candidates:
                raters = self.item_users.get(item, {})
                item_neighbors = [
                    (sim, raters[v], mu_v)
                    for v, sim, mu_v in positive_neighbors
                    if v in raters
                ]
                if not item_neighbors:
                    pred = self._fallback_prediction(user_id, item)
                else:
                    item_neighbors.sort(key=lambda x: -x[0])
                    top_k = item_neighbors[: self.k]
                    sim_sum = sum(s for s, _, _ in top_k)
                    if sim_sum <= 1e-9:
                        pred = self._fallback_prediction(user_id, item)
                    else:
                        weighted_delta = sum(s * (r_vi - mu_v) for s, r_vi, mu_v in top_k)
                        pred = self.user_means[user_id] + (weighted_delta / sim_sum)
                scores.append((item, float(np.clip(pred, 1.0, 5.0))))

        scores.sort(key=lambda x: (-x[1], x[0]))
        return scores[:n]
