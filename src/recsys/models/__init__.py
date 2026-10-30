"""
Models package for collaborative filtering.
"""

from src.recsys.models.base import BaseRecommender
from src.recsys.models.popularity import PopularityBaseline
from src.recsys.models.user_knn import UserKNNRecommender
from src.recsys.models.item_knn import ItemKNNRecommender
from src.recsys.models.svd import TruncatedSVDRecommender

__all__ = [
    "BaseRecommender",
    "PopularityBaseline",
    "UserKNNRecommender",
    "ItemKNNRecommender",
    "TruncatedSVDRecommender",
]
