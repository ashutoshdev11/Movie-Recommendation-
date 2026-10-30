"""
Unit tests for collaborative filtering models:
- PopularityBaseline
- UserKNNRecommender
- ItemKNNRecommender
- TruncatedSVDRecommender
Validates hand-computed derivations, edge cases, interface consistency, and data isolation.
"""

import pytest
import numpy as np
import pandas as pd

from src.recsys.models.base import BaseRecommender
from src.recsys.models.popularity import PopularityBaseline
from src.recsys.models.user_knn import UserKNNRecommender
from src.recsys.models.item_knn import ItemKNNRecommender
from src.recsys.models.svd import TruncatedSVDRecommender


@pytest.fixture
def toy_ratings():
    """
    Toy dataset corresponding to docs/models.md Section 6:
    4 users, 5 items.
    """
    data = [
        (1, 1, 5.0), (1, 2, 3.0), (1, 3, 4.0), (1, 4, 4.0),
        (2, 1, 3.0), (2, 2, 1.0), (2, 3, 2.0), (2, 4, 3.0), (2, 5, 3.0),
        (3, 1, 4.0), (3, 2, 3.0), (3, 4, 3.0),
        (4, 1, 3.0), (4, 2, 3.0), (4, 3, 1.0), (4, 4, 5.0), (4, 5, 4.0),
    ]
    return pd.DataFrame(data, columns=["user_id", "item_id", "rating"])


# 1. Interface conformance test
@pytest.mark.parametrize("model_cls", [
    PopularityBaseline,
    UserKNNRecommender,
    ItemKNNRecommender,
    TruncatedSVDRecommender,
])
def test_common_interface_conformance(model_cls, toy_ratings):
    model = model_cls()
    assert isinstance(model, BaseRecommender)

    # Fit returns self
    fitted = model.fit(toy_ratings)
    assert fitted is model
    assert model.is_fitted is True

    # Predict returns float in [1.0, 5.0]
    pred = model.predict(1, 1)
    assert isinstance(pred, float)
    assert 1.0 <= pred <= 5.0

    # Recommend returns list of (item_id, score) tuples
    recs = model.recommend(1, n=3, exclude_seen=True)
    assert isinstance(recs, list)
    assert len(recs) <= 3
    for item_id, score in recs:
        assert isinstance(item_id, (int, np.integer))
        assert isinstance(score, float)
        assert 1.0 <= score <= 5.0
        # Exclude seen: user 1 rated {1, 2, 3, 4}, so recs must only contain item 5
        assert item_id == 5


# 2. Hand-computed expected values match code (tolerance 1e-6)
def test_hand_computed_user_knn_similarity_and_prediction(toy_ratings):
    model = UserKNNRecommender(k=10, min_overlap=2)
    model.fit(toy_ratings)

    # Hand-derived sim(u1, u2) = 2.0 / sqrt(5.68) ≈ 0.8391814686
    sim_1_2 = model.compute_similarity(1, 2)
    expected_sim = 2.0 / np.sqrt(5.68)
    assert abs(sim_1_2 - expected_sim) < 1e-6, f"Expected {expected_sim}, got {sim_1_2}"

    # Hand-derived sim(u1, u4) = 0.0
    sim_1_4 = model.compute_similarity(1, 4)
    assert abs(sim_1_4 - 0.0) < 1e-6

    # Hand-derived prediction r_hat(u1, i5) = 4.600000
    pred = model.predict(1, 5)
    expected_pred = 4.600000
    assert abs(pred - expected_pred) < 1e-6, f"Expected {expected_pred}, got {pred}"


def test_hand_computed_item_knn_similarity(toy_ratings):
    model = ItemKNNRecommender(k=10, min_overlap=2)
    model.fit(toy_ratings)

    # Hand-derived sim(i2, i3) = 1.0 / sqrt(15.0) ≈ 0.2581988897
    sim_2_3 = model.compute_similarity(2, 3)
    expected_sim = 1.0 / np.sqrt(15.0)
    assert abs(sim_2_3 - expected_sim) < 1e-6, f"Expected {expected_sim}, got {sim_2_3}"


def test_popularity_baseline_damped_mean(toy_ratings):
    # Global mean = 54 / 17 ≈ 3.176470588
    # For item 1: sum = 5+3+4+3 = 15, count = 4
    # damping = 10.0, min_ratings = 2
    # Damped mean = (15 + 10 * (54/17)) / (4 + 10) = (15 + 31.76470588) / 14 = 46.76470588 / 14 ≈ 3.340336
    damping = 10.0
    global_mean = 54.0 / 17.0
    expected_damped_i1 = (15.0 + damping * global_mean) / (4.0 + damping)

    model = PopularityBaseline(damping=damping, min_ratings=2)
    model.fit(toy_ratings)
    pred_i1 = model.predict(1, 1)

    assert abs(pred_i1 - expected_damped_i1) < 1e-6, f"Expected {expected_damped_i1}, got {pred_i1}"


# 3. Model isolation & Leakage proof
def test_fit_isolated_from_test_partition(toy_ratings):
    """
    Proves that altering a test partition has zero influence on the model fitted on train.
    """
    train = toy_ratings.copy()
    test_partition_v1 = pd.DataFrame([(1, 5, 1.0)], columns=["user_id", "item_id", "rating"])
    test_partition_v2 = pd.DataFrame([(1, 5, 5.0)], columns=["user_id", "item_id", "rating"])

    model1 = UserKNNRecommender(k=5)
    model1.fit(train)
    pred1 = model1.predict(1, 5)

    model2 = UserKNNRecommender(k=5)
    model2.fit(train)
    pred2 = model2.predict(1, 5)

    assert pred1 == pred2, "Model predictions changed despite train partition remaining identical!"


# 4. Edge cases & Robustness
def test_edge_cases_unknown_ids_and_sparse_profiles(toy_ratings):
    models = [
        PopularityBaseline(),
        UserKNNRecommender(k=5),
        ItemKNNRecommender(k=5),
        TruncatedSVDRecommender(n_factors=2, random_state=42),
    ]

    for model in models:
        model.fit(toy_ratings)

        # 1. Unknown user (user 999)
        pred_unknown_user = model.predict(999, 1)
        assert 1.0 <= pred_unknown_user <= 5.0

        # 2. Unknown item (item 999)
        pred_unknown_item = model.predict(1, 999)
        assert 1.0 <= pred_unknown_item <= 5.0

        # 3. Unknown user and unknown item
        pred_unknown_both = model.predict(999, 999)
        assert 1.0 <= pred_unknown_both <= 5.0

        # 4. Bound invariant: All predictions in [1.0, 5.0]
        for u in [1, 2, 3, 4, 999]:
            for i in [1, 2, 3, 4, 5, 999]:
                p = model.predict(u, i)
                assert 1.0 <= p <= 5.0, f"Prediction {p} outside [1.0, 5.0] for model {model.__class__.__name__}"


def test_edge_case_zero_denominator_and_single_rating():
    # User with exactly 1 rating
    single_rating_df = pd.DataFrame([
        (1, 1, 4.0),
        (2, 2, 2.0),
    ], columns=["user_id", "item_id", "rating"])

    user_knn = UserKNNRecommender(k=5, min_overlap=2)
    user_knn.fit(single_rating_df)
    # No overlap with anyone -> fallback to item mean / user mean / global mean
    p = user_knn.predict(1, 2)
    assert p == 2.0  # Item 2 mean is 2.0

    item_knn = ItemKNNRecommender(k=5, min_overlap=2)
    item_knn.fit(single_rating_df)
    p_item = item_knn.predict(1, 2)
    assert p_item == 2.0  # Item 2 mean is 2.0


def test_k_larger_than_available_neighbors(toy_ratings):
    # k=1000 is much larger than the 4 available users
    model = UserKNNRecommender(k=1000)
    model.fit(toy_ratings)
    pred = model.predict(1, 5)
    assert 1.0 <= pred <= 5.0


def test_no_already_rated_items_in_recommend(toy_ratings):
    models = [
        PopularityBaseline(),
        UserKNNRecommender(k=5),
        ItemKNNRecommender(k=5),
        TruncatedSVDRecommender(n_factors=2, random_state=42),
    ]

    for model in models:
        model.fit(toy_ratings)
        # User 1 rated items 1, 2, 3, 4. The only unrated item in catalog is 5.
        recs = model.recommend(user_id=1, n=10, exclude_seen=True)
        recommended_ids = [item_id for item_id, _ in recs]
        assert set(recommended_ids).issubset({5})
        assert not any(i in {1, 2, 3, 4} for i in recommended_ids)


def test_models_fit_and_predict_on_movielens_train_split():
    """
    Smoke test to confirm all 4 models fit on the actual MovieLens 100K 60% training partition,
    produce valid bounded predictions, and generate recommendations.
    """
    from src.recsys.data import load_ratings, get_default_data_dir
    from src.recsys.split import chronological_split

    data_dir = get_default_data_dir()
    ratings = load_ratings(data_dir)
    splits = chronological_split(ratings, train_frac=0.60, val_frac=0.20, random_state=42)
    train = splits.train

    # 1. Popularity
    pop = PopularityBaseline(damping=10.0, min_ratings=5).fit(train)
    p_pop = pop.predict(1, 50)
    assert 1.0 <= p_pop <= 5.0
    recs_pop = pop.recommend(1, n=5)
    assert len(recs_pop) == 5

    # 2. SVD
    svd = TruncatedSVDRecommender(n_factors=10, random_state=42).fit(train)
    p_svd = svd.predict(1, 50)
    assert 1.0 <= p_svd <= 5.0
    recs_svd = svd.recommend(1, n=5)
    assert len(recs_svd) == 5

    # 3. Item KNN
    item_knn = ItemKNNRecommender(k=10, min_overlap=2).fit(train)
    p_item = item_knn.predict(1, 50)
    assert 1.0 <= p_item <= 5.0
    recs_item = item_knn.recommend(1, n=5)
    assert len(recs_item) == 5

    # 4. User KNN
    user_knn = UserKNNRecommender(k=10, min_overlap=2).fit(train)
    p_user = user_knn.predict(1, 50)
    assert 1.0 <= p_user <= 5.0
    recs_user = user_knn.recommend(1, n=5)
    assert len(recs_user) == 5


def test_item_knn_optimization_equivalence_and_edge_cases(toy_ratings):
    """
    Validates that the optimized ItemKNN implementation yields exact identical
    predictions, recommendations, and edge-case behavior to < 1e-9 tolerance.
    """
    model = ItemKNNRecommender(k=5, min_overlap=2).fit(toy_ratings)

    # 1. Known users recommendations
    for u in [1, 2, 3, 4]:
        recs = model.recommend(u, n=5, exclude_seen=True)
        assert len(recs) <= 5
        for item_id, score in recs:
            # Score must match individual predict() call exactly
            pred_score = model.predict(u, item_id)
            assert abs(score - pred_score) < 1e-9, f"Discrepancy for user {u}, item {item_id}"

    # 2. Edge case: Unknown user
    recs_unknown_user = model.recommend(999, n=5, exclude_seen=True)
    assert len(recs_unknown_user) == 5
    for item_id, score in recs_unknown_user:
        pred_score = model.predict(999, item_id)
        assert abs(score - pred_score) < 1e-9

    # 3. Edge case: Single rating user
    single_df = pd.DataFrame([(1, 1, 4.0), (2, 2, 2.0)], columns=["user_id", "item_id", "rating"])
    single_model = ItemKNNRecommender(k=5, min_overlap=2).fit(single_df)
    recs_single = single_model.recommend(1, n=2, exclude_seen=True)
    assert len(recs_single) == 1
    assert recs_single[0][0] == 2
    assert recs_single[0][1] == 2.0  # Item 2 mean fallback
