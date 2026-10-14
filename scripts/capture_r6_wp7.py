#!/usr/bin/env python3
"""
scripts/capture_r6_wp7.py - Capture screenshots for WP7 verification.
Captures home, category, and product detail at 1366x768, 1536x864, 1920x1080, and 390x844.
"""

from pathlib import Path
import sys

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("FATAL: playwright is not installed.")
    sys.exit(1)

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from scripts.e2e_browser import ServerManager, find_free_port, wait_for_server

VIEWPORTS = [
    ("1366x768", {"width": 1366, "height": 768}),
    ("1536x864", {"width": 1536, "height": 864}),
    ("1920x1080", {"width": 1920, "height": 1080}),
    ("390x844", {"width": 390, "height": 844}),
]

OUT_DIR = BASE_DIR / "docs" / "ui-review" / "r6" / "wp7"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def capture():
    port = find_free_port()
    base_url = f"http://127.0.0.1:{port}"
    server = ServerManager(port=port)
    server.start()

    if not wait_for_server(base_url, timeout=30):
        print("FATAL: Test server failed to start.")
        server.stop()
        sys.exit(1)

    print("Capturing WP7 screenshots...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for vp_name, vp_size in VIEWPORTS:
            context = browser.new_context(viewport=vp_size)
            page = context.new_page()

            # 1. Home
            page.goto(f"{base_url}/", wait_until="networkidle")
            page.wait_for_timeout(600)
            home_path = OUT_DIR / f"home_{vp_name}.png"
            page.screenshot(path=str(home_path))
            print(f"Captured: {home_path}")

            # 2. Category Detail
            page.goto(f"{base_url}/c/smartphones/", wait_until="networkidle")
            page.wait_for_timeout(600)
            cat_path = OUT_DIR / f"category_{vp_name}.png"
            page.screenshot(path=str(cat_path))
            print(f"Captured: {cat_path}")

            # 3. Product Detail
            page.goto(f"{base_url}/p/amazon-basics-flexible-premium-hdmi-cable-black-4k60hz-18gbps-3-foot-b07ksmbl2h/", wait_until="networkidle")
            page.wait_for_timeout(600)
            pdp_path = OUT_DIR / f"pdp_{vp_name}.png"
            page.screenshot(path=str(pdp_path))
            print(f"Captured: {pdp_path}")

            context.close()

        browser.close()

    server.stop()
    print("WP7 capture complete.")


if __name__ == "__main__":
    capture()
