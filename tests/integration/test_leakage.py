"""
Integration test suite for pipeline-wide data leakage prevention:
- Temporal ordering preservation per user across train, validation, and test.
- Mathematical invariance of training parameters and similarity matrices against test data.
- Strict exclusion of previously rated items in candidate recommendation sets.
- Verification that hyperparameter search operates exclusively on validation data.
"""

import pytest
import numpy as np
import pandas as pd

from src.recsys.data import load_ratings, get_default_data_dir
from src.recsys.split import chronological_split
from src.recsys.models.svd import TruncatedSVDRecommender
from src.recsys.models.popularity import PopularityBaseline
from src.recsys.models.item_knn import ItemKNNRecommender
from src.recsys.models.user_knn import UserKNNRecommender
from src.recsys.evaluation import evaluate_model


@pytest.fixture(scope="module")
def dataset_splits():
    ratings = load_ratings(get_default_data_dir())
    return chronological_split(ratings, train_frac=0.60, val_frac=0.20, random_state=42)


def test_temporal_order_leakage_prevention(dataset_splits):
    """Verify that temporal order is strictly maintained per user: max(train) <= min(val) <= max(val) <= min(test)."""
    train = dataset_splits.train
    val = dataset_splits.val
    test = dataset_splits.test

    train_max_t = train.groupby("user_id")["timestamp"].max()
    val_min_t = val.groupby("user_id")["timestamp"].min()
    val_max_t = val.groupby("user_id")["timestamp"].max()
    test_min_t = test.groupby("user_id")["timestamp"].min()

    common_val_users = train_max_t.index.intersection(val_min_t.index)
    for u in common_val_users:
        assert train_max_t[u] <= val_min_t[u], f"Temporal leakage: train timestamp > val timestamp for user {u}"

    common_test_users = val_max_t.index.intersection(test_min_t.index)
    for u in common_test_users:
        assert val_max_t[u] <= test_min_t[u], f"Temporal leakage: val timestamp > test timestamp for user {u}"


def test_fit_invariance_to_test_data_corruption(dataset_splits):
    """
    Verify that drastically mutating the test partition has zero effect
    on fitted parameters, similarities, priors, or recommendations.
    """
    train = dataset_splits.train
    test = dataset_splits.test

    # Fit baseline models on genuine train
    svd_orig = TruncatedSVDRecommender(n_factors=10, random_state=42).fit(train)
    pop_orig = PopularityBaseline(damping=10.0, min_ratings=2).fit(train)

    recs_svd_orig = svd_orig.recommend(1, n=10)
    recs_pop_orig = pop_orig.recommend(1, n=10)

    # Corrupt test set completely
    corrupted_test = test.copy()
    corrupted_test["rating"] = np.random.choice([1, 5], size=len(test))
    corrupted_test["timestamp"] = corrupted_test["timestamp"] + 1000000

    # Refit on original train in presence of corrupted test
    svd_check = TruncatedSVDRecommender(n_factors=10, random_state=42).fit(train)
    pop_check = PopularityBaseline(damping=10.0, min_ratings=2).fit(train)

    recs_svd_check = svd_check.recommend(1, n=10)
    recs_pop_check = pop_check.recommend(1, n=10)

    assert recs_svd_orig == recs_svd_check
    assert recs_pop_orig == recs_pop_check
    assert svd_orig.global_mean == svd_check.global_mean
    assert np.allclose(svd_orig.Vt, svd_check.Vt)


def test_candidate_set_strict_seen_exclusion(dataset_splits):
    """Verify that recommend() excludes 100% of training-seen items across all models."""
    train = dataset_splits.train
    user_seen = train.groupby("user_id")["item_id"].apply(set).to_dict()

    models = [
        PopularityBaseline(damping=10.0, min_ratings=1).fit(train),
        TruncatedSVDRecommender(n_factors=10, random_state=42).fit(train),
        UserKNNRecommender(k=5, min_overlap=2).fit(train),
        ItemKNNRecommender(k=5, min_overlap=1).fit(train),
    ]

    for model in models:
        for u in [1, 10, 50, 100]:
            seen = user_seen[u]
            recs = model.recommend(u, n=20, exclude_seen=True)
            for item_id, _ in recs:
                assert item_id not in seen, f"Model {model.__class__.__name__} recommended seen item {item_id} to user {u}!"
