#!/usr/bin/env python3
"""
Visual QA Screenshot Harness for ELECTROCART (Phase 4 Quality Gate).
Uses Playwright Chromium to capture full-page screenshots across viewports:
  - 390px (Mobile iPhone 14/15)
  - 768px (Tablet portrait)
  - 1280px (Laptop / Desktop)
  - 1920px (Wide Desktop)
Saves outputs to reports/screenshots/ (git-ignored).
Checks for horizontal overflow (document.scrollWidth > clientWidth) at every width.
"""

import os
from pathlib import Path
import subprocess
import sys
import time

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Playwright is not installed. Install with: pip install playwright && playwright install chromium")
    sys.exit(1)

VIEWPORTS = [
    {"name": "390", "width": 390, "height": 844},
    {"name": "768", "width": 768, "height": 1024},
    {"name": "1280", "width": 1280, "height": 800},
    {"name": "1920", "width": 1920, "height": 1080},
]

PAGES = [
    {"slug": "home", "path": "/"},
    {"slug": "categories", "path": "/categories/"},
    {"slug": "category-detail", "path": "/c/earphones-headphones/"},
    {"slug": "product-detail", "path": "/p/boat-bassheads-100-in-ear-wired-headphones-with-mic-black-b071z8m4kx/"},
    {"slug": "cart-empty", "path": "/cart/"},
    {"slug": "checkout-start", "path": "/checkout/"},
    {"slug": "track-lookup", "path": "/orders/track/"},
    {"slug": "brands", "path": "/brands/"},
    {"slug": "login", "path": "/accounts/login/"},
    {"slug": "not-found", "path": "/404-test-page/"},
]


def wait_for_server(url: str, timeout: int = 15) -> bool:
    import urllib.request
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(url) as response:
                if response.status in (200, 302, 404):
                    return True
        except Exception:
            time.sleep(0.5)
    return False


def run_harness():
    base_dir = Path(__file__).resolve().parent.parent
    reports_dir = base_dir / "reports" / "screenshots"
    reports_dir.mkdir(parents=True, exist_ok=True)

    server_process = None
    server_url = "http://127.0.0.1:8000"

    # Start Django dev server if not already running
    if not wait_for_server(f"{server_url}/health/", timeout=2):
        print("Starting Django development server in background...")
        python_bin = base_dir / ".venv" / "Scripts" / "python.exe"
        if not python_bin.exists():
            python_bin = sys.executable
        server_process = subprocess.Popen(
            [str(python_bin), "manage.py", "runserver", "127.0.0.1:8000", "--noreload"],
            cwd=str(base_dir),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if not wait_for_server(f"{server_url}/health/", timeout=15):
            print("Failed to start or connect to Django dev server.")
            if server_process:
                server_process.terminate()
            sys.exit(1)

    print(f"Server is responding at {server_url}. Launching Chromium via Playwright...")
    overflow_errors = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            for vp in VIEWPORTS:
                print(f"\n--- Viewport: {vp['width']}x{vp['height']} ({vp['name']}) ---")
                context = browser.new_context(
                    viewport={"width": vp["width"], "height": vp["height"]},
                    device_scale_factor=1,
                )
                page = context.new_page()

                for page_info in PAGES:
                    url = f"{server_url}{page_info['path']}"
                    try:
                        page.goto(url, wait_until="networkidle", timeout=10000)
                    except Exception:
                        page.goto(url, wait_until="domcontentloaded", timeout=10000)

                    # Check horizontal overflow
                    scroll_width = page.evaluate("() => document.documentElement.scrollWidth")
                    client_width = page.evaluate("() => document.documentElement.clientWidth")
                    if scroll_width > client_width:
                        diff = scroll_width - client_width
                        overflow_msg = f"Overflow on {page_info['slug']} @ {vp['width']}px (scrollWidth={scroll_width} > clientWidth={client_width}, +{diff}px)"
                        print(f"  [OVERFLOW] {overflow_msg}")
                        overflow_errors.append(overflow_msg)

                    out_file = reports_dir / f"{page_info['slug']}_{vp['name']}.png"
                    page.screenshot(path=str(out_file), full_page=True)
                    print(f"  Saved screenshot: {out_file.name}")

                context.close()

            browser.close()

    finally:
        if server_process:
            server_process.terminate()
            server_process.wait()

    print("\n" + "=" * 80)
    if overflow_errors:
        print(f"SCREENSHOT HARNESS FINISHED WITH {len(overflow_errors)} HORIZONTAL OVERFLOW DEFECTS:")
        for err in overflow_errors:
            print(f"  - {err}")
        return False
    else:
        print("SCREENSHOT HARNESS COMPLETE: All viewports clean. Zero horizontal overflows detected.")
        print(f"Screenshots saved to: {reports_dir}")
        print("=" * 80 + "\n")
        return True


if __name__ == "__main__":
    success = run_harness()
    sys.exit(0 if success else 1)
