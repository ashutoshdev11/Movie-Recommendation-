# Project Specification: Movie Recommendation System

## 1. Project Objectives
The objective of this project is to build, evaluate, and demonstrate an end-to-end, reproducible, and explainable collaborative-filtering movie recommendation system using the MovieLens 100K dataset (`ml-100k`). Designed as an academic project for viva defense, every component—from data preprocessing and mathematical formulation to model serving and web UI—emphasizes clarity, rigorous evaluation hygiene, transparency, and architectural simplicity without relying on high-level recommendation black boxes.

## 2. Scope
- **Dataset:** GroupLens MovieLens 100K (`ml-100k`), consisting of 100,000 ratings from 943 users across 1,682 movies.
- **Data Engineering:** Automated download, verification, data integrity validation, exploratory data analysis (EDA), and per-user chronological splitting (60% train, 20% validation, 20% test).
- **Core Algorithms:**
  1. Popularity Baseline (damped mean rating with global prior).
  2. User-based Collaborative Filtering (k-Nearest Neighbors with mean-centering and Pearson correlation).
  3. Item-based Collaborative Filtering (k-Nearest Neighbors with adjusted cosine similarity).
  4. Truncated SVD Benchmark (matrix factorization via `scipy.sparse.linalg.svds` on user-mean-centred ratings).
- **Evaluation Framework:** Both error-based metrics (MAE, RMSE) and top-N ranking metrics (Precision@K, Recall@K, NDCG@K for $K \in \{5, 10, 20\}$), Catalog Coverage, Novelty/Diversity, plus cold-start performance analysis.
- **Model Selection:** Explicit pre-committed rule prioritizing NDCG@10 on validation data, with RMSE as a secondary metric.
- **Application & Service:** A clean modular service layer (`RecommenderService`) feeding an interactive Streamlit application that allows interactive user rating, recommendation generation, genre filtering, and model-grounded explanations.
- **Academic & Viva Preparation:** Rigorous decision logging, mathematical formulations, and plain-language viva questions with answers.

## 3. Out-of-Scope
- Deep learning / neural collaborative filtering architectures (e.g., NeuMF, AutoRec, Transformers).
- Hybrid content-based algorithms relying on external movie posters, synopses, text embeddings, or third-party web scraping.
- Multi-armed bandit or reinforcement learning online recommendation mechanisms.
- Production distributed deployment, multi-tenant authentication, or commercial cloud hosting.
- Use of unverified high-level recommender frameworks (e.g., Surprise, LightFM, implicit) to maintain full viva explainability.

## 4. Functional Requirements
- **FR1: Data Acquisition & Validation:** Script to download `ml-100k.zip` from GroupLens, verify structure, unpack to `data/raw/`, and validate data types, range ($[1, 5]$ integer ratings), uniqueness of $(u, i)$ pairs, and timestamp consistency.
- **FR2: Exploratory Data Analysis:** Generate at least 5 annotated figures covering user activity distribution, item popularity long-tail, rating distribution, sparsity, and temporal rating trends.
- **FR3: Per-User Chronological Splitting:** Order each user's rating history chronologically by timestamp and assign the first 60% to training, next 20% to validation, and final 20% to test. Users are guaranteed representation in train; ties broken with fixed seed (42).
- **FR4: Model Implementation & Common Interface:** All models must implement:
  - `fit(train_ratings)`: Learn parameters/similarities exclusively from training observations.
  - `predict(user_id, item_id) -> float`: Return bounded rating prediction $[1, 5]$ with fallback chain (item mean -> user mean -> global mean).
  - `recommend(user_id, n, exclude_seen=True) -> list[(item_id, score)]`: Return ranked recommendations of unseen items.
- **FR5: Model Evaluation & Benchmarking:**
  - Compute MAE, RMSE, Precision@K, Recall@K, NDCG@K ($K \in \{5, 10, 20\}$), item coverage, and novelty.
  - Validate hyperparameter tuning strictly on validation set.
  - Execute test set evaluation exactly once via a logged `--final` script flag.
  - Conduct cold-start experiments truncating user profiles to $\{1, 3, 5, 10\}$ ratings.
- **FR6: Recommendation Service:** `RecommenderService` providing user recommendations, item similarity lookup, movie title searching, and cold-start fallback (popularity-ranked items with clear labeling).
- **FR7: Interactive Streamlit UI:** Search/select movies, input ratings, select top-$N$, filter by genre, inspect predictions, and view transparent explanations based on item/neighbor contributions.

## 5. Non-Functional Requirements
- **NFR1: Evaluation Hygiene & Zero Data Leakage:** Held-out validation and test data must never influence training-dependent values (e.g., user means, item means, similarity matrices, factor decompositions).
- **NFR2: Reproducibility:** Fixed random seed `42` utilized across splits, tie-breakers, and matrix decomposition initializations. All configurations, seeds, and execution timestamps logged to CSVs.
- **NFR3: Computational Efficiency:** Sparse matrix representations (SciPy CSR) for memory efficiency, avoiding dense full matrix expansions where possible; fit and evaluation runtime suitable for standard local hardware.
- **NFR4: Viva Explainability:** Code clarity over extreme optimization; every formula documented in markdown and traceable to fundamental linear algebra and collaborative-filtering principles.
- **NFR5: Robustness & Test Coverage:** Strict unit and integration tests across data splitting, toy-matrix math proofs, edge cases (unknown IDs, zero denominators, sparse profiles), and Streamlit workflows (`AppTest`).

## 6. Workspace Environment Inspection Findings
An initial non-destructive environment inspection performed during Phase 0 revealed:
- **Operating System:** Windows 11 (Microsoft Windows NT 10.0.26300.0).
- **Workspace State:** Initial workspace was empty. Prompt kit files successfully initialized. No code, installs, or dataset files present.
- **Python Availability:** `python` in standard PATH points to the WindowsApps app execution alias, requiring Python 3.10+ installation or environment configuration in Phase 1.
- **Git Availability:** `git` is currently not in PATH. Version control must be configured or accommodated in subsequent phases.

## 7. Risk Register

| ID | Risk Description | Likelihood | Impact | Mitigation Strategy |
|---|---|:---:|:---:|---|
| **R1** | **Python Environment Missing in PATH:** WindowsApps execution alias prevents direct execution of sandboxed Python commands. | High | High | In Phase 1 setup, install or locate standard Python 3.10+ (or active venv) and ensure absolute path or PATH resolution is verified before package installation. |
| **R2** | **Git Executable Missing:** Git is not recognized in PATH, potentially complicating automated repo tracking or gitignore checks. | Medium | Medium | Install Git for Windows or ensure `.gitignore` is manually verified and standard folder exclusion practices are strictly enforced in tests. |
| **R3** | **Data Leakage into Feature Spaces:** Computing global means, user means, or item similarities using all ratings (train + val + test) skews evaluation. | High | Critical | Compute all statistics, means, priors, and similarities strictly inside `fit()` on the provided training partition only. Enforce with invariant tests. |
| **R4** | **Unrated Movies Treated as Zero:** Treating missing matrix entries as explicit 0 ratings severely distorts user preferences and similarity values. | Medium | High | Maintain sparse matrix representations where unobserved entries represent missing values rather than zeros; compute similarities only across co-rated items. |
| **R5** | **Test Set Snooping / Overfitting:** Hyperparameters adjusted based on test set results, invalidating reported generalization metrics. | Medium | Critical | Restrict all tuning sweeps strictly to the validation split. Gate the test evaluation behind a logged `--final` CLI flag permitted to run only once per chosen model. |
| **R6** | **Cold-Start Users with Zero Test Hits:** Users with no test ratings $\ge 4.0$ lead to division by zero in Precision@K and NDCG@K. | High | Medium | Follow explicit protocol rule: exclude users with zero relevant test items from ranking metrics, log and report the exact count of excluded users. |
| **R7** | **Zero Denominator in kNN Similarity:** Target item or user has zero overlapping neighbors with positive similarity, causing division by zero or NaN. | High | High | Implement deterministic fallback chain: fallback to item mean rating $\rightarrow$ user mean rating $\rightarrow$ global training mean rating. Clip all outputs to $[1, 5]$. |
| **R8** | **Truncated SVD Sparsity Invalidation:** Subtracting user means across unrated items turns a sparse matrix dense, creating huge memory overhead. | Medium | High | Perform mean-centering only on observed ratings, or use a custom sparse linear operator / SVD formulation that avoids materializing dense $U \times I$ matrices. |
| **R9** | **GroupLens Dataset Redistribution Violation:** Accidentally committing MovieLens dataset violates GroupLens redistribution terms. | Low | High | Enforce `.gitignore` on `data/`, provide automated download script `scripts/download_data.py`, and test that no data files are tracked. |
| **R10** | **Streamlit App Component Desynchronization:** UI controls or filters fail to interact with underlying `RecommenderService`. | Medium | Medium | Implement automated UI integration tests with `streamlit.testing.v1.AppTest` verifying every control impacts rendered results. |
