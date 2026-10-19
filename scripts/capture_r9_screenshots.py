#!/usr/bin/env python3
import os
import sys
import time
import subprocess
import urllib.request
from pathlib import Path

# Setup Django environment
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

import django
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.auth import BACKEND_SESSION_KEY, HASH_SESSION_KEY, SESSION_KEY
from apps.cart.services.cart_service import get_or_create_cart, add_to_cart
from apps.catalog.models import Product
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:8000"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "reports" / "screenshots" / "r9"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def wait_for_server(timeout=15):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(f"{BASE_URL}/", timeout=1) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.5)
    return False

def create_authenticated_session():
    User = get_user_model()
    admin_user = User.objects.filter(email="admin@gmail.com").first()
    if not admin_user:
        admin_user = User.objects.create_superuser("admin@gmail.com", "AdminPass123!", full_name="Admin User")
    
    session = SessionStore()
    session[SESSION_KEY] = str(admin_user.pk)
    session[BACKEND_SESSION_KEY] = 'django.contrib.auth.backends.ModelBackend'
    session[HASH_SESSION_KEY] = admin_user.get_session_auth_hash()
    
    # Populate a cart for this user
    cart = get_or_create_cart(user=admin_user)
    p = Product.objects.filter(is_available=True, selling_price__gt=0).first()
    if p:
        add_to_cart(cart, p, quantity=1)
        
    session["checkout_address"] = {
        "full_name": "Admin User",
        "phone": "9876543210",
        "address_line1": "101 Monograph High Street",
        "city": "Ahmedabad",
        "state": "Gujarat",
        "pincode": "380001",
    }
    session["pincode"] = "380001"
    session.save()
    return session.session_key

def main():
    print("Starting Django development server...")
    server = subprocess.Popen(
        [sys.executable, "manage.py", "runserver", "127.0.0.1:8000", "--noreload"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    
    try:
        if not wait_for_server():
            print("Failed to start Django server within timeout.")
            sys.exit(1)
        print("Server is up and responding!")

        session_key = create_authenticated_session()
        print(f"Created authenticated session: {session_key}")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            context.add_cookies([{
                "name": "sessionid",
                "value": session_key,
                "domain": "127.0.0.1",
                "path": "/",
                "httpOnly": True,
                "secure": False,
                "sameSite": "Lax",
            }])

            page = context.new_page()

            # 1. Homepage hero with thumbnails
            print("Capturing 01_homepage_hero.png...")
            page.goto(f"{BASE_URL}/", wait_until="networkidle")
            page.wait_for_timeout(1000)
            page.screenshot(path=str(OUTPUT_DIR / "01_homepage_hero.png"))

            # 2. PDP as authenticated user
            print("Capturing 02_pdp_authenticated.png...")
            pdp = Product.objects.filter(is_available=True, media__media_type="image", selling_price__gt=0).first()
            if pdp:
                page.goto(f"{BASE_URL}/p/{pdp.slug}/", wait_until="networkidle")
                page.wait_for_timeout(1000)
                page.screenshot(path=str(OUTPUT_DIR / "02_pdp_authenticated.png"))

            # 3. Compare rivals
            print("Capturing 03_compare_rivals.png...")
            page.goto(f"{BASE_URL}/compare/", wait_until="networkidle")
            page.wait_for_timeout(1000)
            page.screenshot(path=str(OUTPUT_DIR / "03_compare_rivals.png"))

            # 4. Search results with top horizontal bar
            print("Capturing 04_search_oppo_results.png...")
            page.goto(f"{BASE_URL}/search/?q=oppo", wait_until="networkidle")
            page.wait_for_timeout(1000)
            page.screenshot(path=str(OUTPUT_DIR / "04_search_oppo_results.png"))

            # 5. Shopping bag with Available Coupons and quantity stepper
            print("Capturing 05_cart_coupons_stepper.png...")
            page.goto(f"{BASE_URL}/cart/", wait_until="networkidle")
            page.wait_for_timeout(1000)
            page.screenshot(path=str(OUTPUT_DIR / "05_cart_coupons_stepper.png"))

            # 6. Checkout review with Available Coupons
            print("Capturing 06_checkout_review_coupons.png...")
            page.goto(f"{BASE_URL}/checkout/review/", wait_until="networkidle")
            page.wait_for_timeout(1000)
            page.screenshot(path=str(OUTPUT_DIR / "06_checkout_review_coupons.png"))

            # 7. Cancelled order page with crimson Order Cancelled banner
            print("Capturing 07_order_cancelled_page.png...")
            from apps.orders.models import Order
            canc_order = Order.objects.filter(status=Order.STATUS_CANCELLED).first()
            if canc_order:
                page.goto(f"{BASE_URL}/orders/{canc_order.order_number}/success/", wait_until="networkidle")
                page.wait_for_timeout(1000)
                page.screenshot(path=str(OUTPUT_DIR / "07_order_cancelled_page.png"))

            browser.close()
            print("All 7 screenshots successfully captured!")

    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
        print("Server stopped cleanly.")

if __name__ == "__main__":
    main()
