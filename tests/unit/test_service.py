"""
Unit and integration tests for RecommenderService (Phase 4):
- Service initialization and metadata loading.
- Recommendation equivalence with direct model calls.
- Candidate filtering (seen items excluded).
- Prediction bounds within [1.0, 5.0].
- Movie search and similarity retrieval.
- Cold-start fallback logic (< 3 ratings).
- SVD profile folding-in (>= 3 ratings).
- Genre filtering.
- Input validation and readable error messages.
- Artifact persistence and reloading equivalence.
"""

import os
import shutil
import pytest
import numpy as np
import pandas as pd

from src.recsys.service import RecommenderService


@pytest.fixture(scope="module")
def shared_service():
    """Create a module-scoped RecommenderService to speed up test execution."""
    return RecommenderService()


def test_service_initialization_and_metadata(shared_service):
    """Verify service loads movie metadata and model statistics correctly."""
    assert len(shared_service.movie_metadata) == 1682
    info = shared_service.get_movie_info(1)
    assert info["item_id"] == 1
    assert "Toy Story" in info["title"]
    assert info["year"] == 1995
    assert "Animation" in info["genres"]
    assert info["rating_count"] > 0
    assert 1.0 <= info["avg_rating"] <= 5.0


def test_service_recommend_for_user_matches_model_direct(shared_service):
    """Verify that service.recommend_for_user produces identical output to direct SVD model."""
    user_id = 1
    direct_recs = shared_service.svd_model.recommend(user_id, n=5, exclude_seen=True)
    service_recs = shared_service.recommend_for_user(user_id, n=5)

    assert len(service_recs) == len(direct_recs)
    for (dir_item, dir_score), s_dict in zip(direct_recs, service_recs):
        assert dir_item == s_dict["item_id"]
        assert abs(dir_score - s_dict["predicted_rating"]) < 0.05  # Rounded in service


def test_no_already_rated_movies_returned(shared_service):
    """Verify that no previously seen/rated movie is ever returned in recommendations."""
    user_id = 1
    seen_items = shared_service.svd_model.user_seen_items[user_id]
    service_recs = shared_service.recommend_for_user(user_id, n=20)

    for rec in service_recs:
        assert rec["item_id"] not in seen_items, f"Seen item {rec['item_id']} returned in recommendations!"

    # Also test for profile
    profile = {1: 5.0, 50: 4.0, 100: 4.5}
    profile_recs = shared_service.recommend_for_profile(profile, n=20)
    for rec in profile_recs:
        assert rec["item_id"] not in profile, f"Profile item {rec['item_id']} returned in recommendations!"


def test_predictions_bounded_in_1_to_5(shared_service):
    """Verify all predicted scores remain bounded strictly within [1.0, 5.0]."""
    user_recs = shared_service.recommend_for_user(1, n=20)
    for r in user_recs:
        assert 1.0 <= r["predicted_rating"] <= 5.0

    profile_recs = shared_service.recommend_for_profile({1: 5.0, 2: 1.0, 3: 5.0}, n=20)
    for r in profile_recs:
        assert 1.0 <= r["predicted_rating"] <= 5.0


def test_search_movies(shared_service):
    """Verify title substring search and ranking by popularity."""
    results = shared_service.search_movies("Star Wars")
    assert len(results) > 0
    assert results[0]["title"] == "Star Wars (1977)"

    # Empty search
    assert shared_service.search_movies("") == []
    assert shared_service.search_movies("   ") == []

    # Non-matching search
    assert shared_service.search_movies("xyznonexistentmovie12345") == []


def test_similar_movies(shared_service):
    """Verify SVD item factor cosine similarity returns meaningful neighbors."""
    # Toy Story (1) should be similar to classic animation blockbusters
    sims = shared_service.similar_movies(1, n=5)
    assert len(sims) == 5
    sim_ids = [s["item_id"] for s in sims]
    assert 1 not in sim_ids  # Target movie excluded

    # Beauty and the Beast (588) or Lion King (71) or Aladdin (95) should be among top neighbors
    animation_or_family = False
    for s in sims:
        if any(g in ["Animation", "Children's", "Musical"] for g in s["genres"]):
            animation_or_family = True
            break
    assert animation_or_family, "Top similar movies to Toy Story should include family/animated films!"


def test_recommend_for_profile_cold_start_fallback(shared_service):
    """Profiles with < 3 ratings must trigger Popularity Baseline and be labeled as cold-start."""
    cold_profile = {1: 5.0}  # 1 rating < 3 threshold
    recs = shared_service.recommend_for_profile(cold_profile, n=5)

    assert len(recs) == 5
    for r in recs:
        assert r["is_cold_start"] is True
        assert r["strategy"] == "popularity_cold_start"
        assert "Popularity Baseline" in r["explanation"]
        assert r["item_id"] != 1


def test_recommend_for_profile_personalized_svd(shared_service):
    """Profiles with >= 3 ratings must trigger personalized SVD folding-in."""
    warm_profile = {1: 5.0, 50: 5.0, 100: 4.0}  # 3 ratings == threshold
    recs = shared_service.recommend_for_profile(warm_profile, n=5)

    assert len(recs) == 5
    for r in recs:
        assert r["is_cold_start"] is False
        assert r["strategy"] == "svd_personalized"
        assert r["item_id"] not in warm_profile


def test_genre_filtering(shared_service):
    """Verify that recommendations respect genre filter criteria."""
    profile = {1: 5.0, 50: 5.0, 100: 4.0}
    recs = shared_service.recommend_for_profile(profile, n=5, filter_genres=["Animation"])

    assert len(recs) > 0
    for r in recs:
        assert "Animation" in r["genres"], f"Movie {r['title']} does not have Animation genre!"


def test_input_validation_and_clear_errors(shared_service):
    """Verify clear error handling for invalid user, invalid movie, invalid rating, and empty profile."""
    # 1. Unknown user
    with pytest.raises(ValueError, match="Unknown user ID: 99999"):
        shared_service.recommend_for_user(99999)

    # 2. Unknown movie in get_movie_info
    with pytest.raises(ValueError, match="Movie ID 99999 not found in catalog"):
        shared_service.get_movie_info(99999)

    # 3. Unknown movie in profile
    with pytest.raises(ValueError, match="Unknown movie ID in profile: 99999"):
        shared_service.recommend_for_profile({99999: 4.0})

    # 4. Rating > 5.0
    with pytest.raises(ValueError, match="Ratings must be between 1.0 and 5.0"):
        shared_service.recommend_for_profile({1: 6.0})

    # 5. Rating < 1.0
    with pytest.raises(ValueError, match="Ratings must be between 1.0 and 5.0"):
        shared_service.recommend_for_profile({1: 0.5})

    # 6. Empty profile
    with pytest.raises(ValueError, match="User profile cannot be empty"):
        shared_service.recommend_for_profile({})

    # 7. Non-positive n
    with pytest.raises(ValueError, match="n must be a positive integer"):
        shared_service.recommend_for_user(1, n=0)

    with pytest.raises(ValueError, match="n must be a positive integer"):
        shared_service.recommend_for_profile({1: 5.0}, n=-1)


def test_artifact_save_and_load_equivalence(shared_service, tmp_path):
    """Verify that saving and reloading artifacts produces identical recommendations."""
    art_dir = str(tmp_path / "artifacts")
    shared_service.save_artifacts(art_dir)

    reloaded_service = RecommenderService(artifacts_dir=art_dir)

    recs_orig = shared_service.recommend_for_user(1, n=5)
    recs_reloaded = reloaded_service.recommend_for_user(1, n=5)

    assert recs_orig == recs_reloaded
