#!/usr/bin/env python3
"""
scripts/allowlist_audit.py - Network Request Host Allowlist Audit (Rule F).

Verifies that no network requests are made to any domain outside the strict allowlist:
- self (localhost / 127.0.0.1 / data: URLs)
- cdnjs.cloudflare.com
- cdn.jsdelivr.net
- m.media-amazon.com
- checkout.razorpay.com (STRICTLY on /checkout/ only)

Exits 0 if all pages respect the allowlist with zero unexpected hosts.
Exits 1 if any unauthorized network request is detected.
"""

from pathlib import Path
import sys
from urllib.parse import urlparse

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

ALLOWED_GLOBAL_HOSTS = {
    "cdnjs.cloudflare.com",
    "cdn.jsdelivr.net",
    "m.media-amazon.com",
}

CHECKOUT_ONLY_HOSTS = {
    "checkout.razorpay.com",
}

TEST_PAGES = [
    ("/", "Home Monograph"),
    ("/categories/", "Categories Index"),
    ("/c/smartphones/", "Category Faceted Marquee"),
    ("/p/amazon-basics-flexible-premium-hdmi-cable-black-4k60hz-18gbps-3-foot-b07ksmbl2h/", "Product Detail"),
    ("/cart/", "Shopping Bag"),
    ("/checkout/", "Checkout Gateway"),
]


def run_allowlist_audit():
    port = find_free_port()
    base_url = f"http://127.0.0.1:{port}"
    server = ServerManager(port=port)
    server.start()

    if not wait_for_server(base_url, timeout=30):
        print("FATAL: Test server failed to start.")
        server.stop()
        sys.exit(1)

    print("======================================================================")
    print("ELECTROCART NETWORK HOST ALLOWLIST AUDIT (RULE F)")
    print("======================================================================")
    print(f"Target Server: {base_url}")
    print(f"Global Allowed Hosts: {sorted(list(ALLOWED_GLOBAL_HOSTS))}")
    print(f"Checkout-Only Hosts: {sorted(list(CHECKOUT_ONLY_HOSTS))}\n")

    overall_passed = True
    all_violations = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1456, "height": 900})
            page = context.new_page()

            for path, label in TEST_PAGES:
                page_url = f"{base_url}{path}"
                is_checkout = path.startswith("/checkout")
                page_violations = []
                requested_hosts = set()
                csp_errors = []

                def on_request(request):
                    url = request.url
                    if url.startswith("data:") or url.startswith("blob:"):
                        return
                    parsed = urlparse(url)
                    host = parsed.hostname
                    port_str = f":{parsed.port}" if parsed.port else ""
                    self_host = f"127.0.0.1{port_str}"

                    if host in ("127.0.0.1", "localhost"):
                        return

                    requested_hosts.add(host)

                    if host in ALLOWED_GLOBAL_HOSTS:
                        return
                    elif is_checkout and host in CHECKOUT_ONLY_HOSTS:
                        return
                    else:
                        page_violations.append(f"UNAUTHORIZED HOST: {host} (URL: {url[:100]})")

                def on_console(msg):
                    text = msg.text
                    if "Content Security Policy" in text or "violates the following Content Security Policy" in text:
                        csp_errors.append(text)

                page.on("request", on_request)
                page.on("console", on_console)

                print(f"--> Auditing {label} ({path})...")
                res = page.goto(page_url, wait_until="domcontentloaded", timeout=30000)

                # Wait 1000ms for deferred scripts and network requests
                page.wait_for_timeout(1000)

                status = res.status if res else 0
                if status != 200:
                    page_violations.append(f"HTTP Status {status} != 200")

                if csp_errors:
                    for err in csp_errors:
                        page_violations.append(f"CSP ERROR: {err}")

                page.remove_listener("request", on_request)
                page.remove_listener("console", on_console)

                if page_violations:
                    overall_passed = False
                    print(f"    FAIL ({len(page_violations)} violations)")
                    for v in page_violations:
                        print(f"      - {v}")
                    all_violations.extend(page_violations)
                else:
                    print(f"    PASS (status 200, hosts: {sorted(list(requested_hosts)) or ['self-only']})")

            browser.close()
    finally:
        server.stop()

    print("\n----------------------------------------------------------------------")
    if overall_passed:
        print("SUMMARY: ALL PAGES PASSED. Zero unauthorized network requests.")
        return 0
    else:
        print(f"SUMMARY: FAILED with {len(all_violations)} violations.")
        return 1


if __name__ == "__main__":
    sys.exit(run_allowlist_audit())
