# Phase 2 Completion Report: Collaborative-Filtering Engine

**Date:** 2026-10-30  
**Phase:** Phase 2 (Collaborative-Filtering Engine)  
**Status:** Completed (Ready for Audit)

---

## 1. Summary of Work Completed
- **Unified Interface Architecture (`src/recsys/models/base.py`):**
  - Implemented `BaseRecommender` defining standard contracts: `fit(train_ratings)`, `predict(user_id, item_id) -> float`, and `recommend(user_id, n, exclude_seen=True) -> list[(item_id, score)]`.
  - Built internal index mappers (`user2idx`, `item2idx`) and sparse matrix helpers (SciPy CSR).
  - Implemented deterministic candidate scoring with secondary `item_id` tie-breaking.
  - Implemented hierarchical fallback chain: item mean $\mu_i \to$ user mean $\mu_u \to$ global mean $\mu$, with all predictions clamped to $[1.0, 5.0]$.
- **Popularity Baseline (`src/recsys/models/popularity.py`):**
  - Implemented Bayesian damped mean: $\hat{r}_i = (\sum r_{ui} + m \cdot \mu) / (|U_i| + m)$ with default damping $m=10.0$ and minimum ratings threshold.
- **User-Based Collaborative Filtering (`src/recsys/models/user_knn.py`):**
  - Implemented Pearson correlation on co-rated items with user mean-centering:
    $$s(u, v) = \frac{\sum (r_{ui} - \mu_u)(r_{vi} - \mu_v)}{\sqrt{\sum (r_{ui} - \mu_u)^2} \sqrt{\sum (r_{vi} - \mu_v)^2}}$$
  - Implemented neighborhood aggregation over positive similarities ($s > 0$) with parameter $k$ and minimum overlap.
- **Item-Based Collaborative Filtering (`src/recsys/models/item_knn.py`):**
  - Implemented Adjusted Cosine similarity subtracting user rating means:
    $$s(i, j) = \frac{\sum (r_{ui} - \mu_u)(r_{uj} - \mu_u)}{\sqrt{\sum (r_{ui} - \mu_u)^2} \sqrt{\sum (r_{uj} - \mu_u)^2}}$$
  - Implemented top-$k$ item neighborhood aggregation over positive similarities.
- **Truncated SVD Matrix Factorization Benchmark (`src/recsys/models/svd.py`):**
  - Centered observed ratings by user mean to maintain sparse CSR structure (unobserved entries stay 0).
  - Integrated `scipy.sparse.linalg.svds` with configurable `n_factors` and fixed seed `42`.
  - Implemented reconstruction $\hat{r}_{ui} = \mu_u + (U_k \Sigma_k V_k^T)_{ui}$ clipped to $[1.0, 5.0]$.
- **Documentation & Math Specifications (`docs/models.md`):**
  - Authored comprehensive documentation of all formulas, parameters, edge-case behaviors, and full step-by-step hand-computed derivations on a $4 \times 5$ toy matrix.
- **Unit Testing & Verification (`tests/unit/test_models.py`):**
  - Added unit tests matching hand-derived similarity and prediction values to $< 10^{-6}$ precision.
  - Added data-isolation tests proving that modifying test partition data leaves fitted model predictions unchanged.
  - Verified edge cases: unknown user, unknown item, zero denominator, single-rating user, $k$ exceeding available neighbors, and exclusion of already-rated items.
  - Executed full test suite: **24 passed, 0 failures in 6.31s**.
  - Confirmed no hyperparameter tuning or final metric tables were generated in this phase.

---

## 2. Files Created / Changed
- `src/recsys/models/base.py` (Created)
- `src/recsys/models/popularity.py` (Created)
- `src/recsys/models/user_knn.py` (Created)
- `src/recsys/models/item_knn.py` (Created)
- `src/recsys/models/svd.py` (Created)
- `src/recsys/models/__init__.py` (Created)
- `docs/models.md` (Created)
- `tests/unit/test_models.py` (Created)
- `docs/decisions.md` (Updated with Phase 2 decisions)
- `docs/reports/phase_2_report.md` (Created)
- `PROJECT_STATUS.md` (Updated)

---

## 3. Commands and Tests Run
- `pytest -v`:
  - 24 passing tests, 0 failures, 0 warnings.
  - Runtime: 6.31s.

---

## 4. Acceptance Criteria Verification

| Acceptance Criterion | Verification Evidence | Status |
|---|---|:---:|
| All 4 models implement common interface | `test_common_interface_conformance` verified across all 4 classes. | **VERIFIED** |
| Hand-computed values match code on toy matrix (tol 1e-6) | `test_hand_computed_user_knn_similarity_and_prediction`, `test_hand_computed_item_knn_similarity`, `test_popularity_baseline_damped_mean` passed with error $< 10^{-6}$. | **VERIFIED** |
| `fit` on modified test partition gives identical results | `test_fit_isolated_from_test_partition` passed; predictions are identical. | **VERIFIED** |
| Tests cover zero denominator, 1 rating, unknown user/item, $k >$ neighbors | `test_edge_cases_unknown_ids_and_sparse_profiles`, `test_edge_case_zero_denominator_and_single_rating`, `test_k_larger_than_available_neighbors` passed. | **VERIFIED** |
| No prediction outside $[1, 5]$; no seen item in `recommend` | `test_no_already_rated_items_in_recommend` and range assertions passed. | **VERIFIED** |
| No dense full user-item matrix built for similarity | Sparse representations and lazy caching utilized; zero full dense expansion. | **VERIFIED** |
| `pytest` passes with 0 failures | Observed output: 24 passed in 6.31s. | **VERIFIED** |
| No hyperparameter tuning or final metrics table | Evaluation and tuning reserved for Phase 3. | **VERIFIED** |

---

## 5. Known Issues / Limitations
- None.

---

## 6. Unverified Criteria
- None. All Phase 2 criteria are verified with passing tests.
