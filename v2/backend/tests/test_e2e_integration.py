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
from app.core.security import verify_password, get_password_hash
from app.services.recommender_service import recommender_service

TEST_DB_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def client():
    return TestClient(app)

# -------------------------------------------------------------
# 1. Full-Stack Auth, Hashing & Cookie Flow
# -------------------------------------------------------------
def test_argon2id_hashing_and_no_leak():
    password = "SuperSecretPassword123!"
    hashed = get_password_hash(password)
    assert hashed.startswith("$argon2id$")
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False

def test_full_auth_lifecycle(client):
    # Register User A
    reg_res = client.post(
        "/api/v1/auth/register",
        json={"username": "alice", "email": "alice@galaxy.com", "password": "PasswordAlice123!"},
    )
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert "user" in reg_data
    user_a = reg_data["user"]
    assert user_a["username"] == "alice"
    assert user_a["email"] == "alice@galaxy.com"
    # Verify no password hash is exposed
    assert "password" not in user_a
    assert "hashed_password" not in user_a

    # Login User A
    login_res = client.post(
        "/api/v1/auth/login",
        json={"username_or_email": "alice", "password": "PasswordAlice123!"},
    )
    assert login_res.status_code == 200
    assert "movierec_access_token" in login_res.cookies

    # Get /me using cookie
    me_res = client.get("/api/v1/auth/me")
    assert me_res.status_code == 200
    assert me_res.json()["username"] == "alice"

    # Logout
    logout_res = client.post("/api/v1/auth/logout")
    assert logout_res.status_code == 200
    # After logout, cookie is deleted/expired
    unauth_me = client.get("/api/v1/auth/me")
    assert unauth_me.status_code == 401

# -------------------------------------------------------------
# 2. Strict User Data Isolation
# -------------------------------------------------------------
def test_strict_user_data_isolation(client):
    # Create User A & User B
    resp_a = client.post(
        "/api/v1/auth/register",
        json={"username": "user_iso_a", "email": "iso_a@test.com", "password": "PasswordA123!"},
    )
    headers_a = {"Authorization": f"Bearer {resp_a.json()['access_token']}"}

    resp_b = client.post(
        "/api/v1/auth/register",
        json={"username": "user_iso_b", "email": "iso_b@test.com", "password": "PasswordB123!"},
    )
    headers_b = {"Authorization": f"Bearer {resp_b.json()['access_token']}"}

    # User A rates movie 1 and adds movie 1 to watchlist
    r1 = client.post("/api/v1/ratings", json={"movie_id": 1, "rating": 5.0}, headers=headers_a)
    assert r1.status_code == 201
    w1 = client.post("/api/v1/watchlist", json={"movie_id": 1}, headers=headers_a)
    assert w1.status_code == 201

    # Check User A data
    a_ratings = client.get("/api/v1/ratings/me", headers=headers_a).json()
    a_watchlist = client.get("/api/v1/watchlist/me", headers=headers_a).json()
    assert len(a_ratings) == 1
    assert len(a_watchlist) == 1
    assert a_ratings[0]["movie_id"] == 1

    # User B checks their ratings and watchlist
    b_ratings = client.get("/api/v1/ratings/me", headers=headers_b).json()
    b_watchlist = client.get("/api/v1/watchlist/me", headers=headers_b).json()

    # User B MUST see an empty list (complete isolation)
    assert len(b_ratings) == 0
    assert len(b_watchlist) == 0

    # User B attempting to delete User A's rating or watchlist item
    del_r = client.delete("/api/v1/ratings/1", headers=headers_b)
    assert del_r.status_code == 404

    del_w = client.delete("/api/v1/watchlist/1", headers=headers_b)
    assert del_w.status_code == 404

    # User A data remains intact
    a_ratings_after = client.get("/api/v1/ratings/me", headers=headers_a).json()
    assert len(a_ratings_after) == 1
    assert a_ratings_after[0]["movie_id"] == 1

# -------------------------------------------------------------
# 3. Model Loading & Online SVD Folding-In Verification
# -------------------------------------------------------------
def test_svd_artifacts_loaded():
    assert recommender_service.svd_model is not None
    assert recommender_service.popularity_model is not None
    assert recommender_service.svd_model.n_factors == 30
    assert recommender_service.popularity_model.damping == 50.0
    assert recommender_service.movies_df is not None
    assert len(recommender_service.movies_df) == 3883

def test_cold_start_vs_folded_svd_recommendations(client):
    # Register new user with 0 ratings
    resp = client.post(
        "/api/v1/auth/register",
        json={"username": "cold_user", "email": "cold@test.com", "password": "PasswordCold123!"},
    )
    headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}

    # When user has < 3 ratings, backend uses popularity cold start
    cold_recs = client.get("/api/v1/recommendations/me?n=5", headers=headers).json()
    assert cold_recs["is_cold_start"] is True
    assert cold_recs["strategy"] == "popularity_cold_start"
    assert len(cold_recs["items"]) == 5

    # Now submit 3 ratings
    client.post("/api/v1/ratings", json={"movie_id": 260, "rating": 5.0}, headers=headers)   # Star Wars IV
    client.post("/api/v1/ratings", json={"movie_id": 1196, "rating": 5.0}, headers=headers)  # Star Wars V
    client.post("/api/v1/ratings", json={"movie_id": 1210, "rating": 5.0}, headers=headers)  # Star Wars VI

    # Query personalized recommendations again
    svd_recs = client.get("/api/v1/recommendations/me?n=5", headers=headers).json()
    assert svd_recs["is_cold_start"] is False
    assert svd_recs["strategy"] == "svd_personalized_folding"
    assert len(svd_recs["items"]) == 5
    # The rated movies should be excluded from recommendations
    rec_ids = [m["movie_id"] for m in svd_recs["items"]]
    assert 260 not in rec_ids
    assert 1196 not in rec_ids
    assert 1210 not in rec_ids

# -------------------------------------------------------------
# 4. Interactive Anonymous Fold-In
# -------------------------------------------------------------
def test_anonymous_fold_in_endpoint(client):
    res = client.post(
        "/api/v1/recommendations/anonymous",
        json={
            "ratings": {
                1: 5.0,     # Toy Story
                3114: 5.0,  # Toy Story 2
                2355: 4.5,  # Bug's Life
            },
            "n": 6,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["strategy"] == "svd_personalized_folding"
    assert data["is_cold_start"] is False
    assert len(data["items"]) == 6

# -------------------------------------------------------------
# 5. Catalog Search, Filter & Similar Endpoints
# -------------------------------------------------------------
def test_movie_catalog_and_similarity(client):
    # Catalog search
    res = client.get("/api/v1/movies?q=Matrix")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    assert any("Matrix" in m["title"] for m in data["items"])

    # Similar movies
    sim_res = client.get("/api/v1/movies/2571/similar?n=4")
    assert sim_res.status_code == 200
    sim_data = sim_res.json()
    assert len(sim_data) == 4
    assert all("movie_id" in s for s in sim_data)
    assert all("title" in s for s in sim_data)
    assert all(s["movie_id"] != 2571 for s in sim_data)

# -------------------------------------------------------------
# 6. Poster Endpoints Verification
# -------------------------------------------------------------
def test_poster_routes(client):
    test_ids = [1196, 2858, 1210, 260, 2028]
    for mid in test_ids:
        # Test standard route /api/v1/posters/{mid}
        res = client.get(f"/api/v1/posters/{mid}", follow_redirects=False)
        assert res.status_code in [200, 307]
        if res.status_code == 200:
            assert res.headers["content-type"].startswith("image/svg+xml")
            assert "<svg" in res.text

        # Test placeholder query param
        res_ph = client.get(f"/api/v1/posters/{mid}?placeholder=true")
        assert res_ph.status_code == 200
        assert res_ph.headers["content-type"].startswith("image/svg+xml")
        assert "<svg" in res_ph.text
