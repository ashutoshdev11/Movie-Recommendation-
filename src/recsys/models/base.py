"""
Base recommender interface and shared collaborative-filtering utilities.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Set, Tuple
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix


class BaseRecommender(ABC):
    """
    Abstract base class for all collaborative filtering models.
    Enforces the fit, predict, and recommend contract.
    """

    def __init__(self) -> None:
        self.is_fitted: bool = False
        self.global_mean: float = 3.5
        self.user_means: Dict[int, float] = {}
        self.item_means: Dict[int, float] = {}
        self.user_ratings_count: Dict[int, int] = {}
        self.item_ratings_count: Dict[int, int] = {}
        self.user_seen_items: Dict[int, Set[int]] = {}
        self.all_items: List[int] = []

        # Internal ID mappers
        self.user2idx: Dict[int, int] = {}
        self.idx2user: Dict[int, int] = {}
        self.item2idx: Dict[int, int] = {}
        self.idx2item: Dict[int, int] = {}

    def _init_base_statistics(self, train_ratings: pd.DataFrame) -> None:
        """Compute base means, frequencies, mappings, and CSR representations."""
        if train_ratings.empty:
            raise ValueError("Training DataFrame cannot be empty.")

        self.global_mean = float(train_ratings["rating"].mean())

        # Group means and counts
        user_grouped = train_ratings.groupby("user_id")["rating"]
        self.user_means = user_grouped.mean().to_dict()
        self.user_ratings_count = user_grouped.count().to_dict()

        item_grouped = train_ratings.groupby("item_id")["rating"]
        self.item_means = item_grouped.mean().to_dict()
        self.item_ratings_count = item_grouped.count().to_dict()

        # Seen items per user
        self.user_seen_items = (
            train_ratings.groupby("user_id")["item_id"].apply(lambda s: set(s)).to_dict()
        )
        self.all_items = sorted(train_ratings["item_id"].unique().tolist())

        # ID mappers
        unique_users = sorted(train_ratings["user_id"].unique().tolist())
        self.user2idx = {u: idx for idx, u in enumerate(unique_users)}
        self.idx2user = {idx: u for idx, u in enumerate(unique_users)}
        self.item2idx = {i: idx for idx, i in enumerate(self.all_items)}
        self.idx2item = {idx: i for idx, i in enumerate(self.all_items)}

    def _build_sparse_matrix(self, train_ratings: pd.DataFrame) -> csr_matrix:
        """Build a SciPy CSR user-item matrix where missing entries are unobserved."""
        rows = [self.user2idx[u] for u in train_ratings["user_id"]]
        cols = [self.item2idx[i] for i in train_ratings["item_id"]]
        data = train_ratings["rating"].values.astype(np.float64)
        shape = (len(self.user2idx), len(self.item2idx))
        return csr_matrix((data, (rows, cols)), shape=shape, dtype=np.float64)

    def _fallback_prediction(self, user_id: int, item_id: int) -> float:
        """Fallback chain: item mean -> user mean -> global mean."""
        if item_id in self.item_means:
            return self.item_means[item_id]
        if user_id in self.user_means:
            return self.user_means[user_id]
        return self.global_mean

    @abstractmethod
    def fit(self, train_ratings: pd.DataFrame) -> "BaseRecommender":
        """Fit model parameters exclusively from train_ratings."""
        pass

    @abstractmethod
    def predict(self, user_id: int, item_id: int) -> float:
        """Predict rating bounded in [1.0, 5.0] with graceful fallback."""
        pass

    def recommend(
        self,
        user_id: int,
        n: int = 10,
        exclude_seen: bool = True,
    ) -> List[Tuple[int, float]]:
        """
        Generate top-n recommendations for user_id.
        - Unseen items only when exclude_seen=True.
        - Deterministic secondary sort on item_id to break score ties.
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before generating recommendations.")

        seen = self.user_seen_items.get(user_id, set()) if exclude_seen else set()
        candidates = [item for item in self.all_items if item not in seen]

        if not candidates:
            return []

        # Score all candidate items
        scores: List[Tuple[int, float]] = []
        for item_id in candidates:
            score = self.predict(user_id, item_id)
            scores.append((item_id, float(score)))

        # Sort descending by score, ascending by item_id as tiebreaker
        scores.sort(key=lambda x: (-x[1], x[0]))
        return scores[:n]
