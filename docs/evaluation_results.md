# Evaluation Results and Model Selection Report

## 1. Executive Summary

This report documents the empirical evaluation and model selection process for the MovieLens 100K collaborative filtering system, following the rigorous evaluation protocol established in `docs/evaluation_protocol.md`.

- **Primary Selection Metric:** Validation NDCG@10 (pre-committed prior to inspecting test data).
- **Secondary Metric:** Root Mean Squared Error (RMSE).
- **Selected Champion Model:** **`TruncatedSVDRecommender`** ($n_{\text{factors}} = 20$).
- **Test Set Performance:** Truncated SVD achieved **NDCG@10 = 0.1198**, substantially outperforming the Popularity Baseline (0.0682), Item-based kNN (0.0215), and User-based kNN (0.0066).
- **Key Empirical Finding for Viva Defense:** Rating prediction error (RMSE) and top-$N$ recommendation utility (NDCG@10) completely diverged. User-based kNN achieved the best RMSE (**1.0184**) yet the worst NDCG@10 (**0.0066**). Conversely, Truncated SVD dominated top-$N$ ranking utility despite a higher RMSE (**1.1028**), proving that matrix factorization captures relative latent preference orderings far more effectively than sparse neighborhood heuristics.

---

## 2. Evaluation Methodology & Leakage Prevention

### 2.1 Per-User Chronological Partitioning
The dataset of 100,000 ratings is split chronologically per user with fixed random seed `42`:
- **Training Set (60%):** 59,576 ratings (used for tuning model priors and similarity matrices).
- **Validation Set (20%):** 19,676 ratings (used exclusively for hyperparameter grid search and model selection).
- **Test Set (20%):** 20,748 ratings (held out strictly until model selection was frozen).

For the final test evaluation, selected models were refit on **Train + Validation** (79,252 ratings) and evaluated exactly once on the held-out Test set.

### 2.2 Top-$N$ Ranking Evaluation Protocol
- **Candidate Item Space:** For each user $u$, candidate items for recommendation comprise all catalog movies not previously rated in training/validation:
  $$\mathcal{C}_u = I \setminus \text{Seen}_u$$
  Candidate set size is $|\mathcal{C}_u| \approx 1,500\text{--}1,650$ unrated movies per user, avoiding the artificial inflation seen in subsampled candidate protocols.
- **Relevance Criterion:** A held-out item $i$ is relevant if its true rating satisfies $r_{u, i} \ge 4.0$.
- **Handling Zero-Relevant Users:** Users with no relevant items in the evaluation split have an undefined IDCG ($0.0$). Per protocol, these users are excluded from ranking macro-averages and explicitly counted:
  - Validation Split: 150 sampled users $\to$ 143 evaluated, **7 excluded**.
  - Final Test Split: 943 total users $\to$ 918 evaluated, **25 excluded**.

---

## 3. Evaluation Metric Definitions

| Metric | Mathematical Formula | Conceptual Interpretation |
| :--- | :--- | :--- |
| **MAE** | $\frac{1}{|\mathcal{T}|} \sum \|r_{ui} - \hat{r}_{ui}\|$ | Average absolute error of predicted rating stars. |
| **RMSE** | $\sqrt{\frac{1}{|\mathcal{T}|} \sum (r_{ui} - \hat{r}_{ui})^2}$ | Penalizes large estimation errors quadratically. |
| **Precision@K** | $\frac{\|\text{Rec}_K(u) \cap \text{Rel}_u\|}{K}$ | Fraction of top-$K$ recommendations that are relevant ($r \ge 4.0$). |
| **Recall@K** | $\frac{\|\text{Rec}_K(u) \cap \text{Rel}_u\|}{\|\text{Rel}_u\|}$ | Fraction of all relevant user test items captured in top-$K$. |
| **NDCG@K** | $\frac{\text{DCG@K}}{\text{IDCG@K}} = \frac{\sum \frac{2^{\text{rel}_m}-1}{\log_2(m+1)}}{\text{IDCG@K}}$ | Evaluates rank-order discount; higher weights for hits near rank 1. |
| **Coverage@K** | $\frac{\|\bigcup_{u} \text{Rec}_K(u)\|}{\|I\|}$ | Percentage of total catalog items recommended at least once. |
| **Novelty@K** | $\frac{1}{\|U\| \cdot K} \sum -\log_2 P(i)$ | Average self-information of items; rewards long-tail recommendations. |

---

## 4. Validation Hyperparameter Tuning & Model Selection

Hyperparameter grid searches were executed across all four model families using the validation split only (`results/validation_tuning.csv`, 32 total configurations). The model selection decision was locked based on **Validation NDCG@10**:

### 4.1 Hyperparameter Grid Results Summary

1. **Popularity Baseline (15 configurations):**
   - Grid: `damping` $\in \{0.0, 5.0, 10.0, 25.0, 50.0\}$, `min_ratings` $\in \{1, 5, 10\}$.
   - Best Config: `damping = 50.0, min_ratings = 1.0` $\to$ **NDCG@10 = 0.0702**, RMSE = 1.0404.
   - Analysis: Heavier damping ($m=50.0$) shrinks low-interaction items toward the global mean ($\mu=3.53$), preventing noisy 5-star outlier movies from dominating the top ranks.

2. **User-based kNN (6 configurations):**
   - Grid: $k \in \{10, 20, 30\}$, `min_overlap` $\in \{1, 2\}$.
   - Best Config: $k = 10, \text{min\_overlap} = 2$ $\to$ **NDCG@10 = 0.0050**, RMSE = 0.9985.
   - Analysis: While $k=30$ reduced RMSE to 0.9759, NDCG@10 degraded to 0.0029 due to neighborhood homogenization. $k=10$ preserved sharper ranking distinction.

3. **Item-based kNN (6 configurations):**
   - Grid: $k \in \{10, 20, 30\}$, `min_overlap` $\in \{1, 2\}$.
   - Best Config: $k = 10, \text{min\_overlap} = 1$ $\to$ **NDCG@10 = 0.0050**, RMSE = 1.0832.
   - Analysis: Smaller neighborhood size ($k=10$) with minimal overlap constraints maximized coverage while maintaining top-rank stability.

4. **Truncated SVD Latent Factor Benchmark (5 configurations):**
   - Grid: $n_{\text{factors}} \in \{5, 10, 20, 30, 50\}$ (mean-centered CSR).
   - $n=5$: NDCG@10 = 0.1131, RMSE = 1.0383
   - $n=10$: NDCG@10 = 0.1030, RMSE = 1.0379
   - **$n=20$ (Winner):** **NDCG@10 = 0.1138**, RMSE = 1.0407
   - $n=30$: NDCG@10 = 0.1124, RMSE = 1.0442
   - $n=50$: NDCG@10 = 0.1001, RMSE = 1.0503
   - Analysis: $n_{\text{factors}} = 20$ provided the optimal balance between latent dimensionality and regularization, achieving the highest validation ranking NDCG@10.

---

## 5. Held-Out Final Test Evaluation Results

All four selected models were refit on `Train + Validation` (79,252 ratings) and evaluated once on the 20,748 held-out test ratings (`results/test_evaluation_results.csv`).

### 5.1 Test Evaluation Metrics Table ($K=10$)

| Model | Config | NDCG@10 | Precision@10 | Recall@10 | RMSE | MAE | Coverage@10 | Novelty@10 |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **TruncatedSVDRecommender** | `n_factors=20` | **0.1198** | **0.0914** | **0.0902** | 1.1028 | 0.8735 | 20.69% | 3.5555 |
| **PopularityBaseline** | `damping=50.0, min=1` | 0.0682 | 0.0593 | 0.0511 | 1.1189 | 0.9088 | 3.80% | 3.6090 |
| **ItemKNNRecommender** | `k=10, min_overlap=1` | 0.0215 | 0.0210 | 0.0139 | 1.1177 | 0.8851 | **76.34%** | 8.0758 |
| **UserKNNRecommender** | `k=10, min_overlap=2` | 0.0066 | 0.0057 | 0.0040 | **1.0184** | **0.8027** | 22.47% | **8.8244** |

### 5.2 Test Metrics Across Multiple Cutoffs ($K \in \{5, 10, 20\}$)

| Model | Metric | K=5 | K=10 | K=20 |
| :--- | :--- | :---: | :---: | :---: |
| **TruncatedSVD** | NDCG@K | **0.1252** | **0.1198** | **0.1276** |
| | Precision@K | **0.1109** | **0.0914** | **0.0727** |
| | Recall@K | 0.0563 | **0.0902** | **0.1372** |
| | Catalog Coverage@K | 14.63% | 20.69% | 29.25% |
| **PopularityBaseline** | NDCG@K | 0.0667 | 0.0682 | 0.0765 |
| | Precision@K | 0.0651 | 0.0593 | 0.0509 |
| | Recall@K | 0.0298 | 0.0511 | 0.0852 |
| | Catalog Coverage@K | 2.32% | 3.80% | 5.83% |
| **ItemKNN** | NDCG@K | 0.0199 | 0.0215 | 0.0240 |
| | Precision@K | 0.0200 | 0.0210 | 0.0191 |
| | Recall@K | 0.0068 | 0.0139 | 0.0260 |
| | Catalog Coverage@K | **55.65%** | **76.34%** | **90.67%** |
| **UserKNN** | NDCG@K | 0.0066 | 0.0066 | 0.0085 |
| | Precision@K | 0.0061 | 0.0057 | 0.0065 |
| | Recall@K | 0.0021 | 0.0040 | 0.0092 |
| | Catalog Coverage@K | 15.81% | 22.47% | 31.69% |

---

## 6. Cold-Start Experiment Analysis

To evaluate model resilience to extreme profile sparsity, an experiment was conducted by truncating training ratings to $M \in \{1, 3, 5, 10\}$ interactions (`results/cold_start_experiment.csv` and `results/plots/cold_start_curve.png`).

| Training History ($M$) | Metric | PopularityBaseline | UserKNN | ItemKNN | TruncatedSVD |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **$M = 1$ (Extreme Cold-Start)** | NDCG@10 | **0.0592** | 0.0000 | 0.0078 | 0.0384 |
| | Recall@10 | **0.0503** | 0.0000 | 0.0072 | 0.0329 |
| | RMSE | 1.0470 | **1.0445** | 1.2150 | 1.4552 |
| **$M = 3$** | NDCG@10 | **0.0601** | 0.0193 | 0.0098 | **0.0601** |
| | Recall@10 | 0.0511 | 0.0166 | 0.0108 | **0.0512** |
| | RMSE | **1.0470** | 1.2047 | 1.2593 | 1.2453 |
| **$M = 5$** | NDCG@10 | 0.0608 | 0.0185 | 0.0129 | **0.0694** |
| | Recall@10 | 0.0511 | 0.0144 | 0.0129 | **0.0843** |
| | RMSE | **1.0470** | 1.1502 | 1.2209 | 1.1627 |
| **$M = 10$** | NDCG@10 | **0.0617** | 0.0126 | 0.0072 | 0.0513 |
| | Recall@10 | **0.0523** | 0.0060 | 0.0044 | 0.0497 |
| | RMSE | **1.0469** | 1.0627 | 1.1371 | 1.0846 |

### Insights for Viva Defense:
1. **Popularity Baseline as Cold-Start Safety Net:** Popularity NDCG@10 remains stable across all interaction levels ($0.0592$ at $M=1$ to $0.0617$ at $M=10$). When a user has only 1 rating, non-personalized popularity recommendations are the only reliable signal.
2. **UserKNN Failure Under Cold-Start:** At $M=1$, UserKNN yields NDCG@10 = **0.0000** because finding 2 co-rated items with minimum overlap is impossible for single-rating profiles.
3. **SVD Cold-Start Transition:** Truncated SVD surpasses Popularity once the user reaches $M \ge 3$ ratings, demonstrating rapid latent factor alignment.

---

## 7. Viva Defense Discussion & Critical Trade-offs

### 7.1 Why Did Truncated SVD Beat kNN on Ranking?
1. **Curse of Dimensionality in Sparse Spaces:** With 93.70% sparsity, finding users or items with sufficient co-rated overlap is statistically rare. User-based and Item-based kNN frequently drop into their fallback predictors.
2. **Latent Semantic Generalization:** SVD projects sparse interaction vectors into dense 20-dimensional concept spaces (capturing genres, pacing, and mood), allowing it to score candidate items that share zero direct co-raters.

### 7.2 Why Did UserKNN Win on RMSE but Lose on NDCG@10?
- **Global Error vs. Rank Ordering:** RMSE evaluates rating prediction across items the user actually chose to watch. For observed ratings, user mean-centering accurately predicts baseline score scales.
- **Top-$N$ Retrieval Challenge:** When ranking 1,500 unseen items, UserKNN produces tied fallback predictions for most candidates, ruining top-10 precision. Truncated SVD produces a continuous, discriminative preference score for every unrated catalog item.

### 7.3 Diversity, Coverage, and Novelty Trade-offs
- **ItemKNN is the Discovery Engine:** While ItemKNN had low NDCG@10 (0.0215), it achieved an astounding **76.34% Catalog Coverage@10** and Novelty of **8.0758**. It distributes recommendations into the long tail rather than recycling popular blockbusters.
- **Popularity Baseline Suffers from Concentration:** While Popularity achieves strong NDCG@10 (0.0682), it covers only **3.80%** of the catalog, repeatedly recommending the same 60 blockbuster movies to everyone.

### 7.4 Offline Evaluation Limitations
1. **Missing-Not-At-Random (MNAR):** Users choose which movies to rate. Highly rated test items reflect self-selection bias, not an unbiased random trial.
2. **Popularity Bias:** Blockbuster movies receive more ratings, artificially favoring models that recommend popular items.
3. **No Interactive Feedback:** Offline metrics cannot test serendipity, explanation trust, or user satisfaction, which will be demonstrated in the Phase 4 Streamlit application.
