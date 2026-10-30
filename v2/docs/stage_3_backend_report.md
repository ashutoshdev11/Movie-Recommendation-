# MovieRec Version 2 — Stage 3: FastAPI Backend & User Authentication Report

**Date:** 2026-10-30  
**Phase/Stage:** Stage 3 (FastAPI Backend, SQLAlchemy 2.0, Authentication, User Isolation, & TMDB Service)  
**Status:** Completed & Verified  

---

## 1. Backend Architecture & Files Created

The complete backend for MovieRec Version 2 was constructed strictly inside `v2/backend/` using modern Python, FastAPI, and SQLAlchemy 2.0:

```
v2/backend/
├── app/
│   ├── api/
│   │   ├── deps.py                      # JWT cookie & header extraction, active user validation
│   │   └── v1/
│   │       ├── auth.py                  # Register, login, logout, current user (/me)
│   │       ├── movies.py                # Catalog search, genres, details, trending, similar
│   │       ├── ratings.py               # User rating CRUD with server-side ownership
│   │       ├── watchlist.py             # User watchlist CRUD with server-side ownership
│   │       ├── recommendations.py       # Personalized SVD folding-in & guest recommendations
│   │       ├── posters.py               # Holographic SVG artwork delivery
│   │       └── router.py                # Aggregated v1 API router
│   ├── core/
│   │   ├── config.py                    # Pydantic Settings (secrets, JWT, CORS, database, TMDB)
│   │   ├── database.py                  # SQLAlchemy 2.0 engine, sessionmaker, declarative Base
│   │   └── security.py                  # Argon2id password hashing & JWT token encoding/decoding
│   ├── db/
│   │   └── models.py                    # User, UserRating, WatchlistItem models
│   ├── schemas/
│   │   ├── all_schemas.py               # Input validation models & response schemas
│   │   └── __init__.py
│   ├── services/
│   │   ├── poster_service.py            # TMDB client with local disk caching & SVG fallback
│   │   └── recommender_service.py       # V2 artifact loader, catalog search, SVD folding-in
│   └── main.py                          # FastAPI application, CORS middleware, table init
├── artifacts/                           # V2 model artifacts (SVD-1M, Popularity-1M, metrics)
├── cache/posters/                       # Local disk cache for poster metadata
├── tests/
│   ├── test_dataset.py                  # 8 tests: ML-1M ingestion, split integrity
│   ├── test_models.py                   # 6 tests: SVD/Pop fitting, artifact loading, folding-in
│   └── test_api.py                      # 8 tests: Auth, JWT, user isolation, ratings, recs
```

---

## 2. API Endpoints Implemented

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/v1/auth/register` | Register new user with Argon2id hash & set HTTP-only cookie | No |
| `POST` | `/api/v1/auth/login` | Authenticate credentials, issue JWT & set HTTP-only cookie | No |
| `POST` | `/api/v1/auth/logout` | Clear HTTP-only authentication cookie | No |
| `GET` | `/api/v1/auth/me` | Fetch active user profile (ID, username, email) | **Yes (JWT)** |
| `GET` | `/api/v1/movies` | Paginated catalog search by title substring and/or genre | No |
| `GET` | `/api/v1/movies/genres` | List all 18 MovieLens 1M genres | No |
| `GET` | `/api/v1/movies/trending`| Top 12 most-rated catalog titles | No |
| `GET` | `/api/v1/movies/top-rated`| Top 12 critically acclaimed titles (Bayesian damped) | No |
| `GET` | `/api/v1/movies/{id}` | Detailed movie metadata + artwork links | No |
| `GET` | `/api/v1/movies/{id}/similar` | Top-$N$ similar movies via 30D SVD latent cosine angle | No |
| `POST` | `/api/v1/ratings` | Submit or update movie rating ($1.0$ to $5.0$) | **Yes (JWT)** |
| `GET` | `/api/v1/ratings/me` | Fetch active user's saved rating history | **Yes (JWT)** |
| `DELETE` | `/api/v1/ratings/{id}` | Delete rating from user profile | **Yes (JWT)** |
| `POST` | `/api/v1/watchlist` | Add movie to user's saved watchlist | **Yes (JWT)** |
| `GET` | `/api/v1/watchlist/me` | Fetch user's saved watchlist | **Yes (JWT)** |
| `DELETE` | `/api/v1/watchlist/{id}`| Remove movie from user's watchlist | **Yes (JWT)** |
| `GET` | `/api/v1/recommendations/me` | Personalized SVD folding-in for logged-in user | **Yes (JWT)** |
| `POST` | `/api/v1/recommendations/anonymous` | Real-time recommendations for unauthenticated guests | No |
| `GET` | `/api/v1/posters/fallback/{id}` | Serve sleek holographic SVG poster placeholder | No |
| `GET` | `/health` | Service health and model status probe | No |

---

## 3. Authentication & Security Measures

1. **Argon2id Password Hashing**:
   - `pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")`.
   - Resistant to GPU and ASIC brute-force attacks via memory-hard parameters.
   - Plaintext passwords are never logged, stored, or returned in any API schema.
2. **Dual JWT Transmission**:
   - Primary: Secure, `HTTP-only` cookie (`movierec_access_token`) preventing cross-site scripting (XSS) token theft.
   - Secondary: `Authorization: Bearer <token>` header for cross-origin SPA requests.
3. **Short-Lived Access Tokens**:
   - Signed with `HS256`, 60-minute expiration, and cryptographic salt.
4. **Input Sanitization**:
   - Pydantic models validate email format, username alphanumeric constraints (`3-50` chars), and rating bounds ($[1.0, 5.0]$).

---

## 4. Database Schema (SQLAlchemy 2.0)

```sql
-- 1. Users Table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 2. User Ratings Table
CREATE TABLE user_ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    movie_id INTEGER NOT NULL,
    rating FLOAT NOT NULL CHECK (rating >= 1.0 AND rating <= 5.0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UNIQUE(user_id, movie_id)
);

-- 3. Watchlists Table
CREATE TABLE user_watchlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    movie_id INTEGER NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UNIQUE(user_id, movie_id)
);
```

- **ID Separation**: Internal account IDs (`users.id`) are completely independent of MovieLens 1M benchmark user IDs.

---

## 5. Strict User Isolation Verification

Verified via `test_user_data_isolation_between_accounts` in `v2/backend/tests/test_api.py`:
- User A created a rating for Movie 1 and added Movie 2 to their watchlist.
- User B logged in with their own token and queried `/api/v1/ratings/me` and `/api/v1/watchlist/me`.
- Result: User B received **0 items** in both responses.
- User B attempted to delete User A's rating via `DELETE /api/v1/ratings/1` $\to$ rejected with **404 Not Found** (record does not exist in User B's scope).
- User A's data was verified to remain completely intact and uncorrupted.

---

## 6. Recommendation Integration Verification

Verified via `test_recommendation_cold_start_fallback_and_folding`:
- **0 Ratings in DB**: `/api/v1/recommendations/me` returns `is_cold_start=True` and `strategy="popularity_cold_start"`.
- **1-2 Ratings in DB**: Still returns `strategy="popularity_cold_start"`, but strictly excludes the user's rated movie from recommendations.
- **$\ge 3$ Ratings in DB**: Automatically transitions to `strategy="svd_personalized_folding"`. User ratings are projected onto right singular vectors ($p = x V$, $\Delta = p V^T$), generating personalized recommendations in $< 3$ ms while excluding all rated movies.

---

## 7. TMDB Configuration & Artwork Fallback Status

- **TMDB API Key Environment Variable**: Configured via `TMDB_API_KEY` in `.env.v2` or system environment.
- **Disk Caching**: When an artwork match is retrieved, metadata is written to `v2/backend/cache/posters/poster_{id}.json` to prevent duplicate API queries.
- **Graceful Holographic SVG Fallbacks**: When `TMDB_API_KEY` is not present or when network requests fail, the service dynamically serves a customized futuristic SVG poster via `GET /api/v1/posters/fallback/{movie_id}` (verified in `test_poster_svg_fallback_endpoint`).

---

## 8. Test Execution Results

### 1. V2 Full Test Suite (`v2/backend/tests/`):
- `v2/backend/tests/test_api.py`: **8 passed** (Registration, Duplicate rejection, Login/Logout, Unauthenticated 401, User isolation, Recommendation routing, Catalog search, SVG fallback).
- `v2/backend/tests/test_dataset.py`: **8 passed** (Dimensions, Integrity, Year parsing, Demographics, Statistics, 60/20/20 split, Temporal ordering invariant, Processed storage).
- `v2/backend/tests/test_models.py`: **6 passed** (Popularity scoring, SVD bounds & seen filtering, Artifact equivalence, Profile folding-in, Seed reproducibility, Production artifact loading).
- **Total V2 Tests:** **22 passed in 7.23s** (100% pass rate).

### 2. Version 1 Regression Suite (`tests/`):
- **Total V1 Tests:** **53 passed in 17.37s** (0 errors, 0 regressions).

---

## 9. Version 1 Protection Verification

All 9 protected Version 1 files maintain identical SHA-256 hashes:
- `src/recsys/service.py`: `DC5112DF428587AB0CCEF19DD3BB57369445D42B0E5857D6A9660353A32F3714` (Unmodified)
- `src/recsys/models/svd.py`: `4C34DE8AB3F982BA1A3BBC91EF3EA96AFD225BD7BEA954FBF3EAE449B506BE3B` (Unmodified)
- `src/recsys/models/popularity.py`: `6D2774E0F4AB719D658085EFA6D134A6974DBAAF9BF6528A74ACBE0D3AC5DED4` (Unmodified)
- `src/recsys/data.py`: `EF14EA3209E00204DAE8727B0084F3B264643942579D5F2C38FEF39433DDC788` (Unmodified)
- `src/recsys/split.py`: `4BA0CDB4C71B2BD58B9000B6BE9BA5263195F29C86E17B38B2D6887E179278FD` (Unmodified)
- `src/recsys/evaluation.py`: `3C93F268A86400226B6D47AD2500EE3B41968764CE90E5E85624772DDC471712` (Unmodified)
- `tests/unit/test_app.py`: `09E3CE0BB117039658BE8D8F675C41EAE7BECCCE9C5CF938D82588947AA2C4C6` (Unmodified)
- `PROJECT_STATUS.md`: `1625D64BE32F2A4458103253731848206AB5C8AD2B8894F4908F59DD73244537` (Unmodified)
- `RULES.md`: `C2B644F33A70A5C17AC5D8F089204D678354729C20AE48697F9383E37E005A54` (Unmodified)

---

## 10. Known Limitations

1. **Guest Recommendations**: Unauthenticated users using `/recommendations/anonymous` maintain state solely within their client session memory; persistence requires account registration.
2. **External Rate Limits**: When using a live TMDB API key, third-party network quotas apply. The local disk cache mitigates this by permanently storing all queried posters.
