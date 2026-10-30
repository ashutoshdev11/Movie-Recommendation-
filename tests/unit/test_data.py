"""
Unit tests for data loaders and dataset validation.
"""

import os
import pytest
import numpy as np
import pandas as pd

from src.recsys.data import (
    load_ratings,
    load_movies,
    load_users,
    validate_dataset,
    GENRE_COLUMNS,
    get_default_data_dir,
)


@pytest.fixture(scope="module")
def dataset():
    data_dir = get_default_data_dir()
    if not os.path.exists(data_dir):
        pytest.skip("Dataset not downloaded yet.")
    ratings = load_ratings(data_dir)
    movies = load_movies(data_dir)
    users = load_users(data_dir)
    return ratings, movies, users


def test_dataset_dimensions(dataset):
    ratings, movies, users = dataset
    # Rule / Criteria: 100,000 ratings, 943 users, 1,682 movies
    assert len(ratings) == 100000, f"Expected 100,000 ratings, got {len(ratings)}"
    assert ratings["user_id"].nunique() == 943, f"Expected 943 users, got {ratings['user_id'].nunique()}"
    assert ratings["item_id"].nunique() == 1682, f"Expected 1,682 movies, got {ratings['item_id'].nunique()}"
    assert len(users) == 943, f"Expected 943 users in u.user, got {len(users)}"
    assert len(movies) == 1682, f"Expected 1,682 movies in u.item, got {len(movies)}"


def test_rating_values_and_types(dataset):
    ratings, _, _ = dataset
    # Ratings must be integers in 1..5
    assert pd.api.types.is_integer_dtype(ratings["rating"]), "Rating column must be integer"
    assert ratings["rating"].min() == 1, f"Minimum rating expected 1, got {ratings['rating'].min()}"
    assert ratings["rating"].max() == 5, f"Maximum rating expected 5, got {ratings['rating'].max()}"
    assert set(ratings["rating"].unique()) == {1, 2, 3, 4, 5}


def test_no_duplicate_pairs(dataset):
    ratings, _, _ = dataset
    duplicates = ratings.duplicated(subset=["user_id", "item_id"]).sum()
    assert duplicates == 0, f"Found {duplicates} duplicate (user, item) pairs"


def test_sparsity_calculation(dataset):
    ratings, movies, users = dataset
    report = validate_dataset(ratings, movies, users)
    # Sparsity should be near 93.7%
    assert 0.936 < report.sparsity < 0.938, f"Expected sparsity ~93.7%, got {report.sparsity*100:.2f}%"
    assert report.is_valid is True, f"Validation report failed: {report.summary}"


def test_id_consistency_across_tables(dataset):
    ratings, movies, users = dataset
    rating_users = set(ratings["user_id"])
    catalog_users = set(users["user_id"])
    assert rating_users.issubset(catalog_users), "Found ratings referencing users not present in u.user"

    rating_items = set(ratings["item_id"])
    catalog_items = set(movies["item_id"])
    assert rating_items.issubset(catalog_items), "Found ratings referencing movies not present in u.item"


def test_movie_genre_flags(dataset):
    _, movies, _ = dataset
    for genre in GENRE_COLUMNS:
        assert genre in movies.columns, f"Genre column {genre} missing from movies"
        assert set(movies[genre].unique()).issubset({0, 1}), f"Genre {genre} has values outside {{0, 1}}"
