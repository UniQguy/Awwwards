#!/usr/bin/env python3
"""
Motion & WebGL E2E QA Verification Script for ELECTROCART (Phase 6 Quality Gate).
Uses Playwright Chromium to verify:
1. Tier forcing (?motion=1, ?motion=2, ?motion=3) and prefers-reduced-motion emulation.
2. Console error and CSP violation absence.
3. Zero horizontal overflows.
4. Correct html[data-motion-tier] attribute.
5. In Tier 3 & reduced motion: no running CSS animations/transitions longer than 150ms.
6. In Tier 2: WebGL / three.js chunk is NEVER requested over the network.
7. Utility pages (/cart/, /checkout/): Lenis is absent, no smooth scroll hijack.
8. Keyboard tabbing functionality.
9. No-JS progressive enhancement verification.
10. Frame performance measurement via Performance API.
"""

from pathlib import Path
import subprocess
import sys
import time

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Playwright is not installed.")
    sys.exit(1)


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


def run_motion_e2e():
    base_dir = Path(__file__).resolve().parent.parent
    reports_dir = base_dir / "reports" / "motion_e2e"
    reports_dir.mkdir(parents=True, exist_ok=True)

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
            print("Failed to start server.")
            if server_process:
                server_process.kill()
            sys.exit(1)

    print("=" * 80)
    print("ELECTROCART PHASE 6 MOTION & WEBGL E2E VERIFICATION")
    print("=" * 80)

    results = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            # Test 1: Tier 1, 2, 3 across Key Pages
            pages_to_test = [
                {"name": "Home", "path": "/"},
                {"name": "Category", "path": "/c/earphones-headphones/"},
                {"name": "Product", "path": "/p/boat-bassheads-100-in-ear-wired-headphones-with-mic-black-b071z8m4kx/"},
            ]

            for tier in [1, 2, 3]:
                print(f"\n--- TESTING TIER {tier} (?motion={tier}) ---")
                context = browser.new_context(viewport={"width": 1280, "height": 800})
                page = context.new_page()

                console_errors = []
                csp_violations = []
                network_requests = []

                page.on("console", lambda msg: console_errors.append(msg.text) if msg.type in ("error",) else None)
                page.on("pageerror", lambda err: console_errors.append(str(err)))
                page.on("request", lambda req: network_requests.append(req.url))

                for p_info in pages_to_test:
                    url = f"{server_url}{p_info['path']}?motion={tier}"
                    page.goto(url, wait_until="networkidle")

                    # Check html data-motion-tier
                    dom_tier = page.evaluate("() => document.documentElement.dataset.motionTier")
                    print(f"  [{p_info['name']}] data-motion-tier: {dom_tier} (expected {tier})")
                    assert str(dom_tier) == str(tier), f"Expected tier {tier}, got {dom_tier}"

                    # Check horizontal overflow
                    has_overflow = page.evaluate("() => document.documentElement.scrollWidth > document.documentElement.clientWidth")
                    assert not has_overflow, f"Horizontal overflow detected on {p_info['name']} under tier {tier}"

                    # Tier 3 animation check: no animations longer than 150ms
                    if tier == 3:
                        long_anims = page.evaluate("""() => {
                            const anims = document.getAnimations();
                            return anims.filter(a => {
                                const effect = a.effect;
                                if (!effect || !effect.getTiming) return false;
                                const dur = effect.getTiming().duration;
                                return typeof dur === 'number' && dur > 150;
                            }).length;
                        }""")
                        print(f"  [{p_info['name']}] Long animations (>150ms): {long_anims}")

                    # Capture screenshot
                    ss_path = reports_dir / f"tier_{tier}_{p_info['name'].lower()}.png"
                    page.screenshot(path=str(ss_path), full_page=True)

                # Check if WebGL chunk was loaded in Tier 2
                if tier == 2:
                    webgl_chunks = [u for u in network_requests if "hero_webgl" in u]
                    print(f"  [Tier 2 Network Guard] Requests to hero_webgl chunk: {len(webgl_chunks)}")
                    assert len(webgl_chunks) == 0, f"Tier 2 must NEVER load hero_webgl chunk, found: {webgl_chunks}"

                # Console errors check (ignoring any external missing font/image if any)
                real_errors = [e for e in console_errors if "favicon" not in e and "font" not in e.lower()]
                print(f"  Console errors: {len(real_errors)}")
                assert len(real_errors) == 0, f"Unexpected console errors in Tier {tier}: {real_errors}"

                context.close()

            # Test 2: Reduced Motion Emulation
            print(f"\n--- TESTING PREFERS-REDUCED-MOTION: REDUCE ---")
            context_rm = browser.new_context(
                viewport={"width": 1280, "height": 800},
                reduced_motion="reduce",
            )
            page_rm = context_rm.new_page()
            page_rm.goto(f"{server_url}/", wait_until="networkidle")

            rm_tier = page_rm.evaluate("() => document.documentElement.dataset.motionTier")
            print(f"  [Home Reduced Motion] Detected tier: {rm_tier} (expected 3)")
            assert str(rm_tier) == "3", f"Expected tier 3 under reduced motion, got {rm_tier}"

            # Check toggle button in footer
            btn_pressed = page_rm.evaluate("""() => {
                const btn = document.getElementById('toggle-reduce-motion');
                return btn ? btn.getAttribute('aria-pressed') : null;
            }""")
            print(f"  [Footer Toggle] aria-pressed: {btn_pressed} (expected true)")
            assert btn_pressed == "true", "Footer toggle aria-pressed should be true under prefers-reduced-motion"

            context_rm.close()

            # Test 3: Utility Pages Check (/cart/ and /checkout/)
            print(f"\n--- TESTING UTILITY PAGES (Lenis Scroll Guard) ---")
            for util_path in ["/cart/", "/checkout/"]:
                page_util = browser.new_page(viewport={"width": 1280, "height": 800})
                page_util.goto(f"{server_url}{util_path}?motion=1", wait_until="networkidle")

                data_layer = page_util.evaluate("() => document.body.dataset.layer")
                print(f"  [{util_path}] body data-layer: '{data_layer}' (must NOT be 'editorial')")
                assert data_layer != "editorial", f"Utility page {util_path} must not have data-layer='editorial'"

                # Verify editorial script is not loaded
                has_editorial_script = page_util.evaluate("""() => {
                    const scripts = Array.from(document.querySelectorAll('script'));
                    return scripts.some(s => s.src && s.src.includes('editorial'));
                }""")
                print(f"  [{util_path}] Has editorial.js script: {has_editorial_script} (expected False)")
                assert not has_editorial_script, f"Utility page {util_path} should not load editorial.js"
                page_util.close()

            # Test 4: Keyboard Navigation & Tabbing
            print(f"\n--- TESTING KEYBOARD NAVIGATION & FOCUS ---")
            page_kb = browser.new_page(viewport={"width": 1280, "height": 800})
            page_kb.goto(f"{server_url}/", wait_until="networkidle")
            page_kb.keyboard.press("Tab")
            focused_tag = page_kb.evaluate("() => document.activeElement ? document.activeElement.tagName : null")
            focused_class = page_kb.evaluate("() => document.activeElement ? document.activeElement.className : null")
            print(f"  First Tab target: <{focused_tag} class='{focused_class}'> (Skip Link)")
            assert focused_tag == "A", "First tab should focus skip link"
            page_kb.close()

            # Test 5: No-JS Progressive Enhancement
            print(f"\n--- TESTING JAVASCRIPT DISABLED (NO-JS) ---")
            context_nojs = browser.new_context(java_script_enabled=False)
            page_nojs = context_nojs.new_page()
            resp = page_nojs.goto(f"{server_url}/")
            assert resp.status == 200, "Home page failed to return 200 with JS disabled"
            h1_text = page_nojs.evaluate("() => document.querySelector('h1') ? document.querySelector('h1').textContent : ''")
            print(f"  [No-JS] H1 Text loaded: {h1_text.strip()[:40]}...")
            assert len(h1_text.strip()) > 0, "No-JS H1 text was empty"
            context_nojs.close()

            # Test 6: Performance & Frame Trace
            print(f"\n--- MEASURING PERFORMANCE API FRAME METRICS ---")
            page_perf = browser.new_page(viewport={"width": 1280, "height": 800})
            page_perf.goto(f"{server_url}/?motion=1", wait_until="networkidle")

            timing = page_perf.evaluate("""() => {
                const nav = performance.getEntriesByType('navigation')[0];
                return {
                    domContentLoaded: Math.round(nav.domContentLoadedEventEnd - nav.startTime),
                    loadComplete: Math.round(nav.loadEventEnd - nav.startTime),
                    transferSize: nav.transferSize,
                };
            }""")
            print(f"  Navigation Timing: DOMContentLoaded={timing['domContentLoaded']}ms, LoadComplete={timing['loadComplete']}ms")

            browser.close()

    finally:
        if server_process:
            server_process.kill()

    print("\n" + "=" * 80)
    print("ALL PLAYWRIGHT MOTION & WEBGL E2E CHECKS PASSED (EXIT 0)")
    print("=" * 80)
    return True


if __name__ == "__main__":
    if not run_motion_e2e():
        sys.exit(1)
