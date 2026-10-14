#!/usr/bin/env python3
"""
Capture loop screenshots for WP5 (Category Page) across 4 viewports:
1366x768, 1536x864, 1920x1080, 390x844.
Captures:
- category_shelf: Page 1 with compact header, quick chips, and 6-card Most Rated shelf
- category_filtered: Category with active brand filter showing chip and catalog grid
- category_page2: Category page 2 pagination
"""

import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from scripts.e2e_browser import ServerManager, find_free_port, wait_for_server

OUT_DIR = BASE_DIR / "docs" / "ui-review" / "r6" / "wp5"
OUT_DIR.mkdir(parents=True, exist_ok=True)

VIEWPORTS = [
    ("1366x768", 1366, 768),
    ("1536x864", 1536, 864),
    ("1920x1080", 1920, 1080),
    ("390x844", 390, 844),
]

PAGES = [
    ("category_shelf", "/c/earphones-headphones/"),
    ("category_filtered", "/c/smartphones/?brand=Samsung"),
    ("category_page2", "/c/cameras/?page=2"),
]


def capture():
    port = find_free_port()
    base_url = f"http://127.0.0.1:{port}"
    server = ServerManager(port=port)
    server.start()

    if not wait_for_server(base_url, timeout=30):
        print("Server start failed")
        server.stop()
        sys.exit(1)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            for vp_name, w, h in VIEWPORTS:
                vp_dir = OUT_DIR / vp_name
                vp_dir.mkdir(parents=True, exist_ok=True)
                ctx = browser.new_context(viewport={"width": w, "height": h})
                page = ctx.new_page()

                for name, path in PAGES:
                    page.goto(f"{base_url}{path}", wait_until="load", timeout=15000)
                    page.wait_for_timeout(600)
                    shot_path = vp_dir / f"{name}.png"
                    page.screenshot(path=str(shot_path))
                    print(f"Captured {shot_path}")

                ctx.close()
            browser.close()
    finally:
        server.stop()


if __name__ == "__main__":
    capture()
