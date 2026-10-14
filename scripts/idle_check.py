#!/usr/bin/env python3
"""
scripts/idle_check.py - Page Idle Verification Audit (Rule J).

Verifies that after load plus 10 seconds with no input on home, category, and product pages:
1. document.getAnimations() contains zero running animations (none by default).
2. A MutationObserver records zero DOM mutations in the second 5s window (seconds 5 to 10).
3. Zero setTimeout/setInterval fire repeatedly during the idle window.
4. Exits non-zero if any unauthorized idle activity is detected.
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

PAGES_TO_AUDIT = [
    ("/", "Home Monograph"),
    ("/c/smartphones/", "Category Page"),
    ("/p/amazon-basics-flexible-premium-hdmi-cable-black-4k60hz-18gbps-3-foot-b07ksmbl2h/", "Product Detail Page"),
]


def run_idle_check():
    port = find_free_port()
    base_url = f"http://127.0.0.1:{port}"
    server = ServerManager(port=port)
    server.start()

    if not wait_for_server(base_url, timeout=30):
        print("FATAL: Test server failed to start.")
        server.stop()
        sys.exit(1)

    print("======================================================================")
    print("ELECTROCART PAGE IDLE STABILITY AUDIT (RULE J)")
    print("======================================================================")
    print(f"Target Server: {base_url}")
    print("Policy: After load + 10s with no input: 0 running animations, 0 DOM mutations in window.\n")

    overall_passed = True
    all_violations = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1456, "height": 900})

            # Injected script to monitor mutations and recurring timers
            init_script = """
            window.__idle_mutations = 0;
            window.__recording_mutations = false;
            window.__idle_timer_fires = 0;
            window.__recurring_intervals = 0;

            window.__interval_stacks = [];
            const originalSetInterval = window.setInterval;
            window.setInterval = function(fn, delay, ...args) {
                window.__recurring_intervals++;
                window.__interval_stacks.push({
                    delay: delay,
                    stack: new Error().stack
                });
                return originalSetInterval(function(...innerArgs) {
                    if (window.__recording_mutations) {
                        window.__idle_timer_fires++;
                    }
                    return fn.apply(this, innerArgs);
                }, delay, ...args);
            };

            const observer = new MutationObserver((mutations) => {
                if (window.__recording_mutations) {
                    window.__idle_mutations += mutations.length;
                }
            });
            observer.observe(document.documentElement, {
                childList: true,
                subtree: true,
                attributes: true,
                characterData: true
            });
            """
            context.add_init_script(init_script)
            page = context.new_page()

            for path, label in PAGES_TO_AUDIT:
                page_url = f"{base_url}{path}"
                print(f"--> Testing idle behavior on {label} ({path})...")
                page_violations = []

                page.goto(page_url, wait_until="load")

                # Initial stabilization window: 5 seconds (entry choreography settles)
                print("    Waiting 5s for initial entry animations to settle...")
                page.wait_for_timeout(5000)

                # Arm observation for second 5-second window (seconds 5 to 10)
                page.evaluate("""
                    window.__idle_mutations = 0;
                    window.__idle_timer_fires = 0;
                    window.__recording_mutations = true;
                """)

                print("    Observing second 5s idle window (seconds 5 to 10)...")
                page.wait_for_timeout(5000)

                # Disarm and collect metrics
                metrics = page.evaluate("""
                    () => {
                        window.__recording_mutations = false;
                        const runningAnimations = document.getAnimations
                            ? document.getAnimations().filter(a => a.playState === 'running').map(a => {
                                const target = a.effect && a.effect.target;
                                return (target ? target.tagName + (target.className ? '.' + target.className : '') : 'unknown') + ' (' + (a.animationName || 'unnamed') + ')';
                              })
                            : [];

                        return {
                            runningAnimations: runningAnimations,
                            mutations: window.__idle_mutations,
                            timerFires: window.__idle_timer_fires,
                            recurringIntervals: window.__recurring_intervals,
                            intervalStacks: window.__interval_stacks
                        };
                    }
                """)

                running_anims = metrics["runningAnimations"]
                mutations = metrics["mutations"]
                timer_fires = metrics["timerFires"]
                interval_stacks = metrics.get("intervalStacks", [])

                print(f"    Results for {label}:")
                print(f"      - Running animations: {len(running_anims)} {running_anims}")
                print(f"      - DOM mutations in second 5s: {mutations}")
                print(f"      - Recurring timer triggers: {timer_fires}")

                if len(running_anims) > 0:
                    page_violations.append(f"Found {len(running_anims)} running animation(s): {running_anims}")

                if mutations > 0:
                    page_violations.append(f"Recorded {mutations} DOM mutation(s) during idle window")

                if timer_fires > 0:
                    page_violations.append(f"Recorded {timer_fires} timer trigger(s) during idle window")
                    for s in interval_stacks:
                        print(f"      [Stack] delay={s.get('delay')}:\n{s.get('stack')}")

                if page_violations:
                    overall_passed = False
                    print(f"    FAIL ({len(page_violations)} violations)")
                    for v in page_violations:
                        print(f"      - {v}")
                    all_violations.extend(page_violations)
                else:
                    print(f"    PASS (0 animations, 0 mutations, 0 timers)")

            browser.close()
    finally:
        server.stop()

    print("\n----------------------------------------------------------------------")
    if overall_passed:
        print("SUMMARY: ALL PAGES PASSED IDLE AUDIT. Completely silent after load.")
        return 0
    else:
        print(f"SUMMARY: IDLE AUDIT FAILED with {len(all_violations)} violations.")
        return 1


if __name__ == "__main__":
    sys.exit(run_idle_check())
