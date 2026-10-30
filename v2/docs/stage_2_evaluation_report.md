# MovieRec Version 2 — Stage 2: Model Training & Evaluation Report

**Date:** 2026-10-30  
**Phase/Stage:** Stage 2 (V2 ML-1M Model Training, Selection & Evaluation)  
**Status:** Completed & Verified  

---

## 1. Models Implemented & Configurations

All training and evaluation were performed on the MovieLens 1M dataset (597,742 training ratings):

### 1. Truncated SVD Recommender (`TruncatedSVDRecommender`)
- **Latent Dimensions ($k$):** $30$ factors
- **Random Seed:** $42$ (`random_state=42` using SciPy ARPACK `svds`)
- **Rating Centering:** User mean centering ($R_{u,i} - \mu_u$)
- **Prediction Bounds:** $[\text{clip}(1.0, 5.0)]$
- **Training Runtime:** $0.73$ seconds (597,742 training ratings)

### 2. Damped Popularity Baseline (`PopularityBaseline`)
- **Damping Parameter ($m$):** $50.0$
- **Formula:** $\hat{r}_i = \frac{\sum_{u \in U_i} r_{u,i} + m \cdot \mu_0}{|U_i| + m}$
- **Training Runtime:** $0.30$ seconds

---

## 2. Evaluation Methodology & Relevance Protocol

- **Candidate Space:** All catalog items not previously rated by the user in the training partition ($I \setminus \text{Seen}_u$).
- **Relevance Threshold:** A held-out interaction is defined as relevant if and only if **$r_{u,i} \ge 4.0$** (standard academic threshold for positive recommendation utility).
- **Ranking Cutoff:** Top-10 recommendations ($K = 10$).
- **Discount Formula (NDCG@10):** Exponential relevance gain $\frac{2^{\text{rel}} - 1}{\log_2(i + 1)}$.
- **Average Precision Formula (MAP@10):** $\text{AP}@10 = \frac{1}{\min(10, |R_u^{\text{rel}}|)} \sum_{i=1}^{10} P(i) \cdot \mathbb{I}(i \in R_u^{\text{rel}})$.
- **Partition Independence:** Model selection performed strictly on the **Validation Partition** (197,656 ratings); final metrics computed on the **Held-Out Test Partition** (204,811 ratings).

---

## 3. Validation & Test Evaluation Metrics

| Partition | Model | NDCG@10 | MAP@10 | RMSE | Evaluated Users | Interactions |
|---|---|---|---|---|---|---|
| **Validation** | **TruncatedSVD ($k=30$)** | **0.0989** | **0.0509** | 1.0128 | 5,981 | 197,656 |
| **Validation** | Popularity ($m=50.0$) | 0.0477 | 0.0221 | **0.9998** | 5,981 | 197,656 |
| **Held-Out Test** | **TruncatedSVD ($k=30$)** | **0.0802** | **0.0388** | 1.0657 | 5,982 | 204,811 |
| **Held-Out Test** | Popularity ($m=50.0$) | 0.0423 | 0.0192 | **1.0149** | 5,982 | 204,811 |

---

## 4. Model Selection Reasoning

- **Pre-Committed Selection Criterion:** Ranking utility as measured by **Validation NDCG@10**.
- **Result:** **`TruncatedSVDRecommender(k=30)`** achieved a Validation NDCG@10 of **0.0989** (and MAP@10 of 0.0509), outperforming the Popularity Baseline (NDCG@10 of 0.0477) by **+107.3%**.
- **Rating-Ranking Divergence:** Although Popularity achieved a marginally lower RMSE (0.9998 vs 1.0128) because popular movies sit closer to the global centroid, its ranking capacity is severely degraded compared to personalized latent factor decomposition.
- **Champion Selection:** `TruncatedSVDRecommender(k=30)` is officially selected as the primary recommendation engine for Version 2, with `PopularityBaseline(m=50.0)` designated as the cold-start fallback when a user profile has $< 3$ ratings.

---

## 5. Artifact Paths

All generated artifacts are housed exclusively within the `v2/backend/artifacts/` directory:

| Artifact | File Size | Description |
|---|---|---|
| `v2/backend/artifacts/svd_1m_artifacts.npz` | 3,966,202 bytes | Fitted $U$, $\Sigma$, $V^T$ matrices, user means, item indices, and serialized user seen items for folding-in. |
| `v2/backend/artifacts/popularity_1m_artifacts.json` | 136,368 bytes | Damped scores, rating counts, global mean, and hyperparameters. |
| `v2/backend/artifacts/evaluation_metrics.json` | 1,842 bytes | Complete JSON evaluation records for validation and test partitions. |
| `v2/backend/artifacts/model_comparison.csv` | 448 bytes | Tabular model comparison CSV. |

---

## 6. Test Results

### 1. V2 Unit Tests (`v2/backend/tests/`):
- `test_ratings_raw_dimensions_and_types`: **PASSED**
- `test_ratings_integrity_and_bounds`: **PASSED**
- `test_movies_schema_and_year_parsing`: **PASSED**
- `test_users_demographics_schema`: **PASSED**
- `test_dataset_statistics_computation`: **PASSED**
- `test_chronological_split_partition_sizes`: **PASSED**
- `test_temporal_leakage_prevention_invariant`: **PASSED**
- `test_processed_files_exist_and_match`: **PASSED**
- `test_popularity_baseline_scores_and_recommendations`: **PASSED**
- `test_svd_recommender_prediction_bounds_and_seen_exclusion`: **PASSED**
- `test_svd_artifact_save_and_load_equivalence`: **PASSED**
- `test_svd_profile_folding_in`: **PASSED**
- `test_svd_reproducibility`: **PASSED**
- `test_production_artifacts_exist_and_load`: **PASSED**
- **Total V2 Suite:** **14 passed in 7.12s**

### 2. Version 1 Regression Suite (`tests/`):
- **Total V1 Suite:** **53 passed in 49.44s** (100% passing, 0 regressions).

---

## 7. Version 1 Protection Verification

All 9 protected Version 1 files maintain bit-for-bit SHA-256 hash identity:
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

## 8. Limitations & Known Issues

1. **Catalog Drift:** In the MovieLens 1M dataset, 82 catalog movies out of 3,883 were never rated in the 60% training partition. The recommender correctly falls back to global/user averages for these unrated items.
2. **Cold-Start Sensitivity:** Profiles with fewer than 3 ratings lack sufficient variance in singular vector projections, which is cleanly resolved by delegating to the Bayesian Damped Popularity baseline.
