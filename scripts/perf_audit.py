#!/usr/bin/env python3
"""
Performance audit script executing Rule E & WP9 requirements:
- Playwright at 4x CPU throttle (via CDP Emulation.setCPUThrottlingRate)
- Scripted scroll across Home, Category, and Product Detail
- Measures:
  1. Long tasks over 100ms
  2. p95 frame time (target < 33ms)
  3. Cumulative Layout Shift (CLS)
  4. Scroll height
"""

import json
import math
import os
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from scripts.e2e_browser import ServerManager, find_free_port, wait_for_server

PAGES_TO_TEST = [
    ("Home Monograph", "/"),
    ("Category Detail", "/c/smartphones/"),
    ("Product Detail", "/p/amazon-basics-flexible-premium-hdmi-cable-black-4k60hz-18gbps-3-foot-b07ksmbl2h/"),
]


def audit_page(page, url, name):
    print(f"\n--- Testing {name} ({url}) at 4x CPU throttle ---")
    page.goto(url, wait_until="networkidle")
    page.wait_for_timeout(800)

    # Initialize frame & performance observers
    page.evaluate("""() => {
        window.__longTasks = [];
        window.__clsScore = 0;
        window.__frameDeltas = [];

        // Observe Long Tasks
        try {
            const ltObserver = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    if (entry.duration > 100) {
                        window.__longTasks.push({
                            name: entry.name,
                            startTime: entry.startTime,
                            duration: entry.duration
                        });
                    }
                }
            });
            ltObserver.observe({ entryTypes: ['longtask'] });
        } catch (e) {}

        // Observe CLS
        try {
            const clsObserver = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    if (!entry.hadRecentInput) {
                        window.__clsScore += entry.value;
                    }
                }
            });
            clsObserver.observe({ type: 'layout-shift', buffered: true });
        } catch (e) {}

        window.__frameDeltas = [];
    }""")

    # Perform in-browser scripted rAF scroll from top to bottom and back
    page.evaluate("""async () => {
        return new Promise(resolve => {
            const max = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
            let pos = 0;
            const step = Math.max(30, Math.floor(max / 70));
            let lastTime = 0;
            function stepDown(now) {
                if (lastTime > 0) {
                    const delta = now - lastTime;
                    if (delta > 0 && delta < 500) window.__frameDeltas.push(delta);
                }
                lastTime = now;
                pos += step;
                window.scrollTo(0, Math.min(max, pos));
                if (pos < max) {
                    requestAnimationFrame(stepDown);
                } else {
                    lastTime = 0;
                    setTimeout(() => {
                        function stepUp(nowUp) {
                            if (lastTime > 0) {
                                const delta = nowUp - lastTime;
                                if (delta > 0 && delta < 500) window.__frameDeltas.push(delta);
                            }
                            lastTime = nowUp;
                            pos -= step * 2;
                            window.scrollTo(0, Math.max(0, pos));
                            if (pos > 0) {
                                requestAnimationFrame(stepUp);
                            } else {
                                resolve();
                            }
                        }
                        requestAnimationFrame(stepUp);
                    }, 50);
                }
            }
            requestAnimationFrame(stepDown);
        });
    }""")

    # Stop frame collection and retrieve metrics
    metrics = page.evaluate("""() => {
        window.__stopFrameLoop = true;
        const deltas = window.__frameDeltas || [];
        deltas.sort((a, b) => a - b);
        let p95 = 0;
        if (deltas.length > 0) {
            const idx = Math.min(deltas.length - 1, Math.floor(deltas.length * 0.95));
            p95 = deltas[idx];
        }
        return {
            scrollHeight: document.documentElement.scrollHeight,
            longTasks: window.__longTasks || [],
            cls: window.__clsScore || 0,
            frameSamplesCount: deltas.length,
            p95FrameTime: p95,
            medianFrameTime: deltas.length > 0 ? deltas[Math.floor(deltas.length * 0.5)] : 0
        };
    }""")

    metrics["name"] = name
    metrics["url"] = url
    print(f"  -> Scroll Height: {metrics['scrollHeight']}px")
    print(f"  -> Long Tasks (>100ms): {len(metrics['longTasks'])}")
    print(f"  -> p95 Frame Time: {metrics['p95FrameTime']:.2f}ms (target < 33ms)")
    print(f"  -> CLS Score: {metrics['cls']:.4f}")
    return metrics


def main():
    port = find_free_port()
    base_url = f"http://127.0.0.1:{port}"
    server = ServerManager(port=port)
    server.start()

    if not wait_for_server(base_url, timeout=30):
        print("Failed to start server")
        server.stop()
        sys.exit(1)

    results = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1366, "height": 768})
            page = context.new_page()

            # Enable 4x CPU Throttling via Chrome DevTools Protocol
            cdp = context.new_cdp_session(page)
            cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4})
            print("[+] 4x CPU throttling enabled via CDP.")

            for name, path in PAGES_TO_TEST:
                full_url = f"{base_url}{path}"
                res = audit_page(page, full_url, name)
                results.append(res)

            browser.close()
    finally:
        server.stop()

    # Verify gates
    all_passed = True
    print("\n=======================================================")
    print("RULE E PERFORMANCE GATE EVALUATION")
    print("=======================================================")
    for r in results:
        long_tasks_count = len(r["longTasks"])
        p95 = r["p95FrameTime"]
        lt_pass = long_tasks_count == 0
        p95_pass = p95 < 33.0
        status = "PASS" if (lt_pass and p95_pass) else "FAIL"
        if not (lt_pass and p95_pass):
            all_passed = False
        print(f"[{status}] {r['name']:<18} | Long Tasks: {long_tasks_count} | p95: {p95:.2f}ms | CLS: {r['cls']:.4f} | Height: {r['scrollHeight']}px")

    out_json = BASE_DIR / "reports" / "perf_audit.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nReport written to {out_json}")

    if all_passed:
        print("\nOVERALL STATUS: PASSED (All performance gates satisfied)")
        sys.exit(0)
    else:
        print("\nOVERALL STATUS: FAILED (Performance gate exceeded)")
        sys.exit(1)


if __name__ == "__main__":
    main()
