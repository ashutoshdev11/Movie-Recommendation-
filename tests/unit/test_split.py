"""
Unit tests for per-user chronological dataset splitting.
"""

import os
import pytest
import numpy as np
import pandas as pd

from src.recsys.data import load_ratings, get_default_data_dir
from src.recsys.split import chronological_split


@pytest.fixture(scope="module")
def ratings():
    data_dir = get_default_data_dir()
    if not os.path.exists(data_dir):
        pytest.skip("Dataset not downloaded yet.")
    return load_ratings(data_dir)


def test_split_proportions_and_sizes(ratings):
    splits = chronological_split(ratings, train_frac=0.60, val_frac=0.20, random_state=42)
    total_ratings = len(ratings)

    # Sum of splits equals total
    assert len(splits.train) + len(splits.val) + len(splits.test) == total_ratings

    # Approximate proportions across total
    train_pct = len(splits.train) / total_ratings
    val_pct = len(splits.val) / total_ratings
    test_pct = len(splits.test) / total_ratings

    assert 0.58 < train_pct < 0.62, f"Train proportion unexpected: {train_pct:.3f}"
    assert 0.18 < val_pct < 0.22, f"Val proportion unexpected: {val_pct:.3f}"
    assert 0.18 < test_pct < 0.22, f"Test proportion unexpected: {test_pct:.3f}"


def test_no_row_overlap_between_partitions(ratings):
    splits = chronological_split(ratings, train_frac=0.60, val_frac=0.20, random_state=42)

    # Use index-based or tuple-based membership
    train_pairs = set(zip(splits.train["user_id"], splits.train["item_id"]))
    val_pairs = set(zip(splits.val["user_id"], splits.val["item_id"]))
    test_pairs = set(zip(splits.test["user_id"], splits.test["item_id"]))

    assert len(train_pairs.intersection(val_pairs)) == 0, "Overlap found between train and validation"
    assert len(train_pairs.intersection(test_pairs)) == 0, "Overlap found between train and test"
    assert len(val_pairs.intersection(test_pairs)) == 0, "Overlap found between validation and test"


def test_every_user_appears_in_train(ratings):
    splits = chronological_split(ratings, train_frac=0.60, val_frac=0.20, random_state=42)
    all_users = set(ratings["user_id"])
    train_users = set(splits.train["user_id"])

    # Acceptance criterion: every user appears in train
    assert train_users == all_users, "Some users do not appear in the training partition"
    assert len(train_users) == 943


def test_chronological_ordering_per_user(ratings):
    splits = chronological_split(ratings, train_frac=0.60, val_frac=0.20, random_state=42)

    # For every user: max(t_train) <= min(t_val) <= max(t_val) <= min(t_test)
    train_grouped = splits.train.groupby("user_id")["timestamp"]
    val_grouped = splits.val.groupby("user_id")["timestamp"]
    test_grouped = splits.test.groupby("user_id")["timestamp"]

    train_max = train_grouped.max()
    val_min = val_grouped.min()
    val_max = val_grouped.max()
    test_min = test_grouped.min()

    # Compare users present in both
    common_val_users = train_max.index.intersection(val_min.index)
    assert (train_max.loc[common_val_users] <= val_min.loc[common_val_users]).all(), (
        "Found user where train timestamp exceeds validation timestamp"
    )

    common_test_users = val_max.index.intersection(test_min.index)
    assert (val_max.loc[common_test_users] <= test_min.loc[common_test_users]).all(), (
        "Found user where validation timestamp exceeds test timestamp"
    )


def test_split_reproducibility(ratings):
    split1 = chronological_split(ratings, train_frac=0.60, val_frac=0.20, random_state=42)
    split2 = chronological_split(ratings, train_frac=0.60, val_frac=0.20, random_state=42)

    pd.testing.assert_frame_equal(split1.train, split2.train)
    pd.testing.assert_frame_equal(split1.val, split2.val)
    pd.testing.assert_frame_equal(split1.test, split2.test)
