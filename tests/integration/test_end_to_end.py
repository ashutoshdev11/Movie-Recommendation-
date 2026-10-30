"""
End-to-End integration test for the Movie Recommendation System:
Traces the complete pipeline from data loading, temporal splitting, model fitting,
metric computation, service inference, online folding-in, to Streamlit UI rendering.
"""

import os
import pytest
import numpy as np
import pandas as pd

from src.recsys.data import load_ratings, load_movies, get_default_data_dir
from src.recsys.split import chronological_split
from src.recsys.models.svd import TruncatedSVDRecommender
from src.recsys.models.popularity import PopularityBaseline
from src.recsys.evaluation import evaluate_model
from src.recsys.service import RecommenderService
from streamlit.testing.v1 import AppTest


def test_full_pipeline_end_to_end():
    # 1. Load Data
    data_dir = get_default_data_dir()
    ratings = load_ratings(data_dir)
    movies = load_movies(data_dir)
    assert len(ratings) == 100000
    assert len(movies) == 1682

    # 2. Chronological Per-User Splitting (60/20/20)
    splits = chronological_split(ratings, train_frac=0.60, val_frac=0.20, random_state=42)
    assert len(splits.train) + len(splits.val) + len(splits.test) == 100000
    assert splits.train["user_id"].nunique() == 943

    # 3. Fit Models on Train
    svd = TruncatedSVDRecommender(n_factors=20, random_state=42).fit(splits.train)
    pop = PopularityBaseline(damping=50.0, min_ratings=1).fit(splits.train)
    assert svd.is_fitted
    assert pop.is_fitted

    # 4. Evaluate on Validation Split
    sample_val = splits.val[splits.val["user_id"].isin([1, 2, 3, 4, 5])].copy()
    val_metrics = evaluate_model(svd, sample_val, splits.train, k_values=(5, 10))
    assert "ndcg@10" in val_metrics
    assert "rmse" in val_metrics
    assert 0.0 <= val_metrics["ndcg@10"] <= 1.0
    assert val_metrics["rmse"] > 0.0

    # 5. Service Layer Initialization and Recommendation
    service = RecommenderService(data_dir=data_dir, auto_fit=True)
    user_recs = service.recommend_for_user(1, n=5)
    assert len(user_recs) == 5
    for r in user_recs:
        assert 1.0 <= r["predicted_rating"] <= 5.0
        assert r["is_cold_start"] is False

    # 6. Online Profile Folding-In (Warm vs Cold)
    cold_recs = service.recommend_for_profile({1: 5.0}, n=5)
    assert cold_recs[0]["is_cold_start"] is True
    assert cold_recs[0]["strategy"] == "popularity_cold_start"

    warm_recs = service.recommend_for_profile({1: 5.0, 50: 5.0, 100: 4.0}, n=5)
    assert warm_recs[0]["is_cold_start"] is False
    assert warm_recs[0]["strategy"] == "svd_personalized"

    # 7. Similar Movies Search
    sims = service.similar_movies(1, n=5)
    assert len(sims) == 5
    assert sims[0]["item_id"] != 1

    # 8. Streamlit App Rendering via AppTest
    at = AppTest.from_file("app/streamlit_app.py", default_timeout=25)
    at.run()
    assert not at.exception
    assert "Movie Recommendation System" in at.title[0].value
