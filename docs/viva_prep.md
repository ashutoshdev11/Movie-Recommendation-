# Viva Defense Preparation Guide: Collaborative Filtering Recommendation System

## 1. Project Overview & 3-Minute Elevator Pitch

### The Core Problem
Most recommendation tutorials use naive random train/test splits, evaluate on rating estimation error (RMSE) rather than top-$N$ ranking utility (NDCG), and leak future information into similarity matrices. This project implements an academic-grade, leakage-free collaborative filtering recommendation system on the MovieLens 100K benchmark (`ml-100k`) comparing four canonical architectures:
1. **Non-personalized Baseline:** Bayesian Damped Popularity Mean ($m=50.0$)
2. **User Memory-Based CF:** User-User Pearson Correlation with User Mean-Centering ($k=10$)
3. **Item Memory-Based CF:** Item-Item Adjusted Cosine Similarity with User Mean-Centering ($k=10$)
4. **Latent Factor Matrix Factorization:** Truncated SVD on Mean-Centered Sparse CSR Matrix ($n_{\text{factors}}=20$)

### Key Empirical Finding
**Rating prediction accuracy (RMSE) and top-$N$ ranking utility (NDCG@10) completely diverged.**
- User-based kNN achieved the best RMSE (**1.0184**), yet produced almost zero ranking utility (NDCG@10 = **0.0066**).
- Truncated SVD dominated top-$N$ recommendation utility (NDCG@10 = **0.1198**), despite higher RMSE (**1.1028**).
- *Viva Takeaway:* In real-world recommendation interfaces, users care about receiving relevant movies at ranks 1–10, not about whether an unconsumed 2-star movie was predicted as 2.1 or 2.6 stars.

---

## 2. 16 Likely Viva Questions & Model Answers

### Q1: Why must unrated movies be treated as missing values rather than zero ratings?
**Model Answer:**
In a 5-star rating system, a rating of 1 indicates active dislike, while a missing entry simply means the user has not encountered or chosen to watch the movie. If missing entries are filled with zeros:
1. An unobserved movie is treated as far worse than a movie the user explicitly rated 1 star.
2. The user's average rating $\mu_u$ drops from $\sim 3.6$ to $\sim 0.1$, destroying mean-centering and similarity normalization.
3. The sparse matrix ($93.70\%$ sparsity) would turn into a dense matrix of 1.58 million entries, multiplying memory footprint by $16\times$ without conveying genuine negative feedback.
*Conclusion:* Unrated items are unobserved, and similarities/losses must be computed strictly over co-rated observed pairs $\Omega_u \cap \Omega_v$.

---

### Q2: Why did you use a per-user chronological 60/20/20 split instead of a random interaction split?
**Model Answer:**
A random interaction split causes severe **temporal data leakage**. In real life, recommendation algorithms must predict future consumption using past history.
- If we split randomly, a user rating *The Matrix* in 1999 could be in the training set, while their rating of *Star Wars* in 1997 is in the test set. The model would be predicting the past using future preferences.
- A global timestamp cutoff causes **user cold-start distortion**: early historical users have no test data, and newly joined users have no training data.
- **Our Solution:** A per-user chronological split sorts each user's ratings by timestamp $t$:
  $$\max(t_{\text{train}, u}) \le \min(t_{\text{val}, u}) \le \max(t_{\text{val}, u}) \le \min(t_{\text{test}, u})$$
  This guarantees that every user has at least 12 training ratings ($60\%$ of $n_u \ge 20$) and accurately simulates real-world future consumption forecasting.

---

### Q3: Why is Adjusted Cosine similarity preferred over standard Cosine or Pearson for Item-Item CF?
**Model Answer:**
Standard cosine similarity treats raw ratings as absolute coordinates:
$$\cos(i, j) = \frac{r_i \cdot r_j}{\|r_i\|_2 \|r_j\|_2}$$
This fails because different users have different rating scales—a "harsh" user might give a 4 to an extraordinary movie, while a "lenient" user gives 4s to mediocre movies.
- Standard Pearson correlation subtracts the *item's* average rating, which does not account for user scale bias.
- **Adjusted Cosine** subtracts the **user's rating mean** $\mu_u$ across co-raters $U_{ij}$:
  $$s(i, j) = \frac{\sum_{u \in U_{ij}} (r_{ui} - \mu_u)(r_{uj} - \mu_u)}{\sqrt{\sum_{u \in U_{ij}} (r_{ui} - \mu_u)^2} \sqrt{\sum_{u \in U_{ij}} (r_{uj} - \mu_u)^2}}$$
  This transforms ratings into positive or negative deviations relative to each user's personal baseline before computing angle alignment between items.

---

### Q4: Why did RMSE and NDCG@10 diverge in your final evaluation?
**Model Answer:**
RMSE and NDCG measure fundamentally different operational objectives:
1. **RMSE (Global Residual Magnitude):**
   $$\text{RMSE} = \sqrt{\frac{1}{|\mathcal{T}|} \sum (r_{ui} - \hat{r}_{ui})^2}$$
   RMSE is symmetric and evaluates rating accuracy across items the user actually watched. User-based kNN centers predictions on $\mu_u$, which accurately captures the user's overall score calibration on observed items.
2. **NDCG@10 (Top-Rank Ordering Discount):**
   $$\text{NDCG@10} = \frac{\text{DCG@10}}{\text{IDCG@10}}, \quad \text{DCG@10} = \sum_{m=1}^{10} \frac{2^{\text{rel}_m} - 1}{\log_2(m + 1)}$$
   NDCG evaluates whether the top-10 retrieved items from $1,600$ unseen candidates are actually relevant ($r \ge 4.0$). Under $93.7\%$ sparsity, UserKNN finds zero positive neighbors for most candidate items, collapsing into flat fallback scores. Truncated SVD projects candidates into dense 20D latent space, producing fine-grained relative preference orderings.

---

### Q5: What is the cold-start problem, and how does your architecture solve it?
**Model Answer:**
The cold-start problem occurs when a new user or item enters the system with zero or few interactions, making similarity computation impossible.
Our architecture implements an empirically verified two-tier defense:
1. **$M < 3$ Ratings (Cold-Start Safety Net):**
   Our cold-start experiment (`results/cold_start_experiment.csv`) proved that at $M=1$, UserKNN yields NDCG@10 = $0.0000$, while the Bayesian Popularity Baseline achieves NDCG@10 = $0.0592$. When $< 3$ ratings are provided, the system transparently falls back to damped popularity:
   $$\hat{r}_i = \frac{\sum r_{ui} + m \cdot \mu}{|U_i| + m} \quad (m=50.0)$$
2. **$M \ge 3$ Ratings (Online SVD Folding-In):**
   Once the user provides 3 ratings, SVD surpasses popularity ($0.0601$ vs $0.0601$ at $M=3$, rising to $0.0694$ at $M=5$). The user's ratings are folded into latent space via right singular vectors in $< 3$ ms without retraining.

---

### Q6: How did you implement Truncated SVD without dense matrix memory bloat?
**Model Answer:**
In full matrix SVD, subtracting user mean $\mu_u$ across all unrated items turns a sparse matrix into a dense matrix of $943 \times 1,682 = 1.58 \times 10^6$ floating point numbers.
- **Our Strategy:** We subtract user means **only from observed entries**:
  $$\tilde{r}_{ui} = r_{ui} - \mu_u \quad \forall (u, i) \in \Omega_{\text{train}}$$
  Unobserved coordinates remain numerical zeros in the SciPy CSR matrix.
- In zero-centered space, zero represents the user's average rating (neutral expectation).
- We compute truncated singular value decomposition via `scipy.sparse.linalg.svds`:
  $$\tilde{R} \approx U_k \Sigma_k V_k^T$$
- Reconstruction for prediction:
  $$\hat{r}_{ui} = \mu_u + (U_k \Sigma_k V_k^T)_{ui}$$
  clipped to $[1.0, 5.0]$. Peak memory during SVD fit is only **12.75 MB**.

---

### Q7: How does online SVD profile folding-in work mathematically in real time?
**Model Answer:**
Folding-in projects an ad-hoc rating vector $r_{\text{new}}$ into the existing SVD latent space without modifying fitted matrices or re-running SVD decomposition:
1. Compute profile mean: $\mu_{\text{new}} = \frac{1}{|I_{\text{new}}|} \sum_{i \in I_{\text{new}}} r_i$.
2. Construct sparse mean-centered row vector $x \in \mathbb{R}^{1 \times |I|}$ where $x_i = r_i - \mu_{\text{new}}$ for $i \in I_{\text{new}}$ and $0$ otherwise.
3. Project $x$ onto right singular vectors $V \in \mathbb{R}^{|I| \times k}$ (columns of $V$ are item latent factors):
   $$p_{\text{new}} = x V \in \mathbb{R}^{1 \times k}$$
4. Reconstruct predicted residuals across all catalog items:
   $$\Delta = p_{\text{new}} V^T = (x V) V^T \in \mathbb{R}^{1 \times |I|}$$
5. Final score: $\hat{r}_{\text{new}} = \text{clip}(\mu_{\text{new}} + \Delta, 1.0, 5.0)$.
*Equivalence:* Verified against batch SVD to $< 10^{-14}$ precision with measured execution latency of **2.86 ms**.

---

### Q8: What is Discounted Cumulative Gain (DCG), and why is logarithmic rank discounting appropriate?
**Model Answer:**
DCG evaluates a recommendation list based on two principles:
1. Highly relevant items are desirable.
2. Relevant items appearing at lower ranks (e.g. rank 10) are less valuable because users rarely scroll past the top 3–5 items.
The logarithmic discount $\frac{1}{\log_2(m + 1)}$ models user gaze and click attenuation:
- Rank 1: discount = $\frac{1}{\log_2(2)} = 1.0$ (full credit).
- Rank 2: discount = $\frac{1}{\log_2(3)} \approx 0.631$.
- Rank 10: discount = $\frac{1}{\log_2(11)} \approx 0.289$.
Linear discounting drops too steeply, while power-law discounts over-penalize ranks 5–10. Logarithmic discounting is the international standard in information retrieval and RecSys.

---

### Q9: How did you handle evaluation users who have no relevant test items ($r \ge 4.0$)?
**Model Answer:**
If a user in the test set never rated any movie $\ge 4.0$, their set of relevant items is empty ($|\text{Rel}_u| = 0$).
- Ideal DCG (IDCG@K) is $0.0$.
- Computing $\text{NDCG@K} = \frac{\text{DCG@K}}{\text{IDCG@K}} = \frac{0}{0}$ is mathematically undefined.
- **Protocol Rule:** Following standard evaluation governance (Cremonesi et al., 2010), such users are **excluded from ranking macro-averages** ($U^* = \{u \in U_{\text{test}} : |\text{Rel}_u| \ge 1\}$) and explicitly counted.
- In MovieLens 100K test set: 943 total users $\to$ 918 evaluated, **25 excluded**.

---

### Q10: Why did you gate kNN similarities to strictly positive values ($s > 0$)?
**Model Answer:**
In Pearson correlation and adjusted cosine, negative similarity ($s < 0$) indicates inverted preference.
- However, in collaborative filtering, knowing that user $v$ disliked a movie does not reliably imply that user $u$ will love it. Two users can disagree on one movie while having completely different tastes on everything else.
- Without gating, negative weights in the standard neighborhood aggregation:
  $$\hat{r}_{ui} = \mu_u + \frac{\sum s_{uv}(r_{vi} - \mu_v)}{\sum |s_{uv}|}$$
  can pull predictions in unstable, counter-intuitive directions and create cancelation in the denominator.
- Gating to $s > 0$ restricts neighborhoods to true peers and triggers deterministic fallbacks when no positive peers exist.

---

### Q11: What is the difference between Catalog Coverage and Novelty?
**Model Answer:**
- **Catalog Coverage@K:** The proportion of total catalog movies recommended to at least one user:
  $$\text{Coverage@K} = \frac{|\bigcup_{u} \text{Rec}_K(u)|}{|I|}$$
  ItemKNN achieved **76.34%**, while Popularity achieved only **3.80%**. Coverage reveals whether a system explores the long tail.
- **Novelty@K:** The average self-information (unexpectedness) of recommended items:
  $$\text{Novelty@K} = \frac{1}{|U| \cdot K} \sum_{u} \sum_{i \in \text{Rec}_K(u)} -\log_2 P(i)$$
  where $P(i)$ is the item's historical popularity. Recommending *Star Wars* has low novelty ($\sim 3.4$ bits); recommending an obscure foreign drama has high novelty ($\sim 9.0$ bits).

---

### Q12: Why does the Popularity Baseline achieve high NDCG@10 (0.0682) yet low Coverage (3.80%)?
**Model Answer:**
This is the classic **Popularity Bias** in offline collaborative filtering.
- In MovieLens 100K, the top 5% of movies account for over 35% of all rating interactions.
- In test sets, users frequently rated blockbuster movies (e.g. *Fargo*, *Star Wars*, *Toy Story*).
- Because Popularity Baseline repeatedly recommends these exact blockbusters to every user, it achieves many test hits, scoring high NDCG@10 (0.0682).
- However, it recommends only $\sim 60$ distinct movies across all 943 users, resulting in terrible catalog coverage (**3.80%**) and boring, non-personalized recommendations.

---

### Q13: What was the ItemKNN Inverted Index optimization, and how did you verify mathematical equivalence?
**Model Answer:**
In ItemKNN, finding top-10 recommendations for a user requires scoring up to $1,600$ unrated candidate items.
- Naive computation evaluates adjusted cosine between candidate $j$ and all user rated items $I_u$, requiring $\mathcal{O}(|\mathcal{C}_u| \cdot |I_u|)$ similarity checks.
- **Mathematical Insight:** If candidate $j$ shares **zero co-raters** with user items $I_u$, the adjusted cosine numerator is identically zero. Its similarity is 0.0, and it will receive the fallback prediction.
- **Optimization:** We construct an inverted rater index:
  $$\text{Candidates with co-raters} = \bigcup_{i \in I_u} \bigcup_{v \in \text{Raters}(i)} \text{ItemsRated}(v)$$
  Candidate items outside this set bypass similarity loops directly.
- **Verification:** Unit test `test_item_knn_optimization_equivalence_and_edge_cases` verified 100% identical top-10 rankings and scores to $< 10^{-9}$ tolerance.

---

### Q14: What are the primary limitations of offline recommendation evaluation?
**Model Answer:**
1. **Missing-Not-At-Random (MNAR) Selection Bias:** Users select which movies to watch and rate based on prior interest and marketing. True negative feedback on unconsumed movies is unobserved.
2. **Popularity Bias:** Offline metrics reward recommending popular movies that users were likely to watch anyway, failing to measure serendipity or discovery.
3. **Absence of User Interaction / Trust:** Offline metrics cannot measure explanation transparency, UI satisfaction, or latency perception, which is why we built the Streamlit application for interactive evaluation.

---

### Q15: How did you ensure zero data leakage during hyperparameter tuning?
**Model Answer:**
We enforced strict architectural and experimental isolation:
1. **Validation-Only Tuning:** All 32 grid-search configurations in `results/validation_tuning.csv` were fitted on `train` and evaluated on `val`. Test data was never loaded during tuning.
2. **Pre-Committed Selection Rule:** We committed to Validation NDCG@10 as the decision metric before inspecting test data. Truncated SVD ($n=20$) was selected solely on validation performance ($0.1138$).
3. **Single Test Run Execution:** The test evaluation script was gated behind `--final` and executed exactly once on `train + val` refit, logged to `results/final_run.log`.

---

### Q16: How would this architecture scale from 100K ratings to 20 Million ratings (MovieLens 20M)?
**Model Answer:**
1. **ItemKNN & UserKNN Bottlenecks:** kNN similarity matrices scale as $\mathcal{O}(|I|^2)$ or $\mathcal{O}(|U|^2)$. For 20M ratings (138,000 users, 27,000 items), computing pairwise Pearson/cosine becomes intractable in memory and CPU time.
2. **SVD / Matrix Factorization Scalability:**
   - Truncated SVD on sparse CSR scales as $\mathcal{O}(k \cdot |\Omega|)$, which comfortably handles 20M ratings.
   - For industrial scale ($10^7\text{--}10^9$ interactions), we would transition from SVD to **Alternating Least Squares (ALS)** with implicit feedback (Hu, Koren, Volinsky) or two-tower neural candidate retrieval (YouTube DNN) paired with approximate nearest neighbor vector search (FAISS / ScaNN).
