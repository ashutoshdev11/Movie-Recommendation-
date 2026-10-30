# MovieLens 100K Data Quality & Integrity Report

**Date:** 2026-10-30  
**Dataset Provenance:** GroupLens Research, University of Minnesota (`ml-100k`)  
**Citation:** Harper & Konstan (2015), "The MovieLens Datasets: History and Context", ACM TiiS 5(4).

---

## 1. Summary of Data Assets

The raw MovieLens 100K dataset consists of interaction records, catalog metadata, and demographic descriptors:

| File | Entity | Observed Records | Expected Record Count | Verification Status |
|---|---|:---:|:---:|:---:|
| `u.data` | User-Item Ratings | 100,000 | 100,000 | Verified |
| `u.item` | Movie Catalog & Genres | 1,682 | 1,682 | Verified |
| `u.user` | User Demographics | 943 | 943 | Verified |

---

## 2. Integrity and Schema Validation Checks

1. **Rating Values and Dtypes:**
   - Ratings are strictly integers in the range $[1, 5]$.
   - Observed minimum rating: `1`.
   - Observed maximum rating: `5`.
   - Data types: `int64` across `user_id`, `item_id`, `rating`, `timestamp`.
2. **Duplicate Records:**
   - Duplicate $(u, i)$ pairs checked: `0` duplicate pairs detected. Every interaction is unique.
3. **Missing Values:**
   - Missing fields in `u.data`: `0`.
   - Missing values in `u.item`: `video_release_date` contains null entries (legacy field, not utilized).
   - Missing fields in `u.user`: `0`.
4. **Key Consistency Across Files:**
   - All `user_id` values in `u.data` ($\{1, \dots, 943\}$) map to valid entries in `u.user`.
   - All `item_id` values in `u.data` ($\{1, \dots, 1682\}$) map to valid entries in `u.item`.
5. **Matrix Sparsity:**
   $$\text{Sparsity} = 1 - \frac{|\text{Ratings}|}{|U| \times |I|} = 1 - \frac{100,000}{943 \times 1,682} = 1 - \frac{100,000}{1,586,126} \approx 93.695\%$$
   The interaction matrix is $93.70\%$ sparse. Missing values represent unobserved ratings, never explicit zero ratings.

---

## 3. Cleaning Rules Applied
Because the canonical MovieLens 100K dataset is already curated and validated:
- No rows were dropped or imputated.
- No artificial synthetic ratings were injected.
- Unobserved matrix entries remain missing and are handled strictly via sparse SciPy CSR representations and fallback mechanisms.
