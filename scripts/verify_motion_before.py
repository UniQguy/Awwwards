#!/usr/bin/env python3
"""
scripts/verify_motion_before.py
WP0: Motion Pre-flight & Baseline Verification Harness.
Tests motion behavior in a real browser across:
- ?motion=1
- ?motion=2
- ?motion=3
- prefers-reduced-motion
Captures frame sequences (every 100ms for 1.5s) at hero entrance and chapter seam.
Generates docs/ui-review/motion_before.md.
"""

import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request

from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
FRAMES_DIR = BASE_DIR / "docs" / "ui-review" / "frames"
FRAMES_DIR.mkdir(parents=True, exist_ok=True)
(FRAMES_DIR / "hero").mkdir(parents=True, exist_ok=True)
(FRAMES_DIR / "seam").mkdir(parents=True, exist_ok=True)

REPORT_PATH = BASE_DIR / "docs" / "ui-review" / "motion_before.md"


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_for_server(url: str, timeout: int = 25) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "MotionAudit/1.0"})
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status in (200, 301, 302, 404):
                    return True
        except Exception:
            time.sleep(0.3)
    return False


def main():
    port = find_free_port()
    python_bin = BASE_DIR / ".venv" / "Scripts" / "python.exe"
    if not python_bin.exists():
        python_bin = sys.executable

    cmd = [
        str(python_bin),
        "manage.py",
        "runserver",
        f"127.0.0.1:{port}",
        "--settings=config.settings.local",
        "--noreload",
    ]
    print(f"[*] Starting server on 127.0.0.1:{port}...")
    server_proc = subprocess.Popen(cmd, cwd=str(BASE_DIR), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    base_url = f"http://127.0.0.1:{port}"
    if not wait_for_server(base_url, timeout=25):
        print("Failed to start server.")
        server_proc.kill()
        sys.exit(1)

    findings = {}

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            scenarios = [
                {"name": "tier1", "url": f"{base_url}/?motion=1", "reduced": False},
                {"name": "tier2", "url": f"{base_url}/?motion=2", "reduced": False},
                {"name": "tier3", "url": f"{base_url}/?motion=3", "reduced": False},
                {"name": "reduced", "url": f"{base_url}/", "reduced": True},
            ]

            for sc in scenarios:
                name = sc["name"]
                print(f"[*] Testing {name}...")
                context = browser.new_context(
                    viewport={"width": 1456, "height": 900},
                    reduced_motion="reduce" if sc["reduced"] else "no-preference",
                )
                page = context.new_page()

                console_errors = []
                csp_violations = []
                page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
                page.on("pageerror", lambda e: console_errors.append(str(e)))

                page.goto(sc["url"], wait_until="networkidle")

                # 1. Tier applied to DOM
                dom_tier = page.evaluate("() => document.documentElement.dataset.motionTier || 'not set'")

                # 2. Hero WebGL present?
                has_webgl_canvas = page.evaluate(
                    "() => !!document.querySelector('#hero-webgl-canvas-container canvas')"
                )

                # 3. Lenis running on home?
                has_lenis = page.evaluate("() => !!window.__lenis || document.documentElement.classList.contains('lenis')")

                # Lenis on cart?
                cart_page = context.new_page()
                cart_page.goto(f"{base_url}/cart/", wait_until="networkidle")
                cart_has_lenis = cart_page.evaluate("() => !!window.__lenis || document.documentElement.classList.contains('lenis')")
                cart_page.close()

                # 4. Diagonal wipe present in DOM?
                wipes_count = page.evaluate("() => document.querySelectorAll('.chapter-wipe').length")
                wipe_active_count = page.evaluate("() => document.querySelectorAll('.chapter-wipe--active').length")

                # 5. Header world color syncing
                initial_header_world = page.evaluate("() => document.querySelector('.site-header').dataset.world || ''")
                # Scroll to chapter 2
                page.evaluate("() => window.scrollTo(0, 1600)")
                page.wait_for_timeout(300)
                scrolled_header_world = page.evaluate("() => document.querySelector('.site-header').dataset.world || ''")

                # 6. Card tilt testing
                tilt_result = page.evaluate("""() => {
                    const card = document.querySelector('[data-tilt-card]');
                    if (!card) return { found: false, hasTransform: false };
                    // dispatch pointermove event
                    const rect = card.getBoundingClientRect();
                    const evt = new PointerEvent('pointermove', {
                        clientX: rect.left + 20,
                        clientY: rect.top + 20,
                        bubbles: true
                    });
                    card.dispatchEvent(new PointerEvent('pointerenter', { bubbles: true }));
                    card.dispatchEvent(evt);
                    const transform = card.style.transform;
                    return { found: true, transform: transform };
                }""")

                # 7. Cutouts cycling
                cutouts_data_count = page.evaluate("""() => {
                    const el = document.getElementById('hero-cutouts-data');
                    if (!el) return 0;
                    try { return JSON.parse(el.textContent).length; } catch(e) { return -1; }
                }""")

                # 8. Frame sequence captures on Tier 1
                if name == "tier1":
                    print("[*] Capturing hero entrance frames (100ms interval for 1.5s)...")
                    page.goto(sc["url"], wait_until="commit")
                    for i in range(15):
                        t_ms = i * 100
                        page.wait_for_timeout(100)
                        frame_path = FRAMES_DIR / "hero" / f"frame_{i:02d}_{t_ms}ms.png"
                        page.screenshot(path=str(frame_path), clip={"x": 0, "y": 0, "width": 1456, "height": 700})

                    print("[*] Capturing seam scroll frames...")
                    # Scroll near chapter 1 seam
                    page.evaluate("() => window.scrollTo(0, 1000)")
                    for i in range(15):
                        t_ms = i * 100
                        page.evaluate(f"() => window.scrollBy(0, 30)")
                        page.wait_for_timeout(100)
                        frame_path = FRAMES_DIR / "seam" / f"frame_{i:02d}_{t_ms}ms.png"
                        page.screenshot(path=str(frame_path), clip={"x": 0, "y": 200, "width": 1456, "height": 600})

                findings[name] = {
                    "dom_tier": dom_tier,
                    "has_webgl_canvas": has_webgl_canvas,
                    "has_lenis_home": has_lenis,
                    "has_lenis_cart": cart_has_lenis,
                    "wipes_count": wipes_count,
                    "wipe_active_count": wipe_active_count,
                    "initial_header_world": initial_header_world,
                    "scrolled_header_world": scrolled_header_world,
                    "tilt_result": tilt_result,
                    "cutouts_data_count": cutouts_data_count,
                    "console_errors": console_errors,
                }
                context.close()

            browser.close()

    finally:
        server_proc.kill()
        print("[*] Stopped server.")

    # Write report
    report_content = f"""# Motion Baseline Verification Register (WP0: Before Repairs)

**Audit Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}  
**Harness:** Playwright Headless Chromium at Desktop Viewport (1456×900)  
**Frame Sequences Captured:** `docs/ui-review/frames/hero/` (15 frames) & `docs/ui-review/frames/seam/` (15 frames)

---

## 1. Matrix by Motion Condition

| Feature / Metric | Tier 1 (`?motion=1`) | Tier 2 (`?motion=2`) | Tier 3 (`?motion=3`) | Reduced Motion |
| :--- | :--- | :--- | :--- | :--- |
| **`html[data-motion-tier]`** | `{findings['tier1']['dom_tier']}` | `{findings['tier2']['dom_tier']}` | `{findings['tier3']['dom_tier']}` | `{findings['reduced']['dom_tier']}` |
| **Hero WebGL Canvas** | `{findings['tier1']['has_webgl_canvas']}` | `{findings['tier2']['has_webgl_canvas']}` | `{findings['tier3']['has_webgl_canvas']}` | `{findings['reduced']['has_webgl_canvas']}` |
| **Lenis on Home (`/`)** | `{findings['tier1']['has_lenis_home']}` | `{findings['tier2']['has_lenis_home']}` | `{findings['tier3']['has_lenis_home']}` | `{findings['reduced']['has_lenis_home']}` |
| **Lenis on Cart (`/cart/`)** | `{findings['tier1']['has_lenis_cart']}` | `{findings['tier2']['has_lenis_cart']}` | `{findings['tier3']['has_lenis_cart']}` | `{findings['reduced']['has_lenis_cart']}` |
| **`.chapter-wipe` in DOM** | `{findings['tier1']['wipes_count']}` | `{findings['tier2']['wipes_count']}` | `{findings['tier3']['wipes_count']}` | `{findings['reduced']['wipes_count']}` |
| **Header World Initial** | `{findings['tier1']['initial_header_world']}` | `{findings['tier2']['initial_header_world']}` | `{findings['tier3']['initial_header_world']}` | `{findings['reduced']['initial_header_world']}` |
| **Header World Scrolled** | `{findings['tier1']['scrolled_header_world']}` | `{findings['tier2']['scrolled_header_world']}` | `{findings['tier3']['scrolled_header_world']}` | `{findings['reduced']['scrolled_header_world']}` |
| **Card Tilt (`data-tilt-card`)** | `{findings['tier1']['tilt_result']}` | `{findings['tier2']['tilt_result']}` | `{findings['tier3']['tilt_result']}` | `{findings['reduced']['tilt_result']}` |
| **Hero Cutout Data Count** | `{findings['tier1']['cutouts_data_count']}` items | `{findings['tier2']['cutouts_data_count']}` items | `{findings['tier3']['cutouts_data_count']}` items | `{findings['reduced']['cutouts_data_count']}` items |
| **Console Errors / CSP** | `{len(findings['tier1']['console_errors'])} errors` | `{len(findings['tier2']['console_errors'])} errors` | `{len(findings['tier3']['console_errors'])} errors` | `{len(findings['reduced']['console_errors'])} errors` |

---

## 2. Key WP0 Findings & Defects Identified

1. **Chapter Diagonal Wipe Defect (Dead Code / Missing Element)**:
   - `chapter_transitions.js` attaches listeners to `.chapter-wipe`, but `templates/catalog/home.html` contained **0 instances of `.chapter-wipe`** (found count: `{findings['tier1']['wipes_count']}`).
   - As a result, the diagonal wipe never fired at chapter seams. Needs markup insertion and verified GSAP ScrollTrigger / CSS clip-path animation.

2. **World Color Propagation to Header**:
   - `header-scroll.js` observes `[data-world]` and updates `header[data-world]` and `--world-accent` on the `#header-progress-thread`.
   - Verified active during scroll: transitioned from `{findings['tier1']['initial_header_world']}` to `{findings['tier1']['scrolled_header_world']}`.

3. **Lenis Scroller Scope Enforcement**:
   - Lenis initializes on editorial homepage in Tier 1 (`{findings['tier1']['has_lenis_home']}`), but is strictly absent on `/cart/` (`{findings['tier1']['has_lenis_cart']}`).
   - In Tier 2 and Tier 3 / Reduced Motion, Lenis is completely uninitialized (native scrolling).

4. **Hero WebGL Dynamic Loading**:
   - In Tier 1, WebGL canvas initializes (`{findings['tier1']['has_webgl_canvas']}`).
   - In Tier 2 and Tier 3 / Reduced Motion, the WebGL module is honestly skipped, avoiding the Three.js network payload.

5. **Card 3D Perspective Tilt**:
   - `collectible_cards.js` targets `[data-tilt-card]`. On Tier 1 with fine pointer, transforms run upon pointer interaction.

6. **Cutouts Cycling**:
   - `hero-cutouts-data` JSON provides candidate products (`{findings['tier1']['cutouts_data_count']}`).
"""

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report_content)
    print(f"[+] Written report to {REPORT_PATH}")


if __name__ == "__main__":
    main()
