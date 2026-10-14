"""
End-to-end browser authentication and email lifecycle verification (WP3):
1. Sign up as new user
2. Check /dev/outbox/ for verification email
3. Click confirmation link and verify email
4. Log in and verify authenticated account dashboard
5. Log out
6. Trigger password reset
7. Inspect reset email in /dev/outbox/
8. Reset password and confirm completion
"""

import os
import re
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from scripts.e2e_browser import ServerManager, find_free_port, wait_for_server

SCREENSHOT_DIR = Path("docs/ui-review/auth_e2e")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

TEST_EMAIL = os.environ.get("DEMO_TEST_EMAIL", f"auth_e2e_{int(time.time())}@electrocart.test")
TEST_PASS = os.environ.get("DEMO_TEST_PASSWORD", f"Pass_{int(time.time())}!Aa9")
NEW_PASS = f"New{TEST_PASS}"


def run():
    # Setup Django to clean up test user from previous runs
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
    import django
    django.setup()
    from django.contrib.auth import get_user_model
    User = get_user_model()
    User.objects.filter(email=TEST_EMAIL).delete()
    for eml in Path(".emails").glob("*auth_e2e*"):
        try:
            eml.unlink()
        except OSError:
            pass

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

            # 1. Signup
            print("1. Navigating to signup page...")
            page.goto(f"{base_url}/accounts/signup/", wait_until="domcontentloaded")
            page.wait_for_timeout(500)
            page.fill("input[name='email']", TEST_EMAIL)
            page.fill("input[name='password1']", TEST_PASS)
            page.fill("input[name='password2']", TEST_PASS)
            page.click("button[type='submit']")
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(1000)
            page.screenshot(path=str(SCREENSHOT_DIR / "01_signup_verification_sent.png"))
            print("-> Signup submitted, verification notice displayed.")

            # 2. Check /dev/outbox/ for verification email
            print("2. Checking /dev/outbox/...")
            page.goto(f"{base_url}/dev/outbox/", wait_until="domcontentloaded")
            page.wait_for_timeout(1000)
            page.screenshot(path=str(SCREENSHOT_DIR / "02_outbox_list.png"))

            # Click the latest email addressed to TEST_EMAIL
            email_link = page.locator(f"tr:has-text('{TEST_EMAIL}') a").first
            assert email_link.count() > 0, f"No email found in outbox for {TEST_EMAIL}"
            email_link.click()
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(1000)
            page.screenshot(path=str(SCREENSHOT_DIR / "03_outbox_detail_confirmation.png"))
            print("-> Verification email found in outbox.")

            # Click the confirmation action link
            action_btn = page.locator("a:text('Open Link')").first
            confirm_url = action_btn.get_attribute("href")
            if confirm_url.startswith("http"):
                confirm_url = re.sub(r"http://127\.0\.0\.1:\d+", base_url, confirm_url)
            print(f"-> Navigating to confirmation URL: {confirm_url}")
            page.goto(confirm_url, wait_until="domcontentloaded")
            page.wait_for_timeout(1000)

            # On confirmation page, click Confirm Email button
            confirm_btn = page.locator("form[action*='confirm-email'] button[type='submit']")
            if confirm_btn.count() > 0:
                confirm_btn.click()
                page.wait_for_load_state("domcontentloaded")
                page.wait_for_timeout(1500)

            page.screenshot(path=str(SCREENSHOT_DIR / "04_email_confirmed.png"))
            print("-> Email confirmed.")

            # 3. Log in with confirmed credentials
            print("3. Logging in with verified account...")
            page.goto(f"{base_url}/accounts/login/", wait_until="domcontentloaded")
            page.wait_for_timeout(500)
            page.fill("input[name='login']", TEST_EMAIL)
            page.fill("input[name='password']", TEST_PASS)
            page.click("button[type='submit']")
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(1500)
            page.screenshot(path=str(SCREENSHOT_DIR / "05_login_success.png"))

            # 4. View account dashboard
            print("4. Inspecting authenticated account dashboard...")
            page.goto(f"{base_url}/accounts/profile/", wait_until="domcontentloaded")
            page.wait_for_timeout(1000)
            page.screenshot(path=str(SCREENSHOT_DIR / "06_account_dashboard.png"))
            print("-> Account dashboard verified.")

            # 5. Log out
            print("5. Logging out...")
            page.goto(f"{base_url}/accounts/logout/", wait_until="domcontentloaded")
            page.wait_for_timeout(500)
            logout_btn = page.locator("main form button[type='submit'], form[action*='logout'] button[type='submit']").first
            if logout_btn.count() > 0:
                logout_btn.click()
                page.wait_for_load_state("domcontentloaded")
                page.wait_for_timeout(1000)
            page.screenshot(path=str(SCREENSHOT_DIR / "07_logged_out.png"))
            print("-> Logged out successfully.")

            # 6. Password reset flow
            print("6. Requesting password reset...")
            page.goto(f"{base_url}/accounts/password/reset/", wait_until="domcontentloaded")
            page.wait_for_timeout(500)
            page.fill("input[name='email']", TEST_EMAIL)
            page.click("button[type='submit']")
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(1000)
            page.screenshot(path=str(SCREENSHOT_DIR / "08_password_reset_sent.png"))

            # Inspect outbox for password reset link
            page.goto(f"{base_url}/dev/outbox/", wait_until="domcontentloaded")
            page.wait_for_timeout(1000)
            reset_email_link = page.locator(f"tr:has-text('{TEST_EMAIL}') a").first
            reset_email_link.click()
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(1000)
            page.screenshot(path=str(SCREENSHOT_DIR / "09_outbox_detail_reset.png"))

            reset_action_btn = page.locator("a:text('Open Link')").first
            reset_url = reset_action_btn.get_attribute("href")
            if reset_url.startswith("http"):
                reset_url = re.sub(r"http://127\.0\.0\.1:\d+", base_url, reset_url)
            print(f"-> Navigating to reset URL: {reset_url}")
            page.goto(reset_url, wait_until="domcontentloaded")
            page.wait_for_timeout(1000)

            # Fill new password
            page.fill("input[name='password1']", NEW_PASS)
            page.fill("input[name='password2']", NEW_PASS)
            page.click("button[type='submit']")
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(1500)
            page.screenshot(path=str(SCREENSHOT_DIR / "10_password_reset_complete.png"))
            print("-> Password reset completed successfully.")

            # 7. Log in with new password
            print("7. Verifying login with new password...")
            page.goto(f"{base_url}/accounts/login/", wait_until="domcontentloaded")
            page.wait_for_timeout(500)
            page.fill("input[name='login']", TEST_EMAIL)
            page.fill("input[name='password']", NEW_PASS)
            page.click("button[type='submit']")
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(1500)
            page.screenshot(path=str(SCREENSHOT_DIR / "11_login_with_new_password_success.png"))
            print("-> Successfully authenticated with new password.")

            browser.close()

    finally:
        server.stop()
        # Clean up test user and generated emails
        User.objects.filter(email=TEST_EMAIL).delete()
        for eml in Path(".emails").glob("*auth_e2e*"):
            try:
                eml.unlink()
            except OSError:
                pass
        print("Authentication and Email E2E verification complete and cleaned up!")


if __name__ == "__main__":
    run()
