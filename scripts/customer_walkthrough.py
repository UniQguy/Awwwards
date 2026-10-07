#!/usr/bin/env python3
"""
Customer Walkthrough & Quality Verification for ELECTROCART (Phase 7).
Executes a realistic end-to-end shopping journey using Playwright Chromium:
  1. Home page
  2. Category monograph spread
  3. Filtered catalog grid
  4. Product sheet
  5. Cart with line item
  6. Checkout entry (guest)
  7. Checkout address entry
  8. Checkout review & payment choice
  9. Order confirmed (receipt)
  10. Order shipment tracking (timeline)
  11. GST Tax Invoice / Bill of Supply
  12. Customer account login
  13. 404 Not Found error page

Captures full-page screenshots at both:
  - 1280px (Desktop / Laptop)
  - 390px (Mobile iPhone 14/15)
Checks and asserts 0 horizontal overflow (document.scrollWidth <= clientWidth).
"""

import os
from pathlib import Path
import subprocess
import sys
import time

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Playwright is required. Run: pip install playwright && playwright install chromium")
    sys.exit(1)

VIEWPORTS = [
    {"name": "1280", "width": 1280, "height": 800, "is_mobile": False},
    {"name": "390", "width": 390, "height": 844, "is_mobile": True},
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


def run_customer_walkthrough():
    base_dir = Path(__file__).resolve().parent.parent
    reports_dir = base_dir / "reports" / "screenshots" / "walkthrough"
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Force kill any stale dev server listening on port 8000
    subprocess.run(
        ["powershell", "-Command", "Get-Process -Id (Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue).OwningProcess -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue"],
        capture_output=True,
    )
    time.sleep(1)

    server_process = None
    server_url = "http://127.0.0.1:8000"

    print("Starting fresh Django dev server...")
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
        print("Failed to connect to Django development server.")
        if server_process:
            server_process.terminate()
        sys.exit(1)

    print(f"Dev server active at {server_url}. Launching Chromium...")
    overflow_errors = []
    captured_files = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            for vp in VIEWPORTS:
                vp_name = vp["name"]
                print(f"\n=======================================================")
                print(f"WALKTHROUGH AT VIEWPORT: {vp['width']}x{vp['height']} ({vp_name})")
                print(f"=======================================================")

                context = browser.new_context(
                    viewport={"width": vp["width"], "height": vp["height"]},
                    device_scale_factor=1,
                    is_mobile=vp["is_mobile"],
                )
                page = context.new_page()

                def capture(name: str):
                    time.sleep(0.5)  # allow dynamic components / fonts to settle
                    scroll_w = page.evaluate("() => document.documentElement.scrollWidth")
                    client_w = page.evaluate("() => document.documentElement.clientWidth")
                    if scroll_w > client_w:
                        msg = f"Overflow on {name} @ {vp_name}px: scrollWidth={scroll_w} > clientWidth={client_w} (+{scroll_w - client_w}px)"
                        print(f"  [OVERFLOW WARNING] {msg}")
                        overflow_errors.append(msg)

                    out_path = reports_dir / f"{name}_{vp_name}.png"
                    page.screenshot(path=str(out_path), full_page=True)
                    captured_files.append(out_path)
                    print(f"  Captured: {out_path.name} (scrollWidth={scroll_w}, clientWidth={client_w})")

                # 1. Home
                print("[1/13] Browsing Home...")
                page.goto(f"{server_url}/", wait_until="networkidle")
                capture("01_home")

                # 2. Category Monograph Spread
                print("[2/13] Browsing Category Monograph Spread...")
                page.goto(f"{server_url}/c/earphones-headphones/", wait_until="networkidle")
                capture("02_category_spread")

                # 3. Filtered Catalog Grid
                print("[3/13] Filtering Catalog Grid by Brand 'boat'...")
                page.goto(f"{server_url}/c/earphones-headphones/?brand=boat", wait_until="networkidle")
                capture("03_filtered_grid")

                # 4. Product Sheet
                print("[4/13] Viewing Product Detail Sheet...")
                product_url = f"{server_url}/p/boat-bassheads-100-in-ear-wired-headphones-with-mic-black-b071z8m4kx/"
                page.goto(product_url, wait_until="networkidle")
                capture("04_product_sheet")

                # 5. Add to Cart & View Cart
                print("[5/13] Adding Product to Cart...")
                # Submit the add-to-cart form directly via locator
                add_btn = page.locator("form[action*='/cart/add/'] button[type='submit']").first
                add_btn.click()
                time.sleep(1)

                page.goto(f"{server_url}/cart/", wait_until="networkidle")
                print("  Cart URL:", page.url)
                capture("05_cart")

                # 6. Checkout Start (Guest)
                print("[6/13] Entering Checkout as Guest...")
                page.goto(f"{server_url}/checkout/", wait_until="networkidle")
                print("  Checkout URL:", page.url)
                capture("06_checkout_start")

                # Check if on checkout start or redirected
                if "/checkout/" in page.url and "/address/" not in page.url:
                    guest_form = page.locator("form[action*='guest']")
                    if guest_form.count() > 0:
                        page.fill("input[name='full_name']", "Karan Sharma")
                        page.fill("input[name='email']", "customer.walkthrough@example.com")
                        page.fill("input[name='phone']", "9876543210")
                        guest_btn = page.locator("form[action*='guest'] button[type='submit']")
                        guest_btn.click()
                        page.wait_for_load_state("networkidle")
                        print("  After guest submit, URL:", page.url)

                # 7. Checkout Address
                print("[7/13] Filling Shipping Address... URL is:", page.url)
                capture("07_checkout_address")

                name_field = page.locator("input[name='full_name']")
                if name_field.count() > 0:
                    page.fill("input[name='full_name']", "Karan Sharma")
                    page.fill("input[name='phone']", "9876543210")
                    page.fill("input[name='line1']", "Flat 402, Monograph Heights, 12th Main")
                    page.fill("input[name='city']", "Bengaluru")
                    page.fill("input[name='pincode']", "560001")
                    page.select_option("select[name='state']", "Karnataka")
                    addr_btn = page.locator("form[action*='address'] button[type='submit']")
                    addr_btn.click()
                    page.wait_for_load_state("networkidle")
                    print("  After address submit, URL:", page.url)
                else:
                    print("  [ERROR] No name field on address page, current HTML snippet:")
                    print("  ", page.locator("body").inner_text()[:300].replace("\n", " "))

                # 8. Checkout Review
                print("[8/13] Reviewing Order and Selecting Payment...")
                capture("08_checkout_review")

                # Select COD and place order
                page.locator("input[value='cod']").check()
                place_btn = page.locator("form[action*='place'] button[type='submit']")
                place_btn.click()
                page.wait_for_load_state("networkidle")

                # 9. Order Confirmed
                print("[9/13] Order Confirmed / Receipt...")
                capture("09_order_confirmed")

                # Extract order number from URL
                cur_url = page.url
                order_num = None
                if "/orders/" in cur_url and "/success/" in cur_url:
                    parts = cur_url.split("/orders/")[1].split("/success/")[0]
                    order_num = parts.split("?")[0].strip("/")
                    print(f"  Order placed successfully: #{order_num}")

                # 10. Order Shipment Tracking Timeline
                if order_num:
                    print(f"[10/13] Viewing Shipment Tracking for Order #{order_num}...")
                    page.goto(f"{server_url}/orders/track/{order_num}/verify/", wait_until="networkidle")
                    capture("10_order_track_timeline")

                    # 11. GST Tax Invoice
                    print(f"[11/13] Viewing Statutory GST Invoice for Order #{order_num}...")
                    page.goto(f"{server_url}/orders/{order_num}/invoice/", wait_until="networkidle")
                    capture("11_order_invoice")
                else:
                    print(f"  [ERROR] Order placement failed, stayed at: {cur_url}")

                # 12. Customer Account Login
                print("[12/13] Customer Account Login...")
                page.goto(f"{server_url}/accounts/login/", wait_until="networkidle")
                capture("12_account_login")

                # 13. 404 Error Page
                print("[13/13] 404 Error Page...")
                page.goto(f"{server_url}/404-test-page/", wait_until="networkidle")
                capture("13_not_found")

                context.close()

            browser.close()

    finally:
        if server_process:
            server_process.terminate()
            server_process.wait()

    print("\n" + "=" * 70)
    print(f"WALKTHROUGH COMPLETE: {len(captured_files)} screenshots captured.")
    if overflow_errors:
        print(f"OVERFLOW ISSUES DETECTED ({len(overflow_errors)}):")
        for err in overflow_errors:
            print(f"  - {err}")
        return False
    else:
        print("PERFECT: Zero horizontal overflow defects across all viewports!")
        print(f"Screenshots saved to: {reports_dir}")
        print("=" * 70)
        return True


if __name__ == "__main__":
    success = run_customer_walkthrough()
    sys.exit(0 if success else 1)
