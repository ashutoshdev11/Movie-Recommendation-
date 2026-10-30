# Run Guide — MovieRec Version 2

This document provides exact, copy-pasteable PowerShell commands to launch the complete MovieRec Version 2 application.

---

## 1. Quick Launch Summary

| Component | Port | URL | Command |
| :--- | :--- | :--- | :--- |
| **FastAPI Backend** | 8000 | `http://localhost:8000` | `.venv\Scripts\python.exe -m uvicorn v2.backend.app.main:app --port 8000 --reload` |
| **API Docs (Swagger)**| 8000 | `http://localhost:8000/docs` | Built-in interactive API documentation |
| **React + 3D Frontend**| 5173 | `http://localhost:5173` | `npm run dev` (inside `v2\frontend`) |

---

## 2. Step-by-Step PowerShell Execution

### Terminal 1: Launch FastAPI Backend

Open a PowerShell terminal at the project root directory:

```powershell
# Set root location
cd "C:\Users\ashut\Downloads\MOVIE RECOMMENDATION PROJECT"

# Activate environment and launch Uvicorn server on port 8000
.venv\Scripts\python.exe -m uvicorn v2.backend.app.main:app --port 8000 --reload
```

**Expected Output:**
```
INFO:     Will watch for changes in these directories: [...]
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
[V2RecommenderService] Initializing models and metadata...
[V2RecommenderService] Successfully loaded SVD (k=30) and Damped Popularity (m=50.0).
INFO:     Application startup complete.
```

---

### Terminal 2: Launch React + TypeScript + Three.js Frontend

Open a second PowerShell terminal:

```powershell
# Set root location
cd "C:\Users\ashut\Downloads\MOVIE RECOMMENDATION PROJECT"

# Add node to PATH if using local tools
$nodeDir = (Resolve-Path '.tools\nodejs').Path
$env:PATH = "$nodeDir;$env:PATH"

# Navigate to frontend and start Vite development server
cd v2\frontend
npm run dev
```

**Expected Output:**
```
  VITE v5.4.10  ready in 240 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

---

## 3. Exploring the Application

1. Open your browser and navigate to **`http://localhost:5173`**.
2. **Explore 3D Hero & Universe:** Move your mouse over the hero section to see the real-time 3D particle galaxy and holographic prism track your pointer.
3. **Register an Account:**
   - Click **"Sign In"** in the top navigation bar.
   - Switch to **"Create Account"**.
   - Enter your username, email, and password.
   - You are immediately signed in with a secure `HttpOnly` cookie session.
4. **Browse 3,883 Movies:**
   - Click **"Catalog"** in the navigation bar.
   - Search for titles (e.g., `Matrix`, `Star Wars`, `Toy Story`).
   - Filter by any of the 18 MovieLens genres.
5. **Rate Movies & Build Your Latent Profile:**
   - Click on any movie card to view its details.
   - Rate the movie using the 5-star rating widget.
   - Watch the live indicator confirm: *"Rating recorded! Your personalized SVD latent vector has updated."*
6. **Inspect Personalized SVD Recommendations:**
   - Click **"AI Recs"** in the navbar.
   - Once you have rated 3+ movies, the engine automatically folds your profile into the 30D latent space and displays your ranked recommendations with predicted scores.
7. **Try Cold-Start Profile Builder:**
   - Click **"Profile Builder"** in the navbar.
   - Rate sample movies without creating an account and click **"Generate SVD Recommendations"** to experience instantaneous anonymous folding-in ($<3\text{ ms}$).
8. **Manage Watchlist:**
   - Click the bookmark icon on any movie card to save it.
   - Visit **"Watchlist"** in the navbar to review or remove saved films.
