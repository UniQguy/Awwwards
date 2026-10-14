#!/usr/bin/env python3
"""
Overlap, Occlusion, and Plate Geometry Audit for ELECTROCART (WP0.4).
Validates across key pages and viewports:
 (a) Sibling section bounding boxes do not intersect/overlap.
 (b) Every product card's center point is reachable via elementFromPoint (not occluded).
 (c) Plate aspect ratio is near-square (0.9 to 1.25) and image width >= 70% of plate width.
 (d) No <img> rendered smaller than 40px unless an icon or thumbnail slot.
 (e) Broken image detection (naturalWidth == 0).
"""

import sys
import time
from pathlib import Path
from typing import Dict, List, Any

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("FATAL: playwright is not installed.")
    sys.exit(1)

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from scripts.e2e_browser import ServerManager, find_free_port, wait_for_server

PAGES_TO_AUDIT = [
    ("/", "Home Monograph"),
    ("/categories/", "Categories Index"),
    ("/c/smartphones/", "Smartphones Category"),
    ("/c/speakers/", "Speakers Category"),
    ("/c/cameras/?page=2", "Cameras Page 2"),
    ("/p/amazon-basics-flexible-premium-hdmi-cable-black-4k60hz-18gbps-3-foot-b07ksmbl2h/", "Product Detail"),
    ("/cart/", "Shopping Bag"),
]

VIEWPORTS = [
    ("1366x768", 1366, 768),
    ("1536x864", 1536, 864),
    ("1920x1080", 1920, 1080),
    ("390x844", 390, 844),
]


def audit_page(page, url_path: str, vp_name: str) -> Dict[str, Any]:
    """Runs geometry, occlusion, and image sizing assertions inside the page context."""
    results = page.evaluate("""() => {
        const defects = [];

        // (a) Section overlap check (sibling sections in main or body)
        const sections = Array.from(document.querySelectorAll('main > section, .container > section, .layout-editorial > section, section.chapter-spread, section.spread'));
        for (let i = 0; i < sections.length; i++) {
            for (let j = i + 1; j < sections.length; j++) {
                const s1 = sections[i];
                const s2 = sections[j];
                // Check if they share the same parent and are visible
                if (s1.parentElement === s2.parentElement) {
                    const r1 = s1.getBoundingClientRect();
                    const r2 = s2.getBoundingClientRect();
                    if (r1.height > 10 && r2.height > 10 && r1.width > 50 && r2.width > 50) {
                        // Vertical intersection with 2px tolerance
                        const overlapTop = Math.max(r1.top, r2.top);
                        const overlapBottom = Math.min(r1.bottom, r2.bottom);
                        const overlapHeight = overlapBottom - overlapTop;
                        if (overlapHeight > 5) {
                            defects.push({
                                type: 'SECTION_OVERLAP',
                                detail: `Sections <${s1.tagName} class="${s1.className}"> and <${s2.tagName} class="${s2.className}"> overlap by ${Math.round(overlapHeight)}px`
                            });
                        }
                    }
                }
            }
        }

        // (b) Card occlusion check via elementFromPoint
        const cards = Array.from(document.querySelectorAll('.product-card, .card-collectible, .category-lead-plate, .marquee-pick-plate, .product-card-plate'));
        cards.forEach((card, idx) => {
            const rect = card.getBoundingClientRect();
            // Only test cards within or near viewport
            if (rect.width > 30 && rect.height > 30 && rect.bottom > 0 && rect.top < window.innerHeight * 3) {
                const cx = rect.left + rect.width / 2;
                const cy = rect.top + rect.height / 2;
                if (cx >= 0 && cx <= window.innerWidth && cy >= 0 && cy <= window.innerHeight) {
                    const elem = document.elementFromPoint(cx, cy);
                    if (elem && !card.contains(elem) && elem !== card) {
                        defects.push({
                            type: 'CARD_OCCLUSION',
                            detail: `Card #${idx} (<${card.className}>) center (${Math.round(cx)}, ${Math.round(cy)}) occluded by <${elem.tagName} class="${elem.className}">`
                        });
                    }
                }
            }
        });

        // (c) Plate aspect ratio (0.9 to 1.25) & image width >= 70% of plate width
        const plates = Array.from(document.querySelectorAll('.product-card-plate, .plate, .collectible-plate, .marquee-lead-plate, .marquee-sub-plate'));
        plates.forEach((plate, idx) => {
            const prect = plate.getBoundingClientRect();
            if (prect.width > 40 && prect.height > 40) {
                const ratio = prect.width / prect.height;
                if (ratio < 0.90 || ratio > 1.25) {
                    defects.push({
                        type: 'PLATE_ASPECT_RATIO',
                        detail: `Plate #${idx} (${plate.className}) aspect ratio is ${ratio.toFixed(2)} (expected near-square 0.90 - 1.25). Dimensions: ${Math.round(prect.width)}x${Math.round(prect.height)}px`
                    });
                }

                // Check image width relative to plate width
                const img = plate.querySelector('img');
                if (img) {
                    const irect = img.getBoundingClientRect();
                    if (irect.width > 0 && prect.width > 0) {
                        const coverage = irect.width / prect.width;
                        if (coverage < 0.70) {
                            defects.push({
                                type: 'IMAGE_PLATE_COVERAGE',
                                detail: `Image inside plate #${idx} fills only ${Math.round(coverage * 100)}% of plate width (${Math.round(irect.width)}px / ${Math.round(prect.width)}px, expected >= 70%)`
                            });
                        }
                    }
                }
            }
        });

        // (d) No <img> under 40px unless an icon or thumbnail slot
        const allImgs = Array.from(document.querySelectorAll('img'));
        allImgs.forEach((img, idx) => {
            const irect = img.getBoundingClientRect();
            // Check if hidden or zero dimension
            if (irect.width > 0 && irect.height > 0) {
                const isThumbnailOrIcon = img.closest('.index-row-cutout, .nav-icon, .icon, .swatch, .thumbnail-slot, .picker-thumb, [aria-hidden="true"]');
                if (!isThumbnailOrIcon && (irect.width < 40 || irect.height < 40)) {
                    defects.push({
                        type: 'IMAGE_UNDER_40PX',
                        detail: `Image #${idx} (src="${img.getAttribute('src') || ''}") rendered tiny: ${Math.round(irect.width)}x${Math.round(irect.height)}px`
                    });
                }
            }

            // (e) Broken image
            if (img.complete && img.naturalWidth === 0 && !img.closest('.image-fallback-plate, dialog, [role="dialog"], #mini-bag-dialog') && img.getAttribute('src') && !img.getAttribute('src').startsWith('data:')) {
                defects.push({
                    type: 'BROKEN_IMAGE',
                    detail: `Broken image src: ${img.getAttribute('src') || 'none'}`
                });
            }
        });

        return { defects };
    }""")
    return results


def run_overlap_audit():
    port = find_free_port()
    base_url = f"http://127.0.0.1:{port}"
    server = ServerManager(port=port)
    server.start()

    if not wait_for_server(base_url, timeout=30):
        print("Failed to start server")
        server.stop()
        sys.exit(1)

    print("======================================================================")
    print("ELECTROCART OVERLAP, OCCLUSION & PLATE GEOMETRY AUDIT (WP0.4)")
    print("======================================================================")
    print(f"Target Server: {base_url}")
    print("Evaluating section intersections, elementFromPoint card occlusion, plate ratios, image size/coverage.\n")

    total_defects = 0
    all_defect_records = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            for vp_name, width, height in VIEWPORTS:
                print(f"\n--- AUDITING VIEWPORT {vp_name} ({width}x{height}) ---")
                context = browser.new_context(viewport={"width": width, "height": height})
                page = context.new_page()

                for path, title in PAGES_TO_AUDIT:
                    target = f"{base_url}{path}"
                    try:
                        page.goto(target, wait_until="load", timeout=15000)
                        page.wait_for_timeout(500)
                    except Exception as e:
                        print(f"Error loading {path}: {e}")
                        continue

                    res = audit_page(page, path, vp_name)
                    defects = res.get("defects", [])
                    status = "PASS" if len(defects) == 0 else "FAIL"
                    print(f"[{status}] {title:<25} ({path}) -> {len(defects)} defect(s)")
                    for d in defects:
                        print(f"       ! [{d['type']}] {d['detail']}")
                        all_defect_records.append((vp_name, path, d['type'], d['detail']))
                        total_defects += 1

                context.close()

            browser.close()
    finally:
        server.stop()

    print("\n======================================================================")
    print(f"AUDIT SUMMARY: {total_defects} defect(s) detected across all pages and viewports.")
    if total_defects == 0:
        print("OVERALL STATUS: PASSED")
    else:
        print("OVERALL STATUS: FAILED (As required by WP0.4 on unpatched build)")
    print("======================================================================\n")

    return total_defects


if __name__ == "__main__":
    defects_count = run_overlap_audit()
    # If defects exist, exit with non-zero to prove failure on current build
    sys.exit(0 if defects_count == 0 else 1)
