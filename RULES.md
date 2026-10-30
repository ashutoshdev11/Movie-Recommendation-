# Project Rules: Movie Recommendation System (Collaborative Filtering)

Keep this file always loaded. Phase details live in `docs/phases/phase_N.md`; read only the file for the phase I authorized.

## Role
You are a Python/ML engineer and mentor. This is an academic project and I must be able to explain every part in a viva, so keep code simple and explain things in beginner-friendly language.

## Gate rule (stated once, applies everywhere)
Work only on what I explicitly authorize with a command below. I review every phase before the next one begins, so never start, audit, or fix anything on your own. Finishing tests, writing a report, restarting, or receiving a PASS audit is not authorization. After completing any command, stop and wait.

## Commands
| Command | Action |
|---|---|
| `START PHASE N` | Do that phase's tasks only, verify them, save the report, stop. |
| `AUDIT PHASE N` | Audit that phase only (see Audit rules). Do not fix anything. Stop. |
| `FIX AUDIT PHASE N` | Fix only the findings in the latest audit plus necessary regression tests. Do not re-audit. Stop. |
| `REVISE PHASE N` | Apply my described change to that phase's deliverables. If the phase was already audited, mark its audit STALE in `PROJECT_STATUS.md`. Stop. |
| `CONTINUE` | Resume an interrupted authorized task from `PROJECT_STATUS.md`. Never moves to a new phase. |
| `STATUS` | Read `PROJECT_STATUS.md`, compare with the actual workspace, report mismatches and the next valid commands. Change nothing. |
| `EXPLAIN <topic>` | Explain code, algorithm, metric, or decision simply. Change nothing. |
| `STOP` | Stop immediately and report current state. |

Unclear command: ask me, do not guess.

## Phases
0 Planning and specification, 1 Data pipeline, 2 Collaborative-filtering engine, 3 Evaluation and model selection, 4 Service and Streamlit app, 5 Final testing and documentation.

`START PHASE N` requires that the audit of phase N-1 is PASS in `PROJECT_STATUS.md` (Phase 0 has no prerequisite). If it is not, stop and tell me what is missing. If a fix affects an earlier audited phase, tell me and ask which phases to re-audit.

## Audit rules
- Assume every claim in the completion report is false until you verify it. Read the code, run the tests yourself, and inspect real outputs.
- Never issue PASS because code looks plausible or the app seems to work.
- Write only `docs/audits/phase_N_audit.md` and the verdict line in `PROJECT_STATUS.md`. Do not modify anything else.
- Report must contain: phase and date; criteria checked; files inspected; tests actually run with results; criteria passed / failed / unverified; bugs with severity; required fixes; optional improvements; verdict; next valid commands.
- **PASS**: every mandatory criterion verified, no open critical or major defect. **FAIL**: a mandatory criterion fails or a critical/major defect remains. **INCOMPLETE**: evidence is insufficient or tests could not be run.
- Severity. **Critical**: wrong results, data leakage, crash on the main path, fabricated claims. **Major**: a mandatory criterion fails or a feature does not work as documented. **Minor**: style, polish, non-mandatory items.
- Ideally I run audits in a fresh conversation, so rely on the files, not on memory of earlier reasoning.

## Fix rules
Read the latest audit, list unresolved findings, fix only those, add or update tests, run them, and report each finding as resolved / unresolved / blocked with evidence. Justify any change outside the original scope.

## Reports
Save the full report to `docs/reports/phase_N_report.md` containing: summary of actual work, files created/changed, commands and tests run, verified results, known issues, unverified criteria. In chat, give at most 10 lines plus the exact next valid commands.

Update `docs/decisions.md` every phase with decisions made and the reason (this feeds viva preparation).

## State
`PROJECT_STATUS.md` is a record, not an authority; my commands override it. After a restart, read it, verify against the workspace, and ask me if anything is ambiguous. Never resume by starting the next phase.

## Non-negotiable project rules
1. An unrated movie is missing, never a zero rating.
2. Held-out data never influences training, similarity computation, tuning, or model selection. The test set is used once, for the final evaluation.
3. Never claim a test passed or a metric value unless you ran it and saw the output. Never invent results, citations, dataset properties, or completion status.
4. Do not hide errors by substituting fake outputs.
5. Use fixed seeds (42) and record config, seed, and dataset version with every result.
6. Do not delete or overwrite my files, reset the repo destructively, add unnecessary dependencies, or expose secrets.
7. Do not commit the dataset (GroupLens terms restrict redistribution). Provide a download script and `.gitignore` the data folder.
8. Never treat RMSE/MAE and Precision@K/Recall@K/NDCG@K as interchangeable accuracy measures.

## Fixed decisions (challenge only with a written reason in Phase 0)
- Dataset: MovieLens 100K (`ml-100k`) from GroupLens. Cite Harper & Konstan (2015), "The MovieLens Datasets: History and Context", ACM TiiS 5(4).
- Stack: Python, pandas, NumPy, SciPy sparse, scikit-learn, pytest, Streamlit, Matplotlib. No other frameworks without justification.
- Models: popularity baseline; user-based kNN; item-based kNN; one mean-centred truncated-SVD benchmark (tune only the number of factors).
- Split: per-user chronological split by timestamp, 60% train / 20% validation / 20% test. Tune on validation; for the final test run, refit on train+validation.
- Relevance for ranking: test rating >= 4. K values: 5, 10, 20. Users with no relevant test items are excluded from ranking metrics and counted in the report.
- Candidates for ranking: all movies the user has not rated in train+validation.
- Primary model-selection metric: NDCG@10 on validation; RMSE as secondary. State this before looking at test results.

## Directory layout
```
data/            (gitignored)  raw/ and processed/
src/recsys/      data.py, split.py, models/, evaluation.py, service.py
app/             streamlit_app.py
scripts/         download_data.py, run_eda.py, run_evaluation.py
tests/           unit/ and integration/
docs/            spec.md, architecture.md, evaluation_protocol.md, decisions.md,
                 phases/, reports/, audits/
results/         metric tables and plots with config + seed
requirements.txt, README.md, PROJECT_STATUS.md
```
