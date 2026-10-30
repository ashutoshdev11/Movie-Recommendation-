"""
Truncated SVD Latent Factor Collaborative Filtering Recommender for MovieRec Version 2.
Scalable sparse matrix factorization for MovieLens 1M with k=30 factors and deterministic seeding.
"""

import os
from typing import Dict, List, Optional, Set, Tuple
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import svds

from .base import BaseRecommender


class TruncatedSVDRecommender(BaseRecommender):
    """
    Truncated SVD Recommender for user-item matrix factorization.
    
    Mathematical Formulation:
        R_centered = R - mu_u
        R_centered ≈ U * Sigma * V^T
        pred_rating(u, i) = clip(mu_u + (U * Sigma * V^T)_{u,i}, 1.0, 5.0)
        
    Args:
        n_factors: Number of latent dimensions k (default 30).
        random_state: Deterministic random seed for reproducibility (default 42).
    """

    def __init__(self, n_factors: int = 30, random_state: int = 42):
        super().__init__()
        self.n_factors = int(n_factors)
        self.random_state = int(random_state)

        # Mappings
        self.user2idx: Dict[int, int] = {}
        self.item2idx: Dict[int, int] = {}
        self.idx2user: Dict[int, int] = {}
        self.idx2item: Dict[int, int] = {}

        # Decomposed matrices
        self.U: Optional[np.ndarray] = None          # (n_users, n_factors)
        self.sigma: Optional[np.ndarray] = None      # (n_factors,)
        self.Vt: Optional[np.ndarray] = None         # (n_factors, n_items)
        self.user_means: Dict[int, float] = {}

    def fit(self, train_df: pd.DataFrame) -> "TruncatedSVDRecommender":
        self.global_mean = float(train_df["rating"].mean())
        self.all_users = sorted(train_df["user_id"].unique().tolist())
        self.all_items = sorted(train_df["movie_id"].unique().tolist())

        self.user2idx = {u: i for i, u in enumerate(self.all_users)}
        self.item2idx = {it: j for j, it in enumerate(self.all_items)}
        self.idx2user = {i: u for u, i in self.user2idx.items()}
        self.idx2item = {j: it for it, j in self.item2idx.items()}

        # Build user seen items
        self.user_seen_items = {}
        for uid, grp in train_df.groupby("user_id"):
            self.user_seen_items[int(uid)] = set(grp["movie_id"].tolist())

        # Compute per-user means
        user_sums = train_df.groupby("user_id")["rating"].sum()
        user_counts = train_df.groupby("user_id")["rating"].count()
        self.user_means = (user_sums / user_counts).to_dict()

        # Build centered sparse matrix
        rows = train_df["user_id"].map(self.user2idx).to_numpy()
        cols = train_df["movie_id"].map(self.item2idx).to_numpy()
        
        # Center ratings by subtracting user mean
        user_mean_arr = train_df["user_id"].map(self.user_means).to_numpy()
        centered_ratings = (train_df["rating"].to_numpy() - user_mean_arr).astype(np.float64)

        n_u = len(self.all_users)
        n_i = len(self.all_items)

        R_sparse = csr_matrix((centered_ratings, (rows, cols)), shape=(n_u, n_i))

        # Perform truncated SVD via SciPy ARPACK
        k = min(self.n_factors, min(n_u, n_i) - 1)
        U, s, Vt = svds(R_sparse, k=k, random_state=self.random_state)

        # ARPACK returns singular values in ascending order; reverse to descending
        idx_desc = np.argsort(-s)
        self.sigma = s[idx_desc]
        self.U = U[:, idx_desc]
        self.Vt = Vt[idx_desc, :]

        self.is_fitted = True
        return self

    def predict(self, user_id: int, item_id: int) -> float:
        if not self.is_fitted:
            raise RuntimeError("Model is not fitted.")

        if user_id not in self.user2idx:
            # Cold-start fallback to global mean
            return self.global_mean

        u_idx = self.user2idx[user_id]
        u_mean = self.user_means.get(user_id, self.global_mean)

        if item_id not in self.item2idx:
            # Unseen catalog item returns user mean
            return u_mean

        i_idx = self.item2idx[item_id]

        # Dot product: U[u, :] * sigma * Vt[:, i]
        user_vec = self.U[u_idx, :] * self.sigma
        item_vec = self.Vt[:, i_idx]
        pred_delta = float(np.dot(user_vec, item_vec))
        pred = u_mean + pred_delta
        return float(np.clip(pred, 1.0, 5.0))

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

        if user_id not in self.user2idx:
            # Unseen user: return items with highest global mean
            return [(it, self.global_mean) for it in self.all_items[:n]]

        u_idx = self.user2idx[user_id]
        u_mean = self.user_means.get(user_id, self.global_mean)
        seen = self.user_seen_items.get(user_id, set()) if exclude_seen else set()

        # Vectorized prediction across all catalog items
        user_factors = self.U[u_idx, :] * self.sigma  # (k,)
        scores = u_mean + np.dot(user_factors, self.Vt)  # (n_items,)
        scores = np.clip(scores, 1.0, 5.0)

        # Filter seen items
        candidates = []
        for j, item_id in enumerate(self.all_items):
            if item_id in seen:
                continue
            candidates.append((item_id, float(scores[j])))

        # Sort descending by score, tie-break by item_id ascending
        candidates.sort(key=lambda x: (-x[1], x[0]))
        return candidates[:n]

    def fold_in_profile(self, ratings: Dict[int, float], n: int = 10) -> List[Tuple[int, float]]:
        """
        Real-time SVD latent folding-in for a new user taste profile.
        
        Args:
            ratings: Dict mapping movie_id -> rating (1.0 to 5.0).
            n: Number of recommendations.
        """
        if not self.is_fitted or self.Vt is None:
            raise RuntimeError("Model is not fitted.")
        if not ratings:
            return []

        seen_items = set(ratings.keys())
        user_mean = float(np.mean(list(ratings.values())))

        # V matrix: (n_items, k)
        V = self.Vt.T
        x = np.zeros(len(self.all_items), dtype=np.float64)

        for item_id, r in ratings.items():
            if item_id in self.item2idx:
                idx = self.item2idx[item_id]
                x[idx] = float(r) - user_mean

        # Fold in: user latent factors p = x @ V
        p = np.dot(x, V)
        pred_delta = np.dot(p, self.Vt)
        pred_ratings = np.clip(user_mean + pred_delta, 1.0, 5.0)

        candidates = []
        for idx, item_id in enumerate(self.all_items):
            if item_id in seen_items:
                continue
            candidates.append((item_id, float(pred_ratings[idx])))

        candidates.sort(key=lambda x: (-x[1], x[0]))
        return candidates[:n]

    def save_artifacts(self, filepath: str) -> None:
        """Serialize fitted model arrays to compressed .npz archive."""
        if not self.is_fitted:
            raise RuntimeError("Cannot save unfitted model.")
        
        import json
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        users = np.array(self.all_users, dtype=np.int64)
        items = np.array(self.all_items, dtype=np.int64)
        user_means_arr = np.array([self.user_means[u] for u in users], dtype=np.float64)
        seen_json = json.dumps({int(u): list(items) for u, items in self.user_seen_items.items()})

        np.savez_compressed(
            filepath,
            U=self.U,
            sigma=self.sigma,
            Vt=self.Vt,
            users=users,
            items=items,
            user_means=user_means_arr,
            global_mean=np.array(self.global_mean),
            n_factors=np.array(self.n_factors),
            random_state=np.array(self.random_state),
            user_seen_json=np.array(seen_json),
        )

    @classmethod
    def load_artifacts(cls, filepath: str) -> "TruncatedSVDRecommender":
        """Deserialize model from .npz archive."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Artifact not found at {filepath}")

        import json
        data = np.load(filepath)
        n_factors = int(data["n_factors"])
        random_state = int(data["random_state"])

        model = cls(n_factors=n_factors, random_state=random_state)
        model.U = data["U"]
        model.sigma = data["sigma"]
        model.Vt = data["Vt"]
        model.global_mean = float(data["global_mean"])
        model.all_users = data["users"].tolist()
        model.all_items = data["items"].tolist()

        model.user2idx = {u: i for i, u in enumerate(model.all_users)}
        model.item2idx = {it: j for j, it in enumerate(model.all_items)}
        model.idx2user = {i: u for u, i in model.user2idx.items()}
        model.idx2item = {j: it for it, j in model.item2idx.items()}

        user_means_arr = data["user_means"]
        model.user_means = {u: float(user_means_arr[i]) for i, u in enumerate(model.all_users)}

        if "user_seen_json" in data:
            raw_seen = json.loads(str(data["user_seen_json"]))
            model.user_seen_items = {int(u): set(items) for u, items in raw_seen.items()}

        model.is_fitted = True
        return model
