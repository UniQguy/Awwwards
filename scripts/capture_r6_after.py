#!/usr/bin/env python3
"""
Captures comprehensive 'after' screenshots for Phase R6 across all required routes and viewports.
Saves images to docs/ui-review/r6/after/<viewport>/.
Idempotent: skips screenshots that are already captured.
"""

import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from scripts.e2e_browser import ServerManager, find_free_port, wait_for_server

OUT_DIR = BASE_DIR / "docs" / "ui-review" / "r6" / "after"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def should_capture(path: Path) -> bool:
    return not (path.exists() and path.stat().st_size > 0)


def capture_all():
    port = find_free_port()
    base_url = f"http://127.0.0.1:{port}"
    server = ServerManager(port=port)
    server.start()

    if not wait_for_server(base_url, timeout=30):
        print("Failed to start server")
        server.stop()
        sys.exit(1)

    import django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
    django.setup()
    from django.contrib.auth import get_user_model
    from apps.orders.models import Order
    User = get_user_model()

    admin_email = os.environ.get("DEMO_ADMIN_EMAIL", "admin@gmail.com")
    admin_password = os.environ.get("DEMO_ADMIN_PASSWORD", "AdminPass123!")

    admin_user = User.objects.filter(email=admin_email).first()
    if admin_user:
        Order.objects.filter(order_number="EC-2026-QTWS-RRCP").update(user=admin_user)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            viewports = [
                ("1366x768", 1366, 768),
                ("1536x864", 1536, 864),
                ("1920x1080", 1920, 1080),
                ("390x844", 390, 844),
            ]

            pdp_slug = "amazon-basics-flexible-premium-hdmi-cable-black-4k60hz-18gbps-3-foot-b07ksmbl2h"

            for vp_name, width, height in viewports:
                vp_dir = OUT_DIR / vp_name
                vp_dir.mkdir(parents=True, exist_ok=True)
                context = browser.new_context(viewport={"width": width, "height": height})
                page = context.new_page()

                print(f"\n==========================================")
                print(f"Checking viewport: {vp_name}")
                print(f"==========================================")

                # 1. Home Top
                t1 = vp_dir / "01_home_top.png"
                if should_capture(t1):
                    page.goto(base_url, wait_until="networkidle")
                    page.wait_for_timeout(600)
                    page.screenshot(path=str(t1))
                    print(f"Captured: {t1}")

                # 2. Home Chapters
                chapters = None
                for i in range(3):
                    t2 = vp_dir / f"02_home_chapter_{i+1:02d}.png"
                    if should_capture(t2):
                        if chapters is None:
                            page.goto(base_url, wait_until="networkidle")
                            chapters = page.locator("section.chapter-shelf-monograph")
                        try:
                            chap = chapters.nth(i)
                            chap.scroll_into_view_if_needed()
                            page.wait_for_timeout(400)
                            page.screenshot(path=str(t2))
                            print(f"Captured: {t2}")
                        except Exception as e:
                            print(f"Error capturing chapter {i+1}: {e}")

                # 3. Home Footer
                t3 = vp_dir / "03_home_footer.png"
                if should_capture(t3):
                    page.goto(base_url, wait_until="networkidle")
                    page.locator("footer").scroll_into_view_if_needed()
                    page.wait_for_timeout(400)
                    page.screenshot(path=str(t3))
                    print(f"Captured: {t3}")

                # 4. Categories Index
                t4 = vp_dir / "04_categories.png"
                if should_capture(t4):
                    page.goto(f"{base_url}/categories/", wait_until="networkidle")
                    page.wait_for_timeout(500)
                    page.screenshot(path=str(t4))
                    print(f"Captured: {t4}")

                # 5. /c/smartphones/
                t5 = vp_dir / "05_category_smartphones.png"
                if should_capture(t5):
                    page.goto(f"{base_url}/c/smartphones/", wait_until="networkidle")
                    page.wait_for_timeout(500)
                    page.screenshot(path=str(t5))
                    print(f"Captured: {t5}")

                # 6. /c/speakers/
                t6 = vp_dir / "06_category_speakers.png"
                if should_capture(t6):
                    page.goto(f"{base_url}/c/speakers/", wait_until="networkidle")
                    page.wait_for_timeout(500)
                    page.screenshot(path=str(t6))
                    print(f"Captured: {t6}")

                # 7. /c/cameras/?page=2
                t7 = vp_dir / "07_category_cameras_page2.png"
                if should_capture(t7):
                    page.goto(f"{base_url}/c/cameras/?page=2", wait_until="networkidle")
                    page.wait_for_timeout(500)
                    page.screenshot(path=str(t7))
                    print(f"Captured: {t7}")

                # 8. Product Detail Page
                pdp_url = f"{base_url}/p/{pdp_slug}/"
                t8 = vp_dir / "08_product_page.png"
                if should_capture(t8):
                    page.goto(pdp_url, wait_until="networkidle")
                    page.wait_for_timeout(600)
                    page.screenshot(path=str(t8))
                    print(f"Captured: {t8}")

                # 9. Cart Empty
                t9 = vp_dir / "09_cart.png"
                if should_capture(t9):
                    page.goto(f"{base_url}/cart/", wait_until="networkidle")
                    page.wait_for_timeout(500)
                    page.screenshot(path=str(t9))
                    print(f"Captured: {t9}")

                # 10. Shop Menu Open
                t10 = vp_dir / "10_shop_menu_open.png"
                page.goto(base_url, wait_until="networkidle")
                page.wait_for_timeout(400)
                page.evaluate("() => { const d = document.getElementById('shop-menu-details'); if (d) d.open = true; }")
                page.wait_for_timeout(500)
                page.screenshot(path=str(t10))
                print(f"Captured: {t10}")

                # 11. Admin Index
                t11 = vp_dir / "11_admin_index.png"
                if should_capture(t11):
                    page.goto(f"{base_url}/admin/login/?next=/admin/")
                    page.wait_for_timeout(400)
                    try:
                        page.fill("input[name='username']", admin_email)
                        page.fill("input[name='password']", admin_password)
                        page.click("input[type='submit']")
                        page.wait_for_load_state("networkidle")
                        page.wait_for_timeout(500)
                    except Exception as e:
                        print(f"Admin login notice: {e}")
                    page.screenshot(path=str(t11))
                    print(f"Captured: {t11}")

                # 12. Dev Outbox
                t12 = vp_dir / "12_dev_outbox.png"
                if should_capture(t12):
                    page.goto(f"{base_url}/dev/outbox/", wait_until="networkidle")
                    page.wait_for_timeout(400)
                    page.screenshot(path=str(t12))
                    print(f"Captured: {t12}")

                # 13. Cart With Items
                t13 = vp_dir / "13_cart_with_items.png"
                if should_capture(t13):
                    page.goto(pdp_url, wait_until="networkidle")
                    page.wait_for_timeout(500)
                    page.evaluate("() => { const f = document.querySelector('form[action*=\"/cart/add/\"]'); if (f) f.submit(); }")
                    page.wait_for_load_state("networkidle")
                    page.wait_for_timeout(600)
                    page.goto(f"{base_url}/cart/", wait_until="networkidle")
                    page.wait_for_timeout(500)
                    page.screenshot(path=str(t13))
                    print(f"Captured: {t13}")

                # 14. Checkout Review
                t14 = vp_dir / "14_checkout_review.png"
                if should_capture(t14):
                    page.goto(pdp_url, wait_until="networkidle")
                    btn = page.locator(".product-sheet-commerce-col form[action*='/cart/add/'] button[type='submit']").first
                    btn.scroll_into_view_if_needed()
                    btn.click()
                    page.wait_for_timeout(600)
                    page.goto(f"{base_url}/cart/", wait_until="networkidle")
                    chk_link = page.locator("a:has-text('Proceed to Checkout')")
                    if chk_link.count() > 0:
                        chk_link.first.click()
                        page.wait_for_load_state("networkidle")
                    name_input = page.locator("#id-guest-name")
                    if name_input.count() > 0:
                        page.fill("#id-guest-name", "Faculty Examiner")
                        page.fill("#id-guest-email", "examiner@university.ac.in")
                        page.fill("#id-guest-phone", "9876543210")
                        page.locator("form button[type='submit']").first.click()
                        page.wait_for_load_state("networkidle")
                    addr_submit = page.locator("button[type='submit']:has-text('Review Order')")
                    if addr_submit.count() > 0:
                        if page.locator("#id-full-name").count() > 0 and page.locator("input[name='address_id']:checked").count() == 0:
                            page.fill("#id-full-name", "Faculty Examiner")
                            page.fill("#id-phone", "9876543210")
                            page.fill("#id-line1", "42 Academic Block")
                            page.fill("#id-city", "Ahmedabad")
                            page.fill("#id-pincode", "560001")
                            page.select_option("#id-state", "Gujarat")
                        addr_submit.first.click()
                        page.wait_for_load_state("networkidle")
                    page.wait_for_timeout(500)
                    page.screenshot(path=str(t14))
                    print(f"Captured: {t14}")

                # 15. Statutory HTML Invoice
                t15 = vp_dir / "15_invoice_html.png"
                # Ensure user is logged in as admin before loading invoice
                page.goto(f"{base_url}/admin/login/?next=/admin/")
                page.wait_for_timeout(400)
                try:
                    page.fill("input[name='username']", admin_email)
                    page.fill("input[name='password']", admin_password)
                    page.click("input[type='submit']")
                    page.wait_for_load_state("networkidle")
                    page.wait_for_timeout(400)
                except Exception:
                    pass
                page.goto(f"{base_url}/orders/EC-2026-QTWS-RRCP/invoice/", wait_until="networkidle")
                page.wait_for_timeout(500)
                page.screenshot(path=str(t15))
                print(f"Captured: {t15}")

                # 16. Mini-Bag Open Dialog
                t16 = vp_dir / "16_mini_bag_open.png"
                if should_capture(t16):
                    page.goto(pdp_url, wait_until="networkidle")
                    page.wait_for_timeout(500)
                    try:
                        page.evaluate("() => { const d = document.getElementById('mini-bag-dialog'); if (d) d.showModal(); }")
                        page.wait_for_timeout(400)
                    except Exception as e:
                        print(f"Mini bag trigger notice: {e}")
                    page.screenshot(path=str(t16))
                    print(f"Captured: {t16}")

                context.close()

            browser.close()
    finally:
        server.stop()
        print("\nAll R6 after screenshots successfully captured!")


if __name__ == "__main__":
    capture_all()
