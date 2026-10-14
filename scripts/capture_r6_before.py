#!/usr/bin/env python3
"""
Captures baseline 'before' screenshots for Phase R6 across specified routes and viewports.
Saves images to docs/ui-review/r6/before/.
"""

import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from scripts.e2e_browser import ServerManager, find_free_port, wait_for_server

OUT_DIR = BASE_DIR / "docs" / "ui-review" / "r6" / "before"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def capture_all():
    port = find_free_port()
    base_url = f"http://127.0.0.1:{port}"
    server = ServerManager(port=port)
    server.start()

    if not wait_for_server(base_url, timeout=30):
        print("Failed to start server")
        server.stop()
        sys.exit(1)

    # Setup demo admin for admin_index screenshot
    os.environ["DEMO_ADMIN_EMAIL"] = "admin_r6_before@electrocart.local"
    os.environ["DEMO_ADMIN_PASSWORD"] = "AdminR6Before2026!"
    
    import django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
    django.setup()
    from django.core.management import call_command
    call_command("create_demo_admin")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            # Viewports to capture
            viewports = [
                ("1366x768", 1366, 768),
                ("390x844", 390, 844),
            ]

            for vp_name, width, height in viewports:
                vp_dir = OUT_DIR / vp_name
                vp_dir.mkdir(parents=True, exist_ok=True)
                context = browser.new_context(viewport={"width": width, "height": height})
                page = context.new_page()

                print(f"\n--- Capturing viewport: {vp_name} ---")

                # 1. Home Top
                page.goto(base_url, wait_until="networkidle")
                page.wait_for_timeout(800)
                page.screenshot(path=str(vp_dir / "01_home_top.png"))
                print(f"Captured: {vp_dir / '01_home_top.png'}")

                # 2. Home Chapters (scroll down through sections)
                chapters = page.locator("section.chapter-section, section[data-chapter], section.home-chapter")
                chap_count = chapters.count()
                for i in range(min(chap_count, 6)):
                    try:
                        chap = chapters.nth(i)
                        chap.scroll_into_view_if_needed()
                        page.wait_for_timeout(400)
                        page.screenshot(path=str(vp_dir / f"02_home_chapter_{i+1:02d}.png"))
                        print(f"Captured: {vp_dir / f'02_home_chapter_{i+1:02d}.png'}")
                    except Exception as e:
                        print(f"Error capturing chapter {i+1}: {e}")

                # 3. Home Footer
                page.locator("footer").scroll_into_view_if_needed()
                page.wait_for_timeout(400)
                page.screenshot(path=str(vp_dir / "03_home_footer.png"))
                print(f"Captured: {vp_dir / '03_home_footer.png'}")

                # 4. Categories Index
                page.goto(f"{base_url}/categories/", wait_until="networkidle")
                page.wait_for_timeout(600)
                page.screenshot(path=str(vp_dir / "04_categories.png"))
                print(f"Captured: {vp_dir / '04_categories.png'}")

                # 5. /c/smartphones/
                page.goto(f"{base_url}/c/smartphones/", wait_until="networkidle")
                page.wait_for_timeout(600)
                page.screenshot(path=str(vp_dir / "05_category_smartphones.png"))
                print(f"Captured: {vp_dir / '05_category_smartphones.png'}")

                # 6. /c/speakers/
                page.goto(f"{base_url}/c/speakers/", wait_until="networkidle")
                page.wait_for_timeout(600)
                page.screenshot(path=str(vp_dir / "06_category_speakers.png"))
                print(f"Captured: {vp_dir / '06_category_speakers.png'}")

                # 7. /c/cameras/?page=2
                page.goto(f"{base_url}/c/cameras/?page=2", wait_until="networkidle")
                page.wait_for_timeout(600)
                page.screenshot(path=str(vp_dir / "07_category_cameras_page2.png"))
                print(f"Captured: {vp_dir / '07_category_cameras_page2.png'}")

                # 8. Product Page
                pdp_url = f"{base_url}/p/amazon-basics-flexible-premium-hdmi-cable-black-4k60hz-18gbps-3-foot-b07ksmbl2h/"
                page.goto(pdp_url, wait_until="networkidle")
                page.wait_for_timeout(600)
                page.screenshot(path=str(vp_dir / "08_product_page.png"))
                print(f"Captured: {vp_dir / '08_product_page.png'}")

                # 9. Cart
                page.goto(f"{base_url}/cart/", wait_until="networkidle")
                page.wait_for_timeout(600)
                page.screenshot(path=str(vp_dir / "09_cart.png"))
                print(f"Captured: {vp_dir / '09_cart.png'}")

                # 10. Shop menu open
                page.goto(base_url, wait_until="networkidle")
                page.wait_for_timeout(500)
                shop_btn = page.locator("button:has-text('Shop'), a:has-text('Shop'), [aria-haspopup='true']")
                if shop_btn.count() > 0:
                    try:
                        shop_btn.first.click()
                        page.wait_for_timeout(500)
                    except Exception:
                        pass
                page.screenshot(path=str(vp_dir / "10_shop_menu_open.png"))
                print(f"Captured: {vp_dir / '10_shop_menu_open.png'}")

                # 11. Admin index
                page.goto(f"{base_url}/admin/login/?next=/admin/")
                page.wait_for_timeout(400)
                try:
                    page.fill("input[name='username']", "admin_r6_before@electrocart.local")
                    page.fill("input[name='password']", "AdminR6Before2026!")
                    page.click("input[type='submit']")
                    page.wait_for_load_state("networkidle")
                    page.wait_for_timeout(500)
                except Exception:
                    pass
                page.screenshot(path=str(vp_dir / "11_admin_index.png"))
                print(f"Captured: {vp_dir / '11_admin_index.png'}")

                # 12. Dev outbox
                page.goto(f"{base_url}/dev/outbox/", wait_until="networkidle")
                page.wait_for_timeout(400)
                page.screenshot(path=str(vp_dir / "12_dev_outbox.png"))
                print(f"Captured: {vp_dir / '12_dev_outbox.png'}")

                context.close()

            browser.close()
    finally:
        # Cleanup demo user
        from django.contrib.auth import get_user_model
        User = get_user_model()
        User.objects.filter(email="admin_r6_before@electrocart.local").delete()
        server.stop()
        print("\nAll before screenshots successfully captured!")


if __name__ == "__main__":
    capture_all()
