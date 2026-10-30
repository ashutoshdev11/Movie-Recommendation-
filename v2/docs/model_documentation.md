# Machine Learning Model Documentation — MovieRec Version 2

This document details the mathematical formulation, training protocol, evaluation methodology, and production deployment of the Version 2 recommendation models.

---

## 1. Dataset & Chronological Invariant

MovieRec Version 2 is trained and evaluated exclusively on the **MovieLens 1M** dataset:
- **Total Ratings:** 1,000,209 ratings across 6,040 users and 3,883 movies (3,706 rated).
- **Chronological 60/20/20 Partitioning:** Ratings for every user are sorted by timestamp $t$:
  $$\max(t_{\text{train}}) \le \min(t_{\text{val}}) \le \max(t_{\text{val}}) \le \min(t_{\text{test}})$$
  - **Train Split (60%):** 597,742 ratings.
  - **Validation Split (20%):** 198,903 ratings (used exclusively for model selection).
  - **Test Split (20%):** 203,564 ratings (evaluated once after model selection).

---

## 2. Models Implemented

### 2.1 Truncated SVD Recommender ($k=30$)

#### Mathematical Formulation
Truncated Singular Value Decomposition factorizes the centered user-item interaction matrix $R_c$:
1. Center matrix per user: $R_c = R - \mu_u$, where $\mu_u$ is user $u$'s mean rating.
2. Low-rank decomposition via randomized SVD (seed: 42):
   $$R_c \approx U_k \Sigma_k V_k^T$$
   where:
   - $U_k \in \mathbb{R}^{|U| \times k}$ (user singular vectors)
   - $\Sigma_k \in \mathbb{R}^{k \times k}$ (singular values diagonal matrix)
   - $V_k^T \in \mathbb{R}^{k \times |I|}$ (item singular vectors transposed)
3. Predicted rating for user $u$ on item $i$:
   $$\hat{r}_{u,i} = \text{clip}\left(\mu_u + (U_k \Sigma_k V_k^T)_{u,i}, 1.0, 5.0\right)$$

#### Real-Time Online Profile Folding-In
To recommend for registered website users without slow retraining, online folding-in is implemented:
Given an arbitrary sparse vector of ratings $r_{\text{new}}$:
$$\hat{u}_{\text{new}} = (r_{\text{new}} - \mu_{\text{new}}) V_k \Sigma_k^{-1}$$
$$\hat{r}_{\text{new}, i} = \mu_{\text{new}} + \hat{u}_{\text{new}} \Sigma_k v_i^T$$
- **Inference Complexity:** $\mathcal{O}(|I_{\text{rated}}| \cdot k + |I| \cdot k)$ operations.
- **Observed Production Latency:** $< 3\text{ ms}$ per recommendation query.

---

### 2.2 Bayesian Damped Popularity Baseline ($m=50.0$)

#### Mathematical Formulation
Provides a smooth Bayesian shrinkage estimate of an item's true appeal:
$$\text{score}_i = \frac{\sum_{u} r_{u,i} + m \cdot \mu_{\text{global}}}{N_i + m}$$
where:
- $\mu_{\text{global}} \approx 3.5815$ (mean rating across the entire training split).
- $N_i$ is the number of ratings received by movie $i$.
- $m = 50.0$ is the Bayesian prior weight (damping factor).

Movies with very few ratings are regularized heavily toward the global mean, preventing niche titles with a single 5-star rating from dominating top recommendations.

---

## 3. Evaluation Methodology & Metrics

Models were evaluated on the validation split across 3 standard ranking and error metrics:

1. **NDCG@10 (Normalized Discounted Cumulative Gain):**
   $$\text{DCG@10} = \sum_{k=1}^{10} \frac{2^{r_{(k)}} - 1}{\log_2(k + 1)}, \quad \text{NDCG@10} = \frac{\text{DCG@10}}{\text{IDCG@10}}$$
2. **MAP@10 (Mean Average Precision):**
   $$\text{AP@10} = \frac{1}{\min(10, |R_{\text{rel}}|)} \sum_{k=1}^{10} P@k \cdot \mathbb{I}(k \in R_{\text{rel}})$$
   - *Relevance Threshold:* A movie is strictly defined as relevant if its actual ground-truth rating $r \ge 4.0$.
3. **RMSE (Root Mean Squared Error):**
   $$\text{RMSE} = \sqrt{\frac{1}{|E|} \sum_{(u,i) \in E} (r_{u,i} - \hat{r}_{u,i})^2}$$

---

## 4. Evaluation Results

### Validation Split (Model Selection)

| Model Configuration | Validation NDCG@10 | Validation MAP@10 | Validation RMSE | Selection Decision |
| :--- | :--- | :--- | :--- | :--- |
| **Truncated SVD ($k=30$, seed=42)** | **0.0989** | **0.0494** | **1.0583** | **SELECTED** |
| Damped Popularity ($m=50.0$) | 0.0477 | 0.0163 | 1.0772 | Baseline / Fallback |

*Reasoning:* Truncated SVD more than doubled validation ranking quality over the popularity baseline (NDCG@10: 0.0989 vs 0.0477; MAP@10: 0.0494 vs 0.0163), demonstrating substantial collaborative filtering lift.

### Test Split (Unbiased Final Benchmark)

Evaluated exactly once on the held-out test split after model selection:

| Model | Test NDCG@10 | Test MAP@10 | Test RMSE |
| :--- | :--- | :--- | :--- |
| **Truncated SVD ($k=30$)** | **0.0802** | **0.0388** | **1.0657** |

---

## 5. Artifact Manifest

All artifacts are persisted in `v2/backend/artifacts/`:
1. `v2_svd_k30.npz`:
   - `U`: User factors matrix $(6040, 30)$
   - `sigma`: Singular values $(30,)$
   - `Vt`: Item factors matrix $(30, 3624)$
   - `user_means`: Dictionary of centered user baseline ratings
   - `all_users` & `all_items`: Index mapping arrays
   - `user_seen_items`: JSON string of train-split seen items
2. `v2_popularity_baseline.json`:
   - Ranked item pairs, item counts, and damped scores
3. `v2_model_metadata.json`:
   - Complete hyperparameters, training timestamp, train split stats, and validation/test metrics.
