# Evaluation Protocol: Movie Recommendation System

## 1. Overview and Core Principles
This document establishes the binding experimental protocol for model validation, tuning, selection, and final evaluation. It defines the temporal partitioning strategy, mathematical formulations for all metrics, leakage-prevention mechanisms, relevance criteria, and cold-start experiments.

---

## 2. Dataset Splitting Protocol

### 2.1 Chronological Per-User Partitioning
- **Proportions:** 60% Train / 20% Validation / 20% Test per user.
- **Mechanism:**
  1. For each user $u \in U$, sort their ratings chronologically ascending by timestamp $t$:
     $$R_u = \{(i_{u, 1}, r_{u, 1}, t_{u, 1}), (i_{u, 2}, r_{u, 2}, t_{u, 2}), \dots, (i_{u, n_u}, r_{u, n_u}, t_{u, n_u})\}$$
  2. With $n_u \ge 20$ (guaranteed in MovieLens 100K):
     $$n_{\text{train}} = \lfloor 0.60 \times n_u \rfloor$$
     $$n_{\text{val}} = \lfloor 0.20 \times n_u \rfloor$$
     $$n_{\text{test}} = n_u - n_{\text{train}} - n_{\text{val}}$$
  3. Ratings are partitioned such that:
     $$\max(t_{\text{train}, u}) \le \min(t_{\text{val}, u}) \le \max(t_{\text{val}, u}) \le \min(t_{\text{test}, u})$$
  4. If multiple ratings share the exact same timestamp at split boundaries, tie-breaking is deterministically resolved using fixed random seed `42`.
  5. Every user appears in the training partition ($n_{\text{train}} \ge 12$).

---

## 3. Data Leakage Prevention

Data leakage occurs when information from the evaluation or future sets contaminates model training. We enforce three strict architectural safeguards:

1. **Global and Entity Mean Leakage:**
   - *Risk:* Computing global rating mean $\mu$, user means $\mu_u$, or item means $\mu_i$ using validation or test ratings artificially informs baselines and kNN normalizations.
   - *Prevention:* All mean statistics and priors are computed exclusively from the training partition inside `fit()`. When refitting for the final evaluation, means are recomputed strictly over `train + validation`.
2. **Similarity Matrix / Co-occurrence Leakage:**
   - *Risk:* Building item-item or user-user similarity matrices using ratings from validation or test partitions exposes future co-rating patterns.
   - *Prevention:* Similarity matrices (cosine, adjusted cosine, Pearson) are derived exclusively from the rating matrix of the training partition. Unit tests verify that altering test partition ratings leaves fitted similarities unchanged.
3. **Hyperparameter Overfitting / Test Snooping:**
   - *Risk:* Tuning hyperparameters (e.g., neighborhood size $k$, shrinkage $\lambda$, SVD latent dimension) against test set performance yields overly optimistic metrics.
   - *Prevention:* All hyperparameter searches and model selection decisions are evaluated solely against the validation partition. Test evaluation is locked behind a dedicated script flag (`--final`) permitted to run exactly once per candidate model.

---

## 4. Evaluation Metrics & Mathematical Formulas

Let $U_{\text{eval}}$ be the set of evaluation users, $I$ be the set of all items, $\mathcal{T}_u$ be the ground-truth ratings for user $u$ in the evaluation split, and $\hat{r}_{u, i}$ be the predicted rating.

### 4.1 Rating Prediction Metrics

#### 1. Mean Absolute Error (MAE)
$$\text{MAE} = \frac{1}{\sum_{u \in U_{\text{eval}}} |\mathcal{T}_u|} \sum_{u \in U_{\text{eval}}} \sum_{i \in \mathcal{T}_u} |r_{u, i} - \hat{r}_{u, i}|$$

#### 2. Root Mean Squared Error (RMSE)
$$\text{RMSE} = \sqrt{\frac{1}{\sum_{u \in U_{\text{eval}}} |\mathcal{T}_u|} \sum_{u \in U_{\text{eval}}} \sum_{i \in \mathcal{T}_u} (r_{u, i} - \hat{r}_{u, i})^2}$$

---

### 4.2 Top-$N$ Ranking Metrics

- **Candidate Set:** For user $u$, candidate items for ranking consist of all items in the catalog that user $u$ has **not** rated in the training set (or `train + val` for final test evaluation):
  $$\mathcal{C}_u = I \setminus \text{Seen}_u$$
- **Cutoffs ($K$):** $K \in \{5, 10, 20\}$.
- **Binary Relevance Ground Truth:** An item $i \in \mathcal{T}_u$ is considered relevant ($\text{rel}_{u, i} = 1$) if its true rating satisfies:
  $$\text{rel}_{u, i} = \begin{cases} 1 & \text{if } r_{u, i} \ge 4.0 \\ 0 & \text{otherwise} \end{cases}$$
- Let $\text{Rec}_K(u)$ denote the ordered list of top-$K$ recommended items for user $u$.

#### 3. Precision@K
$$\text{Precision@K}(u) = \frac{|\{i \in \text{Rec}_K(u) : \text{rel}_{u, i} = 1\}|}{K}$$
$$\text{Precision@K} = \frac{1}{|U^*|} \sum_{u \in U^*} \text{Precision@K}(u)$$

#### 4. Recall@K
$$\text{Recall@K}(u) = \frac{|\{i \in \text{Rec}_K(u) : \text{rel}_{u, i} = 1\}|}{|\{i \in \mathcal{T}_u : \text{rel}_{u, i} = 1\}|}$$
$$\text{Recall@K} = \frac{1}{|U^*|} \sum_{u \in U^*} \text{Recall@K}(u)$$

#### 5. Normalized Discounted Cumulative Gain (NDCG@K)
Discounted Cumulative Gain at rank $K$:
$$\text{DCG@K}(u) = \sum_{m=1}^{K} \frac{2^{\text{rel}_{u, \text{Rec}_K(u)[m]}} - 1}{\log_2(m + 1)}$$
Ideal DCG at rank $K$ ($\text{IDCG@K}(u)$) is the DCG@K of the ideal ranking sorted descending by relevance:
$$\text{NDCG@K}(u) = \frac{\text{DCG@K}(u)}{\text{IDCG@K}(u)}$$
$$\text{NDCG@K} = \frac{1}{|U^*|} \sum_{u \in U^*} \text{NDCG@K}(u)$$

#### 6. Handling Users Without Relevant Items ($U^*$)
Users who have no test items with $r_{u, i} \ge 4.0$ have an undefined Recall@K and NDCG@K ($\text{IDCG@K} = 0$).
- Such users are **excluded** from ranking metric averages:
  $$U^* = \{u \in U_{\text{eval}} : \sum_{i \in \mathcal{T}_u} \text{rel}_{u, i} \ge 1\}$$
- The exact number of excluded users ($|U_{\text{eval}}| - |U^*|$) is explicitly counted, logged, and reported in the evaluation tables.

---

### 4.3 Catalog & Distribution Metrics

#### 7. Catalog Coverage@K
Fraction of unique catalog items recommended to at least one user:
$$\text{Coverage@K} = \frac{|\bigcup_{u \in U_{\text{eval}}} \text{Rec}_K(u)|}{|I|}$$

#### 8. Novelty@K
Expected self-information of recommended items (higher value implies less obvious/popular recommendations):
$$\text{Novelty@K} = \frac{1}{|U_{\text{eval}}| \cdot K} \sum_{u \in U_{\text{eval}}} \sum_{i \in \text{Rec}_K(u)} -\log_2 P(i)$$
where $P(i) = \frac{|\{u \in U_{\text{train}} : i \in \text{Seen}_u\}|}{|U_{\text{train}}|}$.

---

## 5. Model Selection Decision Rule
- **Primary Metric:** **NDCG@10** on the **validation partition**.
- **Secondary Metric:** **RMSE** on the validation partition (used as a tie-breaker or balance metric).
- Model selection is finalized prior to running the test partition.
- **Final Evaluation Execution:** Refit the selected configurations on `train + validation`, evaluate once on `test`, and record outputs with git commit, configuration dictionary, seed (`42`), and execution timestamp.

---

## 6. Cold-Start Experiment Protocol
To rigorously evaluate model performance when user preference histories are sparse:
1. Select a stratified evaluation sample of users from the validation/test partition.
2. Truncate their training interactions artificially to $M \in \{1, 3, 5, 10\}$ observed ratings.
3. Measure NDCG@10 and Recall@10 across each truncation level.
4. Compare performance across all 4 models (Popularity Baseline, User-KNN, Item-KNN, SVD).
5. Tabulate cold-start results separately from warm-start results in the evaluation report.
