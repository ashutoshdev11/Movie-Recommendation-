"""
Data loading, validation, and preprocessing for MovieLens 100K.
"""

from dataclasses import dataclass
import os
from typing import Optional
import numpy as np
import pandas as pd

GENRE_COLUMNS = [
    "unknown",
    "Action",
    "Adventure",
    "Animation",
    "Children's",
    "Comedy",
    "Crime",
    "Documentary",
    "Drama",
    "Fantasy",
    "Film-Noir",
    "Horror",
    "Musical",
    "Mystery",
    "Romance",
    "Sci-Fi",
    "Thriller",
    "War",
    "Western",
]


@dataclass
class ValidationReport:
    total_ratings: int
    unique_users: int
    unique_movies: int
    sparsity: float
    rating_min: int
    rating_max: int
    duplicate_user_item_pairs: int
    missing_ratings: int
    is_valid: bool
    summary: str


def get_default_data_dir() -> str:
    """Return the default path to data/raw/ml-100k."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_dir, "data", "raw", "ml-100k")


def load_ratings(data_dir: Optional[str] = None) -> pd.DataFrame:
    """Load u.data into a pandas DataFrame."""
    if data_dir is None:
        data_dir = get_default_data_dir()
    filepath = os.path.join(data_dir, "u.data")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Ratings file not found at: {filepath}")

    names = ["user_id", "item_id", "rating", "timestamp"]
    dtypes = {
        "user_id": np.int64,
        "item_id": np.int64,
        "rating": np.int64,
        "timestamp": np.int64,
    }
    df = pd.read_csv(filepath, sep="\t", names=names, dtype=dtypes, engine="c")
    return df


def load_movies(data_dir: Optional[str] = None) -> pd.DataFrame:
    """Load u.item into a pandas DataFrame with genre indicator flags."""
    if data_dir is None:
        data_dir = get_default_data_dir()
    filepath = os.path.join(data_dir, "u.item")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Movies file not found at: {filepath}")

    names = [
        "item_id",
        "title",
        "release_date",
        "video_release_date",
        "imdb_url",
    ] + GENRE_COLUMNS

    df = pd.read_csv(
        filepath,
        sep="|",
        names=names,
        encoding="latin-1",
        engine="python",
    )
    df["item_id"] = df["item_id"].astype(np.int64)
    for g in GENRE_COLUMNS:
        df[g] = df[g].astype(np.int64)
    return df


def load_users(data_dir: Optional[str] = None) -> pd.DataFrame:
    """Load u.user into a pandas DataFrame."""
    if data_dir is None:
        data_dir = get_default_data_dir()
    filepath = os.path.join(data_dir, "u.user")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Users file not found at: {filepath}")

    names = ["user_id", "age", "gender", "occupation", "zip_code"]
    dtypes = {
        "user_id": np.int64,
        "age": np.int64,
        "gender": str,
        "occupation": str,
        "zip_code": str,
    }
    df = pd.read_csv(filepath, sep="|", names=names, dtype=dtypes, engine="c")
    return df


def validate_dataset(
    ratings: pd.DataFrame,
    movies: pd.DataFrame,
    users: pd.DataFrame,
) -> ValidationReport:
    """
    Validate schema, counts, value ranges, duplicate records,
    integrity across ID keys, and calculate matrix sparsity.
    """
    total_ratings = len(ratings)
    unique_users = ratings["user_id"].nunique()
    unique_movies = ratings["item_id"].nunique()

    # Sparsity = 1 - (|Ratings| / (|Users| * |Items|))
    total_catalog_users = len(users)
    total_catalog_movies = len(movies)
    sparsity = 1.0 - (total_ratings / (total_catalog_users * total_catalog_movies))

    rating_min = int(ratings["rating"].min())
    rating_max = int(ratings["rating"].max())
    duplicate_pairs = int(ratings.duplicated(subset=["user_id", "item_id"]).sum())
    missing_ratings = int(ratings[["user_id", "item_id", "rating", "timestamp"]].isna().sum().sum())

    # Check ID consistency
    user_ids_in_ratings = set(ratings["user_id"])
    catalog_user_ids = set(users["user_id"])
    users_valid = user_ids_in_ratings.issubset(catalog_user_ids)

    item_ids_in_ratings = set(ratings["item_id"])
    catalog_item_ids = set(movies["item_id"])
    items_valid = item_ids_in_ratings.issubset(catalog_item_ids)

    # Ratings range valid
    range_valid = (rating_min >= 1) and (rating_max <= 5) and (ratings["rating"].dtype in [np.int64, int])

    is_valid = (
        (total_ratings == 100000)
        and (unique_users == 943)
        and (unique_movies == 1682)
        and (duplicate_pairs == 0)
        and (missing_ratings == 0)
        and users_valid
        and items_valid
        and range_valid
    )

    summary = (
        f"Validation: Ratings={total_ratings}, Users={unique_users}, Items={unique_movies}, "
        f"Sparsity={sparsity*100:.2f}%, Duplicates={duplicate_pairs}, Missing={missing_ratings}, "
        f"Ratings Range=[{rating_min}, {rating_max}], Valid={is_valid}"
    )

    return ValidationReport(
        total_ratings=total_ratings,
        unique_users=unique_users,
        unique_movies=unique_movies,
        sparsity=sparsity,
        rating_min=rating_min,
        rating_max=rating_max,
        duplicate_user_item_pairs=duplicate_pairs,
        missing_ratings=missing_ratings,
        is_valid=is_valid,
        summary=summary,
    )
