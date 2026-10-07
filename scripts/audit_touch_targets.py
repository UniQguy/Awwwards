#!/usr/bin/env python3
"""
Touch Target Size Auditor (WCAG 2.1 Success Criterion 2.5.5 / 2.5.8).
Tests interactive elements on a mobile viewport (390x844 CSS px).
Asserts that all standalone interactive elements (buttons, inputs, selects, icon triggers,
card action targets) meet the >= 44x44 CSS px touch target minimum,
excluding inline text hyperlinks embedded within flowing prose.
"""

from pathlib import Path
import subprocess
import sys
import time

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Playwright is required. Run: pip install playwright && playwright install chromium")
    sys.exit(1)

VIEWPORT = {"width": 390, "height": 844}
MIN_TARGET_SIZE = 43.5  # Sub-pixel rounding tolerance for 44px

PAGES_TO_INSPECT = [
    {"slug": "home", "path": "/"},
    {"slug": "category-detail", "path": "/c/earphones-headphones/"},
    {"slug": "product-detail", "path": "/p/boat-bassheads-100-in-ear-wired-headphones-with-mic-black-b071z8m4kx/"},
    {"slug": "cart", "path": "/cart/"},
    {"slug": "checkout-start", "path": "/checkout/"},
]


def wait_for_server(url: str, timeout: int = 15) -> bool:
    import urllib.request
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(url) as response:
                if response.status in (200, 302, 404):
                    return True
        except Exception:
            time.sleep(0.5)
    return False


def run_touch_target_audit() -> bool:
    base_dir = Path(__file__).resolve().parent.parent
    server_process = None
    server_url = "http://127.0.0.1:8000"

    if not wait_for_server(f"{server_url}/health/", timeout=2):
        print("Starting Django development server in background...")
        python_bin = base_dir / ".venv" / "Scripts" / "python.exe"
        if not python_bin.exists():
            python_bin = sys.executable
        server_process = subprocess.Popen(
            [str(python_bin), "manage.py", "runserver", "127.0.0.1:8000", "--noreload"],
            cwd=str(base_dir),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if not wait_for_server(f"{server_url}/health/", timeout=15):
            print("Failed to connect to Django dev server.")
            if server_process:
                server_process.terminate()
            sys.exit(1)

    print("\n" + "=" * 80)
    print("ELECTROCART MOBILE TOUCH TARGET SIZE AUDIT (390px Viewport >= 44x44px)")
    print("=" * 80)

    total_violations = 0

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport=VIEWPORT)
            page = context.new_page()

            for item in PAGES_TO_INSPECT:
                url = f"{server_url}{item['path']}"
                try:
                    page.goto(url, wait_until="networkidle", timeout=10000)
                except Exception:
                    page.goto(url, wait_until="domcontentloaded", timeout=10000)

                # Evaluate interactive elements on the page
                elements_data = page.evaluate("""
                    () => {
                        const selector = 'button, input:not([type="hidden"]):not([type="checkbox"]):not([type="radio"]), select, textarea, [role="button"], a.btn, .nav-action-btn, .counter-btn, .filter-chip, .filter-option, .form-checkbox-label';
                        const targets = Array.from(document.querySelectorAll(selector));
                        const report = [];

                        for (const el of targets) {
                            // Check visibility
                            const style = window.getComputedStyle(el);
                            if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
                                continue;
                            }

                            const rect = el.getBoundingClientRect();
                            if (rect.width === 0 || rect.height === 0) continue;

                            // Skip hidden elements offscreen or collapse trays
                            if (rect.bottom < 0 || rect.right < 0) continue;

                            const isUndersized = rect.width < 43.5 || rect.height < 43.5;
                            report.push({
                                tag: el.tagName.toLowerCase(),
                                className: el.className || '',
                                text: (el.textContent || el.value || el.getAttribute('aria-label') || '').trim().substring(0, 30),
                                width: Math.round(rect.width * 10) / 10,
                                height: Math.round(rect.height * 10) / 10,
                                isUndersized: isUndersized
                            });
                        }
                        return report;
                    }
                """)

                undersized = [e for e in elements_data if e["isUndersized"]]
                status_tag = "[PASS]" if not undersized else "[WARN/FAIL]"
                print(f"{status_tag} {item['slug']:<18} ({item['path']}) -> {len(elements_data)} targets evaluated, {len(undersized)} undersized")

                for u in undersized[:5]:
                    print(f"      - <{u['tag']} class='{u['className']}'> '{u['text']}': {u['width']}x{u['height']}px (expected >= 44x44px)")

                total_violations += len(undersized)

            browser.close()

    finally:
        if server_process:
            server_process.terminate()
            server_process.wait()

    print("=" * 80)
    if total_violations > 0:
        print(f"AUDIT RESULT: {total_violations} interactive elements need touch padding expansion.")
        return False
    else:
        print("AUDIT RESULT: All evaluated mobile interactive targets satisfy >= 44x44px.")
        return True


if __name__ == "__main__":
    success = run_touch_target_audit()
    sys.exit(0 if success else 1)
