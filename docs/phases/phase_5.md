# Phase 5: Final Testing and Documentation

Prerequisite: Phase 4 audit = PASS.

## Tasks
1. End-to-end test: raw data to split, fit, evaluate, service, and app.
2. Run the full suite (unit, integration, regression). Add tests for the remaining edge cases: sparse histories, unseen movies, invalid values.
3. Leakage test across the full pipeline.
4. Reproduce all reported results from a clean virtual environment and fresh clone.
5. Measure runtime and memory for fit, evaluate, and recommend on `ml-100k`.
6. Fix integration defects that belong to this phase; record remaining limitations.
7. README: problem statement, dataset and attribution, preprocessing, user-based and item-based CF explained mathematically and intuitively, similarity metrics, evaluation protocol, results tables and figures (from saved CSVs), installation and run commands, directory structure, limitations, future work, references.
8. `docs/viva_prep.md`: presentation points and at least 15 likely viva questions with plain-language answers (for example: why not treat missing as zero, why chronological split, why adjusted cosine, why RMSE and NDCG disagree, what is cold start).
9. `docs/final_readiness_report.md`: feature checklist (implemented, tested, documented), exact list of files needed to run and submit.

## Acceptance criteria
- [ ] Full `pytest` run passes with 0 failures (observed output pasted into the report).
- [ ] A fresh-environment install and the documented commands reproduce the saved metric tables exactly.
- [ ] Every number and feature in README and viva prep matches code and `results/` (spot-check at least 5).
- [ ] No feature is described that does not exist; all citations are real and verifiable.
- [ ] Runtime and memory figures are measured, not estimated.
- [ ] Known limitations include at least: offline evaluation vs real usefulness, popularity bias, cold start, small dataset.
- [ ] Submission file list is complete, and a fresh clone with that list runs the app.

## Audit checklist
Clone into a new folder, follow the README literally, run tests and the app, diff regenerated results against saved ones, verify citations, and check the viva answers against the code.
