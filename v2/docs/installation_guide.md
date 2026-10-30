# Installation & Setup Guide — MovieRec Version 2

This guide outlines the complete setup procedure for MovieRec Version 2 across backend and frontend environments.

---

## 1. Prerequisites

- **Operating System:** Windows 10/11, macOS, or Linux.
- **Python:** Python 3.11+ (Python 3.11.9 recommended).
- **Node.js:** Node.js v20.x+ LTS and npm 10.x+.
- **Disk Space:** Minimum 2 GB free disk space (dataset + virtual environment + dependencies).

---

## 2. Environment Verification

Check Python and Node installations:
```powershell
python --version
# Expected: Python 3.11.x

node -v
# Expected: v20.x.x
npm -v
# Expected: 10.x.x
```

If Node.js was unpacked into the local project `.tools/nodejs` folder, prepend it to your active PowerShell session:
```powershell
$nodeDir = (Resolve-Path '.tools\nodejs').Path
$env:PATH = "$nodeDir;$env:PATH"
```

---

## 3. Backend Setup

### 3.1 Activate Virtual Environment
```powershell
# From project root
.venv\Scripts\Activate.ps1
```

### 3.2 Install Backend Dependencies
The backend requires FastAPI, SQLAlchemy 2.0, Passlib with Argon2, Python-JOSE, and data science libraries:
```powershell
pip install fastapi uvicorn sqlalchemy pydantic passlib[argon2] python-jose python-multipart httpx pandas numpy scipy scikit-learn pytest
```

### 3.3 Verify Dataset & Pretrained Models
Confirm that the MovieLens 1M processed data and trained SVD artifacts exist:
- `v2/backend/data/processed/movies_metadata.csv.gz`
- `v2/backend/artifacts/v2_svd_k30.npz`
- `v2/backend/artifacts/v2_popularity_baseline.json`

*(Note: If training from scratch, run `.venv\Scripts\python.exe v2/backend/app/ml/train_and_evaluate.py`)*

### 3.4 Initialize SQLite Database
The SQLite database tables (`users`, `user_ratings`, `watchlist_items`) are automatically created when the FastAPI application starts.

---

## 4. Frontend Setup

### 4.1 Navigate to Frontend Directory
```powershell
cd v2\frontend
```

### 4.2 Install npm Dependencies
```powershell
npm install
```
Installed packages include:
- `react`, `react-dom`, `react-router-dom`
- `three`, `@types/three`
- `framer-motion`, `lucide-react`, `axios`
- `tailwindcss`, `postcss`, `autoprefixer`
- `vitest`, `@testing-library/react`, `jsdom`

### 4.3 Verify Frontend Build
```powershell
npm run build
```
This runs TypeScript checking (`tsc`) and Vite production bundling into `dist/`.

---

## 5. Running Automated Verification

Run all test suites to confirm complete system integrity:

```powershell
# Run V2 Backend unit & integration tests (29 tests)
.venv\Scripts\python.exe -m pytest v2/backend/tests/

# Run V2 Frontend tests (9 tests)
cd v2\frontend
npm test

# Run V1 regression suite (53 tests)
cd ..\..
.venv\Scripts\python.exe -m pytest tests/
```
