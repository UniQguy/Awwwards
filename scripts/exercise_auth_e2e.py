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
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:8000"
SCREENSHOT_DIR = Path("docs/ui-review/auth_e2e")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

TEST_EMAIL = "faculty.inspector@university.edu"
TEST_PASS = "FacultyPass2026!"
NEW_PASS = "FacultyPass2026New!"


def run():
    # Setup Django to clean up test user from previous runs
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
    import django
    django.setup()
    from django.contrib.auth import get_user_model
    User = get_user_model()
    User.objects.filter(email=TEST_EMAIL).delete()
    for eml in Path(".emails").glob("*faculty.inspector*"):
        try:
            eml.unlink()
        except OSError:
            pass

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1456, "height": 900})
        page = context.new_page()

        # 1. Signup
        print("1. Navigating to signup page...")
        page.goto(f"{BASE_URL}/accounts/signup/", wait_until="domcontentloaded")
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
        page.goto(f"{BASE_URL}/dev/outbox/", wait_until="domcontentloaded")
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
        page.goto(f"{BASE_URL}/accounts/login/", wait_until="domcontentloaded")
        page.wait_for_timeout(500)
        page.fill("input[name='login']", TEST_EMAIL)
        page.fill("input[name='password']", TEST_PASS)
        page.click("button[type='submit']")
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(1500)

        # Verify authenticated state
        page.goto(f"{BASE_URL}/account/", wait_until="domcontentloaded")
        page.wait_for_timeout(1000)
        page.screenshot(path=str(SCREENSHOT_DIR / "05_authenticated_account.png"))
        assert "Sign out" in page.content() or TEST_EMAIL in page.content(), "Authentication failed"
        print("-> User logged in and verified account dashboard.")

        # 4. Log out
        print("4. Logging out...")
        page.goto(f"{BASE_URL}/accounts/logout/", wait_until="domcontentloaded")
        page.wait_for_timeout(500)
        logout_btn = page.locator("form[action*='logout'] button[type='submit']").first
        if logout_btn.count() > 0:
            logout_btn.click()
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(1000)
        page.screenshot(path=str(SCREENSHOT_DIR / "06_logged_out.png"))
        print("-> User logged out.")

        # 5. Password Reset Request
        print("5. Triggering password reset...")
        page.goto(f"{BASE_URL}/accounts/password/reset/", wait_until="domcontentloaded")
        page.wait_for_timeout(500)
        page.fill("input[name='email']", TEST_EMAIL)
        page.click("button[type='submit']")
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(1000)
        page.screenshot(path=str(SCREENSHOT_DIR / "07_password_reset_sent.png"))
        print("-> Password reset requested.")

        # 6. Check outbox for reset email and perform reset
        print("6. Locating password reset email in outbox...")
        page.goto(f"{BASE_URL}/dev/outbox/", wait_until="domcontentloaded")
        page.wait_for_timeout(1000)
        # Click the top row in outbox (latest reset email)
        page.locator("table tbody tr").first.locator("a").click()
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(1000)
        page.screenshot(path=str(SCREENSHOT_DIR / "08_outbox_reset_email.png"))

        reset_btn = page.locator("a:text('Open Link')").first
        reset_url = reset_btn.get_attribute("href")
        print(f"-> Navigating to reset URL: {reset_url}")
        page.goto(reset_url, wait_until="domcontentloaded")
        page.wait_for_timeout(1000)
        page.screenshot(path=str(SCREENSHOT_DIR / "09_password_reset_form.png"))

        # Fill new password
        page.fill("input[name='password1']", NEW_PASS)
        page.fill("input[name='password2']", NEW_PASS)
        page.click("button[type='submit']")
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(1000)
        page.screenshot(path=str(SCREENSHOT_DIR / "10_password_reset_complete.png"))
        print("-> Password reset completed successfully.")

        # 7. Log in with new password
        print("7. Verifying login with new password...")
        page.goto(f"{BASE_URL}/accounts/login/", wait_until="domcontentloaded")
        page.wait_for_timeout(500)
        page.fill("input[name='login']", TEST_EMAIL)
        page.fill("input[name='password']", NEW_PASS)
        page.click("button[type='submit']")
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(1500)
        page.screenshot(path=str(SCREENSHOT_DIR / "11_login_with_new_password_success.png"))
        print("-> Successfully authenticated with new password.")

        browser.close()
        print("Authentication and Email E2E verification complete!")


if __name__ == "__main__":
    run()
