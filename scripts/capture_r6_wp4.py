#!/usr/bin/env python3
"""
Capture screenshots for WP4 (Header & Mega-Menu) across 4 viewports:
1366x768, 1536x864, 1920x1080, 390x844.
Captures:
- header_default: Closed header on home page
- mega_menu_open: Mega-menu open showing 2-column layout and preview
- mega_menu_hover: Mega-menu with hover on 3rd category demonstrating dynamic preview
"""

import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from scripts.e2e_browser import ServerManager, find_free_port, wait_for_server

OUT_DIR = BASE_DIR / "docs" / "ui-review" / "r6" / "wp4"
OUT_DIR.mkdir(parents=True, exist_ok=True)

VIEWPORTS = [
    ("1366x768", 1366, 768),
    ("1536x864", 1536, 864),
    ("1920x1080", 1920, 1080),
    ("390x844", 390, 844),
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

                page.goto(f"{base_url}/", wait_until="load", timeout=15000)
                page.wait_for_timeout(800)

                # 1. Closed Header
                shot_closed = vp_dir / "header_default.png"
                page.screenshot(path=str(shot_closed))
                print(f"Captured {shot_closed}")

                # 2. Open Mega Menu
                page.click(".shop-menu-summary")
                page.wait_for_timeout(400)
                shot_open = vp_dir / "mega_menu_open.png"
                page.screenshot(path=str(shot_open))
                print(f"Captured {shot_open}")

                # 3. Hover 3rd category (on desktop viewports)
                if w > 768:
                    items = page.query_selector_all(".mega-menu-cat-item")
                    if len(items) >= 3:
                        items[2].hover()
                        page.wait_for_timeout(300)
                        shot_hover = vp_dir / "mega_menu_hover.png"
                        page.screenshot(path=str(shot_hover))
                        print(f"Captured {shot_hover}")

                ctx.close()
            browser.close()
    finally:
        server.stop()


if __name__ == "__main__":
    capture()
