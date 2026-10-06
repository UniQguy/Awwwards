#!/usr/bin/env python3
"""
Accessibility (a11y) QA Auditor for ELECTROCART (Phase 4 Quality Gate).
Uses Playwright Chromium to load pages and inject axe-core.
Asserts ZERO serious or critical violations across primary templates.
"""

from pathlib import Path
import subprocess
import sys
import time

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Playwright is not installed. Run: pip install playwright && playwright install chromium")
    sys.exit(1)

PAGES_TO_AUDIT = [
    {"slug": "home", "path": "/"},
    {"slug": "categories", "path": "/categories/"},
    {"slug": "category-detail", "path": "/c/earphones-headphones/"},
    {"slug": "product-detail", "path": "/p/boat-bassheads-100-in-ear-wired-headphones-with-mic-black-b071z8m4kx/"},
    {"slug": "cart-empty", "path": "/cart/"},
    {"slug": "checkout-start", "path": "/checkout/"},
    {"slug": "brands", "path": "/brands/"},
    {"slug": "login", "path": "/accounts/login/"},
    {"slug": "terms", "path": "/legal/terms/"},
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


def run_a11y_audit() -> bool:
    base_dir = Path(__file__).resolve().parent.parent
    axe_path = base_dir / "node_modules" / "axe-core" / "axe.min.js"

    if not axe_path.exists():
        print(f"Error: axe-core script not found at {axe_path}")
        return False

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
            print("Failed to start or connect to Django dev server.")
            if server_process:
                server_process.terminate()
            sys.exit(1)

    print("\n" + "=" * 80)
    print("ELECTROCART AUTOMATED AXE-CORE ACCESSIBILITY (a11y) AUDIT")
    print("=" * 80)

    axe_script = axe_path.read_text(encoding="utf-8")
    critical_or_serious_count = 0
    all_violations_by_page = {}

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 800})

            for p_info in PAGES_TO_AUDIT:
                url = f"{server_url}{p_info['path']}"
                try:
                    page.goto(url, wait_until="networkidle", timeout=10000)
                except Exception:
                    page.goto(url, wait_until="domcontentloaded", timeout=10000)

                # Inject axe-core
                page.evaluate(axe_script)

                # Execute axe.run()
                results = page.evaluate("""
                    async () => {
                        const r = await axe.run(document, {
                            runOnly: {
                                type: 'tag',
                                values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']
                            }
                        });
                        return r.violations;
                    }
                """)

                severe_page_violations = [
                    v for v in results if v.get("impact") in ("critical", "serious")
                ]
                minor_page_violations = [
                    v for v in results if v.get("impact") not in ("critical", "serious")
                ]

                critical_or_serious_count += len(severe_page_violations)
                all_violations_by_page[p_info["slug"]] = results

                status_tag = "[PASS]" if not severe_page_violations else "[FAIL]"
                print(f"{status_tag} {p_info['slug']:<18} ({p_info['path']}) -> {len(severe_page_violations)} serious/critical, {len(minor_page_violations)} moderate/minor")
                for sv in severe_page_violations:
                    print(f"      - [{sv.get('impact').upper()}] {sv.get('id')}: {sv.get('help')} (Nodes: {len(sv.get('nodes', []))})")
                    for node in sv.get('nodes', [])[:5]:
                        print(f"         Node: {node.get('html')[:120]}")
                        print(f"         Summary: {node.get('failureSummary', '').replace('\n', ' ')}")

            browser.close()

    finally:
        if server_process:
            server_process.terminate()
            server_process.wait()

    print("=" * 80)
    if critical_or_serious_count > 0:
        print(f"A11Y AUDIT FAILED: {critical_or_serious_count} serious/critical violations detected.")
        return False
    else:
        print("A11Y AUDIT PASSED: ZERO critical or serious accessibility violations across all pages.")
        return True


if __name__ == "__main__":
    success = run_a11y_audit()
    sys.exit(0 if success else 1)
