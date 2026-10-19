#!/usr/bin/env python3
"""
Captures baseline screenshots for WP0: Visual Truth Reset at 1456x820 and 390x844.
Saves to docs/ui-review/r4/before/
"""

import os
from pathlib import Path
import sys
import time

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from django.contrib.auth import get_user_model
from apps.catalog.models import Category, Product
from apps.orders.models import Order
from scripts.e2e_browser import ServerManager, find_free_port
from playwright.sync_api import sync_playwright

OUT_DIR = BASE_DIR / "docs" / "ui-review" / "r4" / "before"
OUT_DIR.mkdir(parents=True, exist_ok=True)

VIEWPORTS = [
    ("1456", {"width": 1456, "height": 820}),
    ("390", {"width": 390, "height": 844}),
]

def run_capture():
    port = find_free_port()
    server = ServerManager(port=port)
    server.start()
    base_url = f"http://127.0.0.1:{port}"

    try:
        p_instock = Product.objects.filter(is_available=True, inventory__quantity__gt=5).first()
        p_low = Product.objects.filter(is_available=True, inventory__quantity__lte=5, inventory__quantity__gt=0).first()
        p_unpriced = Product.objects.filter(selling_price__isnull=True).first()

        instock_slug = p_instock.slug if p_instock else "amazon-basics-flexible-premium-hdmi-cable-black-4k60hz-18gbps-3-foot-b07ksmbl2h"
        low_slug = p_low.slug if p_low else instock_slug
        unpriced_slug = p_unpriced.slug if p_unpriced else instock_slug

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            for vp_name, vp_size in VIEWPORTS:
                print(f"\n[*] Capturing baseline for viewport {vp_name} ({vp_size['width']}x{vp_size['height']})...")
                context = browser.new_context(viewport=vp_size)
                page = context.new_page()

                # --- 1. HOME PAGE ---
                page.goto(f"{base_url}/", wait_until="load")
                page.wait_for_timeout(1000)
                # top
                page.screenshot(path=str(OUT_DIR / f"home_top_{vp_name}.png"))

                # Chapters
                spreads = page.locator(".spread[data-world]")
                count = spreads.count()
                for i in range(min(count, 6)):
                    spread = spreads.nth(i)
                    spread.scroll_into_view_if_needed()
                    page.wait_for_timeout(400)
                    world = spread.get_attribute("data-world") or f"ch{i+1}"
                    page.screenshot(path=str(OUT_DIR / f"home_chapter_{i+1:02d}_{world}_{vp_name}.png"))

                # Typographic Index
                index_sec = page.locator(".category-index-section, #contents, section:has-text('Typographic Index'), section:has-text('Categories')").first
                if index_sec.count() > 0:
                    index_sec.scroll_into_view_if_needed()
                    page.wait_for_timeout(400)
                    page.screenshot(path=str(OUT_DIR / f"home_index_{vp_name}.png"))

                # Buying / How purchasing works
                buying_sec = page.locator("section:has-text('How Purchasing Works'), section:has-text('How purchasing works')").first
                if buying_sec.count() > 0:
                    buying_sec.scroll_into_view_if_needed()
                    page.wait_for_timeout(400)
                    page.screenshot(path=str(OUT_DIR / f"home_buying_{vp_name}.png"))

                # Brands
                brands_sec = page.locator("section:has-text('Curated hardware from'), section:has-text('Brands')").first
                if brands_sec.count() > 0:
                    brands_sec.scroll_into_view_if_needed()
                    page.wait_for_timeout(400)
                    page.screenshot(path=str(OUT_DIR / f"home_brands_{vp_name}.png"))

                # Footer
                footer = page.locator("footer, .site-footer").first
                if footer.count() > 0:
                    footer.scroll_into_view_if_needed()
                    page.wait_for_timeout(400)
                    page.screenshot(path=str(OUT_DIR / f"home_footer_{vp_name}.png"))

                # --- 2. /categories/ ---
                page.goto(f"{base_url}/categories/", wait_until="load")
                page.wait_for_timeout(500)
                page.screenshot(path=str(OUT_DIR / f"categories_{vp_name}.png"))

                # --- 3. THREE CATEGORY PAGES ---
                # A: marquee (page 1)
                page.goto(f"{base_url}/c/earphones-headphones/", wait_until="load")
                page.wait_for_timeout(500)
                page.screenshot(path=str(OUT_DIR / f"category_marquee_top_{vp_name}.png"))

                # marquee grid (scrolled past divider)
                divider = page.locator("h2:has-text('Listings'), #products-heading").first
                if divider.count() > 0:
                    divider.scroll_into_view_if_needed()
                    page.wait_for_timeout(600)
                else:
                    page.evaluate("() => window.scrollTo(0, 700)")
                    page.wait_for_timeout(600)
                page.screenshot(path=str(OUT_DIR / f"category_marquee_grid_{vp_name}.png"))

                # B: filtered
                page.goto(f"{base_url}/c/smartphones/?brand=OnePlus", wait_until="load")
                page.wait_for_timeout(500)
                page.screenshot(path=str(OUT_DIR / f"category_filtered_{vp_name}.png"))

                # C: page 2
                page.goto(f"{base_url}/c/earphones-headphones/?page=2", wait_until="load")
                page.wait_for_timeout(500)
                page.screenshot(path=str(OUT_DIR / f"category_page2_{vp_name}.png"))

                # --- 4. THREE PRODUCT PAGES ---
                page.goto(f"{base_url}/p/{instock_slug}/", wait_until="load")
                page.wait_for_timeout(500)
                page.screenshot(path=str(OUT_DIR / f"pdp_instock_{vp_name}.png"))

                page.goto(f"{base_url}/p/{low_slug}/", wait_until="load")
                page.wait_for_timeout(500)
                page.screenshot(path=str(OUT_DIR / f"pdp_lowstock_{vp_name}.png"))

                page.goto(f"{base_url}/p/{unpriced_slug}/", wait_until="load")
                page.wait_for_timeout(500)
                page.screenshot(path=str(OUT_DIR / f"pdp_unpriced_{vp_name}.png"))

                # --- 5. SEARCH ---
                page.goto(f"{base_url}/search/?q=cable", wait_until="load")
                page.wait_for_timeout(500)
                page.screenshot(path=str(OUT_DIR / f"search_{vp_name}.png"))

                # --- 6. CART (EMPTY & FILLED) ---
                page.goto(f"{base_url}/cart/", wait_until="load")
                page.wait_for_timeout(500)
                page.screenshot(path=str(OUT_DIR / f"cart_empty_{vp_name}.png"))

                # Add item to bag
                page.goto(f"{base_url}/p/{instock_slug}/", wait_until="load")
                add_btn = page.locator("button[type='submit']:has-text('Add to Bag'), button[type='submit']:has-text('Add to Shopping Bag')").first
                if add_btn.count() > 0:
                    add_btn.click()
                    page.wait_for_timeout(800)

                page.goto(f"{base_url}/cart/", wait_until="load")
                page.wait_for_timeout(500)
                page.screenshot(path=str(OUT_DIR / f"cart_filled_{vp_name}.png"))

                # --- 7. AUTH PAGES ---
                page.goto(f"{base_url}/accounts/login/", wait_until="load")
                page.wait_for_timeout(500)
                page.screenshot(path=str(OUT_DIR / f"login_{vp_name}.png"))

                page.goto(f"{base_url}/accounts/signup/", wait_until="load")
                page.wait_for_timeout(500)
                page.screenshot(path=str(OUT_DIR / f"signup_{vp_name}.png"))

                # --- 8. CHECKOUT STEPS ---
                # Step 1: Guest checkout
                page.goto(f"{base_url}/cart/", wait_until="load")
                proc_btn = page.locator("a:has-text('Proceed to Checkout')").first
                if proc_btn.count() > 0:
                    proc_btn.click()
                    page.wait_for_load_state("load")
                    page.wait_for_timeout(500)
                page.screenshot(path=str(OUT_DIR / f"checkout_start_{vp_name}.png"))

                # Fill guest details
                name_input = page.locator("#id-guest-name")
                if name_input.count() > 0:
                    name_input.fill("Gallery Reviewer")
                    page.locator("#id-guest-email").fill("reviewer@example.com")
                    page.locator("#id-guest-phone").fill("9876543210")
                    page.locator("button[type='submit']:has-text('Continue')").first.click()
                    page.wait_for_load_state("load")
                    page.wait_for_timeout(500)

                # Address step
                page.screenshot(path=str(OUT_DIR / f"checkout_address_{vp_name}.png"))

                addr_name = page.locator("#id-full-name")
                if addr_name.count() > 0:
                    addr_name.fill("Gallery Reviewer")
                    page.locator("#id-phone").fill("9876543210")
                    page.locator("#id-line1").fill("100 Exhibition Road")
                    page.locator("#id-city").fill("Ahmedabad")
                    page.locator("#id-pincode").fill("560001")
                    page.select_option("#id-state", "Gujarat")
                    page.locator("button[type='submit']:has-text('Review Order')").first.click()
                    page.wait_for_load_state("load")
                    page.wait_for_timeout(500)

                # Review step
                page.screenshot(path=str(OUT_DIR / f"checkout_review_{vp_name}.png"))

                # Place COD Order to capture real success page
                cod_radio = page.locator("input[value='cod']")
                if cod_radio.count() > 0:
                    cod_radio.check()
                place_btn = page.locator("button[type='submit']:has-text('Place Order')").first
                if place_btn.count() > 0:
                    place_btn.click()
                    page.wait_for_load_state("load")
                    page.wait_for_timeout(800)

                page.screenshot(path=str(OUT_DIR / f"order_success_{vp_name}.png"))

                # --- 9. ERROR PAGES ---
                page.goto(f"{base_url}/403-test/", wait_until="load")
                page.wait_for_timeout(500)
                page.screenshot(path=str(OUT_DIR / f"error_403_{vp_name}.png"))

                page.goto(f"{base_url}/404-test-page/", wait_until="load")
                page.wait_for_timeout(500)
                page.screenshot(path=str(OUT_DIR / f"error_404_{vp_name}.png"))

                context.close()

            browser.close()

        print(f"\n[+] Successfully saved baseline captures to {OUT_DIR}")
    finally:
        server.stop()

if __name__ == "__main__":
    run_capture()
