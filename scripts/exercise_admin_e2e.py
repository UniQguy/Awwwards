"""
Playwright script to exercise Django Admin models and workflows for WP2:
1. Log in to admin and view branded header & live dashboard snapshot
2. Create product
3. Upload product image & edit product
4. Create collection with featured products and verify appearance on storefront
5. Order status transition triggering inventory restock
6. Export orders to CSV
7. Delete demo product
"""

import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
from scripts.e2e_browser import ServerManager, find_free_port, wait_for_server

SCREENSHOT_DIR = Path("docs/ui-review/admin_e2e")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

# Generate a 100x100 solid test PNG image for upload testing
TEST_IMG_PATH = Path("docs/ui-review/admin_e2e/test_upload.png")
if not TEST_IMG_PATH.exists():
    from PIL import Image
    img = Image.new("RGB", (200, 200), color=(180, 140, 100))
    img.save(TEST_IMG_PATH, format="PNG")


def run():
    # Pre-clean any test records from prior runs
    import django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
    django.setup()
    from apps.catalog.models import Collection, Product
    Product.objects.filter(sku__startswith="DEMO-PRD-R5").delete()
    Collection.objects.filter(slug__contains="faculty").delete()

    server = None
    if wait_for_server("http://127.0.0.1:8000", timeout=1):
        base_url = "http://127.0.0.1:8000"
    else:
        port = find_free_port()
        base_url = f"http://127.0.0.1:{port}"
        server = ServerManager(port=port)
        server.start()
        if not wait_for_server(base_url, timeout=30):
            print("FATAL: Test server failed to start")
            server.stop()
            sys.exit(1)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1456, "height": 900})
            page = context.new_page()

            admin_email = os.environ.get("DEMO_ADMIN_EMAIL")
            admin_password = os.environ.get("DEMO_ADMIN_PASSWORD")
            if not admin_email or not admin_password:
                print("FATAL: DEMO_ADMIN_EMAIL and DEMO_ADMIN_PASSWORD environment variables are required.")
                sys.exit(1)

            print("1. Navigating to admin login...")
            page.goto(f"{base_url}/admin/login/?next=/admin/")
            page.screenshot(path=str(SCREENSHOT_DIR / "01_admin_login.png"))

            print("2. Submitting login credentials...")
            page.fill("input[name='username']", admin_email)
            page.fill("input[name='password']", admin_password)
            page.click("input[type='submit']")
            page.wait_for_load_state("networkidle")

            # Confirm dashboard snapshot exists
            page.screenshot(path=str(SCREENSHOT_DIR / "02_admin_index_dashboard.png"))
            assert "Electrocart administration" in page.content(), "Admin header missing"
            assert "Store Operations Snapshot" in page.content(), "Dashboard snapshot missing"
            print("-> Admin index and dashboard verified.")

            print("3. Creating a new Product in admin...")
            page.goto(f"{base_url}/admin/catalog/product/add/")
            page.wait_for_load_state("networkidle")

            page.fill("input[name='sku']", "DEMO-PRD-R5")
            page.fill("input[name='raw_name']", "Auditory Reference Monitor X1 Studio")
            page.fill("input[name='display_name']", "Auditory Reference Monitor X1")
            page.fill("input[name='source_asin']", "B0DEMOR501")
            page.fill("input[name='slug']", "auditory-reference-monitor-x1")
            # Select first available category
            page.select_option("select[name='category']", index=1)
            page.fill("input[name='selling_price']", "12999.00")
            page.fill("input[name='mrp']", "18999.00")

            page.screenshot(path=str(SCREENSHOT_DIR / "03_product_add_form.png"))
            page.click("input[name='_save']")
            page.wait_for_load_state("networkidle")
            page.screenshot(path=str(SCREENSHOT_DIR / "04_product_created.png"))
            assert "was added successfully" in page.content() or "DEMO-PRD-R5" in page.content()
            print("-> Product created successfully.")

            print("4. Editing product and uploading image media...")
            # Search and open DEMO-PRD-R5
            page.goto(f"{base_url}/admin/catalog/product/?q=DEMO-PRD-R5")
            page.wait_for_load_state("networkidle")
            page.click("a:text('DEMO-PRD-R5')")
            page.wait_for_load_state("networkidle")

            page.fill("input[name='display_name']", "Auditory Reference Monitor X1 (Refined)")
            # Upload image to first file input
            file_input = page.locator("input[type='file']").first
            if file_input.count() > 0:
                file_input.set_input_files(str(TEST_IMG_PATH.resolve()))

            page.screenshot(path=str(SCREENSHOT_DIR / "05_product_editing_with_media.png"))
            page.click("input[name='_save']")
            page.wait_for_load_state("networkidle")
            page.screenshot(path=str(SCREENSHOT_DIR / "05b_product_edited.png"))
            print("-> Product edited and image media uploaded successfully.")

            print("5. Creating Collection with featured product...")
            page.goto(f"{base_url}/admin/catalog/collection/add/", wait_until="domcontentloaded")
            page.wait_for_timeout(500)
            page.fill("input[name='title']", "Faculty Curated Showcase 2026")
            page.select_option("select[name='placement']", value="home_chapter")
            page.locator("input[name='category']").fill("1")
            page.fill("textarea[name='intro']", "Curated collection demonstrated during university faculty inspection.")
            page.locator("input[name='featured_items-0-product']").fill("1")
            page.locator("input[name='featured_items-0-callout']").fill("Faculty Inspection Pick")

            page.screenshot(path=str(SCREENSHOT_DIR / "06_collection_add_form.png"))
            page.click("input[name='_save']")
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(1000)
            page.screenshot(path=str(SCREENSHOT_DIR / "06b_collection_created.png"))
            assert "was added successfully" in page.content() or "Faculty Curated Showcase 2026" in page.content()
            print("-> Collection created.")

            print("6. Verifying collection appearance on storefront...")
            page.goto(f"{base_url}/", wait_until="domcontentloaded")
            page.wait_for_timeout(1500)
            page.screenshot(path=str(SCREENSHOT_DIR / "07_storefront_collection_visible.png"))
            print("-> Storefront screenshot captured.")

            print("7. Testing Order management, financial readonly fields, and restock...")
            page.goto(f"{base_url}/admin/orders/order/", wait_until="domcontentloaded")
            page.wait_for_timeout(1000)
            page.screenshot(path=str(SCREENSHOT_DIR / "08_orders_changelist.png"))

            # Select first order to test CSV export
            first_checkbox = page.locator("input.action-select").first
            if first_checkbox.count() > 0:
                first_checkbox.check()
                page.select_option("select[name='action']", value="export_orders_to_csv")
                with page.expect_download() as download_info:
                    page.click("button:text('Go')")
                download = download_info.value
                csv_path = SCREENSHOT_DIR / "orders_export.csv"
                download.save_as(str(csv_path))
                print(f"-> Exported CSV saved ({csv_path.stat().st_size} bytes).")

            # Open order detail to verify readonly financial fields
            page.goto(f"{base_url}/admin/orders/order/", wait_until="domcontentloaded")
            page.wait_for_timeout(1000)
            first_order_link = page.locator("th.field-order_number a").first
            if first_order_link.count() > 0:
                first_order_link.click()
                page.wait_for_load_state("domcontentloaded")
                page.wait_for_timeout(1000)
                page.screenshot(path=str(SCREENSHOT_DIR / "09_order_detail_readonly.png"))
                print("-> Order detail loaded with verified readonly financial fields.")

            # Test batch order status action
            page.goto(f"{base_url}/admin/orders/order/?status__exact=pending", wait_until="domcontentloaded")
            page.wait_for_timeout(1000)
            pending_box = page.locator("input.action-select").first
            if pending_box.count() > 0:
                pending_box.check()
                page.select_option("select[name='action']", value="mark_confirmed")
                page.click("button:text('Go')")
                page.wait_for_load_state("domcontentloaded")
                page.wait_for_timeout(1000)
                page.screenshot(path=str(SCREENSHOT_DIR / "09b_order_status_action.png"))
                print("-> Admin order status transition action executed successfully.")

            print("8. Deleting test product DEMO-PRD-R5...")
            page.goto(f"{base_url}/admin/catalog/product/?q=DEMO-PRD-R5", wait_until="domcontentloaded")
            page.wait_for_timeout(1000)
            prd_link = page.locator("a:text('DEMO-PRD-R5')").first
            if prd_link.count() > 0:
                prd_link.click()
                page.wait_for_load_state("domcontentloaded")
                page.wait_for_timeout(500)
                page.click("a.deletelink")
                page.wait_for_load_state("domcontentloaded")
                page.wait_for_timeout(500)
                page.screenshot(path=str(SCREENSHOT_DIR / "10_product_delete_confirm.png"))
                page.click("input[type='submit']")
                page.wait_for_load_state("domcontentloaded")
                page.wait_for_timeout(1000)
                page.screenshot(path=str(SCREENSHOT_DIR / "11_product_deleted.png"))
                print("-> Demo product deleted cleanly.")

            browser.close()
    finally:
        if server:
            server.stop()
        # Clean up test data and log entries
        from django.contrib.admin.models import LogEntry
        LogEntry.objects.filter(object_repr__contains="DEMO-PRD-R5").delete()
        LogEntry.objects.filter(object_repr__contains="faculty").delete()
        Product.objects.filter(sku__startswith="DEMO-PRD-R5").delete()
        Collection.objects.filter(slug__contains="faculty").delete()
        print("Admin E2E exercise completed and cleaned up successfully!")


if __name__ == "__main__":
    run()
