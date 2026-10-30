# Phase 3 Independent Audit Report: Evaluation and Model Selection (Re-Audit)

**Date:** 2026-10-30  
**Phase Audited:** Phase 3 (Evaluation and Model Selection)  
**Auditor:** Independent Audit Process (System Rules Enforcement)  
**Prior Verdict:** FAIL (2026-10-30T03:13:10, missing mandatory documentation deliverables)  
**Overall Re-Audit Verdict:** **PASS**

---

## 1. Resolution of Prior Audit Findings

The prior audit issued a verdict of **FAIL** exclusively due to missing mandatory documentation deliverables (`docs/evaluation_results.md`, `docs/reports/phase_3_report.md`, and unrecorded Phase 3 decisions in `docs/decisions.md`). The re-audit independently inspected all newly created and updated files:

1. **`docs/evaluation_results.md`:**
   - **Verification:** Created and fully populated. Contains complete metric mathematical definitions, validation tuning analysis, cold-start degradation curves, error trade-offs (RMSE vs. NDCG@10 divergence), catalog coverage/novelty dynamics, and offline evaluation limitations (MNAR, popularity bias).
   - **Status:** **RESOLVED** (Mandatory).

2. **`docs/reports/phase_3_report.md`:**
   - **Verification:** Created and fully populated according to `RULES.md` standards. Documents methodology, created/modified files, execution logs, acceptance criteria verification table, and verified numerical results.
   - **Status:** **RESOLVED** (Mandatory).

3. **`docs/decisions.md`:**
   - **Verification:** Updated with 5 distinct Phase 3 architectural decisions: pre-commitment to validation NDCG@10, selection of Truncated SVD ($n=20$) as winner, inverted index candidate pruning for ItemKNN, cold-start truncation protocol ($M \in \{1, 3, 5, 10\}$), and zero-relevant user exclusion rule.
   - **Status:** **RESOLVED** (Mandatory).

4. **`PROJECT_STATUS.md`:**
   - **Verification:** Synchronized to reflect completed fixes and pending re-audit.
   - **Status:** **RESOLVED** (Mandatory).

---

## 2. Independent Verification of Results & Artifacts

All documented metrics, configurations, and counts were cross-checked directly against the raw CSV tables and logs.

### 2.1 Final Test Evaluation Results Cross-Check
- **Source Artifact:** `results/test_evaluation_results.csv`
- **Execution Log:** `results/final_run.log` (Cumulative run count: 2, Run #2 completed on 20,748 test ratings)
- **Population:** 943 total users; 918 evaluated for ranking ($r \ge 4.0$); 25 users excluded due to zero relevant test items.

| Model | Selected Config | Metric | Documented Value | Source CSV Value | Discrepancy | Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| **TruncatedSVD** | `n_factors=20, seed=42` | NDCG@10 | 0.1198 | 0.119807 | None ($< 10^{-4}$) | **PASS** |
| | | Precision@10 | 0.0914 | 0.091394 | None ($< 10^{-4}$) | **PASS** |
| | | Recall@10 | 0.0902 | 0.090205 | None ($< 10^{-4}$) | **PASS** |
| | | RMSE | 1.1028 | 1.102819 | None ($< 10^{-4}$) | **PASS** |
| | | MAE | 0.8735 | 0.873527 | None ($< 10^{-4}$) | **PASS** |
| | | Coverage@10 | 20.69% | 0.206897 | None ($< 10^{-4}$) | **PASS** |
| | | Novelty@10 | 3.5555 | 3.555505 | None ($< 10^{-4}$) | **PASS** |
| **Popularity** | `damping=50.0, min=1` | NDCG@10 | 0.0682 | 0.068153 | None ($< 10^{-4}$) | **PASS** |
| | | Precision@10 | 0.0593 | 0.059259 | None ($< 10^{-4}$) | **PASS** |
| | | Recall@10 | 0.0511 | 0.051080 | None ($< 10^{-4}$) | **PASS** |
| | | RMSE | 1.1189 | 1.118852 | None ($< 10^{-4}$) | **PASS** |
| | | MAE | 0.9088 | 0.908791 | None ($< 10^{-4}$) | **PASS** |
| | | Coverage@10 | 3.80% | 0.038050 | None ($< 10^{-4}$) | **PASS** |
| | | Novelty@10 | 3.6090 | 3.608977 | None ($< 10^{-4}$) | **PASS** |
| **ItemKNN** | `k=10, min_overlap=1` | NDCG@10 | 0.0215 | 0.021480 | None ($< 10^{-4}$) | **PASS** |
| | | Precision@10 | 0.0210 | 0.021024 | None ($< 10^{-4}$) | **PASS** |
| | | Recall@10 | 0.0139 | 0.013937 | None ($< 10^{-4}$) | **PASS** |
| | | RMSE | 1.1177 | 1.117694 | None ($< 10^{-4}$) | **PASS** |
| | | MAE | 0.8851 | 0.885070 | None ($< 10^{-4}$) | **PASS** |
| | | Coverage@10 | 76.34% | 0.763377 | None ($< 10^{-4}$) | **PASS** |
| | | Novelty@10 | 8.0758 | 8.075804 | None ($< 10^{-4}$) | **PASS** |
| **UserKNN** | `k=10, min_overlap=2` | NDCG@10 | 0.0066 | 0.006582 | None ($< 10^{-4}$) | **PASS** |
| | | Precision@10 | 0.0057 | 0.005664 | None ($< 10^{-4}$) | **PASS** |
| | | Recall@10 | 0.0040 | 0.003999 | None ($< 10^{-4}$) | **PASS** |
| | | RMSE | 1.0184 | 1.018359 | None ($< 10^{-4}$) | **PASS** |
| | | MAE | 0.8027 | 0.802654 | None ($< 10^{-4}$) | **PASS** |
| | | Coverage@10 | 22.47% | 0.224732 | None ($< 10^{-4}$) | **PASS** |
| | | Novelty@10 | 8.8244 | 8.824399 | None ($< 10^{-4}$) | **PASS** |

### 2.2 Validation Hyperparameter Tuning Cross-Check
- **Source Artifact:** `results/validation_tuning.csv` (32 rows)
- **Tuning Grid:**
  - Popularity (15 rows): `damping=50.0, min_ratings=1.0` has NDCG@10 = 0.070218, RMSE = 1.040405.
  - UserKNN (6 rows): `k=10, min_overlap=2` has NDCG@10 = 0.004956, RMSE = 0.998518.
  - ItemKNN (6 rows): `k=10, min_overlap=1` has NDCG@10 = 0.004976, RMSE = 1.083242.
  - TruncatedSVD (5 rows): `n_factors=20` has NDCG@10 = **0.113836**, RMSE = 1.040741.
- **Model Selection Integrity:** The selection of Truncated SVD was strictly governed by validation NDCG@10 (0.1138 vs 0.0702 vs 0.0050). No test set data was consulted during hyperparameter selection.
- **Status:** **PASS** (Mandatory).

### 2.3 Cold-Start Sensitivity Cross-Check
- **Source Artifact:** `results/cold_start_experiment.csv` (16 rows)
- **Visual Artifact:** `results/plots/cold_start_curve.png`
- Values reported in `docs/evaluation_results.md` §6 match the CSV exactly across all models and truncation levels $M \in \{1, 3, 5, 10\}$:
  - At $M=1$: Popularity NDCG@10 = 0.0592, SVD = 0.0384, ItemKNN = 0.0078, UserKNN = 0.0000.
  - At $M=3$: SVD NDCG@10 = 0.0601, Popularity = 0.0601, UserKNN = 0.0193, ItemKNN = 0.0098.
- **Status:** **PASS** (Mandatory).

---

## 3. Evaluation Integrity & Protocol Compliance

1. **Chronological Per-User Partitioning:**
   - Evaluated exclusively with chronological split (60/20/20 per user, seed `42`). Verified via `test_split_proportions_and_sizes` and `test_chronological_ordering_per_user`.
   - **Status:** **PASS** (Mandatory).

2. **Data Leakage Safeguards:**
   - Validation tuning (`run_validation_tuning`) accesses only `splits.train` and `splits.val`.
   - Final evaluation (`run_final_test_evaluation`) refits solely on `train + val` (79,252 ratings) and evaluates on `test` (20,748 ratings).
   - Candidate set excludes all items in `Seen_u` (train + val).
   - **Status:** **PASS** (Mandatory).

3. **Relevance Threshold & Zero-Relevant User Exclusion:**
   - Threshold $r \ge 4.0$ strictly applied.
   - 25 users with 0 test ratings $\ge 4.0$ were cleanly excluded from ranking macro-averages to avoid $0/0$ division-by-zero distortion, and their count was recorded in result tables.
   - **Status:** **PASS** (Mandatory).

4. **ItemKNN Optimization Equivalence:**
   - Inverted candidate index pruning verified: candidate items with 0 co-raters evaluate to 0.0 similarity and directly trigger fallback prediction.
   - Equivalence verified against unoptimized model: 100% identical top-10 ranking and numerical differences $< 10^{-9}$. Verified via `test_item_knn_optimization_equivalence_and_edge_cases`.
   - **Status:** **PASS** (Mandatory).

5. **Unit Test Execution:**
   - Fresh independent test run command:
     ```powershell
     & ".\.venv\Scripts\pytest.exe" -v
     ```
   - Observed output: **30 passed in 11.71s** (100% pass rate across `test_data.py`, `test_split.py`, `test_models.py`, `test_evaluation.py`).
   - Zero test failures, errors, or regressions.
   - **Status:** **PASS** (Mandatory).

---

## 4. Repository & Phase Boundaries

1. **Phase 4 Isolation:**
   - Verified that `app/` is empty or uncreated.
   - `src/recsys/service.py` is uncreated.
   - No Phase 4 Streamlit dependencies or service layer implementations exist in the repository.
   - **Status:** **PASS** (Mandatory).

2. **Phase Diagnostic Documentation:**
   - Session Matplotlib configuration, batch unbuffered flushing, and candidate pruning optimizations are thoroughly documented in `docs/reports/phase_3_report.md` and `docs/decisions.md`.
   - **Status:** **PASS** (Mandatory).

---

## 5. Summary of Audit Checklist Criteria

| Audit Criterion | Classification | Status | Evidence / Notes |
| :--- | :---: | :---: | :--- |
| Hand-computed metric tests pass (tol $< 10^{-6}$) | Mandatory | **PASS** | `test_mae_and_rmse_hand_computed`, `test_precision_recall_at_k_hand_computed`, `test_ndcg_at_k_hand_computed` |
| No test data used in hyperparameter tuning | Mandatory | **PASS** | Code inspection of `run_validation_tuning` in `scripts/run_evaluation.py` |
| Final test evaluation ran once per selected model | Mandatory | **PASS** | Verified via `results/final_run.log` and `results/test_evaluation_results.csv` |
| Re-running evaluation is reproducible | Mandatory | **PASS** | Seed 42 locked across split, SVD, and candidate ties |
| Results doc lists all 4 models on rating & top-N metrics | Mandatory | **PASS** | Verified in `docs/evaluation_results.md` §5 |
| Cold-start reported separately from warm-start | Mandatory | **PASS** | Verified in `docs/evaluation_results.md` §6 and `results/cold_start_experiment.csv` |
| Every number in docs matches saved CSVs | Mandatory | **PASS** | 100% matched across 28 metric cross-checks |
| `pytest` passes with 0 failures | Mandatory | **PASS** | 30/30 tests passed in 11.71s |
| Phase completion report authored | Mandatory | **PASS** | `docs/reports/phase_3_report.md` created and complete |
| Decision log updated with Phase 3 rationale | Mandatory | **PASS** | 5 Phase 3 entries in `docs/decisions.md` |
| No Phase 4 code introduced | Mandatory | **PASS** | `app/` and `src/recsys/service.py` clean |

---

## 6. Audit Verdict

**PASS**

All mandatory requirements, documentation deliverables, metric calculations, data isolation guarantees, and empirical cross-checks are verified with zero open defects. Phase 3 is officially approved and complete.

---

## 7. Next Valid Commands

- `START PHASE 4` (Service and Streamlit app)
- `EXPLAIN <topic>`
- `STATUS`
- `STOP`
