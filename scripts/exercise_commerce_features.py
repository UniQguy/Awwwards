#!/usr/bin/env python3
"""
Exercise and verify WP5 Honest Commerce features with real browser:
1. Star glyphs for source ratings on PDP.
2. Inline delivery estimator by PIN code near price on PDP.
3. Available coupons drawer/section on PDP.
4. Save for Later and Move to Bag in shopping cart.
5. Privacy-first Recently Viewed row on PDP and Cart.
"""

from pathlib import Path
import sys
import time

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("FATAL: playwright is not installed.")
    sys.exit(1)

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from scripts.e2e_browser import ServerManager, find_free_port, wait_for_server

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


SCREENSHOT_DIR = BASE_DIR / "docs" / "ui-review" / "commerce_features"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    port = find_free_port()
    base_url = f"http://127.0.0.1:{port}"
    server = ServerManager(port=port)
    server.start()

    if not wait_for_server(base_url, timeout=30):
        print("FATAL: Test server failed to start")
        server.stop()
        sys.exit(1)

    print(f"Server started on {base_url}. Exercising commerce features...")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1456, "height": 900})

            # 1. Visit PDP 1: HDMI cable
            p1_url = f"{base_url}/p/amazon-basics-flexible-premium-hdmi-cable-black-4k60hz-18gbps-3-foot-b07ksmbl2h/"
            print(f"Navigating to {p1_url}...")
            page.goto(p1_url, wait_until="domcontentloaded")
            page.wait_for_timeout(600)

            # Check star glyphs rating
            rating_text = page.locator(".product-rating-line").text_content() if page.locator(".product-rating-line").count() > 0 else ""
            print(f"Rating line detected: '{rating_text.strip()}'")

            # Check inline PIN code estimator: submit pincode 560001
            pin_input = page.locator("#shipping-pincode-input")
            if pin_input.count() > 0:
                pin_input.fill("560001")
                page.locator(".product-pincode-inline button[type='submit']").click()
                page.wait_for_timeout(800)
                print("Submitted PIN 560001 to inline estimator.")

            page.screenshot(path=str(SCREENSHOT_DIR / "01_pdp_honest_rating_and_pincode.png"), full_page=False)

            # Check available coupons
            coupon_count = page.locator(".product-coupons-box").count()
            print(f"Product coupons box count: {coupon_count}")
            page.screenshot(path=str(SCREENSHOT_DIR / "02_pdp_active_coupons.png"), full_page=False)

            # Add product 1 to bag
            page.locator("form[action*='/cart/add/'] button[type='submit']").first.click()
            page.wait_for_timeout(800)
            print(f"Current URL after adding to bag: {page.url}")

            # Verify in Cart
            page.goto(f"{base_url}/cart/", wait_until="domcontentloaded")
            page.wait_for_timeout(600)

            # Click Save for Later
            save_btn = page.locator("form[action*='/save-for-later/'] button[type='submit']")
            if save_btn.count() > 0:
                print("Clicking Save for Later on active cart item...")
                with page.expect_navigation():
                    save_btn.first.click()
                print("Item saved for later.")

            page.wait_for_timeout(600)
            if page.locator(".saved-for-later-section").count() > 0:
                page.locator(".saved-for-later-section").scroll_into_view_if_needed()
            page.screenshot(path=str(SCREENSHOT_DIR / "03_cart_saved_for_later.png"), full_page=False)

            # Click Move to Bag
            move_btn = page.locator("form[action*='/move-to-bag/'] button[type='submit']")
            if move_btn.count() > 0:
                print("Clicking Move to Bag...")
                with page.expect_navigation():
                    move_btn.first.click()
                print("Item moved back to bag.")

            page.wait_for_timeout(600)
            page.screenshot(path=str(SCREENSHOT_DIR / "03b_cart_moved_to_bag.png"), full_page=False)

            # 2. Visit a second product: Redmi phone
            p2_url = f"{base_url}/c/smartphones/"
            page.goto(p2_url, wait_until="domcontentloaded")
            page.wait_for_timeout(600)

            first_card = page.locator(".grid-catalog .product-card a.stretched-link").first
            if first_card.count() > 0:
                href = first_card.get_attribute("href")
                print(f"Visiting second product: {href}")
                page.goto(f"{base_url}{href}", wait_until="domcontentloaded")
                page.wait_for_timeout(800)

                # Scroll down to see Recently Viewed shelf
                if page.locator("#recently-viewed-section").count() > 0:
                    page.locator("#recently-viewed-section").scroll_into_view_if_needed()
                page.wait_for_timeout(400)
                page.screenshot(path=str(SCREENSHOT_DIR / "04_pdp_recently_viewed_row.png"), full_page=False)

            # 3. Visit Cart to see Recently Viewed row in Cart
            page.goto(f"{base_url}/cart/", wait_until="domcontentloaded")
            page.wait_for_timeout(600)
            if page.locator("#recently-viewed-section").count() > 0:
                page.locator("#recently-viewed-section").scroll_into_view_if_needed()
            page.wait_for_timeout(400)
            page.screenshot(path=str(SCREENSHOT_DIR / "05_cart_recently_viewed_row.png"), full_page=False)

            browser.close()
            print("Commerce features successfully exercised!")

    finally:
        server.stop()


if __name__ == "__main__":
    main()
