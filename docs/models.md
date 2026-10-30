# Collaborative Filtering Models Specification & Equations

This document details the mathematical formulation, parameter configurations, fallback chains, and edge-case behaviors for all four models implemented in Phase 2.

---

## 1. Unified Interface Contract
All models in `src/recsys/models/` inherit from `BaseRecommender` and provide:
- `fit(train_ratings: pd.DataFrame) -> self`:
  Estimates all parameters, entity means, similarities, and latent matrices strictly from `train_ratings`.
- `predict(user_id: int, item_id: int) -> float`:
  Estimates $\hat{r}_{u, i}$ bounded in $[1.0, 5.0]$. If target user or item lacks sufficient data, executes the deterministic fallback chain.
- `recommend(user_id: int, n: int = 10, exclude_seen: bool = True) -> list[tuple[int, float]]`:
  Scores and ranks candidate items. Excludes previously rated items by default and breaks score ties deterministically by `item_id`.

---

## 2. Model 1: Popularity Baseline (`PopularityBaseline`)

### 2.1 Formulation
To avoid small-sample distortion (e.g. an obscure movie rated 5.0 by 1 user outranking a classic rated 4.6 by 500 users), we use a damped / Bayesian mean with a global prior:
$$\hat{r}_i = \frac{\sum_{u \in U_i} r_{ui} + m \cdot \mu}{|U_i| + m}$$
where:
- $|U_i|$ is the number of ratings for movie $i$ in training.
- $\mu = \frac{1}{|\Omega_{\text{train}}|} \sum_{(u, i) \in \Omega_{\text{train}}} r_{ui}$ is the global training mean rating.
- $m \ge 0$ is the damping weight (`damping`, default = 10.0).

### 2.2 Edge Cases & Fallback
- If item $i$ has fewer than $v_{\text{min}}$ ratings (`min_ratings`, default = 5) or is unobserved in training:
  $$\hat{r}_i = \mu$$
- Output is clipped to $[1.0, 5.0]$.

---

## 3. Model 2: User-Based Collaborative Filtering (`UserKNNRecommender`)

### 3.1 Formulation
1. **User Centering:** Compute each user's mean training rating:
   $$\mu_u = \frac{1}{|I_u|} \sum_{i \in I_u} r_{ui}$$
2. **Pearson Similarity on Co-rated Items:**
   For users $u$ and $v$ with co-rated items $I_{uv} = I_u \cap I_v$:
   $$s(u, v) = \begin{cases} \frac{\sum_{i \in I_{uv}} (r_{ui} - \mu_u)(r_{vi} - \mu_v)}{\sqrt{\sum_{i \in I_{uv}} (r_{ui} - \mu_u)^2} \cdot \sqrt{\sum_{i \in I_{uv}} (r_{vi} - \mu_v)^2}} & \text{if } |I_{uv}| \ge \text{min\_overlap} \\ 0 & \text{otherwise} \end{cases}$$
3. **Neighborhood Aggregation:**
   Identify all users $v \ne u$ who rated item $i$ ($i \in I_v$) with positive correlation $s(u, v) > 0$. Select the top-$k$ neighbours $N_k(u; i)$.
   $$\hat{r}(u, i) = \mu_u + \frac{\sum_{v \in N_k(u; i)} s(u, v) (r_{vi} - \mu_v)}{\sum_{v \in N_k(u; i)} |s(u, v)|}$$

### 3.2 Edge Cases & Fallback
- If $u$ or $i$ is unknown, or if $N_k(u; i) = \emptyset$, or if $\sum |s(u, v)| \le 10^{-9}$:
  Execute fallback chain: $\mu_i \to \mu_u \to \mu$.
- Output is clipped to $[1.0, 5.0]$.

---

## 4. Model 3: Item-Based Collaborative Filtering (`ItemKNNRecommender`)

### 4.1 Formulation
1. **Adjusted Cosine Similarity:**
   Unlike standard cosine, adjusted cosine subtracts the user mean $\mu_u$ to account for differences in user rating scales. For items $i$ and $j$ co-rated by users $U_{ij} = U_i \cap U_j$:
   $$s(i, j) = \begin{cases} \frac{\sum_{u \in U_{ij}} (r_{ui} - \mu_u)(r_{uj} - \mu_u)}{\sqrt{\sum_{u \in U_{ij}} (r_{ui} - \mu_u)^2} \cdot \sqrt{\sum_{u \in U_{ij}} (r_{uj} - \mu_u)^2}} & \text{if } |U_{ij}| \ge \text{min\_overlap} \\ 0 & \text{otherwise} \end{cases}$$
2. **Neighborhood Aggregation:**
   Identify all items $j \ne i$ rated by user $u$ ($j \in I_u$) with positive similarity $s(i, j) > 0$. Select the top-$k$ neighbours $N_k(i; u)$.
   $$\hat{r}(u, i) = \frac{\sum_{j \in N_k(i; u)} s(i, j) r_{uj}}{\sum_{j \in N_k(i; u)} |s(i, j)|}$$

### 4.2 Edge Cases & Fallback
- If $u$ or $i$ is unknown, or if $N_k(i; u) = \emptyset$, or if $\sum |s(i, j)| \le 10^{-9}$:
  Execute fallback chain: $\mu_i \to \mu_u \to \mu$.
- Output is clipped to $[1.0, 5.0]$.

---

## 5. Model 4: Truncated SVD Benchmark (`TruncatedSVDRecommender`)

### 5.1 Formulation
1. **Centering Observed Ratings:**
   To prevent turning a 93.7% sparse matrix into an unmanageable dense matrix, we center only observed ratings:
   $$\tilde{r}_{ui} = r_{ui} - \mu_u \quad \forall (u, i) \in \Omega_{\text{train}}$$
   Unobserved matrix entries remain $0$ in the SciPy CSR sparse matrix $\tilde{R} \in \mathbb{R}^{|U| \times |I|}$.
2. **Truncated SVD Decomposition:**
   Using `scipy.sparse.linalg.svds`:
   $$\tilde{R} \approx U_k \Sigma_k V_k^T$$
   where $k = \text{n\_factors}$ (default = 20), $U_k \in \mathbb{R}^{|U| \times k}$, $\Sigma_k \in \mathbb{R}^{k}$, $V_k^T \in \mathbb{R}^{k \times |I|}$.
3. **Rating Reconstruction:**
   $$\hat{r}(u, i) = \mu_u + (U_k \Sigma_k V_k^T)_{ui} = \mu_u + \sum_{f=1}^k U_k[u, f] \cdot \Sigma_k[f] \cdot V_k^T[f, i]$$

### 5.2 Edge Cases & Fallback
- If $u$ or $i$ is unknown:
  Execute fallback chain: $\mu_i \to \mu_u \to \mu$.
- Output is clipped to $[1.0, 5.0]$.

---

## 6. Deterministic Hand-Computed Proof Matrix

Consider a toy matrix of 4 users ($u_1, u_2, u_3, u_4$) and 5 items ($i_1, i_2, i_3, i_4, i_5$):

| User | $i_1$ | $i_2$ | $i_3$ | $i_4$ | $i_5$ | User Mean $\mu_u$ |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| $u_1$ | 5.0 | 3.0 | 4.0 | 4.0 | ? | **4.00** |
| $u_2$ | 3.0 | 1.0 | 2.0 | 3.0 | 3.0 | **2.40** |
| $u_3$ | 4.0 | 3.0 | ? | 3.0 | ? | **3.33** ($10/3$) |
| $u_4$ | 3.0 | 3.0 | 1.0 | 5.0 | 4.0 | **3.20** |
| **Item Mean $\mu_i$** | **3.75** | **2.50** | **2.33** | **3.75** | **3.50** | Global Mean $\mu = 3.1765$ ($54/17$) |

### User-User Similarity $s(u_1, u_2)$:
Co-rated items: $\{i_1, i_2, i_3, i_4\}$
- $u_1$ deviations: $[5-4, 3-4, 4-4, 4-4] = [1.0, -1.0, 0.0, 0.0]$
- $u_2$ deviations: $[3-2.4, 1-2.4, 2-2.4, 3-2.4] = [0.6, -1.4, -0.4, 0.6]$
- Numerator: $1.0(0.6) + (-1.0)(-1.4) + 0(0) + 0(0) = 0.6 + 1.4 = 2.0$
- Denominator: $\sqrt{1^2 + (-1)^2} \cdot \sqrt{0.6^2 + (-1.4)^2 + (-0.4)^2 + 0.6^2} = \sqrt{2} \cdot \sqrt{2.84} = \sqrt{5.68} \approx 2.383275$
- **$s(u_1, u_2) = \frac{2.0}{\sqrt{5.68}} \approx 0.83918147$**

### UserKNN Prediction $\hat{r}(u_1, i_5)$:
Raters of $i_5$: $u_2$ (rating = 3.0) and $u_4$ (rating = 4.0).
- $s(u_1, u_2) \approx 0.839181 > 0$
- $s(u_1, u_4)$:
  $u_1$ dev: $[1, -1, 0, 0]$; $u_4$ dev: $[-0.2, -0.2, -2.2, 1.8]$.
  $\text{Num} = 1(-0.2) + (-1)(-0.2) + 0 + 0 = 0.0 \implies s(u_1, u_4) = 0.0$ (not positive).
- Only $u_2$ qualifies as a positive neighbour!
- Prediction: $\hat{r}(u_1, i_5) = \mu_1 + \frac{s(u_1, u_2)(r_{2, 5} - \mu_2)}{s(u_1, u_2)} = \mu_1 + (r_{2, 5} - \mu_2) = 4.0 + (3.0 - 2.4) = \mathbf{4.600000}$

### Item-Item Adjusted Cosine Similarity $s(i_2, i_3)$:
Co-raters: $\{u_1, u_2, u_4\}$
- $u_1$ dev: $i_2 - \mu_1 = 3 - 4 = -1.0$; $i_3 - \mu_1 = 4 - 4 = 0.0$
- $u_2$ dev: $i_2 - \mu_2 = 1 - 2.4 = -1.4$; $i_3 - \mu_2 = 2 - 2.4 = -0.4$
- $u_4$ dev: $i_2 - \mu_4 = 3 - 3.2 = -0.2$; $i_3 - \mu_4 = 1 - 3.2 = -2.2$
- Numerator: $(-1)(0) + (-1.4)(-0.4) + (-0.2)(-2.2) = 0 + 0.56 + 0.44 = 1.0$
- Denominator: $\sqrt{(-1)^2 + (-1.4)^2 + (-0.2)^2} \cdot \sqrt{0^2 + (-0.4)^2 + (-2.2)^2} = \sqrt{3.0} \cdot \sqrt{5.0} = \sqrt{15.0} \approx 3.872983$
- **$s(i_2, i_3) = \frac{1.0}{\sqrt{15.0}} \approx 0.25819889$**
