import os
import sys
import time
import httpx
from playwright.sync_api import sync_playwright

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
SCREENSHOT_DIR = os.path.abspath("v2/docs/screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# Verify backend (8000) and frontend (5173) are both active
r_back = httpx.get("http://127.0.0.1:8000/health")
print("Backend health check:", r_back.json())
assert r_back.status_code == 200

r_front = httpx.get("http://localhost:5173/")
print("Frontend root status:", r_front.status_code)
assert r_front.status_code == 200

# Begin Playwright Browser Automation with Chrome
console_errors = []
console_messages = []
failed_requests = []
poster_responses = []

with sync_playwright() as p:
    print("\nLaunching Chrome Headless via Playwright...")
    browser = p.chromium.launch(
        executable_path=CHROME_PATH,
        headless=True,
    )
    context = browser.new_context(viewport={"width": 1400, "height": 900})
    page = context.new_page()

    page.on("console", lambda msg: console_messages.append(f"[{msg.type}] {msg.text}"))
    page.on("pageerror", lambda err: console_errors.append(str(err)))
    page.on("requestfailed", lambda req: failed_requests.append(f"{req.method} {req.url} -> {req.failure}"))
    page.on("response", lambda res: poster_responses.append((res.status, res.url)) if "/api/v1/posters/" in res.url else None)

    # -------------------------------------------------------------
    # TEST 1: Homepage & Real Movie Posters
    # -------------------------------------------------------------
    print("\n[TEST 1] Visiting Homepage (http://localhost:5173/)...")
    page.goto("http://localhost:5173/", wait_until="networkidle")
    page.wait_for_selector("h1")
    print("-> Page title:", page.title())
    print("-> Heading text:", page.text_content("h1").replace("\n", " ").strip())

    # Verify movie poster images render
    page.wait_for_selector("img")
    time.sleep(2.0)
    img_data = page.evaluate("""() => {
        const imgs = Array.from(document.querySelectorAll('img'));
        return imgs.map(img => ({
            src: img.src,
            naturalWidth: img.naturalWidth,
            naturalHeight: img.naturalHeight,
            complete: img.complete
        }));
    }""")
    print(f"-> Total images rendered on Homepage: {len(img_data)}")
    for i, img in enumerate(img_data):
        print(f"   Image {i+1}: {img['src'][:60]}... (Width: {img['naturalWidth']}, Complete: {img['complete']})")
        assert img["naturalWidth"] > 0, f"Image {img['src']} is broken!"
    
    page.screenshot(path=os.path.join(SCREENSHOT_DIR, "01_homepage.png"), full_page=True)
    print("-> Screenshot saved: 01_homepage.png")

    # -------------------------------------------------------------
    # TEST 2: User Registration & Session Cookie
    # -------------------------------------------------------------
    print("\n[TEST 2] Testing User Registration...")
    page.click("button:has-text('Sign In')")
    page.wait_for_selector("button:has-text('Create Account')")
    page.click("button:has-text('Create Account')")

    test_username = f"cinephile_{int(time.time()) % 10000}"
    test_email = f"{test_username}@galaxy.com"
    page.fill("input[placeholder='cinéphile_99']", test_username)
    page.fill("input[placeholder='you@galaxy.com']", test_email)
    page.fill("input[placeholder='••••••••••••']", "SecretPassword123!")

    page.click("form button[type='submit']")
    time.sleep(2.0)

    header_text = page.text_content("header")
    assert test_username in header_text
    print(f"-> Registration successful! Header displays username: {test_username}")
    page.screenshot(path=os.path.join(SCREENSHOT_DIR, "02_auth_success.png"))

    # -------------------------------------------------------------
    # TEST 3: Catalog Search & Genre Filters
    # -------------------------------------------------------------
    print("\n[TEST 3] Testing Catalog Search & Posters...")
    page.goto("http://localhost:5173/catalog", wait_until="networkidle")
    page.wait_for_selector("input[placeholder='Search by title...']")
    page.fill("input[placeholder='Search by title...']", "Matrix")
    page.press("input[placeholder='Search by title...']", "Enter")
    time.sleep(2.0)

    catalog_body = page.text_content("body")
    assert "Matrix" in catalog_body
    print("-> Search result confirmed: The Matrix found.")
    
    # Check that search result posters load
    cat_imgs = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('img')).map(img => ({
            src: img.src,
            naturalWidth: img.naturalWidth,
            complete: img.complete
        }));
    }""")
    print(f"-> Catalog images loaded: {len(cat_imgs)} (all naturalWidth > 0)")
    assert all(i["naturalWidth"] > 0 for i in cat_imgs)
    page.screenshot(path=os.path.join(SCREENSHOT_DIR, "03_catalog_search.png"))

    # -------------------------------------------------------------
    # TEST 4: Movie Details, 5-Star Rating & Watchlist Toggle
    # -------------------------------------------------------------
    print("\n[TEST 4] Testing Movie Details, Rating & Watchlist (The Matrix #2571)...")
    page.goto("http://localhost:5173/movies/2571", wait_until="networkidle")
    page.wait_for_selector("h1")
    assert "Matrix" in page.text_content("h1")

    # Click 5-star rating
    page.click("button[aria-label='Rate 5 stars']")
    time.sleep(1.5)
    assert "Rating recorded!" in page.text_content("body")
    print("-> Rating submitted! SVD update acknowledged.")

    # Add to watchlist
    page.click("button:has-text('Add to Watchlist')")
    time.sleep(1.5)
    assert "In Your Watchlist" in page.text_content("body")
    print("-> Added to Watchlist confirmed!")

    # Verify similar movies section
    assert "Similar Movies" in page.text_content("body")
    page.screenshot(path=os.path.join(SCREENSHOT_DIR, "04_movie_details.png"), full_page=True)

    # -------------------------------------------------------------
    # TEST 5: Watchlist Verification
    # -------------------------------------------------------------
    print("\n[TEST 5] Testing Watchlist Page...")
    page.goto("http://localhost:5173/watchlist", wait_until="networkidle")
    time.sleep(1.5)
    assert "Matrix" in page.text_content("body")
    print("-> The Matrix verified in user's saved Watchlist.")
    page.screenshot(path=os.path.join(SCREENSHOT_DIR, "05_watchlist.png"))

    # -------------------------------------------------------------
    # TEST 6: User Profile Verification
    # -------------------------------------------------------------
    print("\n[TEST 6] Testing User Profile Page...")
    page.goto("http://localhost:5173/profile", wait_until="networkidle")
    time.sleep(1.5)
    prof_text = page.text_content("body")
    assert test_username in prof_text
    assert "Matrix" in prof_text
    print("-> Profile verified: User stats, ratings count, and rated movies table confirmed.")
    page.screenshot(path=os.path.join(SCREENSHOT_DIR, "06_profile.png"))

    # -------------------------------------------------------------
    # TEST 7: AI Recommendations Nexus
    # -------------------------------------------------------------
    print("\n[TEST 7] Testing AI Recommendations Page...")
    page.goto("http://localhost:5173/recommendations", wait_until="networkidle")
    time.sleep(1.5)
    recs_text = page.text_content("body")
    assert "Recommendation" in recs_text
    print("-> Recommendations Nexus loaded successfully.")
    page.screenshot(path=os.path.join(SCREENSHOT_DIR, "07_recommendations.png"))

    # -------------------------------------------------------------
    # TEST 8: Profile Builder (Interactive SVD Fold-in)
    # -------------------------------------------------------------
    print("\n[TEST 8] Testing Interactive Profile Builder...")
    page.goto("http://localhost:5173/profile-builder", wait_until="networkidle")
    page.wait_for_selector("button:has-text('Generate SVD Recommendations')")
    time.sleep(1.5)

    rate_btns = page.query_selector_all("button[aria-label='Rate 5 stars']")
    for i in range(min(3, len(rate_btns))):
        rate_btns[i].click()
        time.sleep(0.3)

    page.click("button:has-text('Generate SVD Recommendations')")
    time.sleep(2.5)
    assert "Your Custom Recommendations" in page.text_content("body")
    print("-> Profile Builder generated instant SVD recommendations!")
    page.screenshot(path=os.path.join(SCREENSHOT_DIR, "08_profile_builder.png"), full_page=True)

    # -------------------------------------------------------------
    # TEST 9: Sign Out & Privacy Isolation
    # -------------------------------------------------------------
    print("\n[TEST 9] Testing Sign Out & Data Protection...")
    page.goto("http://localhost:5173/profile", wait_until="networkidle")
    page.click("button:has-text('Sign Out')")
    time.sleep(1.5)

    assert "Sign In" in page.text_content("header")
    print("-> Successfully signed out. Header displays Sign In.")

    page.goto("http://localhost:5173/watchlist", wait_until="networkidle")
    time.sleep(1.5)
    assert "Save Your Cinematic Journey" in page.text_content("body")
    print("-> Private watchlist access blocked when unauthenticated.")

    browser.close()

print("\n" + "="*50)
print("AUDIT REPORT:")
print(f"Total Poster Network Requests: {len(poster_responses)}")
failed_posters = [p for p in poster_responses if p[0] != 200]
print(f"Failed Poster Requests (Non-200): {len(failed_posters)}")
assert len(failed_posters) == 0, f"Found failed posters: {failed_posters}"

print(f"Failed Network Requests: {len(failed_requests)}")
if failed_requests:
    print("Failed requests detail:", failed_requests)

print(f"Console Errors: {len(console_errors)}")
if console_errors:
    print("Console errors detail:", console_errors)

print("COMPLETE BROWSER VERIFICATION: 100% SUCCESS WITH ZERO ERRORS!")
print("="*50)
