"""
Comprehensive API integration tests for MovieRec Version 2 FastAPI Backend.
Verifies authentication, JWT/cookie handling, user data isolation,
ratings, watchlists, recommendations, and poster SVG fallbacks.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure v2 backend is in sys.path
V2_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if V2_BACKEND_DIR not in sys.path:
    sys.path.insert(0, V2_BACKEND_DIR)

from app.main import app
from app.core.database import Base, get_db

# Use an isolated in-memory SQLite database with StaticPool for multi-threaded TestClient
TEST_DB_URL = "sqlite:///:memory:"
engine_test = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    """Create all database tables for test session."""
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture
def client():
    """FastAPI TestClient instance."""
    return TestClient(app)


# ------------------------------------------------------------------------------
# 1. Authentication Tests
# ------------------------------------------------------------------------------

def test_user_registration_and_jwt_cookie(client):
    """Verify registration creates user, returns token, sets cookie, and does not leak password."""
    payload = {
        "email": "alice@example.com",
        "username": "alice",
        "password": "SuperSecretPassword123",
    }
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 201
    data = resp.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "alice@example.com"
    assert data["user"]["username"] == "alice"
    assert "password" not in data["user"]
    assert "hashed_password" not in data["user"]

    # Verify HTTP-only cookie
    assert "movierec_access_token" in resp.cookies


def test_duplicate_registration_fails(client):
    """Verify duplicate email and duplicate username are rejected with 409 Conflict."""
    payload1 = {"email": "alice@example.com", "username": "alice2", "password": "Password123!"}
    resp1 = client.post("/api/v1/auth/register", json=payload1)
    assert resp1.status_code == 409

    payload2 = {"email": "other@example.com", "username": "alice", "password": "Password123!"}
    resp2 = client.post("/api/v1/auth/register", json=payload2)
    assert resp2.status_code == 409


def test_user_login_success_and_failure(client):
    """Verify login with valid credentials succeeds and invalid fails with 401."""
    # Success
    resp = client.post("/api/v1/auth/login", json={"username_or_email": "alice", "password": "SuperSecretPassword123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()

    # Wrong password
    resp_wrong = client.post("/api/v1/auth/login", json={"username_or_email": "alice", "password": "WrongPassword"})
    assert resp_wrong.status_code == 401


def test_unauthenticated_protected_routes_blocked(client):
    """Verify that unauthenticated requests to protected endpoints return 401."""
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.get("/api/v1/ratings/me").status_code == 401
    assert client.get("/api/v1/watchlist/me").status_code == 401
    assert client.get("/api/v1/recommendations/me").status_code == 401


# ------------------------------------------------------------------------------
# 2. Strict User Data Isolation Tests
# ------------------------------------------------------------------------------

def test_user_data_isolation_between_accounts(client):
    """
    STRICT USER ISOLATION INVARIANT:
    Prove that User B cannot view, modify, or delete User A's ratings or watchlist.
    """
    # Register User A
    resp_a = client.post("/api/v1/auth/register", json={"email": "usera@test.com", "username": "usera", "password": "PasswordA123"})
    token_a = resp_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Register User B
    resp_b = client.post("/api/v1/auth/register", json={"email": "userb@test.com", "username": "userb", "password": "PasswordB123"})
    token_b = resp_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A submits rating for Movie 1 (Toy Story) and adds Movie 2 to Watchlist
    client.post("/api/v1/ratings", json={"movie_id": 1, "rating": 5.0}, headers=headers_a)
    client.post("/api/v1/watchlist", json={"movie_id": 2}, headers=headers_a)

    # User A verifies their data
    ratings_a = client.get("/api/v1/ratings/me", headers=headers_a).json()
    assert len(ratings_a) == 1
    assert ratings_a[0]["movie_id"] == 1

    watchlist_a = client.get("/api/v1/watchlist/me", headers=headers_a).json()
    assert len(watchlist_a) == 1
    assert watchlist_a[0]["movie_id"] == 2

    # User B checks their ratings and watchlist -> MUST BE EMPTY (0 items)
    ratings_b = client.get("/api/v1/ratings/me", headers=headers_b).json()
    assert len(ratings_b) == 0

    watchlist_b = client.get("/api/v1/watchlist/me", headers=headers_b).json()
    assert len(watchlist_b) == 0

    # User B tries to delete Movie 1 from their ratings -> 404 (does not exist in B's profile)
    del_resp = client.delete("/api/v1/ratings/1", headers=headers_b)
    assert del_resp.status_code == 404

    # User A's rating remains intact
    ratings_a_after = client.get("/api/v1/ratings/me", headers=headers_a).json()
    assert len(ratings_a_after) == 1


# ------------------------------------------------------------------------------
# 3. Recommendation Endpoints & Cold-Start Tests
# ------------------------------------------------------------------------------

def test_recommendation_cold_start_fallback_and_folding(client):
    """Verify recommendation routing: < 3 ratings uses Popularity, >= 3 ratings uses SVD folding."""
    # Register User C
    resp_c = client.post("/api/v1/auth/register", json={"email": "userc@test.com", "username": "userc", "password": "PasswordC123"})
    headers_c = {"Authorization": f"Bearer {resp_c.json()['access_token']}"}

    # 0 ratings -> Popularity cold-start fallback
    rec_0 = client.get("/api/v1/recommendations/me?n=5", headers=headers_c).json()
    assert rec_0["is_cold_start"] is True
    assert rec_0["strategy"] == "popularity_cold_start"
    assert len(rec_0["items"]) == 5

    # Add 1 rating (< 3) -> Still cold-start
    client.post("/api/v1/ratings", json={"movie_id": 1, "rating": 5.0}, headers=headers_c)
    rec_1 = client.get("/api/v1/recommendations/me?n=5", headers=headers_c).json()
    assert rec_1["is_cold_start"] is True
    assert rec_1["strategy"] == "popularity_cold_start"
    # Rated movie 1 must be excluded
    assert 1 not in [it["movie_id"] for it in rec_1["items"]]

    # Add 2 more ratings (total 3 ratings) -> Personalized SVD folding active!
    client.post("/api/v1/ratings", json={"movie_id": 50, "rating": 5.0}, headers=headers_c)  # Star Wars
    client.post("/api/v1/ratings", json={"movie_id": 100, "rating": 4.0}, headers=headers_c) # Fargo

    rec_3 = client.get("/api/v1/recommendations/me?n=5", headers=headers_c).json()
    assert rec_3["is_cold_start"] is False
    assert rec_3["strategy"] == "svd_personalized_folding"
    assert len(rec_3["items"]) == 5

    # Ensure none of the 3 rated movies appear in recommendations
    recommended_mids = [it["movie_id"] for it in rec_3["items"]]
    assert 1 not in recommended_mids
    assert 50 not in recommended_mids
    assert 100 not in recommended_mids


# ------------------------------------------------------------------------------
# 4. Catalog Search and Poster Fallback Tests
# ------------------------------------------------------------------------------

def test_catalog_search_and_similar_movies(client):
    """Verify movie search and item similarity endpoints."""
    # Search
    resp = client.get("/api/v1/movies?q=Toy Story")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert any("Toy Story" in item["title"] for item in data["items"])

    # Similar movies
    resp_sim = client.get("/api/v1/movies/1/similar?n=5")
    assert resp_sim.status_code == 200
    similar_items = resp_sim.json()
    assert len(similar_items) == 5
    # Target item 1 should not be in similar items
    assert all(it["movie_id"] != 1 for it in similar_items)


def test_poster_svg_fallback_endpoint(client):
    """Verify that fallback SVG poster endpoint delivers valid SVG content."""
    resp = client.get("/api/v1/posters/fallback/1")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("image/svg+xml")
    assert "<svg" in resp.text
    assert "</svg>" in resp.text
