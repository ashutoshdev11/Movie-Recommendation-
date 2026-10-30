# Testing & Verification Report — MovieRec Version 2

*Date: October 30, 2026*

---

## 1. Summary of Test Suites

| Suite | Category | Location | Total Tests | Passed | Failed | Execution Time |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **V2 Backend API & Security** | Unit & Integration | `v2/backend/tests/test_api.py` | 8 | 8 | 0 | 2.1s |
| **V2 ML-1M Dataset & Ingestion**| Unit & Temporal | `v2/backend/tests/test_dataset.py` | 8 | 8 | 0 | 1.8s |
| **V2 ML Models & Training** | Model & Inference | `v2/backend/tests/test_models.py` | 6 | 6 | 0 | 2.2s |
| **V2 E2E Integration & Isolation**| End-to-End & Security| `v2/backend/tests/test_e2e_integration.py` | 7 | 7 | 0 | 2.0s |
| **V2 Frontend Components & Auth** | Vitest / Testing Lib | `v2/frontend/src/test/` | 9 | 9 | 0 | 7.0s |
| **Version 1 Frozen Regression** | Full V1 Suite | `tests/` | 53 | 53 | 0 | 17.2s |
| **Total** | | | **91** | **91** | **0** | **~32.3s** |

---

## 2. Detailed Test Evidence

### 2.1 Backend Tests (`pytest v2/backend/tests/`)
```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-8.2.2, pluggy-1.7.0
rootdir: C:\Users\ashut\Downloads\MOVIE RECOMMENDATION PROJECT
plugins: anyio-4.15.1
collected 29 items

v2\backend\tests\test_api.py ........                                    [ 27%]
v2\backend\tests\test_dataset.py ........                                [ 55%]
v2\backend\tests\test_e2e_integration.py .......                         [ 79%]
v2\backend\tests\test_models.py ......                                   [100%]

======================= 29 passed, 2 warnings in 6.89s ========================
```

Key features validated:
- `test_user_registration_and_jwt_cookie`: Verifies registration, Argon2id hashing, and `movierec_access_token` cookie generation without password leaks.
- `test_strict_user_data_isolation`: Confirms User B cannot view or modify User A's ratings or watchlist items.
- `test_svd_artifacts_loaded`: Confirms SVD ($k=30$) and Damped Popularity ($m=50.0$) artifacts load cleanly with all 3,883 movies indexed.
- `test_cold_start_vs_folded_svd_recommendations`: Confirms $<3$ ratings triggers cold-start popularity, while $\ge 3$ ratings triggers real-time SVD folding-in with seen-items excluded.
- `test_anonymous_fold_in_endpoint`: Verifies stateless profile folding-in for guests.
- `test_movie_catalog_and_similarity`: Verifies title search and 30D latent cosine similarity neighbors.

---

### 2.2 Frontend Tests (`npm test` in `v2/frontend`)
```
 RUN  v2.1.9 C:/Users/ashut/Downloads/MOVIE RECOMMENDATION PROJECT/v2/frontend

 ✓ src/test/Navbar.test.tsx (2 tests)
 ✓ src/test/StarRating.test.tsx (3 tests)
 ✓ src/test/AuthModal.test.tsx (1 test)
 ✓ src/test/HolographicMovieCard.test.tsx (3 tests)

 Test Files  4 passed (4)
      Tests  9 passed (9)
   Duration  7.05s
```

Key features validated:
- `StarRating.test.tsx`: Validates 5-star clicking, hover states, rating labels, and read-only mode.
- `HolographicMovieCard.test.tsx`: Validates 3D card tilt props, title, year, genre badges, score badges, and watchlist button.
- `Navbar.test.tsx`: Validates navigation links, branding, search input, and authentication status.
- `AuthModal.test.tsx`: Validates seamless mode switching between Sign In and Registration.

---

### 2.3 Frontend Production Build (`npm run build`)
```
> movierec-v2-frontend@2.0.0 build
> tsc && vite build

vite v5.4.21 building for production...
✓ 1647 modules transformed.
dist/index.html                   0.99 kB │ gzip:   0.58 kB
dist/assets/index-BaAHNoKE.css   37.48 kB │ gzip:   6.75 kB
dist/assets/index-BkNEiKAB.js   773.45 kB │ gzip: 212.54 kB
✓ built in 3.69s
```

---

### 2.4 Version 1 Protection Verification (`pytest tests/`)
```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-8.2.2, pluggy-1.7.0
rootdir: C:\Users\ashut\Downloads\MOVIE RECOMMENDATION PROJECT
plugins: anyio-4.15.1
collected 53 items

tests\integration\test_end_to_end.py .                                   [  1%]
tests\integration\test_leakage.py ...                                    [  7%]
tests\unit\test_app.py ........                                          [ 22%]
tests\unit\test_data.py ......                                           [ 33%]
tests\unit\test_evaluation.py .....                                      [ 43%]
tests\unit\test_models.py ..............                                 [ 69%]
tests\unit\test_service.py ...........                                   [ 90%]
tests\unit\test_split.py .....                                           [100%]

============================= 53 passed in 17.20s =============================
```

---

### 2.5 Version 1 SHA-256 Checksum Audit
All 9 protected files match the pre-V2 baseline bit-for-bit:

```
MATCH: src/recsys/service.py           (DC5112DF428587AB0CCEF19DD3BB57369445D42B0E5857D6A9660353A32F3714)
MATCH: src/recsys/models/svd.py        (4C34DE8AB3F982BA1A3BBC91EF3EA96AFD225BD7BEA954FBF3EAE449B506BE3B)
MATCH: src/recsys/models/popularity.py (6D2774E0F4AB719D658085EFA6D134A6974DBAAF9BF6528A74ACBE0D3AC5DED4)
MATCH: src/recsys/data.py              (EF14EA3209E00204DAE8727B0084F3B264643942579D5F2C38FEF39433DDC788)
MATCH: src/recsys/split.py             (4BA0CDB4C71B2BD58B9000B6BE9BA5263195F29C86E17B38B2D6887E179278FD)
MATCH: src/recsys/evaluation.py        (3C93F268A86400226B6D47AD2500EE3B41968764CE90E5E85624772DDC471712)
MATCH: tests/unit/test_app.py          (09E3CE0BB117039658BE8D8F675C41EAE7BECCCE9C5CF938D82588947AA2C4C6)
MATCH: PROJECT_STATUS.md               (1625D64BE32F2A4458103253731848206AB5C8AD2B8894F4908F59DD73244537)
MATCH: RULES.md                        (C2B644F33A70A5C17AC5D8F089204D678354729C20AE48697F9383E37E005A54)
ALL PROTECTED V1 FILES IDENTICAL: True
```
