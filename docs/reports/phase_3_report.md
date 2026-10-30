# Phase 3 Completion Report: Evaluation and Model Selection

**Date:** 2026-10-30  
**Phase:** Phase 3 (Evaluation and Model Selection)  
**Status:** Completed (Audit Findings Resolved, Ready for Re-Audit)

---

## 1. Summary of Work Completed

1. **Evaluation Engine Implementation (`src/recsys/evaluation.py`):**
   - Implemented rating prediction error metrics: Mean Absolute Error (MAE) and Root Mean Squared Error (RMSE).
   - Implemented Top-$K$ ranking metrics: Precision@K, Recall@K, and Normalized Discounted Cumulative Gain (NDCG@K) with logarithmic position discounting for $K \in \{5, 10, 20\}$.
   - Implemented distribution and catalog diversity metrics: Catalog Coverage@K and Novelty@K (smoothed self-information).
   - Implemented binary relevance thresholding ($r \ge 4.0$) and handling of zero-relevant users, excluding them from ranking macro-averages and logging counts (25 excluded test users).
   - Implemented candidate item filtering, ranking over all catalog items unseen in training/validation ($I \setminus \text{Seen}_u$).

2. **Metric Unit Testing & Verification (`tests/unit/test_evaluation.py`):**
   - Implemented 5 rigorous unit tests validating metrics against hand-calculated values to $< 10^{-6}$ precision:
     - `test_mae_and_rmse_hand_computed`: Hand-calculated MAE (1.0) and RMSE ($\sqrt{1.5}$).
     - `test_precision_recall_at_k_hand_computed`: Precision and recall at cutoffs 3 and 5.
     - `test_ndcg_at_k_hand_computed`: Discounted Cumulative Gain and Ideal DCG matching manual derivation.
     - `test_no_relevant_items_case`: Zero relevant items handled gracefully without ZeroDivisionError.
     - `test_coverage_and_novelty_hand_computed`: Catalog coverage and self-information novelty verified on a toy catalog.

3. **Validation Hyperparameter Tuning & Leakage Safeguards (`scripts/run_evaluation.py`):**
   - Evaluated 32 hyperparameter combinations strictly against the validation partition (59,576 training ratings $\to$ 19,676 validation ratings).
   - Zero test-partition data or timestamps were accessed during tuning.
   - Saved full tuning grid to `results/validation_tuning.csv`.

4. **Model Selection Protocol Enforcement:**
   - Model selection was locked based on **Validation NDCG@10** (RMSE secondary) before inspecting test results:
     - **Popularity Baseline:** `damping = 50.0, min_ratings = 1.0` (Val NDCG@10 = 0.0702, RMSE = 1.0404)
     - **User-based kNN:** $k = 10, \text{min\_overlap} = 2$ (Val NDCG@10 = 0.0050, RMSE = 0.9985)
     - **Item-based kNN:** $k = 10, \text{min\_overlap} = 1$ (Val NDCG@10 = 0.0050, RMSE = 1.0832)
     - **Truncated SVD (Selected Winner):** $n_{\text{factors}} = 20$ (Val NDCG@10 = **0.1138**, RMSE = 1.0407)

5. **Diagnostic Performance Fix & Candidate Pruning:**
   - Optimized `ItemKNNRecommender.recommend()` by building an inverted rater index to prune candidate items with zero co-raters.
   - Proved 100% ranking equivalence and score equivalence to $< 10^{-9}$ numerical precision on toy and MovieLens datasets (`test_item_knn_optimization_equivalence_and_edge_cases`).
   - Added unbuffered progress logging (`flush=True`) across batch evaluation routines.

6. **Cold-Start Sensitivity Experiment:**
   - Evaluated models across interaction truncation levels $M \in \{1, 3, 5, 10\}$ ratings per user (`results/cold_start_experiment.csv`).
   - Generated cold-start sensitivity visualization (`results/plots/cold_start_curve.png`).
   - Verified that Popularity Baseline serves as the optimal cold-start safety net ($M=1$), while Truncated SVD overtakes it at $M \ge 3$.

7. **Single Final Test Run Execution:**
   - Refitted selected models on `Train + Validation` (79,252 ratings) and evaluated once on `Test` (20,748 ratings) with `--final` flag.
   - Logged run audit trail to `results/final_run.log` and saved full test metrics to `results/test_evaluation_results.csv`.
   - Generated model comparison plot (`results/plots/model_comparison_ndcg10.png`).

8. **Comprehensive Results Interpretation (`docs/evaluation_results.md`):**
   - Authored in-depth analysis documenting all metrics, error trade-offs, why SVD won top-$N$ ranking while UserKNN won RMSE, catalog coverage nuances, and offline evaluation limitations.

---

## 2. Files Created / Changed

| File | Status | Description |
| :--- | :---: | :--- |
| `src/recsys/evaluation.py` | Created | Metric calculations and evaluation harness. |
| `tests/unit/test_evaluation.py` | Created | Hand-computed metric unit tests and edge cases. |
| `scripts/run_evaluation.py` | Created | Orchestration script for tuning, cold-start, and test evaluation. |
| `src/recsys/models/item_knn.py` | Modified | Candidate co-rater inverted index pruning optimization. |
| `tests/unit/test_models.py` | Modified | Added ItemKNN equivalence and edge-case unit tests. |
| `results/validation_tuning.csv` | Generated | 32 validation tuning configurations. |
| `results/cold_start_experiment.csv` | Generated | Cold-start results across $M \in \{1, 3, 5, 10\}$. |
| `results/test_evaluation_results.csv` | Generated | Final test evaluation metrics across cutoffs 5, 10, 20. |
| `results/final_run.log` | Generated | Audit trail of `--final` test runs. |
| `results/plots/model_comparison_ndcg10.png` | Generated | Test NDCG@10 comparison bar chart. |
| `results/plots/cold_start_curve.png` | Generated | Cold-start sensitivity curve. |
| `docs/evaluation_results.md` | Created | In-depth results interpretation, trade-off analysis, and limitations. |
| `docs/decisions.md` | Updated | Documented Phase 3 architectural and empirical decisions. |
| `docs/reports/phase_3_report.md` | Created | Phase 3 completion report. |
| `PROJECT_STATUS.md` | Updated | State synchronization. |

---

## 3. Commands and Tests Run

1. **Test Suite Execution:**
   - Command: `& ".\.venv\Scripts\pytest.exe" -v`
   - Result: **30 passed in 16.39s** (100% pass rate across data, split, models, and evaluation tests).
2. **Final Test Evaluation Run:**
   - Command: `$env:MPLCONFIGDIR = "$env:LOCALAPPDATA\Temp\matplotlib"; & ".\.venv\Scripts\python.exe" -u scripts/run_evaluation.py --final`
   - Result: Exit code 0, runtime 10m 13s, logged to `results/final_run.log`.

---

## 4. Acceptance Criteria Verification

| Acceptance Criterion | Verification Evidence | Status |
| :--- | :--- | :---: |
| Metric tests pass against hand-computed values | `tests/unit/test_evaluation.py` tests MAE, RMSE, Precision, Recall, NDCG, Coverage, Novelty (error $< 10^{-6}$). | **VERIFIED** |
| No test-partition data is used in tuning | Inspected `scripts/run_evaluation.py`: tuning is isolated to `splits.train` and `splits.val`. | **VERIFIED** |
| Final test evaluation ran exactly once per selected config | Verified in `results/final_run.log` (Run #2 completed; Run #1 was interrupted). | **VERIFIED** |
| Evaluation reproducible with fixed seeds | Seed 42 used throughout; re-running produces identical tables. | **VERIFIED** |
| Results document lists all 4 models on rating & top-N metrics | `docs/evaluation_results.md` tables report all 4 models with baseline, stating SVD winner. | **VERIFIED** |
| Cold-start results reported separately from warm-start | Reported in separate section in `docs/evaluation_results.md` and `results/cold_start_experiment.csv`. | **VERIFIED** |
| Every number in docs matches saved CSV | Cross-checked numbers between `docs/evaluation_results.md` and CSV artifacts. | **VERIFIED** |
| `pytest` passes with 0 failures | Observed output: 30 passed in 16.39s. | **VERIFIED** |

---

## 5. Summary of Final Test Results

| Model | Config | NDCG@10 | Precision@10 | Recall@10 | RMSE | MAE | Coverage@10 | Novelty@10 |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **TruncatedSVDRecommender** | `n_factors=20` | **0.1198** | **0.0914** | **0.0902** | 1.1028 | 0.8735 | 20.69% | 3.5555 |
| **PopularityBaseline** | `damping=50.0, min=1` | 0.0682 | 0.0593 | 0.0511 | 1.1189 | 0.9088 | 3.80% | 3.6090 |
| **ItemKNNRecommender** | `k=10, min_overlap=1` | 0.0215 | 0.0210 | 0.0139 | 1.1177 | 0.8851 | **76.34%** | 8.0758 |
| **UserKNNRecommender** | `k=10, min_overlap=2` | 0.0066 | 0.0057 | 0.0040 | **1.0184** | **0.8027** | 22.47% | **8.8244** |

---

## 6. Known Issues / Limitations

1. **UserKNN Sparsity Degradation:** Under 93.70% sparsity and candidate pools of $\sim 1,600$ items, UserKNN produces flat fallback rankings for most items, resulting in poor NDCG@10 (0.0066) despite good RMSE.
2. **Missing-Not-At-Random (MNAR) Bias:** Offline metrics evaluate only on movies the user opted to rate; true online satisfaction will be explored via interactive simulation in Phase 4.

---

## 7. Unverified Criteria
- *None.* All mandatory criteria are verified with empirical evidence and passing tests.
