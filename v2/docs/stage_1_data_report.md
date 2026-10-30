# MovieRec Version 2 — Stage 1: ML-1M Ingestion & Chronological Splitting Report

**Date:** 2026-10-30  
**Phase/Stage:** Stage 1 (V2 Foundation & ML-1M Ingestion)  
**Status:** Completed & Verified  

---

## 1. Overview & Objective

Stage 1 established the data foundation for **MovieRec Version 2**, integrating the official GroupLens **MovieLens 1M (ml-1m)** benchmark dataset in a fully isolated, standalone directory structure (`v2/`).

All operations were conducted without modifying or affecting Version 1.

---

## 2. Dataset Ingestion & Integrity

The dataset was retrieved directly from GroupLens (`https://files.grouplens.org/datasets/movielens/ml-1m.zip`) and extracted into `v2/backend/data/raw/ml-1m/`:

| File | Size (Bytes) | Format | Description |
|---|---|---|---|
| `ratings.dat` | 24,594,131 | `UserID::MovieID::Rating::Timestamp` | 1,000,209 ratings on 1 to 5 star scale |
| `movies.dat` | 171,308 | `MovieID::Title::Genres` | 3,883 catalog movie titles and genres |
| `users.dat` | 134,368 | `UserID::Gender::Age::Occupation::Zip-code` | 6,040 user demographic profiles |
| `README` | 5,577 | Plain Text | Official dataset documentation & citations |

### Validation Checks Passed:
- **Zero Missing Values**: No nulls across ratings, users, or movie IDs.
- **Valid Rating Range**: All rating values are within $[1.0, 5.0]$.
- **Zero Duplicate Interactions**: 0 duplicate `(user_id, movie_id)` pairs.
- **User Activity Criterion**: Every user has a minimum of 20 ratings.

---

## 3. Preprocessing Decisions

1. **Title and Release Year Parsing**:
   - Cleaned title strings and parsed 4-digit release years from title suffixes (e.g., `"Toy Story (1995)"` $\to$ title: `"Toy Story"`, year: `1995`).
   - Standardized article inversions (e.g., `"Matrix, The"` $\to$ `"The Matrix"`).
2. **Genre Multi-Hot Encoding**:
   - Extracted 18 distinct MovieLens genres: `Action`, `Adventure`, `Animation`, `Children's`, `Comedy`, `Crime`, `Documentary`, `Drama`, `Fantasy`, `Film-Noir`, `Horror`, `Musical`, `Mystery`, `Romance`, `Sci-Fi`, `Thriller`, `War`, `Western`.
   - Populated binary indicator columns ($0/1$) for every catalog movie.
3. **Optimized Storage**:
   - Exported clean, compressed data frames to `v2/backend/data/processed/` using gzip-compressed CSVs (`train_ratings.csv.gz`, `val_ratings.csv.gz`, `test_ratings.csv.gz`, `movies_metadata.csv.gz`), eliminating external binary dependency issues while maintaining high I/O throughput.

---

## 4. Dataset Statistics

From `v2/backend/data/processed/dataset_statistics.json`:

| Statistic | Value | Notes |
|---|---|---|
| **Total Ratings** | 1,000,209 | Exactly 1M benchmark interactions |
| **Active Users** | 6,040 | Verified active raters |
| **Rated Movies** | 3,706 | Catalog movies with $\ge 1$ rating |
| **Total Catalog Movies** | 3,883 | Total registered titles in `movies.dat` |
| **Global Rating Mean** | 3.5816 | Standard deviation: 1.1171 |
| **Matrix Sparsity** | 95.7353% | Calculated on user $\times$ catalog items |
| **User Interactions** | Min: 20, Max: 2,314 | Median: 96.0, Mean: 165.6 |
| **Movie Popularity** | Min: 1, Max: 3,428 | Median: 123.5, Mean: 269.89 |

### Rating Distribution:
- **1.0 Star:** 56,174 (5.62%)
- **2.0 Stars:** 107,557 (10.75%)
- **3.0 Stars:** 261,197 (26.11%)
- **4.0 Stars:** 348,971 (34.89%)
- **5.0 Stars:** 226,310 (22.63%)

---

## 5. Leakage-Proof Chronological Splitting

To strictly eliminate temporal leakage where future ratings inform past recommendations, an individual user-level chronological split was executed:

1. **Ordering Invariant**:
   For every user $u$, ratings were ordered ascending by `timestamp` (with deterministic tie-breaking on `movie_id`):
   $$\max(t_{\text{train}}) \le \min(t_{\text{val}}) \le \max(t_{\text{val}}) \le \min(t_{\text{test}})$$
2. **Partition Proportions**:
   - **Train Split (60%):** 597,742 ratings (59.76%)
   - **Validation Split (20%):** 197,656 ratings (19.76%) — reserved for hyperparameter tuning in Stage 2.
   - **Held-out Test Split (20%):** 204,811 ratings (20.48%) — strictly reserved for one-shot final evaluation.
3. **User Coverage**:
   - 100% of the 6,040 users are present in the training partition, guaranteeing that user representation factors can be learned for all active benchmark users.

---

## 6. Test Results

### 1. V2 Dataset Suite (`v2/backend/tests/test_dataset.py`):
- `test_ratings_raw_dimensions_and_types`: **PASSED**
- `test_ratings_integrity_and_bounds`: **PASSED**
- `test_movies_schema_and_year_parsing`: **PASSED**
- `test_users_demographics_schema`: **PASSED**
- `test_dataset_statistics_computation`: **PASSED**
- `test_chronological_split_partition_sizes`: **PASSED**
- `test_temporal_leakage_prevention_invariant`: **PASSED**
- `test_processed_files_exist_and_match`: **PASSED**
- **Result:** **8 passed in 4.75s**

### 2. V1 Regression Suite (`tests/`):
- **Result:** **53 passed in 17.76s** (0 regressions, 0 failures).

---

## 7. Version 1 Protection Verification

Cryptographic SHA-256 hashes of all protected Version 1 files were checked before and after Stage 1. All hashes remain **100% identical**:

- `src/recsys/service.py`: `DC5112DF428587AB0CCEF19DD3BB57369445D42B0E5857D6A9660353A32F3714` (Matched)
- `src/recsys/models/svd.py`: `4C34DE8AB3F982BA1A3BBC91EF3EA96AFD225BD7BEA954FBF3EAE449B506BE3B` (Matched)
- `src/recsys/models/popularity.py`: `6D2774E0F4AB719D658085EFA6D134A6974DBAAF9BF6528A74ACBE0D3AC5DED4` (Matched)
- `src/recsys/data.py`: `EF14EA3209E00204DAE8727B0084F3B264643942579D5F2C38FEF39433DDC788` (Matched)
- `src/recsys/split.py`: `4BA0CDB4C71B2BD58B9000B6BE9BA5263195F29C86E17B38B2D6887E179278FD` (Matched)
- `src/recsys/evaluation.py`: `3C93F268A86400226B6D47AD2500EE3B41968764CE90E5E85624772DDC471712` (Matched)
- `tests/unit/test_app.py`: `09E3CE0BB117039658BE8D8F675C41EAE7BECCCE9C5CF938D82588947AA2C4C6` (Matched)
- `PROJECT_STATUS.md`: `1625D64BE32F2A4458103253731848206AB5C8AD2B8894F4908F59DD73244537` (Matched)
- `RULES.md`: `C2B644F33A70A5C17AC5D8F089204D678354729C20AE48697F9383E37E005A54` (Matched)
