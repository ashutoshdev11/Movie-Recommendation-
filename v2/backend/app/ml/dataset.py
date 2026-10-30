"""
MovieLens 1M Ingestion, Validation, and Leakage-Proof Chronological Splitting.
Designed for MovieRec Version 2 (Standalone ML-1M Pipeline).
"""

from dataclasses import dataclass
import json
import os
import re
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

# MovieLens 1M Genre Definitions
ML_1M_GENRES = [
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


@dataclass(frozen=True)
class DatasetSplits:
    """Holds chronological train, validation, and test partitions."""
    train: pd.DataFrame
    val: pd.DataFrame
    test: pd.DataFrame

    def summary(self) -> Dict[str, int]:
        return {
            "train_ratings": len(self.train),
            "val_ratings": len(self.val),
            "test_ratings": len(self.test),
            "total_ratings": len(self.train) + len(self.val) + len(self.test),
        }


def get_default_raw_dir() -> str:
    """Return default directory path for raw ML-1M files."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_dir, "data", "raw", "ml-1m")


def get_default_processed_dir() -> str:
    """Return default directory path for processed ML-1M files."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_dir, "data", "processed")


def load_raw_ratings(data_dir: Optional[str] = None) -> pd.DataFrame:
    """
    Load and validate ratings.dat from MovieLens 1M.
    
    Columns:
        user_id (int64)
        movie_id (int64)
        rating (float64, 1.0 to 5.0)
        timestamp (int64)
    """
    path = os.path.join(data_dir or get_default_raw_dir(), "ratings.dat")
    if not os.path.exists(path):
        raise FileNotFoundError(f"ratings.dat not found at {path}")

    df = pd.read_csv(
        path,
        sep="::",
        names=["user_id", "movie_id", "rating", "timestamp"],
        engine="python",
        dtype={
            "user_id": np.int64,
            "movie_id": np.int64,
            "rating": np.float64,
            "timestamp": np.int64,
        },
    )

    # Validation
    if df.isnull().any().any():
        raise ValueError("Missing values detected in ratings.dat")
    if not df["rating"].between(1.0, 5.0).all():
        raise ValueError("Ratings contain values outside [1.0, 5.0]")
    
    # Check duplicate user-movie pairs
    duplicates = df.duplicated(subset=["user_id", "movie_id"]).sum()
    if duplicates > 0:
        raise ValueError(f"Found {duplicates} duplicate (user_id, movie_id) pairs in ratings.dat")

    return df


def load_raw_movies(data_dir: Optional[str] = None) -> pd.DataFrame:
    """
    Load and parse movies.dat from MovieLens 1M with release year and genre extraction.
    
    Columns:
        movie_id (int64)
        title (str, cleaned)
        raw_title (str)
        year (Optional[int])
        genres (List[str])
        + binary 0/1 column for each genre in ML_1M_GENRES
    """
    path = os.path.join(data_dir or get_default_raw_dir(), "movies.dat")
    if not os.path.exists(path):
        raise FileNotFoundError(f"movies.dat not found at {path}")

    df = pd.read_csv(
        path,
        sep="::",
        names=["movie_id", "raw_title", "genres_str"],
        engine="python",
        encoding="latin-1",
        dtype={"movie_id": np.int64, "raw_title": str, "genres_str": str},
    )

    clean_titles = []
    years = []
    genre_lists = []

    year_pattern = re.compile(r"\s*\((\d{4})\)\s*$")

    for _, row in df.iterrows():
        raw_title = str(row["raw_title"]).strip()
        match = year_pattern.search(raw_title)
        if match:
            year = int(match.group(1))
            clean_title = raw_title[:match.start()].strip()
        else:
            year = None
            clean_title = raw_title
        
        # Remove trailing articles e.g. "Matrix, The" -> "The Matrix"
        article_match = re.search(r"^(.*),\s*(The|A|An|Le|La|Les|Der|Die|Das|Il|El|Los|Las)$", clean_title, re.IGNORECASE)
        if article_match:
            clean_title = f"{article_match.group(2)} {article_match.group(1)}"

        clean_titles.append(clean_title)
        years.append(year)

        genres = [g.strip() for g in str(row["genres_str"]).split("|") if g.strip()]
        genre_lists.append(genres)

    df["title"] = clean_titles
    df["year"] = years
    df["genres"] = genre_lists

    # Create one-hot genre columns
    for g in ML_1M_GENRES:
        df[g] = df["genres"].apply(lambda glist: 1 if g in glist else 0)

    return df


def load_raw_users(data_dir: Optional[str] = None) -> pd.DataFrame:
    """
    Load users.dat from MovieLens 1M.
    
    Columns:
        user_id (int64)
        gender (str, 'M' or 'F')
        age (int)
        occupation (int)
        zip_code (str)
    """
    path = os.path.join(data_dir or get_default_raw_dir(), "users.dat")
    if not os.path.exists(path):
        raise FileNotFoundError(f"users.dat not found at {path}")

    df = pd.read_csv(
        path,
        sep="::",
        names=["user_id", "gender", "age", "occupation", "zip_code"],
        engine="python",
        dtype={
            "user_id": np.int64,
            "gender": str,
            "age": np.int32,
            "occupation": np.int32,
            "zip_code": str,
        },
    )
    return df


def compute_dataset_statistics(
    ratings_df: pd.DataFrame,
    movies_df: pd.DataFrame,
    users_df: pd.DataFrame,
) -> Dict:
    """
    Compute comprehensive dataset statistics for ML-1M.
    """
    n_ratings = len(ratings_df)
    n_users = ratings_df["user_id"].nunique()
    n_movies = ratings_df["movie_id"].nunique()
    total_catalog_movies = len(movies_df)

    user_counts = ratings_df.groupby("user_id").size()
    movie_counts = ratings_df.groupby("movie_id").size()

    sparsity = 1.0 - (n_ratings / (n_users * total_catalog_movies))

    rating_dist = ratings_df["rating"].value_counts().sort_index().to_dict()
    rating_percentages = {float(k): round((v / n_ratings) * 100, 2) for k, v in rating_dist.items()}

    genre_counts = {}
    for g in ML_1M_GENRES:
        genre_counts[g] = int(movies_df[g].sum())

    stats = {
        "dataset_name": "MovieLens 1M (ml-1m)",
        "total_ratings": int(n_ratings),
        "total_rated_movies": int(n_movies),
        "total_catalog_movies": int(total_catalog_movies),
        "total_users": int(n_users),
        "total_demographic_users": int(len(users_df)),
        "global_rating_mean": float(round(ratings_df["rating"].mean(), 4)),
        "global_rating_std": float(round(ratings_df["rating"].std(), 4)),
        "sparsity": float(round(sparsity, 6)),
        "rating_distribution_counts": {float(k): int(v) for k, v in rating_dist.items()},
        "rating_distribution_pct": rating_percentages,
        "user_activity": {
            "min": int(user_counts.min()),
            "max": int(user_counts.max()),
            "median": float(user_counts.median()),
            "mean": float(round(user_counts.mean(), 2)),
        },
        "movie_popularity": {
            "min": int(movie_counts.min()),
            "max": int(movie_counts.max()),
            "median": float(movie_counts.median()),
            "mean": float(round(movie_counts.mean(), 2)),
        },
        "genre_counts": genre_counts,
    }
    return stats


def chronological_split(
    ratings_df: pd.DataFrame,
    train_frac: float = 0.60,
    val_frac: float = 0.20,
    min_ratings: int = 5,
) -> DatasetSplits:
    """
    Partition user ratings chronologically per user to strictly prevent future-to-past temporal leakage.
    
    Invariant guaranteed:
        max(timestamp_train) <= min(timestamp_val) <= max(timestamp_val) <= min(timestamp_test)
        
    Args:
        ratings_df: Raw ratings DataFrame.
        train_frac: Fraction of user interactions for training (default 0.60).
        val_frac: Fraction of user interactions for validation (default 0.20).
        min_ratings: Minimum interactions per user required for splitting.
        
    Returns:
        DatasetSplits dataclass containing train, val, and test DataFrames.
    """
    if not (0.0 < train_frac < 1.0 and 0.0 < val_frac < 1.0 and (train_frac + val_frac) < 1.0):
        raise ValueError("Fractions must be positive and train_frac + val_frac must be < 1.0")

    # Sort strictly by user_id and timestamp ascending, with deterministic tie-breaker on movie_id
    sorted_df = ratings_df.sort_values(
        by=["user_id", "timestamp", "movie_id"],
        ascending=[True, True, True],
    ).reset_index(drop=True)

    train_indices = []
    val_indices = []
    test_indices = []

    # Group by user and assign temporal slices
    for user_id, group in sorted_df.groupby("user_id", sort=False):
        n = len(group)
        indices = group.index.to_numpy()

        if n < min_ratings:
            # Users with very few interactions are retained entirely in train
            train_indices.extend(indices)
            continue

        n_train = max(1, int(np.floor(n * train_frac)))
        n_val = max(1, int(np.floor(n * val_frac)))

        # Ensure train + val does not consume all ratings
        if n_train + n_val >= n:
            n_val = max(1, n - n_train - 1)

        idx_train = indices[:n_train]
        idx_val = indices[n_train : n_train + n_val]
        idx_test = indices[n_train + n_val :]

        train_indices.extend(idx_train)
        val_indices.extend(idx_val)
        test_indices.extend(idx_test)

    train_df = sorted_df.iloc[train_indices].reset_index(drop=True)
    val_df = sorted_df.iloc[val_indices].reset_index(drop=True)
    test_df = sorted_df.iloc[test_indices].reset_index(drop=True)

    return DatasetSplits(train=train_df, val=val_df, test=test_df)


def run_pipeline_and_export() -> Tuple[DatasetSplits, Dict]:
    """Execute full data loading, validation, splitting, and artifact export."""
    raw_dir = get_default_raw_dir()
    proc_dir = get_default_processed_dir()
    os.makedirs(proc_dir, exist_ok=True)

    print("[ML-1M Pipeline] Loading raw tables...")
    ratings = load_raw_ratings(raw_dir)
    movies = load_raw_movies(raw_dir)
    users = load_raw_users(raw_dir)

    print("[ML-1M Pipeline] Computing dataset statistics...")
    stats = compute_dataset_statistics(ratings, movies, users)

    print("[ML-1M Pipeline] Performing chronological train/val/test split (60/20/20)...")
    splits = chronological_split(ratings, train_frac=0.60, val_frac=0.20)

    # Save processed splits and metadata to disk
    train_path = os.path.join(proc_dir, "train_ratings.csv.gz")
    val_path = os.path.join(proc_dir, "val_ratings.csv.gz")
    test_path = os.path.join(proc_dir, "test_ratings.csv.gz")
    movies_path = os.path.join(proc_dir, "movies_metadata.csv.gz")
    stats_path = os.path.join(proc_dir, "dataset_statistics.json")

    splits.train.to_csv(train_path, index=False, compression="gzip")
    splits.val.to_csv(val_path, index=False, compression="gzip")
    splits.test.to_csv(test_path, index=False, compression="gzip")
    movies.to_csv(movies_path, index=False, compression="gzip")

    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    print(f"[ML-1M Pipeline] Processed datasets successfully exported to: {proc_dir}")
    print(f"  • Train ratings: {len(splits.train):,}")
    print(f"  • Val ratings:   {len(splits.val):,}")
    print(f"  • Test ratings:  {len(splits.test):,}")
    print(f"  • Total ratings: {len(ratings):,}")

    return splits, stats


if __name__ == "__main__":
    run_pipeline_and_export()
