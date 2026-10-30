import os
import sys
import time
import shutil
from playwright.sync_api import sync_playwright

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
SCREENSHOT_DIR = os.path.abspath("v2/docs/screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

ARTIFACT_DIR = r"C:\Users\ashut\.gemini\antigravity\brain\7cddea1a-a245-40a8-b9d4-6704253e35d7"

with sync_playwright() as p:
    print("Launching Chrome to verify Fight Club and 3D positioning...")
    browser = p.chromium.launch(executable_path=CHROME_PATH, headless=True)
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()

    page.goto("http://localhost:5173/", wait_until="networkidle")
    page.wait_for_selector("h1")

    # Wait for the featured movie card to load
    time.sleep(2.5)

    # 1. Verify Fight Club Title
    page.wait_for_selector("h3:has-text('Fight Club')")
    title_el = page.query_selector("h3:has-text('Fight Club')")
    assert title_el is not None, "Fight Club title not found!"
    print("-> Confirmed: 'Fight Club' title rendered successfully!")

    # 2. Verify Release Year and Genres
    card_text = page.evaluate("""() => {
        const card = document.querySelector('h3').closest('div.rounded-\\\\[24px\\\\]') || document.querySelector('h3').parentElement;
        return card ? card.innerText : '';
    }""")
    print("-> Card text content:\n", card_text)
    assert "1999" in card_text, "Release year 1999 missing!"
    assert "Drama" in card_text, "MovieLens genre Drama missing!"
    assert "Explore Movie" in card_text, "Explore Movie button missing!"

    # 3. Verify Poster Image loads authentic TMDB Fight Club artwork
    img_info = page.evaluate("""() => {
        const img = document.querySelector("img[alt='Fight Club']");
        if (!img) return null;
        return {
            src: img.src,
            naturalWidth: img.naturalWidth,
            naturalHeight: img.naturalHeight,
            complete: img.complete
        };
    }""")
    print("-> Fight Club Poster Info:", img_info)
    assert img_info is not None, "Fight Club poster element not found!"
    assert img_info["naturalWidth"] > 0, "Fight Club image failed to load or is broken!"

    # 4. Verify 3D Stage & Foreground Card Z-Index
    z_indices = page.evaluate("""() => {
        const stage = document.querySelector('canvas');
        const card = document.querySelector("img[alt='Fight Club']").closest("div.relative.z-20");
        return {
            stageExists: !!stage,
            cardExists: !!card,
            cardClass: card ? card.className : '',
            cardZIndex: card ? window.getComputedStyle(card).zIndex : null
        };
    }""")
    print("-> 3D and Card Layering:", z_indices)
    assert z_indices["cardExists"], "Featured card foreground container missing!"
    assert z_indices["cardZIndex"] == "20", "Featured card must be in z-index 20 above 3D stage!"

    # 5. Capture Hero Section Screenshot and Full Page Screenshot
    hero_path = os.path.join(SCREENSHOT_DIR, "fight_club_featured_hero.png")
    page.screenshot(path=hero_path, clip={"x": 0, "y": 0, "width": 1440, "height": 760})
    print(f"-> Saved hero screenshot: {hero_path}")

    full_path = os.path.join(SCREENSHOT_DIR, "fight_club_homepage_full.png")
    page.screenshot(path=full_path, full_page=True)
    print(f"-> Saved full page screenshot: {full_path}")

    # Copy hero screenshot to artifact dir
    artifact_hero_path = os.path.join(ARTIFACT_DIR, "fight_club_featured_hero.png")
    shutil.copyfile(hero_path, artifact_hero_path)
    print(f"-> Copied hero screenshot to artifact dir: {artifact_hero_path}")

    # 6. Verify Explore Movie click navigates to /movies/2959
    page.click("a:has-text('Explore Movie')")
    page.wait_for_url("**/movies/2959")
    time.sleep(2.0)
    print("-> Navigated to Movie Details page:", page.url)
    details_h1 = page.text_content("h1")
    assert "Fight Club" in details_h1, "Movie details page did not load Fight Club!"
    print("-> Details page confirmed for Fight Club (1999)!")

    details_img = page.evaluate("""() => {
        const img = document.querySelector("img[alt='Fight Club']");
        return img ? { naturalWidth: img.naturalWidth, src: img.src } : null;
    }""")
    print("-> Details page poster info:", details_img)
    assert details_img and details_img["naturalWidth"] > 0, "Details page poster is broken!"

    details_screenshot = os.path.join(SCREENSHOT_DIR, "fight_club_details_page.png")
    page.screenshot(path=details_screenshot)
    shutil.copyfile(details_screenshot, os.path.join(ARTIFACT_DIR, "fight_club_details_page.png"))
    print("-> Details page screenshot captured!")

    browser.close()

print("\n" + "="*50)
print("ALL VERIFICATION CHECKS PASSED 100%!")
print("="*50)
