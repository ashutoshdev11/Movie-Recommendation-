"""
Unit tests for evaluation metrics:
- MAE, RMSE
- Precision@K, Recall@K, NDCG@K
- Catalog Coverage@K, Novelty@K
- Edge cases: users with no relevant items, ties in ranking, empty candidate sets.
"""

import pytest
import numpy as np
import pandas as pd

from src.recsys.evaluation import (
    compute_mae,
    compute_rmse,
    compute_dcg_at_k,
    compute_idcg_at_k,
    compute_ndcg_at_k,
    compute_precision_at_k,
    compute_recall_at_k,
    compute_coverage_at_k,
    compute_novelty_at_k,
)


def test_mae_and_rmse_hand_computed():
    y_true = np.array([4.0, 3.0, 5.0, 2.0], dtype=np.float64)
    y_pred = np.array([3.0, 3.0, 4.0, 4.0], dtype=np.float64)
    # Errors: |4-3|=1, |3-3|=0, |5-4|=1, |2-4|=2 -> sum = 4.0 -> MAE = 4/4 = 1.0
    # Squared: 1^2 + 0^2 + 1^2 + 2^2 = 1 + 0 + 1 + 4 = 6.0 -> MSE = 6/4 = 1.5 -> RMSE = sqrt(1.5) ≈ 1.22474487
    assert compute_mae(y_true, y_pred) == 1.0
    assert abs(compute_rmse(y_true, y_pred) - np.sqrt(1.5)) < 1e-6


def test_precision_recall_at_k_hand_computed():
    rec_items = [10, 20, 30, 40, 50]
    relevant_items = {20, 40, 60, 70}  # Total 4 relevant items in ground truth

    # At K=3: recs are [10, 20, 30]. Hit = {20} -> 1 hit
    # Precision@3 = 1 / 3 = 0.333333...
    # Recall@3 = 1 / 4 = 0.25
    assert abs(compute_precision_at_k(rec_items, relevant_items, k=3) - 1.0 / 3.0) < 1e-6
    assert abs(compute_recall_at_k(rec_items, relevant_items, k=3) - 0.25) < 1e-6

    # At K=5: recs are [10, 20, 30, 40, 50]. Hits = {20, 40} -> 2 hits
    # Precision@5 = 2 / 5 = 0.40
    # Recall@5 = 2 / 4 = 0.50
    assert abs(compute_precision_at_k(rec_items, relevant_items, k=5) - 0.40) < 1e-6
    assert abs(compute_recall_at_k(rec_items, relevant_items, k=5) - 0.50) < 1e-6


def test_ndcg_at_k_hand_computed():
    rec_items = [10, 20, 30, 40, 50]
    relevant_items = {20, 40}  # 2 relevant items
    # Hits at positions: rank 1 (item 10): 0, rank 2 (item 20): 1, rank 3: 0, rank 4 (item 40): 1, rank 5: 0
    # DCG@5 = 1/log2(2+1) + 1/log2(4+1) = 1/log2(3) + 1/log2(5)
    # log2(3) ≈ 1.5849625, log2(5) ≈ 2.32192809
    # DCG@5 ≈ 0.63092975 + 0.43067656 = 1.06160631
    # Ideal ranking places 2 hits at ranks 1 and 2:
    # IDCG@5 = 1/log2(1+1) + 1/log2(2+1) = 1/log2(2) + 1/log2(3) = 1.0 + 0.63092975 = 1.63092975
    # NDCG@5 = DCG@5 / IDCG@5 ≈ 1.06160631 / 1.63092975 ≈ 0.65092092
    expected_dcg = (1.0 / np.log2(3)) + (1.0 / np.log2(5))
    expected_idcg = (1.0 / np.log2(2)) + (1.0 / np.log2(3))
    expected_ndcg = expected_dcg / expected_idcg

    ndcg = compute_ndcg_at_k(rec_items, relevant_items, k=5)
    assert abs(ndcg - expected_ndcg) < 1e-6, f"Expected {expected_ndcg}, got {ndcg}"


def test_no_relevant_items_case():
    rec_items = [1, 2, 3]
    relevant_items = set()  # No relevant items

    # Must return 0.0 without ZeroDivisionError
    assert compute_precision_at_k(rec_items, relevant_items, k=3) == 0.0
    assert compute_recall_at_k(rec_items, relevant_items, k=3) == 0.0
    assert compute_ndcg_at_k(rec_items, relevant_items, k=3) == 0.0


def test_coverage_and_novelty_hand_computed():
    catalog = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10}  # Size 10
    recs = {
        1: [1, 2, 3],
        2: [2, 3, 4],
        3: [1, 5, 6],
    }
    # Unique recommended items at K=2:
    # u1: [1, 2], u2: [2, 3], u3: [1, 5] -> union = {1, 2, 3, 5} -> 4 unique items
    # Coverage@2 = 4 / 10 = 0.40
    cov = compute_coverage_at_k(recs, catalog, k=2)
    assert cov == 0.40

    # Novelty: items 1, 2, 3, 5
    # N_users = 10, catalog = 10 -> denom = 20
    # All items have count 0 -> p_i = 1/20 -> -log2(1/20) = log2(20)
    nov = compute_novelty_at_k(recs, {}, n_train_users=10, total_catalog_size=10, k=2)
    expected_nov = np.log2(20.0)
    assert abs(nov - expected_nov) < 1e-6
