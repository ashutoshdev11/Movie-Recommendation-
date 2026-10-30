# API Documentation — MovieRec Version 2 REST Services

All endpoints are hosted by FastAPI at `http://localhost:8000/api/v1`. Interactive Swagger UI is accessible at `http://localhost:8000/docs`.

---

## 1. Authentication Endpoints (`/api/v1/auth`)

### `POST /api/v1/auth/register`
Creates a new user account with Argon2id password hashing and sets a secure `HttpOnly` cookie.
- **Request Body (`application/json`):**
  ```json
  {
    "username": "cinéphile_99",
    "email": "user@example.com",
    "password": "SecurePassword123!"
  }
  ```
- **Responses:**
  - `201 Created`: Returns `TokenResponse` and sets `movierec_access_token` cookie.
  - `409 Conflict`: Username or email already registered.
  - `422 Unprocessable Entity`: Validation failure (e.g. invalid email format, short password).

### `POST /api/v1/auth/login`
Authenticates user credentials and issues a signed JWT access token in an `HttpOnly` cookie.
- **Request Body (`application/json`):**
  ```json
  {
    "username_or_email": "cinéphile_99",
    "password": "SecurePassword123!"
  }
  ```
- **Responses:**
  - `200 OK`: Returns `TokenResponse` and sets `movierec_access_token` cookie.
  - `401 Unauthorized`: Invalid credentials.

### `GET /api/v1/auth/me`
Fetches the currently authenticated user profile based on cookie or Bearer token.
- **Headers / Cookie:** `Cookie: movierec_access_token=...` or `Authorization: Bearer <token>`
- **Responses:**
  - `200 OK`: Returns `{ "id": 1, "username": "cinéphile_99", "email": "user@example.com", "created_at": "..." }`
  - `401 Unauthorized`: Session expired or missing cookie.

### `POST /api/v1/auth/logout`
Terminates the user session by clearing the `movierec_access_token` cookie.
- **Responses:**
  - `200 OK`: `{ "message": "Successfully logged out." }`

---

## 2. Movies Catalog Endpoints (`/api/v1/movies`)

### `GET /api/v1/movies`
Searches catalog with pagination and genre filtering.
- **Query Parameters:**
  - `q` (string, optional): Title search query (e.g., `Matrix`).
  - `genre` (string, optional): Filter by genre (e.g., `Sci-Fi`).
  - `page` (int, default: 1): Page number.
  - `limit` (int, default: 20, max: 100): Results per page.
- **Response `200 OK`:**
  ```json
  {
    "total": 3883,
    "page": 1,
    "limit": 20,
    "items": [
      {
        "movie_id": 2571,
        "title": "Matrix, The (1999)",
        "year": 1999,
        "genres": ["Action", "Sci-Fi", "Thriller"],
        "avg_rating": 4.31,
        "rating_count": 2590,
        "poster_url": "/api/v1/posters/2571"
      }
    ]
  }
  ```

### `GET /api/v1/movies/trending`
Returns top trending movies ranked by historical rating frequency.
- **Query Parameter:** `limit` (int, default: 12)
- **Response `200 OK`:** Array of `MovieSummary` items.

### `GET /api/v1/movies/top-rated`
Returns top critically acclaimed movies ranked by Bayesian damped average rating.
- **Query Parameter:** `limit` (int, default: 12)
- **Response `200 OK`:** Array of `MovieSummary` items.

### `GET /api/v1/movies/{movie_id}`
Retrieves full details for a specific canonical movie ID.
- **Response `200 OK`:** `MovieDetails` object with synopsis and artwork URLs.
- **Response `404 Not Found`:** Movie ID does not exist in catalog.

### `GET /api/v1/movies/{movie_id}/similar`
Computes top-N most similar movies using cosine similarity in the 30-dimensional SVD item latent space.
- **Query Parameter:** `n` (int, default: 10, max: 30)
- **Response `200 OK`:** Array of `MovieSummary` items.

---

## 3. Ratings Endpoints (`/api/v1/ratings`)

### `GET /api/v1/ratings/me`
Retrieves all ratings submitted by the authenticated user.
- **Requires Authentication:** Yes.
- **Response `200 OK`:** Array of `RatingResponse` items with movie titles and genres.

### `POST /api/v1/ratings`
Submits or updates a movie rating (1.0 to 5.0 stars). Triggers immediate SVD profile update.
- **Requires Authentication:** Yes.
- **Request Body (`application/json`):**
  ```json
  {
    "movie_id": 2571,
    "rating": 5.0
  }
  ```
- **Response `201 Created`:** Created/updated rating object.

### `DELETE /api/v1/ratings/{movie_id}`
Deletes a user's rating for a specific movie.
- **Requires Authentication:** Yes.
- **Response `200 OK`:** `{ "message": "Rating removed successfully." }`
- **Response `404 Not Found`:** If movie was not rated by current user.

---

## 4. Watchlist Endpoints (`/api/v1/watchlist`)

### `GET /api/v1/watchlist/me`
Lists all bookmarked titles for the authenticated user.
- **Requires Authentication:** Yes.
- **Response `200 OK`:** Array of `WatchlistResponse` items.

### `POST /api/v1/watchlist`
Adds a movie to the user's watchlist.
- **Requires Authentication:** Yes.
- **Request Body (`application/json`):** `{ "movie_id": 2571 }`
- **Response `201 Created`:** Created watchlist item.

### `DELETE /api/v1/watchlist/{movie_id}`
Removes a movie from the user's watchlist.
- **Requires Authentication:** Yes.
- **Response `200 OK`:** `{ "message": "Movie removed from watchlist." }`
- **Response `404 Not Found`:** Movie not found in user's watchlist.

---

## 5. Recommendation Endpoints (`/api/v1/recommendations`)

### `GET /api/v1/recommendations/me`
Generates personalized recommendations for the logged-in user.
- **Query Parameter:** `n` (int, default: 10, max: 50)
- **Requires Authentication:** Yes.
- **Routing Protocol:**
  - If user has $\ge 3$ ratings: Computes live **Truncated SVD online folding-in** ($k=30$).
  - If user has $< 3$ ratings: Falls back to **Bayesian Damped Popularity** baseline.
- **Response `200 OK`:**
  ```json
  {
    "user_id": 1,
    "strategy": "svd_personalized_folding",
    "is_cold_start": false,
    "count": 10,
    "items": [
      {
        "rank": 1,
        "movie_id": 1196,
        "title": "Star Wars: Episode V - The Empire Strikes Back (1980)",
        "year": 1980,
        "genres": ["Action", "Adventure", "Sci-Fi"],
        "predicted_rating": 4.82,
        "avg_rating": 4.29,
        "rating_count": 2990,
        "strategy": "svd_personalized_folding",
        "is_cold_start": false,
        "explanation": "Personalized recommendation: folded into 30-dimensional SVD latent space. Predicted score: 4.8 stars.",
        "poster_url": "/api/v1/posters/1196"
      }
    ]
  }
  ```

### `POST /api/v1/recommendations/anonymous`
Stateless recommendation endpoint for unauthenticated visitors (Profile Builder).
- **Request Body (`application/json`):**
  ```json
  {
    "ratings": { "260": 5.0, "1196": 5.0, "1210": 4.5 },
    "n": 10
  }
  ```
- **Response `200 OK`:** Same `RecommendationResponse` structure as above.

---

## 6. Poster Artwork Endpoints (`/api/v1/posters`)

### `GET /api/v1/posters/{movie_id}`
Fetches high-resolution poster artwork. Connects to TMDB if API key is configured, caches poster images on local disk, and falls back seamlessly to SVG generation if offline.
- **Response `200 OK`:** Redirect or direct image stream (`image/jpeg`, `image/webp`, `image/svg+xml`).

### `GET /api/v1/posters/fallback/{movie_id}`
Guaranteed offline fallback delivering a beautifully styled SVG poster with genre gradients, geometric film motifs, and title typography.
- **Response `200 OK`:** `Content-Type: image/svg+xml`.
