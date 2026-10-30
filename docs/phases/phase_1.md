# Phase 1: Environment and Data Pipeline

Prerequisite: Phase 0 audit = PASS.

## Tasks
1. Create the approved folder structure and a virtual environment; write a pinned `requirements.txt`.
2. `scripts/download_data.py`: download `ml-100k` from GroupLens, verify the expected files exist, extract to `data/raw/`; add `data/` to `.gitignore`.
3. `src/recsys/data.py`: loaders for ratings (`u.data`), movies (`u.item`, including genre flags), users (`u.user`).
4. Validate: dtypes, missing values, duplicate (user, item) pairs, ID consistency between files, rating range and integer values, timestamp sanity.
5. Document cleaning rules (even if the data needs none) in `docs/data_quality_report.md`.
6. `scripts/run_eda.py`: user activity, movie popularity (long tail), rating distribution, sparsity, ratings over time; save figures to `results/eda/`.
7. Implement `src/recsys/split.py` (per-user chronological 60/20/20) with fixed seed for any tie-breaking.
8. Tests for loaders, validation, and the split.
9. Setup and run instructions in README (draft is fine).

## Acceptance criteria
- [ ] `pip install -r requirements.txt` works in a fresh virtual environment.
- [ ] A test asserts the loaded data has 100,000 ratings, 943 users, 1,682 movies (verify against the actual files; if different, report it rather than editing the test).
- [ ] Tests assert ratings are integers in 1..5 and there are no duplicate (user, item) pairs.
- [ ] Sparsity is computed and reported (expected near 93.7%).
- [ ] Split tests assert: no row appears in two partitions; every user's train timestamps are <= their validation timestamps <= their test timestamps; every user appears in train.
- [ ] At least 5 EDA figures saved, each with a title and axis labels.
- [ ] `pytest` passes with 0 failures (observed output).
- [ ] No recommendation model code exists yet.
- [ ] `data/` is gitignored and no dataset files are tracked.

## Audit checklist
Re-run the download script (or confirm data exists), run `pytest`, open the split code and verify the ordering assertion is real, check the figures exist, check no model code was added.
