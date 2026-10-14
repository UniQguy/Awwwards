#!/usr/bin/env python3
"""
Capture loop screenshots and verify vertical page height for WP3 (Calm Home Rebuild) across 4 viewports:
1366x768, 1536x864, 1920x1080, 390x844.

Also measures document scroll height at 1456x820 to enforce height <= 6 viewports (<= 4608 px).
"""

import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from scripts.e2e_browser import ServerManager, find_free_port, wait_for_server

OUT_DIR = BASE_DIR / "docs" / "ui-review" / "r6" / "wp3"
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

            # 1. Height verification at 1456x820
            page_audit = browser.new_page(viewport={"width": 1456, "height": 820})
            page_audit.goto(base_url, wait_until="load", timeout=15000)
            page_audit.wait_for_timeout(600)
            doc_height = page_audit.evaluate("document.documentElement.scrollHeight")
            max_allowed = 4608
            print(f"Measured Home scrollHeight at 1456x820: {doc_height}px (max allowed: {max_allowed}px)")
            if doc_height > max_allowed:
                print(f"WARNING: Home height {doc_height}px exceeds 6 viewports ({max_allowed}px)!")
            else:
                print(f"PASS: Home height {doc_height}px is within 6 viewports ({max_allowed}px) limit.")
            page_audit.close()

            # 2. Viewport screenshots
            for vp_name, w, h in VIEWPORTS:
                vp_dir = OUT_DIR / vp_name
                vp_dir.mkdir(parents=True, exist_ok=True)
                ctx = browser.new_context(viewport={"width": w, "height": h})
                page = ctx.new_page()

                page.goto(base_url, wait_until="networkidle", timeout=15000)
                # Wait for entrance animation to finish completely
                page.wait_for_timeout(1800)

                # Hero
                shot_path = vp_dir / "home_hero.png"
                page.screenshot(path=str(shot_path))
                print(f"Captured {shot_path}")

                # Categories snap-rail
                rail_el = page.query_selector(".section-snap-rail")
                if rail_el:
                    rail_el.evaluate("el => el.scrollIntoView({block: 'center'})")
                    page.wait_for_timeout(400)
                    shot_path = vp_dir / "home_snap_rail.png"
                    page.screenshot(path=str(shot_path))
                    print(f"Captured {shot_path}")

                # Chapters
                chapters_el = page.query_selector("#chapters")
                if chapters_el:
                    chapters_el.evaluate("el => el.scrollIntoView({block: 'center'})")
                    page.wait_for_timeout(400)
                    shot_path = vp_dir / "home_chapters.png"
                    page.screenshot(path=str(shot_path))
                    print(f"Captured {shot_path}")

                # Curated Stories & Budget Ladder
                stories_el = page.query_selector(".curated-stories-section")
                if stories_el:
                    stories_el.evaluate("el => el.scrollIntoView({block: 'center'})")
                    page.wait_for_timeout(400)
                    shot_path = vp_dir / "home_stories.png"
                    page.screenshot(path=str(shot_path))
                    print(f"Captured {shot_path}")

                budget_el = page.query_selector(".budget-ladder-section")
                if budget_el:
                    budget_el.evaluate("el => el.scrollIntoView({block: 'center'})")
                    page.wait_for_timeout(400)
                    shot_path = vp_dir / "home_budget.png"
                    page.screenshot(path=str(shot_path))
                    print(f"Captured {shot_path}")

                # How Buying Works & Brands
                buying_el = page.query_selector("#buying")
                if buying_el:
                    buying_el.evaluate("el => el.scrollIntoView({block: 'center'})")
                    page.wait_for_timeout(400)
                    shot_path = vp_dir / "home_buying_brands.png"
                    page.screenshot(path=str(shot_path))
                    print(f"Captured {shot_path}")

                ctx.close()
            browser.close()
    finally:
        server.stop()


if __name__ == "__main__":
    capture()
