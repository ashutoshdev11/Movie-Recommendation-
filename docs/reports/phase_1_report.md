# Phase 1 Completion Report: Environment and Data Pipeline

**Date:** 2026-10-30  
**Phase:** Phase 1 (Environment and Data Pipeline)  
**Status:** Completed (Ready for Audit)

---

## 1. Summary of Work Completed
- **Environment Configuration:**
  - Installed official Python 3.11.9 (64-bit) at user scope (`C:\Users\ashut\AppData\Local\Programs\Python\Python311\python.exe`) using Winget with verified non-elevated parameters (`InstallAllUsers=0 InstallLauncherAllUsers=0 Include_launcher=0 Include_pip=1 PrependPath=1`).
  - Created isolated project virtual environment `.venv` at project root (`c:\Users\ashut\Downloads\MOVIE RECOMMENDATION PROJECT\.venv`).
  - Installed pinned dependencies from `requirements.txt` (`numpy==1.26.4`, `pandas==2.2.2`, `scipy==1.13.1`, `scikit-learn==1.5.0`, `matplotlib==3.9.0`, `streamlit==1.36.0`, `pytest==8.2.2`, `requests==2.32.3`).
- **Dataset Provenance & Ingestion:**
  - Developed `scripts/download_data.py` to stream and extract the official MovieLens 100K dataset from GroupLens (`https://files.grouplens.org/datasets/movielens/ml-100k.zip`) directly into `data/raw/ml-100k/`.
  - Configured `.gitignore` to strictly exclude `data/` and all dataset archives in adherence to GroupLens redistribution restrictions.
- **Data Loaders & Quality Validation:**
  - Implemented `src/recsys/data.py` with typed loaders for ratings (`u.data`), movie metadata with 19 genre indicators (`u.item`), and user demographics (`u.user`).
  - Validated data dimensions (100,000 ratings, 943 users, 1,682 items), integer ratings in $[1, 5]$, zero duplicates, zero missing rating records, and computed interaction sparsity ($93.70\%$).
  - Documented findings in `docs/data_quality_report.md`.
- **Exploratory Data Analysis (EDA):**
  - Developed `scripts/run_eda.py`, generating and saving 5 publication-ready annotated figures in `results/eda/`:
    1. `user_activity_distribution.png`: Histogram showing user interaction frequency (median = 65, mean = 106).
    2. `movie_popularity_long_tail.png`: Long-tail plot highlighting catalog consumption concentration.
    3. `rating_distribution.png`: Bar chart of ratings (peak at 4 stars, 34.2%).
    4. `matrix_sparsity.png`: Sparsity comparison (93.70% unobserved vs. 6.30% observed).
    5. `ratings_over_time.png`: Monthly time-series rating trends (1997–1998).
- **Per-User Chronological Splitting:**
  - Implemented `src/recsys/split.py` with 60% Train, 20% Validation, and 20% Test per user.
  - Enforced strict timestamp ordering: $\max(t_{\text{train}, u}) \le \min(t_{\text{val}, u}) \le \max(t_{\text{val}, u}) \le \min(t_{\text{test}, u})$.
  - Guaranteed every user is represented in the training set ($n_{\text{train}} \ge 12$).
  - Resolved boundary timestamp ties deterministically using seed `42`.
- **Testing & Verification:**
  - Authored comprehensive test suites in `tests/unit/test_data.py` and `tests/unit/test_split.py`.
  - Executed `pytest -v`, observing 11 passing tests with 0 failures in 2.46 seconds.
  - Authored setup and run instructions in `README.md`.
  - Confirmed no recommendation model code exists in `src/recsys/models/`.

---

## 2. Files Created / Changed
- `.gitignore` (Created)
- `requirements.txt` (Created)
- `README.md` (Created)
- `scripts/download_data.py` (Created)
- `scripts/run_eda.py` (Created)
- `src/recsys/__init__.py` (Created)
- `src/recsys/data.py` (Created)
- `src/recsys/split.py` (Created)
- `tests/__init__.py` (Created)
- `tests/unit/__init__.py` (Created)
- `tests/unit/test_data.py` (Created)
- `tests/unit/test_split.py` (Created)
- `docs/data_quality_report.md` (Created)
- `docs/decisions.md` (Updated with Phase 1 decisions)
- `docs/reports/phase_1_report.md` (Created)
- `PROJECT_STATUS.md` (Updated)
- Generated figures in `results/eda/`:
  - `user_activity_distribution.png`
  - `movie_popularity_long_tail.png`
  - `rating_distribution.png`
  - `matrix_sparsity.png`
  - `ratings_over_time.png`

---

## 3. Environment & Tooling Verification
- **Python Executable:** `C:\Users\ashut\AppData\Local\Programs\Python\Python311\python.exe`
- **Virtual Environment Interpreter:** `C:\Users\ashut\Downloads\MOVIE RECOMMENDATION PROJECT\.venv\Scripts\python.exe`
- **Python Version:** `Python 3.11.9`
- **Pip Version:** `26.2.2`
- **Pytest Version:** `8.2.2`

---

## 4. Acceptance Criteria Verification

| Acceptance Criterion | Verification Evidence | Status |
|---|---|:---:|
| `pip install -r requirements.txt` works in a fresh virtual environment | Successfully installed all 8 pinned packages and dependencies inside `.venv`. | **VERIFIED** |
| Test asserts data has 100,000 ratings, 943 users, 1,682 movies | `test_dataset_dimensions` passed against real `ml-100k` files. | **VERIFIED** |
| Tests assert ratings are integers in 1..5, no duplicate pairs | `test_rating_values_and_types`, `test_no_duplicate_pairs` passed. | **VERIFIED** |
| Sparsity computed and reported near 93.7% | `test_sparsity_calculation` confirmed 93.70% sparsity. | **VERIFIED** |
| Split tests assert disjoint partitions, temporal order, every user in train | `test_no_row_overlap_between_partitions`, `test_chronological_ordering_per_user`, `test_every_user_appears_in_train` passed. | **VERIFIED** |
| At least 5 EDA figures saved with titles and labels | 5 figures verified in `results/eda/` with axes and titles. | **VERIFIED** |
| `pytest` passes with 0 failures | 11 passed in 2.46s (observed output recorded). | **VERIFIED** |
| No recommendation model code exists yet | `src/recsys/models/` contains no model implementations. | **VERIFIED** |
| `data/` is gitignored and untracked | Verified in `.gitignore`. | **VERIFIED** |

---

## 5. Known Issues / Limitations
- None. All tasks and acceptance criteria completed cleanly without errors.
