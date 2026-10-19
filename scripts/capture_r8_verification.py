from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:8000"
OUTPUT_DIR = Path("reports/screenshots/r8")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for vp in [
            {"name": "1366x768", "width": 1366, "height": 768},
            {"name": "1920x1080", "width": 1920, "height": 1080},
        ]:
            v_name = vp["name"]
            context = browser.new_context(viewport={"width": vp["width"], "height": vp["height"]})
            page = context.new_page()

            # 1. Mega-Menu Preview
            print(f"[{v_name}] 1. Mega menu...")
            page.goto(f"{BASE_URL}/", wait_until="commit", timeout=15000)
            page.wait_for_timeout(1500)
            shop_summary = page.locator("#shop-menu-details summary")
            if shop_summary.is_visible():
                shop_summary.click()
                page.wait_for_timeout(600)
            page.screenshot(path=str(OUTPUT_DIR / f"01_mega_menu_{v_name}.png"))

            # 2. Homepage Hero & Desk Builder
            print(f"[{v_name}] 2. Homepage...")
            page.goto(f"{BASE_URL}/", wait_until="commit", timeout=15000)
            page.wait_for_timeout(1500)
            page.screenshot(path=str(OUTPUT_DIR / f"02_homepage_hero_{v_name}.png"))
            desk_section = page.locator("#desk-bundle-chapter")
            if desk_section.count() > 0:
                desk_section.scroll_into_view_if_needed()
                page.wait_for_timeout(800)
                page.screenshot(path=str(OUTPUT_DIR / f"02_homepage_desk_builder_{v_name}.png"))

            # 3. Spec Comparison Tray
            print(f"[{v_name}] 3. Spec comparison...")
            page.goto(f"{BASE_URL}/p/redmi-9-sporty-orange-4gb-ram-64gb-storage-b08696w3b3/", wait_until="commit", timeout=15000)
            page.wait_for_timeout(800)
            page.locator("form.compare-form button[type='submit']").first.click()
            page.wait_for_timeout(800)

            page.goto(f"{BASE_URL}/p/redmi-9a-sport-carbon-black-2gb-ram-32gb-storage-b09gfm8cgs/", wait_until="commit", timeout=15000)
            page.wait_for_timeout(800)
            page.locator("form.compare-form button[type='submit']").first.click()
            page.wait_for_timeout(800)

            page.goto(f"{BASE_URL}/compare/", wait_until="commit", timeout=15000)
            page.wait_for_timeout(1000)
            page.screenshot(path=str(OUTPUT_DIR / f"03_spec_comparison_{v_name}.png"))

            # 4. Guest COD OTP Checkout Flow
            print(f"[{v_name}] 4. Guest COD OTP checkout...")
            # Navigate to product page and add to bag
            page.goto(f"{BASE_URL}/p/redmi-9-sporty-orange-4gb-ram-64gb-storage-b08696w3b3/", wait_until="commit", timeout=15000)
            page.wait_for_timeout(800)
            page.locator("form[action*='/cart/add/'] button[type='submit']").first.click()
            page.wait_for_timeout(1200)

            # Go to cart
            page.goto(f"{BASE_URL}/cart/", wait_until="commit", timeout=15000)
            page.wait_for_timeout(1000)
            
            # Click proceed to checkout
            proceed_btn = page.locator("a:has-text('Proceed to Checkout')")
            if proceed_btn.count() > 0:
                proceed_btn.first.click()
                page.wait_for_timeout(1000)
            else:
                page.goto(f"{BASE_URL}/checkout/", wait_until="commit", timeout=15000)
                page.wait_for_timeout(1000)

            print(f"[{v_name}] On checkout page: {page.url}")

            # Fill guest contact if on checkout_start
            if "checkout" in page.url and page.locator("#id-guest-name").count() > 0:
                page.locator("#id-guest-name").fill("Dr Faculty Reviewer")
                page.locator("#id-guest-email").fill("guest.faculty@example.com")
                page.locator("#id-guest-phone").fill("9876543210")
                page.locator("button:has-text('Continue to Delivery Address')").click()
                page.wait_for_timeout(1200)

            # Fill delivery address if on address step
            if page.locator("#id-line1").count() > 0:
                page.locator("#id-full-name").fill("Dr Faculty Reviewer")
                page.locator("#id-phone").fill("9876543210")
                page.locator("#id-line1").fill("Faculty Chamber, Engineering Dept")
                page.locator("#id-city").fill("Ahmedabad")
                page.locator("#id-pincode").fill("380015")
                page.locator("#id-state").select_option("Gujarat")
                page.locator("button:has-text('Review Order & Select Payment')").click()
                page.wait_for_timeout(1200)

            # Review & Pay: select COD
            cod_radio = page.locator("#pay-cod")
            if cod_radio.count() > 0 and cod_radio.is_enabled():
                cod_radio.check()
                page.wait_for_timeout(500)
                page.locator("button:has-text('Place Order')").click()
                page.wait_for_timeout(1500)

            print(f"[{v_name}] Final Checkout OTP page URL: {page.url}")
            page.screenshot(path=str(OUTPUT_DIR / f"04_guest_cod_otp_{v_name}.png"))

            # 5. Guest Order Tracking & Self-Serve Cancellation
            print(f"[{v_name}] 5. Order tracking & cancellation...")
            page.goto(f"{BASE_URL}/orders/track/", wait_until="commit", timeout=15000)
            page.wait_for_timeout(800)
            page.locator("#id-track-order-num").fill("EC-2026-5JDT-PX9H")
            page.locator("#id-track-contact").fill("admin@gmail.com")
            page.locator("button:has-text('Track Shipment')").click()
            page.wait_for_timeout(1500)

            print(f"[{v_name}] Tracking page URL: {page.url}")
            page.screenshot(path=str(OUTPUT_DIR / f"05_guest_order_tracking_{v_name}.png"))

            context.close()

        browser.close()
    print("All verification screenshots completed successfully.")

if __name__ == "__main__":
    run()
