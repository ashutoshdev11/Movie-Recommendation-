# Security & Authentication Architecture — MovieRec Version 2

This document details the security model, cryptographic algorithms, cookie policies, and data isolation mechanisms enforced in MovieRec Version 2.

---

## 1. Cryptographic Password Hashing (Argon2id)

Passlib with **Argon2id** (the winner of the Password Hashing Competition) is used for all user credentials:
- **Algorithm:** `argon2id` (v=19, memory cost: 65,536 KiB, time cost: 3 iterations, parallelism: 4 lanes).
- **Salt:** Cryptographically secure random 128-bit salt generated per password automatically.
- **Resistance:** Highly resistant to GPU/ASIC parallel cracking and side-channel timing attacks.
- **Zero Plaintext Storage:** Plaintext passwords are never stored in memory, logged, or written to SQLite.

---

## 2. Stateless JWT & Secure Cookie Sessions

Authentication employs signed, short-lived **JSON Web Tokens (JWT)**:
- **Algorithm:** HMAC-SHA256 (`HS256`).
- **Secret Key:** Injected via environment variables (`JWT_SECRET_KEY`); defaults to a secure 256-bit string in development.
- **Payload:** Contains user ID (`sub`), issued-at (`iat`), and expiration timestamp (`exp`).
- **Token Lifetime:** 60 minutes (`ACCESS_TOKEN_EXPIRE_MINUTES = 60`).

### Browser Cookie Enforcement
To prevent Cross-Site Scripting (XSS) token theft:
- **`HttpOnly = True`:** JavaScript running in the browser cannot access or read `document.cookie`.
- **`SameSite = Lax`:** Cookies are not sent on cross-site requests, providing baseline CSRF protection for top-level navigations.
- **`Secure = True` in Production:** Cookies are transmitted exclusively over encrypted HTTPS connections.
- **No LocalStorage:** Authentication tokens are never persisted in `localStorage` or `sessionStorage`.

---

## 3. Strict User Data Isolation

The backend enforces server-side ownership checks across every user endpoint:
1. **Ownership Enforcement:**
   - Every rating lookup, creation, and deletion checks `UserRating.user_id == current_user.id`.
   - Every watchlist lookup, creation, and deletion checks `WatchlistItem.user_id == current_user.id`.
2. **Account Segregation Verification:**
   - User B attempting to view `/api/v1/ratings/me` or `/api/v1/watchlist/me` receives an empty list or only their own records.
   - User B attempting to delete User A's rating (`DELETE /api/v1/ratings/{movie_id}`) receives `404 Not Found` because the record is filtered by User B's ID.
3. **Identity Decoupling:**
   - Website user IDs (`users.id`) are completely decoupled from historical MovieLens persona IDs ($1 \dots 6,040$).

---

## 4. Input Validation & Defense-in-Depth

- **Pydantic 2.0 Schemas:** Enforces strict structural typing, bounds checks (ratings constrained to $[1.0, 5.0]$, pagination limits to $\le 100$), and input sanitization on all incoming requests.
- **CORS Policy:** Strict Allowed Origins whitelist (`http://localhost:5173`, `http://127.0.0.1:5173`) with `allow_credentials=True`. Wildcard origins (`*`) are disallowed when cookies are enabled.
- **Error Obfuscation:** Database errors, internal stack traces, and password hashes are never exposed to clients; unhandled exceptions return generic `500 Internal Server Error`.
