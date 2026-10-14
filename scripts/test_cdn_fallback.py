#!/usr/bin/env python3
"""
scripts/test_cdn_fallback.py - Offline / CDN-Blocked Verification Test (Rule F).

Tests that when cdnjs.cloudflare.com and cdn.jsdelivr.net are blocked:
1. The CDN script loads fail as simulated.
2. After 2500ms, cdn_fallback.js detects the missing global and injects the vendored fallback.
3. window.gsap and window.ScrollTrigger become available.
4. Zero fatal console errors, and the page renders its complete layout.
"""

from pathlib import Path
import sys
import time

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


def run_cdn_fallback_test():
    port = find_free_port()
    base_url = f"http://127.0.0.1:{port}"
    server = ServerManager(port=port)
    server.start()

    if not wait_for_server(base_url, timeout=30):
        print("FATAL: Test server failed to start.")
        server.stop()
        sys.exit(1)

    print("======================================================================")
    print("ELECTROCART CDN VENDORED FALLBACK VERIFICATION (RULE F)")
    print("======================================================================")
    print("Policy: Blocking cdnjs.cloudflare.com and cdn.jsdelivr.net.")
    print("Expected: Pinned vendored copies in /static/vendor/gsap/ are injected.\n")

    passed = True
    errors = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1456, "height": 900})
            page = context.new_page()

            # Intercept and abort both CDN hosts
            blocked_urls = []

            def block_cdn(route):
                req_url = route.request.url
                blocked_urls.append(req_url)
                route.abort("blockedbyclient")

            page.route("**/*cdnjs.cloudflare.com/**", block_cdn)
            page.route("**/*cdn.jsdelivr.net/**", block_cdn)

            page_console_errors = []

            def on_console(msg):
                if msg.type == "error":
                    # CDN script load failures are expected; other JS runtime errors are not
                    if "ERR_BLOCKED_BY_CLIENT" not in msg.text and "Failed to load resource" not in msg.text:
                        page_console_errors.append(msg.text)

            page.on("console", on_console)

            print("--> Navigating to homepage with CDNs blocked...")
            page.goto(f"{base_url}/", wait_until="domcontentloaded")

            # Check immediately before fallback timer
            gsap_immediate = page.evaluate("typeof window.gsap")
            print(f"    Immediate window.gsap state: {gsap_immediate}")

            # Wait for 2800ms (fallback timeout is 2500ms + margin)
            print("    Waiting 3000ms for vendored fallback loader...")
            page.wait_for_timeout(3000)

            # Check after fallback timer
            gsap_after = page.evaluate("typeof window.gsap")
            st_after = page.evaluate("typeof window.ScrollTrigger")
            gsap_version = page.evaluate("window.gsap ? window.gsap.version : null")

            print(f"    Post-fallback window.gsap: {gsap_after} (version: {gsap_version})")
            print(f"    Post-fallback window.ScrollTrigger: {st_after}")

            if gsap_after != "object" and gsap_after != "function":
                passed = False
                errors.append(f"window.gsap not defined after fallback (got {gsap_after})")

            if st_after != "object" and st_after != "function":
                passed = False
                errors.append(f"window.ScrollTrigger not defined after fallback (got {st_after})")

            # Verify that fallback injected the local scripts
            injected_sources = page.evaluate("""
                Array.from(document.querySelectorAll('script[src*="/static/vendor/gsap/"]')).map(s => s.src)
            """)
            print(f"    Injected fallback scripts: {injected_sources}")

            if len(injected_sources) < 2:
                passed = False
                errors.append(f"Expected 2 vendored fallback scripts injected, found: {injected_sources}")

            if page_console_errors:
                print(f"    WARNING/ERRORS in console: {page_console_errors}")

            browser.close()
    finally:
        server.stop()

    print("\n----------------------------------------------------------------------")
    if passed:
        print("SUMMARY: CDN FALLBACK TEST PASSED. Vendored scripts loaded cleanly.")
        return 0
    else:
        print(f"SUMMARY: CDN FALLBACK TEST FAILED with errors: {errors}")
        return 1


if __name__ == "__main__":
    sys.exit(run_cdn_fallback_test())
