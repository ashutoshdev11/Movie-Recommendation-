# Phase 4 Independent Audit Report: Recommendation Service and Streamlit App

**Date:** 2026-10-30  
**Phase Audited:** Phase 4 (Service and Streamlit App)  
**Auditor:** Independent Audit Process (System Rules Enforcement)  
**Overall Verdict:** **PASS**

---

## 1. Scope and Files Inspected

The audit independently inspected and verified actual workspace code, web application workflows, public API contracts, test suites, and project documentation:

- `RULES.md`
- `docs/phases/phase_4.md`
- `docs/spec.md`
- `docs/architecture.md`
- `docs/service_interface.md`
- `docs/decisions.md`
- `docs/reports/phase_4_report.md`
- `PROJECT_STATUS.md`
- `src/recsys/service.py`
- `app/streamlit_app.py`
- `tests/unit/test_service.py`
- `tests/unit/test_app.py`
- `results/artifacts/`

---

## 2. Verification of Audit Checklist and Criteria

### 1. Service Layer & Model Encapsulation (`src/recsys/service.py`)
- **Status:** **PASS**
- **Evidence:**
  - `RecommenderService` properly wraps the Phase 3 champion model (`TruncatedSVDRecommender`, $n=20$) and cold-start model (`PopularityBaseline`, $m=50.0$).
  - `recommend_for_user(user_id, n, filter_genres)` produces recommendations matching the direct model call exactly ($< 10^{-14}$ floating point discrepancy; verified via `test_service_recommend_for_user_matches_model_direct`).
  - No previously rated or seen items are ever returned (`test_no_already_rated_movies_returned`).
  - All predicted scores remain bounded in $[1.0, 5.0]$ (`test_predictions_bounded_in_1_to_5`).

### 2. Online SVD Profile Folding-In & Latent Projection
- **Status:** **PASS**
- **Evidence:**
  - Mathematical implementation of `_recommend_svd_folding`:
    $$x_i = r_i - \mu_{\text{prof}}, \quad p = x V, \quad \Delta = p V^T, \quad \hat{r} = \text{clip}(\mu_{\text{prof}} + \Delta, 1.0, 5.0)$$
  - Inspection confirms the folding-in does not retrain, update, or alter fitted model parameters ($U$, $\Sigma$, $V^T$).
  - Empirical benchmark over 100 consecutive requests: **2.35 ms average request latency**, enabling real-time interactive UI updates without multi-second delays.

### 3. Transparent Cold-Start Fallback & Threshold Boundaries
- **Status:** **PASS**
- **Evidence:**
  - Boundary behavior verified empirically:
    - 0 ratings: raises `ValueError("User profile cannot be empty.")`.
    - 1 or 2 ratings: triggers `_recommend_popularity`, sets `is_cold_start=True`, labels `strategy="popularity_cold_start"`.
    - 3 ratings: triggers `_recommend_svd_folding`, sets `is_cold_start=False`, labels `strategy="svd_personalized"`.
  - Cold-start explanations explicitly cite Bayesian Popularity Baseline statistics (rating count and average rating).
  - Verified in `test_recommend_for_profile_cold_start_fallback` and `test_recommend_for_profile_personalized_svd`.

### 4. Movie Catalog Search & Item Similarity
- **Status:** **PASS**
- **Evidence:**
  - `search_movies(query)` performs lowercase substring matching, sorting matches by popularity (rating count descending). Returns empty list on whitespace or unmatched queries (`test_search_movies`).
  - `similar_movies(item_id, n)` computes cosine similarity across normalized 20-dimensional SVD item latent factor vectors ($V_{\text{norm}} \cdot v_i$). Target movie is excluded from its own neighbors. For *Toy Story (1995)*, top neighbors include *Beauty and the Beast*, *The Lion King*, and *Aladdin* (`test_similar_movies`).

### 5. Grounded Explanation Generation
- **Status:** **PASS**
- **Evidence:**
  - `_explain_recommendation` computes latent cosine similarity between the candidate movie and the user's positively rated movies ($r \ge 3.0$).
  - Explanations cite the specific rated movie with highest positive similarity ($s > 0.10$) and include the similarity coefficient (e.g. `Recommended because you rated 'Star Wars (1977)' (5.0 stars) (similarity: 0.85)`).
  - Explanations are strictly grounded in mathematical model outputs with zero fabricated text.

### 6. Artifact Serialization & Deserialization
- **Status:** **PASS**
- **Evidence:**
  - `save_artifacts` and `load_artifacts` serialize to `results/artifacts/svd_artifacts.npz` and `results/artifacts/popularity_artifacts.json`.
  - Verified in `test_artifact_save_and_load_equivalence`: service restored from serialized artifacts produces identical recommendations to the in-memory instance.

### 7. Input Validation & Error Handling
- **Status:** **PASS**
- **Evidence:**
  - Verified in `test_input_validation_and_clear_errors`:
    - Unknown user ID $\to$ `ValueError("Unknown user ID: ...")`
    - Unknown movie ID $\to$ `ValueError("Movie ID ... not found in catalog")`
    - Rating $> 5.0$ or $< 1.0$ $\to$ `ValueError("Ratings must be between 1.0 and 5.0")`
    - Empty profile $\to$ `ValueError("User profile cannot be empty")`
    - Non-positive $N$ $\to$ `ValueError("n must be a positive integer")`

### 8. Streamlit Web Application (`app/streamlit_app.py`)
- **Status:** **PASS**
- **Evidence:**
  - Workflows verified via `streamlit.testing.v1.AppTest` (`tests/unit/test_app.py`):
    - App initial load without uncaught exceptions (`test_app_initial_load`).
    - Empty profile guidance message rendered cleanly (`test_app_empty_profile_guidance`).
    - Adding ratings renders profile table and triggers personalized SVD recommendations (`test_app_rate_movie_and_personalized_recommendation`).
    - Cold-start profile displays warning banner (`test_app_cold_start_fallback_label`).
    - Dynamic $N$ recommendation slider updates cleanly (`test_app_change_n_slider`).
    - Multi-genre filtering filters recommendations accurately (`test_app_genre_filter`).
    - Historical User Inspection mode retrieves recommendations for user IDs ($1..943$) (`test_app_inspect_historical_user_mode`).
    - Movie Similarity Explorer mode renders latent cosine neighbors (`test_app_movie_similarity_explorer_mode`).
  - Architecture decoupling: the Streamlit app delegates all computation to `RecommenderService` and contains zero duplicated collaborative filtering algorithms or model logic.
  - Safe HTML rendering: `render_table()` uses `df.to_html(..., escape=True)`, guaranteeing that user-controlled movie strings cannot execute script injection or corrupt DOM markup.
  - Zero non-functional placeholder buttons and zero fabricated posters/metadata.

### 9. Independent Test Suite Execution
- **Status:** **PASS**
- **Evidence:**
  - Executed `pytest -v` independently during audit:
    ```powershell
    & ".\.venv\Scripts\pytest.exe" -v
    ```
  - Observed output: **49 passed in 20.97s** (100% pass rate).
  - Breakdown: `test_data.py` (6), `test_split.py` (4), `test_models.py` (15), `test_evaluation.py` (5), `test_service.py` (11), `test_app.py` (8).
  - Zero failures, zero warnings, zero regressions.

### 10. Phase Boundaries & State
- **Status:** **PASS**
- **Evidence:**
  - Phase 4 deliverables are complete: `src/recsys/service.py`, `app/streamlit_app.py`, `docs/service_interface.md`, `docs/reports/phase_4_report.md`.
  - `docs/decisions.md` updated with 4 Phase 4 architectural decisions.
  - No Phase 5 code or deliverables exist (`docs/viva_prep.md`, `docs/final_readiness_report.md`, and README are uncreated).

---

## 3. Defects and Findings

### Critical Defects
- *None.*

### Major Defects
- *None.*

### Minor Findings & Optional Improvements
1. **Streamlit App Local Launch Documentation (Optional Improvement for Phase 5):**
   In the final README / documentation (Phase 5), explicitly document the PowerShell command to launch Streamlit outside the sandbox for browser interaction:
   `& ".\.venv\Scripts\streamlit.exe" run app/streamlit_app.py`.

---

## 4. Required Fixes
- *None.* All mandatory acceptance criteria and specifications are verified.

---

## 5. Audit Verdict

**PASS**

Phase 4 has successfully delivered an industrial-grade, leakage-free collaborative filtering service layer with online SVD folding-in ($< 2.5$ ms latency), transparent cold-start handling, grounded model-signal explanations, robust input validation, and an interactive multi-mode Streamlit web application verified with 49 passing automated unit, integration, and AppTest tests.

---

## 6. Next Valid Commands

- `START PHASE 5` (Final testing and documentation)
- `EXPLAIN <topic>`
- `STATUS`
- `STOP`
