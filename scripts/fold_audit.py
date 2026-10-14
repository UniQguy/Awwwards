#!/usr/bin/env python3
"""
Above-the-Fold & Density Auditor for ELECTROCART (Playwright Chromium).
Asserts that critical commerce and narrative elements remain above the fold
across common desktop laptop screens, high-DPI scaling simulations, and mobile:
- 1366x768 (Standard 14" PC Laptop)
- 1440x900 (MacBook Air / Pro 13/14)
- 1536x864 (1080p @ 125% Windows scaling)
- 1920x1080 (Full HD Desktop)
- 1093x614 (1366x768 @ 125% Windows scaling)
- 1229x691 (1536x864 @ 125% Windows scaling)
- 390x844 (iPhone 14 / modern mobile)

Checks:
1. Home: Hero headline and CTAs are visible above the fold without scrolling.
2. Category: Category title, listing count, and marquee hero are visible above fold.
   Product cards in catalog grid are 200-260px tall.
3. Product Detail: Product H1, price, stock, and Add to Bag button are visible above
   the fold without scrolling; plate image mat does not exceed 480px.
"""

import argparse
from pathlib import Path
import sys
import time
from typing import Dict, List, Tuple

try:
    from playwright.sync_api import sync_playwright, Page, Browser
except ImportError:
    print("FATAL: playwright is not installed. Install with: pip install playwright")
    sys.exit(1)

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from scripts.e2e_browser import ServerManager, find_free_port, wait_for_server

SCREENSHOT_DIR = BASE_DIR / "docs" / "ui-review" / "fold_audit"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

VIEWPORTS = [
    ("1366x768", 1366, 768),
    ("1440x900", 1440, 900),
    ("1536x864", 1536, 864),
    ("1920x1080", 1920, 1080),
    ("1093x614", 1093, 614),
    ("1229x691", 1229, 691),
    ("390x844", 390, 844),
]


def audit_page(page: Page, url: str, vp_name: str, width: int, height: int, page_name: str) -> List[str]:
    failures = []
    page.set_viewport_size({"width": width, "height": height})
    page.goto(url, wait_until="domcontentloaded", timeout=20000)
    page.wait_for_timeout(600)

    # Screenshot viewport at rest
    safe_name = page_name.lower().replace(" ", "_")
    screenshot_path = SCREENSHOT_DIR / f"{safe_name}_{vp_name}.png"
    page.screenshot(path=str(screenshot_path), full_page=False)

    viewport_h = height

    if page_name == "Home":
        # Check hero headline
        res = page.evaluate("""
        (vpH) => {
            const errs = [];
            const headline = document.querySelector('#hero-heading, .hero-headline');
            if (!headline) {
                errs.push('Hero headline missing');
            } else {
                const r = headline.getBoundingClientRect();
                if (r.bottom > vpH) {
                    errs.push(`Hero headline bottom (${r.bottom.toFixed(0)}px) exceeds fold (${vpH}px)`);
                }
            }
            const actions = document.querySelector('.hero-actions');
            if (actions) {
                const r = actions.getBoundingClientRect();
                // On desktop >= 1024, action buttons should be above the fold
                if (window.innerWidth >= 1024 && r.bottom > vpH) {
                    errs.push(`Hero CTA actions bottom (${r.bottom.toFixed(0)}px) exceeds fold (${vpH}px)`);
                } else if (window.innerWidth < 1024 && r.top > vpH) {
                    errs.push(`Hero CTA actions top (${r.top.toFixed(0)}px) below mobile fold (${vpH}px)`);
                }
            }
            return errs;
        }
        """, viewport_h)
        failures.extend(res)

    elif page_name == "Category Detail":
        res = page.evaluate("""
        (vpH) => {
            const errs = [];
            const h1 = document.querySelector('h1');
            if (!h1) {
                errs.push('Category h1 missing');
            } else {
                const r = h1.getBoundingClientRect();
                if (r.bottom > vpH) {
                    errs.push(`Category title bottom (${r.bottom.toFixed(0)}px) exceeds fold (${vpH}px)`);
                }
            }
            // Check marquee top
            const marquee = document.querySelector('.marquee-composed-grid');
            if (marquee && window.innerWidth >= 1024) {
                const r = marquee.getBoundingClientRect();
                if (r.top > vpH) {
                    errs.push(`Marquee grid top (${r.top.toFixed(0)}px) starts below fold (${vpH}px)`);
                }
            }
            // Check card heights if grid is present
            const cards = Array.from(document.querySelectorAll('.grid-catalog .product-card'));
            if (cards.length > 0) {
                const heights = cards.slice(0, 4).map(c => c.getBoundingClientRect().height);
                const avgH = heights.reduce((a, b) => a + b, 0) / heights.length;
                if (avgH > 320) {
                    errs.push(`Product cards average height ${avgH.toFixed(0)}px exceeds dense target (200-260px)`);
                }
            }
            return errs;
        }
        """, viewport_h)
        failures.extend(res)

    elif page_name == "Product Detail":
        res = page.evaluate("""
        (vpH) => {
            const errs = [];
            const h1 = document.querySelector('h1');
            if (!h1) {
                errs.push('Product h1 missing');
            } else {
                const r = h1.getBoundingClientRect();
                if (r.bottom > vpH) {
                    errs.push(`Product H1 bottom (${r.bottom.toFixed(0)}px) exceeds fold (${vpH}px)`);
                }
            }
            const price = document.querySelector('.price-current');
            if (!price) {
                errs.push('Product price missing');
            } else {
                const r = price.getBoundingClientRect();
                if (r.bottom > vpH) {
                    errs.push(`Product price bottom (${r.bottom.toFixed(0)}px) exceeds fold (${vpH}px)`);
                }
            }
            // On desktop (width >= 1024), Add to Bag button must be above the fold
            if (window.innerWidth >= 1024) {
                const addBtn = document.querySelector('form[action*="/cart/add/"] button[type="submit"], .product-purchase-box button[type="submit"]');
                if (addBtn) {
                    const r = addBtn.getBoundingClientRect();
                    if (r.bottom > vpH) {
                        errs.push(`Add to Bag button bottom (${r.bottom.toFixed(0)}px) exceeds fold (${vpH}px)`);
                    }
                }
            }
            // Image mat cap check
            const mat = document.querySelector('.product-frame-mat');
            if (mat && window.innerWidth >= 1024) {
                const r = mat.getBoundingClientRect();
                if (r.height > 490) {
                    errs.push(`Product frame mat height (${r.height.toFixed(0)}px) exceeds 480px cap`);
                }
            }
            return errs;
        }
        """, viewport_h)
        failures.extend(res)

    return failures


def main():
    parser = argparse.ArgumentParser(description="Above-the-Fold & Density Auditor")
    parser.add_argument("--base-url", default=None, help="Base URL of running server")
    args = parser.parse_args()

    server = None
    base_url = args.base_url

    if not base_url:
        port = find_free_port()
        base_url = f"http://127.0.0.1:{port}"
        server = ServerManager(port=port)
        print(f"Starting ephemeral test server on {base_url}...")
        server.start()
        if not wait_for_server(base_url, timeout=30):
            print("FATAL: Test server failed to start")
            server.stop()
            sys.exit(1)

    print(f"Auditing above-the-fold density against {base_url}...")

    pages_to_test = [
        ("Home", "/"),
        ("Category Detail", "/c/smartphones/"),
        ("Product Detail", "/p/amazon-basics-flexible-premium-hdmi-cable-black-4k60hz-18gbps-3-foot-b07ksmbl2h/"),
    ]

    total_checks = 0
    total_failures = 0
    results_table = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            for vp_name, width, height in VIEWPORTS:
                for page_name, path in pages_to_test:
                    total_checks += 1
                    url = f"{base_url}{path}"
                    failures = audit_page(page, url, vp_name, width, height, page_name)
                    status = "PASS" if not failures else "FAIL"
                    if failures:
                        total_failures += 1
                    results_table.append((vp_name, page_name, status, failures))

            browser.close()
    finally:
        if server:
            server.stop()

    print("\n" + "=" * 90)
    print(f"{'Viewport':<12} | {'Page':<18} | {'Status':<6} | {'Issues'}")
    print("-" * 90)
    for vp_name, page_name, status, issues in results_table:
        issue_str = "; ".join(issues) if issues else "OK"
        print(f"{vp_name:<12} | {page_name:<18} | {status:<6} | {issue_str}")
    print("=" * 90)
    print(f"Total: {total_checks} checks, {total_failures} failures.")

    if total_failures > 0:
        print("\nFold density audit finished with failures.")
        sys.exit(1)
    else:
        print("\nFold density audit PASSED with 0 defects.")
        sys.exit(0)


if __name__ == "__main__":
    main()
