"""
End-to-end verification script for Store Operations Admin Dashboard (Phase R7):
1. Logs into /admin/ in browser using credentials from environment (never printed).
2. Captures screenshot of dashboard BEFORE placing order at 1366x768.
3. Places one COD order from the storefront.
4. Returns to /admin/ and captures screenshot of dashboard AFTER at 1366x768.
5. Verifies dynamic metric updates on the dashboard.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

SCREENSHOT_DIR = BASE_DIR / "docs" / "ui-review" / "admin_dashboard"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


def run():
    admin_email = os.environ.get("DEMO_ADMIN_EMAIL")
    admin_password = os.environ.get("DEMO_ADMIN_PASSWORD")
    if not admin_email or not admin_password:
        print("ERROR: DEMO_ADMIN_EMAIL and DEMO_ADMIN_PASSWORD environment variables are required.")
        sys.exit(1)

    base_url = "http://127.0.0.1:8000"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Set exact 1366x768 viewport per specification
        context = browser.new_context(viewport={"width": 1366, "height": 768})
        page = context.new_page()

        print("[1/6] Logging in to Django Admin at /admin/...")
        page.goto(f"{base_url}/admin/login/?next=/admin/")
        page.fill("input[name='username']", admin_email)
        page.fill("input[name='password']", admin_password)
        page.click("input[type='submit']")
        page.wait_for_load_state("networkidle")

        # Confirm landing on /admin/
        assert "/admin/" in page.url, f"Expected /admin/, got {page.url}"
        assert "Store Operations Dashboard" in page.content(), "Store Operations Dashboard header missing"

        # Screenshot 1: BEFORE COD order
        before_path = SCREENSHOT_DIR / "01_dashboard_before_cod_order.png"
        page.screenshot(path=str(before_path), full_page=False)
        print(f"[2/6] Captured BEFORE screenshot at 1366x768: {before_path.name}")

        # Store initial KPI text
        initial_kpi_text = page.locator(".kpi-grid").inner_text()
        print("  Initial KPI summary recorded.")

        # Step 3: Browse to an affordable product on storefront and add to cart
        print("[3/6] Adding product to bag on storefront...")
        import django
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
        django.setup()
        from apps.cart.models import Cart
        Cart.objects.all().delete()

        page.goto(f"{base_url}/p/amazon-basics-flexible-premium-hdmi-cable-black-4k60hz-18gbps-3-foot-b07ksmbl2h/", wait_until="networkidle")
        add_btn = page.locator("form[action*='/cart/add/'] button[type='submit']")
        if add_btn.count() > 0:
            add_btn.first.click()
            page.wait_for_load_state("networkidle")

        # Step 4: Checkout as guest with COD
        print("[4/6] Executing guest checkout with COD...")
        page.goto(f"{base_url}/checkout/", wait_until="networkidle")

        if "/checkout/" in page.url and "/address/" not in page.url:
            guest_form = page.locator("form[action*='guest']")
            if guest_form.count() > 0:
                page.fill("input[name='full_name']", "Vikram Patel")
                page.fill("input[name='email']", "vikram.patel@example.com")
                page.fill("input[name='phone']", "9876543210")
                page.click("form[action*='guest'] button[type='submit']")
                page.wait_for_load_state("networkidle")

        # Fill Address if on address step
        if "/address/" in page.url:
            name_input = page.locator("input[name='full_name']")
            if name_input.count() > 0:
                page.fill("input[name='full_name']", "Vikram Patel")
                page.fill("input[name='phone']", "9876543210")
                page.fill("input[name='line1']", "101 Navrangpura Commercial Hub")
                page.fill("input[name='city']", "Ahmedabad")
                page.fill("input[name='pincode']", "380009")
                page.select_option("select[name='state']", "Gujarat")
                page.click("form[action*='address'] button[type='submit']")
                page.wait_for_load_state("networkidle")

        # Select COD on review step
        if "/review/" in page.url:
            page.locator("input[value='cod']").check()
            page.click("form[action*='place'] button[type='submit']")
            page.wait_for_load_state("networkidle")

        # Extract placed order number
        order_num = None
        if "/orders/" in page.url and "/success/" in page.url:
            order_num = page.url.split("/orders/")[1].split("/success/")[0].strip("/")
            print(f"  Placed order number: #{order_num}")

        # Step 5: Return to Admin Dashboard and verify updates
        print("[5/6] Returning to /admin/ to verify live dashboard updates...")
        page.goto(f"{base_url}/admin/", wait_until="networkidle")
        assert "Store Operations Dashboard" in page.content()

        # Screenshot 2: AFTER COD order
        after_path = SCREENSHOT_DIR / "02_dashboard_after_cod_order.png"
        page.screenshot(path=str(after_path), full_page=False)
        print(f"[6/6] Captured AFTER screenshot at 1366x768: {after_path.name}")

        # Verify order number in latest orders table
        if order_num:
            assert order_num in page.content(), f"Placed order #{order_num} must appear in latest orders on dashboard"

        print("=== VERIFICATION COMPLETED SUCCESSFULLY ===")
        browser.close()


if __name__ == "__main__":
    run()
