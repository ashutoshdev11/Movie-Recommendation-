# System Architecture Documentation — MovieRec Version 2

## 1. Architectural Overview

MovieRec Version 2 is a production-grade, full-stack movie recommendation and discovery platform built upon the **MovieLens 1M** dataset (1,000,209 ratings across 3,883 movies and 6,040 users). It completely separates backend inference and state management from an original, interactive 3D frontend interface.

```
+-------------------------------------------------------------------------------+
|                             CLIENT / BROWSER                                  |
|                                                                               |
|   React 18 + TypeScript + Three.js + Tailwind CSS + Lucide Icons (Port 5173)   |
|                                                                               |
|   [ 3D Cosmic Hero ]     [ Holographic 3D Cards ]     [ Profile Builder ]    |
|   [ Catalog & Search ]   [ Latent Similarity ]        [ Auth Modal ]          |
+-------------------------------------------------------------------------------+
                                    |
             HTTP-Only Cookies / REST API JSON (/api/v1/*)
                                    |
+-------------------------------------------------------------------------------+
|                           FASTAPI BACKEND (Port 8000)                         |
|                                                                               |
|  +--------------------+  +--------------------+  +-------------------------+  |
|  |   Auth & Security  |  |    User Data DB    |  |   Recommender Service   |  |
|  | - Argon2id Hashing |  | - Users Table      |  | - SVD Model (k=30)      |  |
|  | - JWT Access Token |  | - UserRatings Table|  | - Damped Pop (m=50.0)   |  |
|  | - HTTP-Only Cookie |  | - Watchlist Table  |  | - Online Folding-In (<3ms)|
|  +--------------------+  +--------------------+  +-------------------------+  |
|                                    |                           |              |
|                             SQLite / Postgres            Precomputed 30D      |
|                                                              Item Factors     |
+-------------------------------------------------------------------------------+
```

---

## 2. Layered Component Decomposition

### 2.1 Frontend Tier (`v2/frontend/`)
- **Vite & React 18 (TypeScript):** Single-page application using client-side routing via React Router DOM 6.
- **Three.js WebGL Engine:** Dynamic cosmic starfield with 1,200 particle vertices and a wireframe holographic prism responding to user pointer parallax with smooth frame-rate capping and reduced-motion fallback.
- **Holographic 3D Card Engine:** Dynamic 3D card tilt calculating angle coordinates relative to element center with real-time radial specular glare.
- **State Management & Context:** Centralized `AuthContext` managing user authentication, guest vs registered sessions, and global modal state.
- **Stateless Client Security:** Zero authentication tokens stored in `localStorage` or `sessionStorage`. All authentication relies on browser-enforced `HttpOnly`, `SameSite=Lax` cookies.

### 2.2 Backend Application Tier (`v2/backend/app/`)
- **FastAPI Framework:** Asynchronous high-performance REST API with automated OpenAPI / Swagger documentation at `/docs`.
- **API Routing Modularization (`app/api/v1/`):**
  - `auth.py`: Registration, login, logout, current user verification (`/me`).
  - `movies.py`: Full catalog querying, search, genre filtering, details, and top-N latent cosine similarity.
  - `ratings.py`: User rating persistence and deletion with cascade recalculations.
  - `watchlist.py`: User watchlist management with existence checking.
  - `recommendations.py`: Dual-mode recommendation engine supporting authenticated online folding-in, cold-start fallback, and anonymous guest calibration.
  - `posters.py`: TMDB artwork retrieval with disk caching and programmatic SVG geometric poster generation.

### 2.3 Machine Learning Inference Tier (`v2/backend/app/ml/`)
- **Truncated SVD Recommender ($k=30$):**
  - Centered matrix factorization: $R - \mu_u \approx U \Sigma V^T$.
  - Fixed random seed: 42 for exact determinism.
  - Fast online profile folding-in: Projects arbitrary user ratings vector $r_{new}$ onto precomputed right singular vectors $V$:
    $$\hat{u}_{new} = (r_{new} - \mu_{new}) V \Sigma^{-1}$$
    $$\hat{r}_{new, i} = \mu_{new} + \hat{u}_{new} \Sigma v_i^T$$
  - Real-time latency: $<3\text{ ms}$ per user inference call.
- **Bayesian Damped Popularity Baseline ($m=50.0$):**
  - Smooth shrinkage toward dataset global mean ($\mu \approx 3.58$):
    $$\text{score}_i = \frac{\sum r_{ui} + m \cdot \mu}{N_i + m}$$
  - Applied automatically as cold-start fallback for users with fewer than 3 ratings.

### 2.4 Data & Persistence Tier
- **Relational Database (`app/db/models.py`):**
  - Managed via SQLAlchemy 2.0 ORM.
  - SQLite backend by default (`sqlite:///movierec_v2.db`), architected with standard column types and foreign keys for immediate drop-in compatibility with PostgreSQL.
- **Preprocessed Datasets & ML Artifacts:**
  - `movies_metadata.csv.gz`: 3,883 movies indexed with genres, release years, vote counts, and Bayesian average scores.
  - `v2_svd_k30.npz`: Compressed singular vectors ($U, \Sigma, V^T$), mappings, and seen item indexes.
  - `v2_popularity_baseline.json`: Damped Bayesian scores and interaction frequencies.

---

## 3. Strict Boundary Invariants

1. **Complete Isolation from Version 1:**
   - All V2 code, models, datasets, dependencies, and docs live strictly inside `v2/`.
   - V1 files maintain bit-for-bit SHA-256 hash identity and pass all 53 existing regression tests.
2. **Identity Separation:**
   - Website user accounts (`users.id`, auto-incremented primary keys) are strictly segregated from historical MovieLens user IDs (1 to 6,040).
3. **Temporal Leakage Prevention:**
   - Evaluation splits enforce strict chronological boundaries ($\max(t_{\text{train}}) \le \min(t_{\text{val}}) \le \max(t_{\text{val}}) \le \min(t_{\text{test}})$) so no future ratings ever leak into training.
