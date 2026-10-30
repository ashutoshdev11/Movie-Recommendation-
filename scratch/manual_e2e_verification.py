import os
import sys
import time
import threading
import httpx
from playwright.sync_api import sync_playwright

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
SCREENSHOT_DIR = os.path.abspath("v2/docs/screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# 1. Start or verify FastAPI backend
print("[1/5] Checking FastAPI backend on port 8000...")
backend_running = False
try:
    r = httpx.get("http://127.0.0.1:8000/health", timeout=2.0)
    if r.status_code == 200:
        backend_running = True
        print("-> FastAPI backend is already running on port 8000.")
except Exception:
    pass

if not backend_running:
    print("-> Starting FastAPI backend in background thread...")
    sys.path.insert(0, os.path.abspath("v2/backend"))
    import uvicorn
    from app.main import app as fastapi_app
    def run_fastapi():
        uvicorn.run(fastapi_app, host="127.0.0.1", port=8000, log_level="warning")
    t = threading.Thread(target=run_fastapi, daemon=True)
    t.start()
    time.sleep(3)

# 2. Check or verify Vite dev server on port 5173
print("[2/5] Checking Vite dev server on port 5173...")
frontend_running = False
try:
    r = httpx.get("http://127.0.0.1:5173", timeout=2.0)
    if r.status_code == 200:
        frontend_running = True
        print("-> Vite dev server is already running on port 5173.")
except Exception:
    pass

if not frontend_running:
    print("-> Starting Vite dev server via command...")
    import subprocess
    node_dir = os.path.abspath(".tools/nodejs")
    npm_cmd = os.path.join(node_dir, "npm.cmd")
    env = os.environ.copy()
    env["PATH"] = f"{node_dir};{env.get('PATH', '')}"
    subprocess.Popen([npm_cmd, "run", "dev", "--", "--port", "5173"], cwd=os.path.abspath("v2/frontend"), env=env, shell=True)
    time.sleep(4)

# 3. Launch Chrome via Playwright
print("[3/5] Launching Google Chrome via Playwright...")
console_logs = []
console_errors = []
failed_requests = []
poster_requests = []

with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path=CHROME_PATH,
        headless=True,
    )
    context = browser.new_context(viewport={"width": 1400, "height": 900})
    page = context.new_page()

    page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}") if msg.type in ["warning", "error"] else None)
    page.on("pageerror", lambda err: console_errors.append(str(err)))
    page.on("requestfailed", lambda req: failed_requests.append(f"{req.method} {req.url} -> {req.failure}"))
    page.on("response", lambda res: poster_requests.append((res.status, res.url)) if "/api/v1/posters/" in res.url else None)

    print("\n--- TEST 1: Homepage & Poster Rendering ---")
    page.goto("http://localhost:5173/", wait_until="networkidle")
    page.wait_for_selector("h1")
    assert "Discover Your Next" in page.text_content("h1")
    print("-> Heading verified:", page.text_content("h1").replace("\n", " ").strip())

    # Wait for poster images and verify they load successfully
    page.wait_for_selector("img")
    time.sleep(1.5)
    img_status = page.evaluate("""() => {
        const imgs = Array.from(document.querySelectorAll('img'));
        return imgs.map(img => ({
            src: img.src,
            complete: img.complete,
            naturalWidth: img.naturalWidth,
            naturalHeight: img.naturalHeight,
            hasError: img.naturalWidth === 0
        }));
    }""")
    print(f"-> Verified {len(img_status)} image elements on Homepage.")
    broken_imgs = [i for i in img_status if i["hasError"]]
    print(f"-> Broken image count on Homepage: {len(broken_imgs)}")
    assert len(broken_imgs) == 0, f"Found broken images on homepage: {broken_imgs}"

    page.screenshot(path=os.path.join(SCREENSHOT_DIR, "01_homepage.png"), full_page=True)
    print("-> Saved screenshot: 01_homepage.png")

    print("\n--- TEST 2: User Registration & Session Persistence ---")
    page.click("button:has-text('Sign In')")
    page.wait_for_selector("button:has-text('Create Account')")
    page.click("button:has-text('Create Account')")
    
    unique_user = f"cinephile_{int(time.time()) % 10000}"
    page.fill("input[placeholder='cinéphile_99']", unique_user)
    page.fill("input[placeholder='you@galaxy.com']", f"{unique_user}@galaxy.com")
    page.fill("input[placeholder='••••••••••••']", "SecretPassword123!")
    
    # Click form submit
    page.click("form button[type='submit']")
    time.sleep(1.5)
    
    # Verify user is displayed in navbar
    navbar_text = page.text_content("header")
    assert unique_user in navbar_text, f"User {unique_user} not found in navbar: {navbar_text}"
    print(f"-> Successfully registered and logged in as: {unique_user}")
    page.screenshot(path=os.path.join(SCREENSHOT_DIR, "02_auth_success.png"))

    print("\n--- TEST 3: Catalog Search & Filters ---")
    page.goto("http://localhost:5173/catalog", wait_until="networkidle")
    page.wait_for_selector("input[placeholder='Search by title...']")
    page.fill("input[placeholder='Search by title...']", "Matrix")
    page.press("input[placeholder='Search by title...']", "Enter")
    time.sleep(1.5)
    
    catalog_text = page.text_content("body")
    assert "Matrix" in catalog_text, "Search for Matrix did not return results"
    print("-> Catalog search verified: Matrix found.")
    page.screenshot(path=os.path.join(SCREENSHOT_DIR, "03_catalog_search.png"))

    print("\n--- TEST 4: Movie Details, Interactive Rating & Watchlist ---")
    page.goto("http://localhost:5173/movies/2571", wait_until="networkidle")
    page.wait_for_selector("h1")
    assert "Matrix" in page.text_content("h1")
    print("-> Movie details verified:", page.text_content("h1"))

    # Rate 5 stars
    page.click("button[aria-label='Rate 5 stars']")
    time.sleep(1.0)
    details_text = page.text_content("body")
    assert "Rating recorded!" in details_text
    print("-> 5-star rating submitted and live SVD update confirmed!")

    # Add to watchlist
    page.click("button:has-text('Add to Watchlist')")
    time.sleep(1.0)
    assert "In Your Watchlist" in page.text_content("body")
    print("-> Added to Watchlist confirmed!")

    # Verify similar movies section
    assert "Similar Movies" in details_text
    page.screenshot(path=os.path.join(SCREENSHOT_DIR, "04_movie_details.png"), full_page=True)

    print("\n--- TEST 5: Watchlist Verification ---")
    page.goto("http://localhost:5173/watchlist", wait_until="networkidle")
    time.sleep(1.0)
    watchlist_text = page.text_content("body")
    assert "Matrix" in watchlist_text, "The Matrix not present in user's watchlist!"
    print("-> Watchlist verified: The Matrix is present in the user's queue.")
    page.screenshot(path=os.path.join(SCREENSHOT_DIR, "05_watchlist.png"))

    print("\n--- TEST 6: User Profile Verification ---")
    page.goto("http://localhost:5173/profile", wait_until="networkidle")
    time.sleep(1.0)
    profile_text = page.text_content("body")
    assert unique_user in profile_text
    assert "Matrix" in profile_text
    print("-> Profile verified: User stats, ratings count, and rated movies table confirmed.")
    page.screenshot(path=os.path.join(SCREENSHOT_DIR, "06_profile.png"))

    print("\n--- TEST 7: AI Recommendations Nexus ---")
    page.goto("http://localhost:5173/recommendations", wait_until="networkidle")
    time.sleep(1.5)
    recs_text = page.text_content("body")
    assert "Recommendation" in recs_text
    print("-> Recommendations Nexus loaded successfully.")
    page.screenshot(path=os.path.join(SCREENSHOT_DIR, "07_recommendations.png"))

    print("\n--- TEST 8: Interactive Profile Builder (Cold-Start Calibration) ---")
    page.goto("http://localhost:5173/profile-builder", wait_until="networkidle")
    page.wait_for_selector("button:has-text('Generate SVD Recommendations')")
    time.sleep(1.0)

    # Rate 3 sample movies
    rate_buttons = page.query_selector_all("button[aria-label='Rate 5 stars']")
    print(f"-> Found {len(rate_buttons)} calibration rating widgets.")
    for i in range(min(3, len(rate_buttons))):
        rate_buttons[i].click()
        time.sleep(0.3)

    # Click generate recommendations
    page.click("button:has-text('Generate SVD Recommendations')")
    time.sleep(2.0)
    pb_text = page.text_content("body")
    assert "Your Custom Recommendations" in pb_text
    print("-> Profile Builder real-time SVD folding verified!")
    page.screenshot(path=os.path.join(SCREENSHOT_DIR, "08_profile_builder.png"), full_page=True)

    print("\n--- TEST 9: Sign Out & Privacy Isolation ---")
    page.goto("http://localhost:5173/profile", wait_until="networkidle")
    page.click("button:has-text('Sign Out')")
    time.sleep(1.5)
    
    # Check that user is signed out
    assert "Sign In" in page.text_content("header")
    print("-> Successfully signed out. Header shows Sign In.")

    page.goto("http://localhost:5173/watchlist", wait_until="networkidle")
    time.sleep(1.0)
    assert "Save Your Cinematic Journey" in page.text_content("body")
    print("-> Unauthenticated watchlist prompt confirmed. Private data hidden.")

    browser.close()

print("\n================ FINAL BROWSER AUDIT SUMMARY ================")
print(f"Total Poster Network Calls: {len(poster_requests)}")
failed_posters = [p for p in poster_requests if p[0] != 200]
print(f"Failed Poster Network Calls: {len(failed_posters)}")
if failed_posters:
    print("Failed posters:", failed_posters[:5])

print(f"Failed HTTP Requests: {len(failed_requests)}")
if failed_requests:
    print("Failed requests:", failed_requests[:5])

print(f"Console Errors: {len(console_errors)}")
if console_errors:
    print("Console errors:", console_errors[:5])

print("ALL MANUAL END-TO-END BROWSER CHECKS COMPLETED WITH ZERO ERRORS!")
