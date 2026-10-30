"""
Automated tests for MovieRec Version 2 - MovieLens 1M Ingestion & Splitting.
Verifies data schema, integrity, chronological partitioning, and temporal leakage prevention.
"""

import os
import sys
import numpy as np
import pandas as pd
import pytest

# Ensure v2 backend is in sys.path
V2_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if V2_BACKEND_DIR not in sys.path:
    sys.path.insert(0, V2_BACKEND_DIR)

from app.ml.dataset import (
    load_raw_ratings,
    load_raw_movies,
    load_raw_users,
    compute_dataset_statistics,
    chronological_split,
    get_default_raw_dir,
    get_default_processed_dir,
    ML_1M_GENRES,
)


@pytest.fixture(scope="module")
def raw_data_dir():
    return get_default_raw_dir()


@pytest.fixture(scope="module")
def ratings_df(raw_data_dir):
    return load_raw_ratings(raw_data_dir)


@pytest.fixture(scope="module")
def movies_df(raw_data_dir):
    return load_raw_movies(raw_data_dir)


@pytest.fixture(scope="module")
def users_df(raw_data_dir):
    return load_raw_users(raw_data_dir)


def test_ratings_raw_dimensions_and_types(ratings_df):
    """Verify ML-1M exact ratings volume and data types."""
    assert len(ratings_df) == 1_000_209
    assert ratings_df["user_id"].nunique() == 6040
    assert ratings_df["movie_id"].nunique() == 3706
    
    # Types
    assert ratings_df["user_id"].dtype == np.int64
    assert ratings_df["movie_id"].dtype == np.int64
    assert ratings_df["rating"].dtype == np.float64
    assert ratings_df["timestamp"].dtype == np.int64


def test_ratings_integrity_and_bounds(ratings_df):
    """Verify that ratings are bounded in [1.0, 5.0] and contain no nulls or duplicates."""
    assert not ratings_df.isnull().any().any()
    assert ratings_df["rating"].min() == 1.0
    assert ratings_df["rating"].max() == 5.0
    
    # Ensure zero duplicate (user_id, movie_id) pairs
    duplicates = ratings_df.duplicated(subset=["user_id", "movie_id"]).sum()
    assert duplicates == 0


def test_movies_schema_and_year_parsing(movies_df):
    """Verify movie catalog dimensions, parsed release years, and genre indicators."""
    assert len(movies_df) == 3883
    assert movies_df["movie_id"].nunique() == 3883
    
    # Check that release years are within sensible range
    valid_years = movies_df["year"].dropna()
    assert len(valid_years) >= 3880  # Almost all titles have standard (YYYY)
    assert valid_years.min() >= 1919
    assert valid_years.max() <= 2001
    
    # Check genres
    for g in ML_1M_GENRES:
        assert g in movies_df.columns
        assert set(movies_df[g].unique()).issubset({0, 1})


def test_users_demographics_schema(users_df):
    """Verify demographic user table structure."""
    assert len(users_df) == 6040
    assert set(users_df["gender"].unique()) == {"M", "F"}
    assert users_df["age"].min() >= 1
    assert users_df["occupation"].min() >= 0


def test_dataset_statistics_computation(ratings_df, movies_df, users_df):
    """Verify statistics calculation matches MovieLens 1M published benchmark values."""
    stats = compute_dataset_statistics(ratings_df, movies_df, users_df)
    assert stats["total_ratings"] == 1_000_209
    assert stats["total_users"] == 6040
    assert stats["total_catalog_movies"] == 3883
    assert abs(stats["global_rating_mean"] - 3.5816) < 0.001
    assert abs(stats["sparsity"] - 0.957353) < 0.0001
    assert stats["user_activity"]["min"] == 20  # ML-1M criterion: each user has >= 20 ratings


def test_chronological_split_partition_sizes(ratings_df):
    """Verify 60/20/20 chronological partition sizes and mutual exclusivity."""
    splits = chronological_split(ratings_df, train_frac=0.60, val_frac=0.20)
    
    n_train = len(splits.train)
    n_val = len(splits.val)
    n_test = len(splits.test)
    total = len(ratings_df)
    
    assert n_train + n_val + n_test == total
    assert abs((n_train / total) - 0.60) < 0.02
    assert abs((n_val / total) - 0.20) < 0.02
    assert abs((n_test / total) - 0.20) < 0.02
    
    # Every single user must be present in train
    assert splits.train["user_id"].nunique() == 6040


def test_temporal_leakage_prevention_invariant(ratings_df):
    """
    STRICT TEMPORAL ORDERING INVARIANT:
    Prove that for every user, train timestamps precede validation, which precede test.
    max(t_train) <= min(t_val) <= max(t_val) <= min(t_test)
    """
    splits = chronological_split(ratings_df, train_frac=0.60, val_frac=0.20)
    
    train_max_t = splits.train.groupby("user_id")["timestamp"].max()
    val_min_t = splits.val.groupby("user_id")["timestamp"].min()
    val_max_t = splits.val.groupby("user_id")["timestamp"].max()
    test_min_t = splits.test.groupby("user_id")["timestamp"].min()
    
    # Compare common users between partitions
    common_train_val = train_max_t.index.intersection(val_min_t.index)
    assert (train_max_t.loc[common_train_val] <= val_min_t.loc[common_train_val]).all()
    
    common_val_test = val_max_t.index.intersection(test_min_t.index)
    assert (val_max_t.loc[common_val_test] <= test_min_t.loc[common_val_test]).all()


def test_processed_files_exist_and_match():
    """Verify processed files exist in data/processed and can be read correctly."""
    proc_dir = get_default_processed_dir()
    train_path = os.path.join(proc_dir, "train_ratings.csv.gz")
    val_path = os.path.join(proc_dir, "val_ratings.csv.gz")
    test_path = os.path.join(proc_dir, "test_ratings.csv.gz")
    movies_path = os.path.join(proc_dir, "movies_metadata.csv.gz")
    stats_path = os.path.join(proc_dir, "dataset_statistics.json")
    
    assert os.path.exists(train_path)
    assert os.path.exists(val_path)
    assert os.path.exists(test_path)
    assert os.path.exists(movies_path)
    assert os.path.exists(stats_path)
    
    df_train = pd.read_csv(train_path, compression="gzip")
    assert len(df_train) == 597_742
