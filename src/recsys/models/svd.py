"""
Truncated SVD matrix factorization benchmark using SciPy sparse linear algebra.
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import svds
from src.recsys.models.base import BaseRecommender


class TruncatedSVDRecommender(BaseRecommender):
    """
    Truncated SVD Matrix Factorization Recommender.
    Centers observed ratings by subtracting the user mean:
        r_tilde(u, i) = r(u, i) - mean_u
    Preserves sparse matrix representation (unobserved entries stay 0).
    Decomposes R_tilde via scipy.sparse.linalg.svds into U, Sigma, Vt.
    Prediction:
        r_hat(u, i) = mean_u + (U * Sigma * Vt)[u, i]
    """

    def __init__(self, n_factors: int = 20, random_state: int = 42) -> None:
        super().__init__()
        self.n_factors: int = int(n_factors)
        self.random_state: int = int(random_state)

        # Latent factor matrices
        self.U: Optional[np.ndarray] = None
        self.sigma: Optional[np.ndarray] = None
        self.Vt: Optional[np.ndarray] = None

    def fit(self, train_ratings: pd.DataFrame) -> "TruncatedSVDRecommender":
        self._init_base_statistics(train_ratings)

        n_users = len(self.user2idx)
        n_items = len(self.item2idx)

        # Center observed entries by subtracting user mean
        rows = [self.user2idx[u] for u in train_ratings["user_id"]]
        cols = [self.item2idx[i] for i in train_ratings["item_id"]]
        ratings_data = train_ratings["rating"].values.astype(np.float64)
        user_means_vec = np.array([self.user_means[u] for u in train_ratings["user_id"]], dtype=np.float64)

        centered_data = ratings_data - user_means_vec
        sparse_centered = csr_matrix((centered_data, (rows, cols)), shape=(n_users, n_items), dtype=np.float64)

        # Ensure k is strictly less than min(shape)
        max_factors = min(n_users, n_items) - 1
        k = max(1, min(self.n_factors, max_factors))

        # Truncated SVD using fixed random seed
        U, s, Vt = svds(sparse_centered, k=k, random_state=self.random_state)

        # Sort singular values in descending order
        sort_indices = np.argsort(s)[::-1]
        self.U = U[:, sort_indices]
        self.sigma = s[sort_indices]
        self.Vt = Vt[sort_indices, :]

        self.is_fitted = True
        return self

    def predict(self, user_id: int, item_id: int) -> float:
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before predict.")

        # Fallback for unknown user or unknown item
        if user_id not in self.user2idx or item_id not in self.item2idx:
            return float(np.clip(self._fallback_prediction(user_id, item_id), 1.0, 5.0))

        u_idx = self.user2idx[user_id]
        i_idx = self.item2idx[item_id]

        # Inner product of latent factor representation: U[u] * diag(sigma) * Vt[:, i]
        latent_score = np.dot(self.U[u_idx, :] * self.sigma, self.Vt[:, i_idx])
        pred = self.user_means[user_id] + float(latent_score)
        return float(np.clip(pred, 1.0, 5.0))

    def recommend(
        self,
        user_id: int,
        n: int = 10,
        exclude_seen: bool = True,
    ) -> List[Tuple[int, float]]:
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before recommend.")

        if user_id not in self.user2idx:
            # Fall back to base class implementation (fallback predictions)
            return super().recommend(user_id, n, exclude_seen)

        u_idx = self.user2idx[user_id]
        seen = self.user_seen_items.get(user_id, set()) if exclude_seen else set()

        # Vectorized prediction across all catalog items
        user_vector = self.U[u_idx, :] * self.sigma
        latent_scores = np.dot(user_vector, self.Vt)
        full_scores = self.user_means[user_id] + latent_scores
        clipped_scores = np.clip(full_scores, 1.0, 5.0)

        candidate_scores: List[Tuple[int, float]] = []
        for idx, score in enumerate(clipped_scores):
            item_id = self.idx2item[idx]
            if item_id not in seen:
                candidate_scores.append((item_id, float(score)))

        # Sort descending by score, ascending by item_id as tiebreaker
        candidate_scores.sort(key=lambda x: (-x[1], x[0]))
        return candidate_scores[:n]
