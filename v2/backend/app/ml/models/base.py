"""
Abstract base class defining the common recommender interface for MovieRec Version 2.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Set, Tuple
import pandas as pd


class BaseRecommender(ABC):
    """Abstract base class for all V2 collaborative filtering and baseline recommenders."""

    def __init__(self):
        self.is_fitted: bool = False
        self.all_users: List[int] = []
        self.all_items: List[int] = []
        self.user_seen_items: Dict[int, Set[int]] = {}
        self.global_mean: float = 3.5

    @abstractmethod
    def fit(self, train_df: pd.DataFrame) -> "BaseRecommender":
        """Fit model parameters on the training DataFrame."""
        pass

    @abstractmethod
    def predict(self, user_id: int, item_id: int) -> float:
        """Predict the rating score for a (user, item) pair, clipped to [1.0, 5.0]."""
        pass

    @abstractmethod
    def recommend(
        self,
        user_id: int,
        n: int = 10,
        exclude_seen: bool = True,
    ) -> List[Tuple[int, float]]:
        """
        Generate top-N recommended item IDs and predicted scores for user_id.
        
        Returns:
            List of (item_id, predicted_score) sorted descending by score with deterministic tie-breaking.
        """
        pass
