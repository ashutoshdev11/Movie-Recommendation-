# Comprehensive Viva & Technical Defense Guide — MovieRec Version 2

This document provides a thorough preparation reference for viva voce, technical interviews, and project defense panels covering MovieRec Version 2.

---

## 1. Project Overview & Motivation

### What is MovieRec Version 2?
MovieRec Version 2 is an end-to-end, commercial-grade movie recommendation and interactive 3D discovery platform. It transitions from the Version 1 Streamlit prototype into a modern, decoupled web architecture comprising:
1. **Frontend:** React 18, TypeScript, Three.js WebGL, and Tailwind CSS in `v2/frontend/`.
2. **Backend:** FastAPI, SQLAlchemy 2.0, Argon2id, and JWT cookie authentication in `v2/backend/`.
3. **Machine Learning:** Truncated SVD matrix factorization ($k=30$) and Bayesian Damped Popularity trained on **MovieLens 1M** (1,000,209 ratings).

### Why was Version 2 built instead of just modifying Version 1?
Version 1 was an audited, frozen research baseline using MovieLens 100K and Streamlit. Version 2 was created in a separate directory (`v2/`) to:
- Scale data volume tenfold to **MovieLens 1M** (~1 million ratings, 3,883 movies).
- Enable real user authentication with database persistence and data isolation.
- Build an original 3D holographic user experience impossible within Streamlit's execution model.
- Strictly preserve Version 1's audited integrity and test suite without a single byte modified.

---

## 2. Machine Learning Deep Dive

### Q1: Explain the mathematical intuition behind Truncated SVD in recommendation systems.
**Answer:**
The user-item interaction matrix $R \in \mathbb{R}^{m \times n}$ contains ratings given by $m$ users to $n$ movies. Because users rate only a tiny fraction of catalog movies, $R$ is extremely sparse.

Truncated Singular Value Decomposition factorizes the centered rating matrix $R_c = R - \mu_u$ into three lower-rank matrices:
$$R_c \approx U_k \Sigma_k V_k^T$$
where $k \ll \min(m, n)$ (in our system, $k=30$):
- $U_k \in \mathbb{R}^{m \times k}$: Represents users in a $k$-dimensional latent feature space (e.g., preference for cerebral sci-fi, fast-paced action, quirky comedy).
- $\Sigma_k \in \mathbb{R}^{k \times k}$: Diagonal matrix representing the relative importance/variance of each latent factor.
- $V_k^T \in \mathbb{R}^{k \times n}$: Represents movies in the same $k$-dimensional latent feature space.

The product reconstructs the dense matrix, predicting ratings for unseen movies:
$$\hat{r}_{u,i} = \mu_u + \sum_{f=1}^{k} U_{u,f} \cdot \sigma_f \cdot V_{i,f}$$

---

### Q2: How does the system recommend for new registered users without retraining the SVD model?
**Answer:**
Through **Online Profile Folding-In** (derived from Latent Semantic Indexing projection).
Retraining an SVD model takes minutes to hours, which is impractical for real-time web interactions. Instead:
1. When a user rates a set of movies $I_{\text{rated}}$, we form their sparse centered rating vector $r_{\text{new}} \in \mathbb{R}^n$ with mean $\mu_{\text{new}}$.
2. We project this vector directly into the precomputed item singular space $V_k$:
   $$\hat{u}_{\text{new}} = (r_{\text{new}} - \mu_{\text{new}}) V_k \Sigma_k^{-1}$$
3. We then compute predicted scores across all candidate catalog movies:
   $$\hat{r}_{\text{new}} = \mu_{\text{new}} + \hat{u}_{\text{new}} \Sigma_k V_k^T$$
This requires only matrix-vector multiplication, executing in **under 3 milliseconds** on a standard CPU.

---

### Q3: What is the Cold-Start problem and how does MovieRec V2 address it?
**Answer:**
Cold start occurs when a user has provided zero or too few ratings for the collaborative filtering algorithm to infer their latent preferences.
- **Protocol:** If a user has $< 3$ ratings, the engine routes to the **Bayesian Damped Popularity Baseline** ($m=50.0$).
- **Formula:**
  $$\text{score}_i = \frac{\sum_{u} r_{u,i} + m \cdot \mu_{\text{global}}}{N_i + m}$$
- **Shrinkage intuition:** If a movie has only one 5-star rating, $N_i=1$, its score is regularized toward the global mean ($3.58$):
  $$\frac{5.0 + 50(3.58)}{1 + 50} = \frac{184}{51} \approx 3.61$$
  Whereas a blockbuster with 2,000 ratings and an average of 4.3 retains its high score ($4.28$). This ensures new users are recommended universally acclaimed films rather than obscure single-rating anomalies.

---

### Q4: Explain the chronological train/val/test split and why random splitting causes data leakage.
**Answer:**
Movie ratings are fundamentally temporal. If we split ratings randomly (e.g. 80/20 random cross-validation), future ratings for a user leak into the training set while past ratings are placed in the test set. The model would effectively "predict the past using the future", artificially inflating NDCG and RMSE.

In MovieRec V2, we enforce a strict **Chronological 60/20/20 Partition**:
For every individual user, ratings are sorted chronologically by timestamp $t$:
$$\max(t_{\text{train}}) \le \min(t_{\text{val}}) \le \max(t_{\text{val}}) \le \min(t_{\text{test}})$$
Training uses the first 60% of interactions, validation uses the next 20%, and test uses the final 20%.

---

### Q5: Define NDCG@10, MAP@10, and RMSE. Why are ranking metrics preferred over RMSE?
**Answer:**
- **RMSE (Root Mean Squared Error):**
  $$\text{RMSE} = \sqrt{\frac{1}{|E|} \sum (r_{ui} - \hat{r}_{ui})^2}$$
  Measures rating prediction error across all items equally.
- **NDCG@10 (Normalized Discounted Cumulative Gain):**
  $$\text{DCG@10} = \sum_{k=1}^{10} \frac{2^{r_{(k)}} - 1}{\log_2(k + 1)}, \quad \text{NDCG@10} = \frac{\text{DCG@10}}{\text{IDCG@10}}$$
  Rewards the model when the most highly rated movies appear at top positions (ranks 1 to 3) with logarithmic discount penalties for lower ranks.
- **MAP@10 (Mean Average Precision):**
  Measures the precision of surfacing relevant items (ground-truth $r \ge 4.0$) in the top 10 positions.
- **Why ranking metrics matter:** A user only views the top 5 to 10 recommended cards on screen. It does not matter if a model accurately predicts whether a terrible movie is 1.2 or 1.8 stars (low RMSE); what matters is that the user's favorite movies appear at the top of their screen (high NDCG@10).

---

## 3. Software Architecture & Security Deep Dive

### Q6: Why was Argon2id chosen over bcrypt, SHA-256, or PBKDF2?
**Answer:**
- SHA-256 is a general cryptographic hash designed for maximum throughput; modern GPUs can compute billions of SHA-256 hashes per second, making brute-force cracking trivial.
- bcrypt is memory-hard but has a strict 72-byte password length limit and cannot scale its memory cost independently of CPU cost.
- **Argon2id** is the state-of-the-art winner of the Password Hashing Competition. It combines data-dependent memory access (resisting GPU/ASIC parallel cracking) with data-independent memory access (resisting cache side-channel attacks). We configure it with 64 MB of RAM cost, 3 time iterations, and 4 parallel threads.

---

### Q7: Why store JWT tokens in `HttpOnly` cookies instead of `localStorage`?
**Answer:**
- Any script running on the page (including third-party CDNs, analytics, or injected XSS attacks) can read `localStorage.getItem("token")` and exfiltrate credentials.
- When tokens are stored in an `HttpOnly` cookie, browser security policy forbids all JavaScript access to `document.cookie`. The browser automatically attaches the cookie to same-origin requests without client code ever touching the secret.
- Combined with `SameSite=Lax`, this architecture mitigates both XSS token theft and Cross-Site Request Forgery (CSRF).

---

### Q8: How is strict user data isolation enforced across endpoints?
**Answer:**
Isolation is enforced strictly at the database query layer:
```python
# Server-side ownership filtering
records = db.query(UserRating).filter(
    UserRating.user_id == current_user.id
).all()
```
User IDs are extracted directly from the verified cryptographic JWT payload (`current_user = Depends(get_current_user)`). The client cannot pass an arbitrary `user_id` query parameter to manipulate another account's data. Attempting to delete another user's rating returns `404 Not Found`.

---

### Q9: How does the 3D WebGL engine maintain 60 FPS performance without lagging UI interactions?
**Answer:**
1. **BufferGeometry Vertex Arrays:** Rather than creating individual Mesh objects for particles, Three.js uses a single `BufferGeometry` with flat `Float32Array` buffers for 1,200 particle positions and colors, rendering them in a single draw call.
2. **Pointer Parallax Smoothing:** Pointer offsets are interpolated using linear damping (`camera.position.x += (targetX - camera.position.x) * 0.05`).
3. **Reduced-Motion Support:** The canvas listens to `window.matchMedia('(prefers-reduced-motion: reduce)')`. If enabled, animation loops and particle counts are reduced.
4. **Lifecycle Disposal:** When the user navigates away, the component cancels `requestAnimationFrame`, strips event listeners, and explicitly calls `.dispose()` on geometries, materials, and renderer WebGL contexts to eliminate memory leaks.

---

## 4. Summary Table of Key Statistics for Defense

| Metric / Parameter | Value | Description |
| :--- | :--- | :--- |
| **Total MovieLens 1M Ratings** | 1,000,209 | Complete raw interaction dataset |
| **Catalog Movies** | 3,883 | Canonical indexed titles |
| **Rated Movies in Train Split** | 3,624 | Unique movies with training ratings |
| **User Count** | 6,040 | Real personas in MovieLens 1M |
| **SVD Latent Factors ($k$)** | 30 | Number of singular vectors preserved |
| **Damped Popularity Prior ($m$)** | 50.0 | Shrinkage parameter |
| **Validation NDCG@10** | 0.0989 | SVD performance (vs 0.0477 baseline) |
| **Test NDCG@10** | 0.0802 | Final unbiased evaluation |
| **Test RMSE** | 1.0657 | Star error on held-out test ratings |
| **Inference Latency** | &lt; 3 ms | Real-time SVD profile folding |
| **V2 Backend Unit Tests** | 29 / 29 Passing | Datasets, models, API, auth, isolation |
| **V2 Frontend Unit Tests** | 9 / 9 Passing | Components, cards, star rating, auth |
| **Version 1 Regression Suite** | 53 / 53 Passing | Frozen V1 tests completely intact |
| **V1 Protected File Hashes** | 9 / 9 Match (100%)| Identical SHA-256 hashes |
