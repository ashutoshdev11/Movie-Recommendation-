# Phase 3: Evaluation and Model Selection

Prerequisite: Phase 2 audit = PASS. Follow `docs/evaluation_protocol.md` and the fixed decisions in RULES.md.

## Tasks
1. `src/recsys/evaluation.py`: MAE, RMSE, Precision@K, Recall@K, NDCG@K (K = 5, 10, 20), item coverage, and a novelty or diversity measure.
2. Hyperparameter search on the validation partition only (for example: k neighbours, minimum overlap, shrinkage, SVD factors, popularity damping).
3. Write the selection rule in `docs/evaluation_protocol.md` before running on test (NDCG@10 on validation, RMSE secondary).
4. Final run: refit chosen configurations on train+validation, evaluate on test once, via a `--final` flag that logs how many times it was used.
5. Cold-start experiment: truncate a sample of users' training history to 1, 3, 5, and 10 ratings; compare models separately from warm-start results.
6. Report users excluded from ranking metrics because they have no relevant test items.
7. Save result tables (CSV) and plots in `results/`, each with config, seed, dataset version, and timestamp.
8. Write `docs/evaluation_results.md` interpreting results with the correct meaning of each metric, plus failure cases and offline-evaluation limitations.
9. Tests for each metric against hand-computed examples.

## Acceptance criteria
- [ ] Metric tests pass against hand-computed values (including a case with no relevant items and a case with ties).
- [ ] No test-partition data is used in tuning (verified by code inspection and a test).
- [ ] Final test evaluation ran exactly once per selected model configuration (log shows it).
- [ ] Re-running the evaluation with the same seed produces identical metric tables.
- [ ] The results document lists all four models on both rating-prediction and top-N metrics, with the baseline included, and states the chosen model with the evidence for it.
- [ ] Cold-start results are reported separately from warm-start results.
- [ ] Every number in the docs matches a saved CSV.
- [ ] `pytest` passes with 0 failures (observed output).

## Audit checklist
Re-run the evaluation script and diff against saved tables; open the tuning code and confirm only validation data is used; check the final-run log; spot-check three numbers in the docs against the CSVs.
