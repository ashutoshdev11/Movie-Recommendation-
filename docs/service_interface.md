# Recommender Service Interface Documentation

## 1. Overview
The `RecommenderService` class located in `src/recsys/service.py` provides the production-grade application and serving layer for the collaborative filtering recommendation engine. It bridges raw data, fitted model artifacts, real-time folding-in inference, cold-start handling, and user interface workflows.

---

## 2. Public Service Contract

### 2.1 Initialization
```python
service = RecommenderService(
    data_dir: Optional[str] = None,
    artifacts_dir: Optional[str] = "results/artifacts",
    min_ratings_for_personalization: int = 3,
    auto_fit: bool = True,
)
```
- **`data_dir`:** Path to raw MovieLens 100K data (`u.data`, `u.item`). Defaults to `data/raw/ml-100k`.
- **`artifacts_dir`:** Directory to load or persist project-produced binary artifacts (`svd_artifacts.npz`, `popularity_artifacts.json`).
- **`min_ratings_for_personalization`:** Threshold number of user ratings required to trigger personalized latent factor folding-in ($N_{\text{min}} = 3$). Profiles with $< 3$ ratings fall back transparently to the Bayesian Popularity Baseline.
- **`auto_fit`:** Boolean flag to fit or load artifacts upon instantiation.

---

### 2.2 Movie Catalog & Search Methods

#### `search_movies(query: str, limit: int = 10) -> List[Dict]`
Performs case-insensitive substring search against all movie titles in the catalog.
- **Parameters:**
  - `query` (str): Search term (e.g., `"Star Wars"`, `"Toy Story"`).
  - `limit` (int): Maximum number of results to return (default 10).
- **Return Format:**
  List of movie metadata dictionaries ordered descending by training popularity (rating count):
  ```python
  [
      {
          "item_id": 1,
          "title": "Toy Story (1995)",
          "year": 1995,
          "genres": ["Animation", "Children's", "Comedy"],
          "imdb_url": "http://...",
          "avg_rating": 3.87,
          "rating_count": 452,
      },
      ...
  ]
  ```

#### `get_movie_info(item_id: int) -> Dict`
Fetches complete metadata for a specific movie ID.
- **Exceptions Raised:** `ValueError` if `item_id` does not exist in the catalog.

---

### 2.3 Recommendation Methods

#### `recommend_for_user(user_id: int, n: int = 10, filter_genres: Optional[List[str]] = None) -> List[Dict]`
Generates top-$n$ recommendations for a historical training user using the champion Truncated SVD model.
- **Parameters:**
  - `user_id` (int): User ID present in training data ($1 \le \text{user\_id} \le 943$).
  - `n` (int): Number of recommendations to retrieve ($n > 0$).
  - `filter_genres` (list[str], optional): Restricts recommendations to items matching any of the specified genre strings.
- **Exceptions Raised:**
  - `ValueError`: If `user_id` is unknown or not an integer.
  - `ValueError`: If $n \le 0$.
- **Return Format:**
  ```python
  [
      {
          "item_id": 100,
          "title": "Fargo (1996)",
          "year": 1996,
          "genres": ["Crime", "Drama", "Thriller"],
          "predicted_rating": 4.68,
          "avg_rating": 4.16,
          "rating_count": 469,
          "explanation": "Recommended because you rated 'Lone Star (1996)' (similarity: 0.53).",
          "is_cold_start": False,
          "strategy": "svd_personalized",
      },
      ...
  ]
  ```

#### `recommend_for_profile(ratings: Dict[int, float], n: int = 10, filter_genres: Optional[List[str]] = None) -> List[Dict]`
Generates top-$n$ recommendations for an ad-hoc or newly registered user profile.
- **Parameters:**
  - `ratings` (dict[int, float]): Dictionary mapping `item_id -> rating` (values in $[1.0, 5.0]$).
  - `n` (int): Number of recommendations to retrieve ($n > 0$).
  - `filter_genres` (list[str], optional): Restricts recommendations by genre.
- **Input Validation:**
  - Empty profile (`{}`) raises `ValueError("User profile cannot be empty.")`.
  - Unknown movie ID raises `ValueError("Unknown movie ID in profile: ...")`.
  - Rating outside $[1.0, 5.0]$ raises `ValueError("Ratings must be between 1.0 and 5.0.")`.
  - Non-positive $n$ raises `ValueError("n must be a positive integer.")`.
- **Cold-Start Logic:**
  - If `len(ratings) < min_ratings_for_personalization`: Returns Bayesian damped Popularity recommendations excluding profile movies. Flagged with `is_cold_start=True` and labeled `strategy="popularity_cold_start"`.
  - If `len(ratings) >= min_ratings_for_personalization`: Folds user profile into latent SVD space using item right singular vectors $V$. Labeled `strategy="svd_personalized"`.

---

### 2.4 Similarity Method

#### `similar_movies(item_id: int, n: int = 10) -> List[Dict]`
Retrieves top-$n$ most similar movies to `item_id` using cosine similarity across normalized 20-dimensional SVD item latent factor vectors:
$$\text{sim}(i, j) = \frac{v_i \cdot v_j}{\|v_i\|_2 \|v_j\|_2}$$
- **Exceptions Raised:** `ValueError` if `item_id` not found or $n \le 0$.
- **Return Format:**
  ```python
  [
      {
          "item_id": 588,
          "title": "Beauty and the Beast (1991)",
          "year": 1991,
          "genres": ["Animation", "Children's", "Musical"],
          "similarity": 0.7068,
          "avg_rating": 3.79,
          "rating_count": 202,
      },
      ...
  ]
  ```

---

### 2.5 Artifact Persistence

#### `save_artifacts(directory: str) -> None`
Serializes project-produced binary models to disk:
- `svd_artifacts.npz`: $U$, $\Sigma$, $V^T$, item/user index maps, and mean vectors.
- `popularity_artifacts.json`: Damped item scores and global priors.

#### `load_artifacts(directory: str) -> None`
Restores models and metadata from project-produced artifacts without recomputing SVD matrix decomposition.

---

## 3. Mathematical Foundations of Online Folding-In

When an interactive user provides rating vector $r_{\text{new}}$ over observed subset $I_{\text{new}}$:
1. User mean is computed: $\mu_{\text{new}} = \frac{1}{|I_{\text{new}}|} \sum_{i \in I_{\text{new}}} r_{\text{new}, i}$.
2. Centered rating row vector $x \in \mathbb{R}^{1 \times |I|}$ is constructed with $x_i = r_{\text{new}, i} - \mu_{\text{new}}$ for $i \in I_{\text{new}}$, and $0$ otherwise.
3. User latent factor projection: $p_{\text{new}} = x V \in \mathbb{R}^{1 \times k}$ where $V = V_k \in \mathbb{R}^{|I| \times k}$ are the right singular vectors of the centered training matrix.
4. Full catalog reconstruction: $\Delta_{\text{new}} = p_{\text{new}} V^T = (x V) V^T$.
5. Final bounded prediction:
   $$\hat{r}_{\text{new}, j} = \text{clip}(\mu_{\text{new}} + \Delta_{\text{new}, j}, 1.0, 5.0)$$
   This projection guarantees exact mathematical continuity with the batch SVD model ($< 10^{-14}$ error) in real time ($< 2$ ms).
