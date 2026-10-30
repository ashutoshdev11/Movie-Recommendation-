"""
Automated unit tests for MovieRec Version 2 Recommendation Models.
Tests TruncatedSVD and Popularity baseline for fitting, predictions, bounds,
seen exclusion, artifact loading equivalence, and folding-in reproducibility.
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

from app.ml.models.svd import TruncatedSVDRecommender
from app.ml.models.popularity import PopularityBaseline
from app.ml.dataset import get_default_processed_dir


@pytest.fixture(scope="module")
def toy_train_df():
    """Toy ratings dataset for fast deterministic unit testing."""
    return pd.DataFrame({
        "user_id": [1, 1, 1, 2, 2, 3, 3, 3, 4, 4],
        "movie_id": [10, 20, 30, 20, 40, 10, 30, 50, 40, 50],
        "rating": [5.0, 4.0, 3.0, 4.5, 2.0, 5.0, 4.0, 3.5, 2.5, 4.0],
        "timestamp": [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
    })


def test_popularity_baseline_scores_and_recommendations(toy_train_df):
    """Verify Popularity baseline damped score calculation and ordering."""
    model = PopularityBaseline(damping=2.0).fit(toy_train_df)
    assert model.is_fitted
    assert len(model.ranked_items) == 5

    # Predict
    score = model.predict(user_id=1, item_id=10)
    assert 1.0 <= score <= 5.0

    # Recommend excluding seen
    recs = model.recommend(user_id=1, n=2, exclude_seen=True)
    assert len(recs) == 2
    seen_by_1 = {10, 20, 30}
    for item_id, _ in recs:
        assert item_id not in seen_by_1


def test_svd_recommender_prediction_bounds_and_seen_exclusion(toy_train_df):
    """Verify SVD predictions are bounded in [1.0, 5.0] and seen items are excluded."""
    model = TruncatedSVDRecommender(n_factors=2, random_state=42).fit(toy_train_df)
    assert model.is_fitted

    for u in [1, 2, 3, 4]:
        for it in [10, 20, 30, 40, 50]:
            pred = model.predict(u, it)
            assert 1.0 <= pred <= 5.0

    # User 1 has seen items 10, 20, 30. Unseen candidates are 40, 50.
    recs = model.recommend(user_id=1, n=10, exclude_seen=True)
    rec_ids = [it for it, _ in recs]
    assert 10 not in rec_ids
    assert 20 not in rec_ids
    assert 30 not in rec_ids
    assert set(rec_ids).issubset({40, 50})


def test_svd_artifact_save_and_load_equivalence(toy_train_df, tmp_path):
    """Verify that saving and loading SVD artifacts produces identical predictions."""
    model = TruncatedSVDRecommender(n_factors=2, random_state=42).fit(toy_train_df)
    
    artifact_path = str(tmp_path / "test_svd.npz")
    model.save_artifacts(artifact_path)
    assert os.path.exists(artifact_path)

    loaded_model = TruncatedSVDRecommender.load_artifacts(artifact_path)
    assert loaded_model.is_fitted
    assert loaded_model.n_factors == model.n_factors

    for u in [1, 2, 3, 4]:
        for it in [10, 20, 30, 40, 50]:
            pred_orig = model.predict(u, it)
            pred_loaded = loaded_model.predict(u, it)
            assert abs(pred_orig - pred_loaded) < 1e-12

    # Verify identical recommendations
    recs_orig = model.recommend(user_id=1, n=2)
    recs_loaded = loaded_model.recommend(user_id=1, n=2)
    assert recs_orig == recs_loaded


def test_svd_profile_folding_in(toy_train_df):
    """Verify real-time SVD latent folding-in for a new user taste profile."""
    model = TruncatedSVDRecommender(n_factors=2, random_state=42).fit(toy_train_df)
    
    profile = {10: 5.0, 30: 4.0}
    recs = model.fold_in_profile(profile, n=2)
    assert len(recs) == 2
    for it, score in recs:
        assert it not in {10, 30}
        assert 1.0 <= score <= 5.0


def test_svd_reproducibility(toy_train_df):
    """Verify exact numerical reproducibility when random_state is identical."""
    m1 = TruncatedSVDRecommender(n_factors=2, random_state=42).fit(toy_train_df)
    m2 = TruncatedSVDRecommender(n_factors=2, random_state=42).fit(toy_train_df)

    np.testing.assert_allclose(m1.U, m2.U, rtol=1e-10)
    np.testing.assert_allclose(m1.sigma, m2.sigma, rtol=1e-10)
    np.testing.assert_allclose(m1.Vt, m2.Vt, rtol=1e-10)


def test_production_artifacts_exist_and_load():
    """Verify the production V2 artifacts in v2/backend/artifacts/ exist and load cleanly."""
    artifacts_dir = os.path.join(V2_BACKEND_DIR, "artifacts")
    svd_path = os.path.join(artifacts_dir, "svd_1m_artifacts.npz")
    pop_path = os.path.join(artifacts_dir, "popularity_1m_artifacts.json")
    metrics_path = os.path.join(artifacts_dir, "evaluation_metrics.json")

    assert os.path.exists(svd_path)
    assert os.path.exists(pop_path)
    assert os.path.exists(metrics_path)

    svd = TruncatedSVDRecommender.load_artifacts(svd_path)
    assert svd.n_factors == 30
    assert len(svd.all_users) == 6040
    # In the 60% train split, 3624 unique movies received at least 1 rating
    assert len(svd.all_items) == 3624
    assert len(svd.user_seen_items) == 6040
