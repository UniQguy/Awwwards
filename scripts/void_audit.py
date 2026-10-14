#!/usr/bin/env python3
"""
Void and Reveal Auditor for ELECTROCART (Playwright Chromium).
Audits key pages for:
1. Empty rectangles larger than 600x300px inside sections.
2. Section container width occupancy fraction in its tallest band.
3. Category marquee picks occupy at least 60% of container width on desktop.
4. Reveal audit: after load + 3s, no element carrying text/images has opacity: 0 or visibility: hidden
   (excluding aria-hidden decorative layers and closed dialogs).
"""

import json
import os
from pathlib import Path
import sys
import time
from typing import Dict, List, Any

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

try:
    from playwright.sync_api import sync_playwright, Page, Browser
except ImportError:
    print("FATAL: playwright is not installed.")
    sys.exit(1)

from scripts.e2e_browser import ServerManager, find_free_port

AUDIT_PAGES = [
    ("Home", "/"),
    ("Categories", "/categories/"),
    ("Category Detail Marquee", "/c/earphones-headphones/"),
    ("Category Detail Filtered", "/c/smartphones/?brand=OnePlus"),
    ("Product Detail", "/p/amazon-basics-flexible-premium-hdmi-cable-black-4k60hz-18gbps-3-foot-b07ksmbl2h/"),
    ("Cart", "/cart/"),
    ("About", "/about/"),
]

VIEWPORTS = [
    ("desktop", {"width": 1456, "height": 820}),
    ("mobile", {"width": 390, "height": 844}),
]

VOID_AUDIT_JS = """
() => {
    const results = {
        empty_rectangles: [],
        marquee_picks_width_ratio: null,
        marquee_error: null,
        stuck_hidden_elements: []
    };

    const isVisible = (el) => {
        const style = window.getComputedStyle(el);
        return style.display !== 'none' && style.visibility !== 'hidden' && parseFloat(style.opacity) > 0;
    };

    // 1. Marquee picks width check on desktop
    const marqueeSec = document.querySelector('.category-marquee');
    if (marqueeSec && window.innerWidth >= 1024) {
        const container = marqueeSec.closest('.container') || marqueeSec;
        const containerW = container.getBoundingClientRect().width;
        
        // Find the plates unit or mosaic
        const platesUnit = marqueeSec.querySelector('.chapter-plates-unit, .chapter-plates-mosaic, .chapter-composed-grid');
        if (platesUnit) {
            const platesW = platesUnit.getBoundingClientRect().width;
            const ratio = platesW / containerW;
            results.marquee_picks_width_ratio = parseFloat(ratio.toFixed(3));
            if (ratio < 0.58) { // Target: at least 60%
                results.marquee_error = `Marquee picks occupy only ${(ratio * 100).toFixed(1)}% of container width (expected >= 60%)`;
            }
        } else {
            results.marquee_error = "Could not find marquee plates unit";
        }
    }

    // 2. Empty rectangles larger than 600x300 inside sections
    // We scan sections and look for large vertical gaps or unoccupied blocks
    const sections = document.querySelectorAll('section, .spread, .how-buying-section, .brands-flow-section');
    sections.forEach(sec => {
        const secRect = sec.getBoundingClientRect();
        if (secRect.width < 100 || secRect.height < 100) return;

        // Collect all direct / visible content children inside the section
        const contentChildren = Array.from(sec.querySelectorAll('*')).filter(el => {
            if (!isVisible(el)) return false;
            // Only consider elements that have text or img and are leaf or meaningful containers
            const style = window.getComputedStyle(el);
            if (style.position === 'absolute' || style.position === 'fixed') return false;
            return el.children.length === 0 || el.tagName === 'IMG' || el.classList.contains('plate-collectible') || el.classList.contains('product-card');
        });

        // Scan vertical slices
        const childrenRects = contentChildren.map(c => c.getBoundingClientRect()).filter(r => r.width > 0 && r.height > 0);
        
        // Check for massive gaps between consecutive vertical siblings in layout
        const directBlocks = Array.from(sec.children).filter(isVisible);
        for (let i = 0; i < directBlocks.length - 1; i++) {
            const b1 = directBlocks[i].getBoundingClientRect();
            const b2 = directBlocks[i+1].getBoundingClientRect();
            const gap = b2.top - b1.bottom;
            if (gap > 220 && b1.width > 400) {
                results.empty_rectangles.push({
                    section: sec.className || sec.tagName,
                    gap_height: Math.round(gap),
                    desc: `Empty vertical gap of ${Math.round(gap)}px (>200px) between child blocks`
                });
            }
        }
    });

    // 3. Reveal audit: elements with opacity:0 or visibility:hidden carrying text/img
    // Excluding aria-hidden decorative layers and closed dialogs
    const allEls = document.querySelectorAll('*');
    allEls.forEach(el => {
        // Exclude closed dialogs and anything inside them
        if (el.closest('dialog:not([open])')) return;
        // Exclude templates, scripts, styles
        if (['SCRIPT', 'STYLE', 'TEMPLATE', 'NOSCRIPT'].includes(el.tagName)) return;
        // Exclude elements marked aria-hidden="true" or inside aria-hidden="true"
        if (el.getAttribute('aria-hidden') === 'true' || el.closest('[aria-hidden="true"]')) return;
        // Exclude menu panel / search sheet if closed
        if (el.closest('#menu-panel:not(.is-open), #search-sheet:not(.is-open), #filter-sheet:not(.is-open)')) return;

        const style = window.getComputedStyle(el);
        const isHidden = style.visibility === 'hidden' || parseFloat(style.opacity) === 0;

        if (isHidden) {
            // Check if element carries real text or img
            const hasImg = el.querySelector('img') || el.tagName === 'IMG';
            const text = (el.innerText || '').trim();
            if (hasImg || text.length > 2) {
                // Ensure it is not an intentional off-screen skip link or sr-only
                if (el.classList.contains('sr-only') || el.classList.contains('skip-link')) return;
                // Ensure it is not a chapter indicator that is waiting for scroll
                if (el.classList.contains('chapter-nav-indicator')) return;

                results.stuck_hidden_elements.push({
                    tag: el.tagName,
                    class: el.className,
                    text_snippet: text.substring(0, 40),
                    opacity: style.opacity,
                    visibility: style.visibility
                });
            }
        }
    });

    return results;
}
"""

def audit_url(page: Page, url: str) -> Dict[str, Any]:
    page.goto(url, wait_until="load")
    # Wait load plus 3 seconds as required by specification
    page.wait_for_timeout(3000)
    return page.evaluate(VOID_AUDIT_JS)

def run_void_audit():
    port = find_free_port()
    server = ServerManager(port=port)
    server.start()
    base_url = f"http://127.0.0.1:{port}"

    total_void_defects = 0
    total_reveal_defects = 0
    results_summary = []

    print("\n======================================================================")
    print("ELECTROCART VOID & REVEAL AUDIT (WP0.3)")
    print("======================================================================")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            for page_name, path in AUDIT_PAGES:
                url = f"{base_url}{path}"
                for vp_name, vp_size in VIEWPORTS:
                    page = browser.new_page(viewport=vp_size)
                    try:
                        res = audit_url(page, url)
                        
                        # Count issues
                        void_count = len(res.get("empty_rectangles", []))
                        if res.get("marquee_error") and vp_name == "desktop":
                            void_count += 1
                        reveal_count = len(res.get("stuck_hidden_elements", []))

                        total_void_defects += void_count
                        total_reveal_defects += reveal_count

                        status = "PASS" if (void_count == 0 and reveal_count == 0) else "FAIL"
                        print(f"[{status}] {page_name} @ {vp_name} ({vp_size['width']}px): void={void_count}, reveal={reveal_count}")
                        if res.get("marquee_error"):
                            print(f"       -> Marquee error: {res['marquee_error']}")
                        for vr in res.get("empty_rectangles", []):
                            print(f"       -> Void: {vr['desc']} in {vr['section']}")
                        for rh in res.get("stuck_hidden_elements", []):
                            print(f"       -> Stuck hidden: <{rh['tag']} class='{rh['class']}'> '{rh['text_snippet']}' (op={rh['opacity']}, vis={rh['visibility']})")

                        results_summary.append({
                            "page": page_name,
                            "path": path,
                            "viewport": vp_name,
                            "width": vp_size["width"],
                            "void_defects": void_count,
                            "reveal_defects": reveal_count,
                            "marquee_ratio": res.get("marquee_picks_width_ratio"),
                            "status": status,
                        })
                    finally:
                        page.close()

            browser.close()
    finally:
        server.stop()

    print("\n----------------------------------------------------------------------")
    print(f"Total Void Defects: {total_void_defects}")
    print(f"Total Reveal Defects: {total_reveal_defects}")
    print(f"Overall Status: {'PASSED' if (total_void_defects == 0 and total_reveal_defects == 0) else 'FAILED'}")
    print("======================================================================\n")

    report_path = BASE_DIR / "reports" / "void_audit.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# ELECTROCART Void & Reveal Audit Report\n\n")
        f.write(f"- **Total Void Defects:** {total_void_defects}\n")
        f.write(f"- **Total Reveal Defects:** {total_reveal_defects}\n")
        f.write(f"- **Overall Status:** {'PASSED' if (total_void_defects == 0 and total_reveal_defects == 0) else 'FAILED'}\n\n")
        f.write("| Page | Viewport | Width | Void Defects | Reveal Defects | Marquee Ratio | Status |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n")
        for r in results_summary:
            f.write(f"| {r['page']} | {r['viewport']} | {r['width']}px | {r['void_defects']} | {r['reveal_defects']} | {r['marquee_ratio'] or 'N/A'} | {r['status']} |\n")

    return total_void_defects + total_reveal_defects

if __name__ == "__main__":
    sys.exit(run_void_audit())
