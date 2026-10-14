#!/usr/bin/env python3
"""
Capture loop screenshots for WP6 (Product Page Exhibition & Commerce) across 4 viewports:
1366x768, 1536x864, 1920x1080, 390x844.

Captures:
- pdp_overview: Top hero layout with 1:1 exhibition plinth, zoom trigger, and sticky sub-nav
- pdp_specs_box: Specifications and In the Box sections
- pdp_compare: 4-column comparative specification matrix
- pdp_lightbox: Native <dialog> modal image zoom open
"""

import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from scripts.e2e_browser import ServerManager, find_free_port, wait_for_server

OUT_DIR = BASE_DIR / "docs" / "ui-review" / "r6" / "wp6"
OUT_DIR.mkdir(parents=True, exist_ok=True)

VIEWPORTS = [
    ("1366x768", 1366, 768),
    ("1536x864", 1536, 864),
    ("1920x1080", 1920, 1080),
    ("390x844", 390, 844),
]

PDP_PATH = "/p/boat-bassheads-100-in-ear-wired-headphones-with-mic-black-b071z8m4kx/"


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

                # 1. PDP Overview
                page.goto(f"{base_url}{PDP_PATH}", wait_until="load", timeout=15000)
                page.wait_for_timeout(600)
                shot_path = vp_dir / "pdp_overview.png"
                page.screenshot(path=str(shot_path))
                print(f"Captured {shot_path}")

                # 2. PDP Specifications & In the Box
                specs_el = page.query_selector("#section-specs")
                if specs_el:
                    specs_el.scroll_into_view_if_needed()
                    page.wait_for_timeout(400)
                    shot_path = vp_dir / "pdp_specs_box.png"
                    page.screenshot(path=str(shot_path))
                    print(f"Captured {shot_path}")

                # 3. PDP Compare Similar
                comp_el = page.query_selector("#section-compare")
                if comp_el:
                    comp_el.scroll_into_view_if_needed()
                    page.wait_for_timeout(400)
                    shot_path = vp_dir / "pdp_compare.png"
                    page.screenshot(path=str(shot_path))
                    print(f"Captured {shot_path}")

                # 4. PDP Lightbox open
                page.evaluate("window.scrollTo(0, 0)")
                page.wait_for_timeout(300)
                zoom_btn = page.query_selector("#open-lightbox-btn")
                if zoom_btn:
                    zoom_btn.click()
                    page.wait_for_timeout(400)
                    shot_path = vp_dir / "pdp_lightbox.png"
                    page.screenshot(path=str(shot_path))
                    print(f"Captured {shot_path}")

                ctx.close()
            browser.close()
    finally:
        server.stop()


if __name__ == "__main__":
    capture()
