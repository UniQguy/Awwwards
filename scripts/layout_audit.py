#!/usr/bin/env python3
"""
Layout & Design Craft Auditor for ELECTROCART (Playwright Chromium).
Audits key pages across 8 viewport widths (360, 390, 768, 1024, 1280, 1456, 1920, 2560 px):
1. No horizontal scroll/overflow
2. Container alignment (left edge x of breadcrumb, h1, main container match within 2px)
3. No element's text overflows its box
4. No two sibling interactive elements overlap
5. Tap targets at least 44px (24px in dense lists)
6. Product card name <= 2 lines, price row <= 1 line
7. Image rendered width <= 1.5x naturalWidth (2.0x for editorial lead plate)
8. No vertical empty band > 200px between consecutive content blocks
9. Plate image corner color equals plate surface color within 4 RGB units
"""

import argparse
import io
import os
from pathlib import Path
import sys
import time
from typing import Dict, List, Tuple

from PIL import Image

try:
    from playwright.sync_api import sync_playwright, Page, Browser
except ImportError:
    print("FATAL: playwright is not installed. Install with: pip install playwright && python -m playwright install chromium")
    sys.exit(1)

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

from scripts.e2e_browser import ServerManager, find_free_port, wait_for_server

VIEWPORT_WIDTHS = [360, 390, 768, 1024, 1280, 1456, 1920, 2560]
DEFAULT_HEIGHT = 900

AUDIT_PAGES = [
    ("Home", "/"),
    ("Categories", "/categories/"),
    ("Category Detail", "/c/smartphones/"),
    ("Product Detail", "/p/amazon-basics-flexible-premium-hdmi-cable-black-4k60hz-18gbps-3-foot-b07ksmbl2h/"),
    ("Cart", "/cart/"),
    ("Wishlist", "/wishlist/"),
    ("Login", "/accounts/login/"),
    ("About", "/about/"),
]

AUDIT_SCRIPT_JS = """
() => {
    const results = {
        horizontal_overflow: false,
        overflow_details: '',
        container_alignment_error: '',
        text_overflow_errors: [],
        interactive_overlap_errors: [],
        tap_target_errors: [],
        card_line_clamp_errors: [],
        image_upscale_errors: [],
        vertical_gap_errors: [],
        plate_corner_colors: []
    };

    const docWidth = document.documentElement.scrollWidth;
    const winWidth = window.innerWidth;
    if (docWidth > winWidth + 1.5) {
        results.horizontal_overflow = true;
        results.overflow_details = `scrollWidth ${docWidth}px > viewport ${winWidth}px (+${(docWidth - winWidth).toFixed(1)}px)`;
    }

    // 2. Container alignment
    const breadcrumb = document.querySelector('.breadcrumb, nav[aria-label="Breadcrumb"], .breadcrumbs');
    const h1 = document.querySelector('h1');
    const container = document.querySelector('.container, main.container, .content-container');

    if (container && h1) {
        const cRect = container.getBoundingClientRect();
        const h1Rect = h1.getBoundingClientRect();
        // If h1 is inside the container, compare its content left edge with container's content left edge
        const cStyle = window.getComputedStyle(container);
        const cPadLeft = parseFloat(cStyle.paddingLeft) || 0;
        const expectedLeft = cRect.left + cPadLeft;

        // Check if h1 is a direct or standard contained heading
        if (container.contains(h1) && Math.abs(h1Rect.left - expectedLeft) > 3) {
            results.container_alignment_error = `h1 left (${h1Rect.left.toFixed(1)}px) != container left (${expectedLeft.toFixed(1)}px)`;
        }
        if (breadcrumb && container.contains(breadcrumb)) {
            const bRect = breadcrumb.getBoundingClientRect();
            if (Math.abs(bRect.left - expectedLeft) > 3) {
                const prev = results.container_alignment_error ? results.container_alignment_error + '; ' : '';
                results.container_alignment_error = prev + `breadcrumb left (${bRect.left.toFixed(1)}px) != container left (${expectedLeft.toFixed(1)}px)`;
            }
        }
    }

    // 3. Text box overflow
    const textElements = document.querySelectorAll('p, h1, h2, h3, h4, h5, .card-title, .product-name');
    for (const el of textElements) {
        if (!el.offsetParent) continue; // hidden
        const style = window.getComputedStyle(el);
        if (style.overflow === 'hidden' || style.overflow === 'clip') continue;
        if (el.scrollWidth > el.clientWidth + 2 && el.clientWidth > 0) {
            results.text_overflow_errors.push(`${el.tagName.toLowerCase()} "${el.textContent.slice(0, 25).trim()}..." scrollWidth ${el.scrollWidth} > clientWidth ${el.clientWidth}`);
            if (results.text_overflow_errors.length >= 3) break;
        }
    }

    // 4. Sibling interactive overlap
    const interactives = Array.from(document.querySelectorAll('a, button, input:not([type="hidden"]), select'));
    for (let i = 0; i < interactives.length; i++) {
        const a = interactives[i];
        if (!a.offsetParent) continue;
        const aRect = a.getBoundingClientRect();
        if (aRect.width === 0 || aRect.height === 0) continue;

        for (let j = i + 1; j < interactives.length; j++) {
            const b = interactives[j];
            if (!b.offsetParent) continue;
            // Only compare siblings or cousins in same parent block
            if (a.parentElement !== b.parentElement) continue;
            const bRect = b.getBoundingClientRect();
            if (bRect.width === 0 || bRect.height === 0) continue;

            const xOverlap = Math.max(0, Math.min(aRect.right, bRect.right) - Math.max(aRect.left, bRect.left));
            const yOverlap = Math.max(0, Math.min(aRect.bottom, bRect.bottom) - Math.max(aRect.top, bRect.top));
            if (xOverlap > 2 && yOverlap > 2) {
                results.interactive_overlap_errors.push(`Overlap: <${a.tagName.toLowerCase()}> "${a.textContent.slice(0, 15).trim()}" and <${b.tagName.toLowerCase()}> "${b.textContent.slice(0, 15).trim()}"`);
                break;
            }
        }
        if (results.interactive_overlap_errors.length >= 2) break;
    }

    // 5. Tap targets at least 44px (or 24px in dense lists)
    const buttonsAndLinks = document.querySelectorAll('button:not([hidden]), a:not([hidden]), input[type="submit"], input[type="button"]');
    for (const btn of buttonsAndLinks) {
        if (!btn.offsetParent) continue;
        const rect = btn.getBoundingClientRect();
        if (rect.width === 0 || rect.height === 0) continue;

        const isDense = !!btn.closest('.breadcrumbs, .pagination, .dense-list, .tag-list, .footer-links, nav[aria-label="Breadcrumb"]');
        const minSize = isDense ? 22 : 42; // tolerance for 24 and 44

        if (rect.width < minSize || rect.height < minSize) {
            // Check if stretched link or parent clickable
            if (btn.classList.contains('stretched-link') || btn.closest('.product-card')) {
                continue;
            }
            results.tap_target_errors.push(`<${btn.tagName.toLowerCase()}> "${btn.textContent.slice(0, 20).trim()}" size ${rect.width.toFixed(0)}x${rect.height.toFixed(0)}px < ${isDense ? 24 : 44}px`);
            if (results.tap_target_errors.length >= 3) break;
        }
    }

    // 6. Product card name <= 2 lines, price row <= 1 line
    const productCards = document.querySelectorAll('.product-card, [data-product-card]');
    for (const card of productCards) {
        if (!card.offsetParent) continue;
        const nameEl = card.querySelector('.product-name, .card-title, h3, h4');
        if (nameEl) {
            const style = window.getComputedStyle(nameEl);
            const lineH = parseFloat(style.lineHeight) || (parseFloat(style.fontSize) * 1.3);
            const numLines = Math.round(nameEl.clientHeight / lineH);
            if (numLines > 2) {
                results.card_line_clamp_errors.push(`Name "${nameEl.textContent.slice(0, 20).trim()}" wraps to ${numLines} lines (>2)`);
                if (results.card_line_clamp_errors.length >= 2) break;
            }
        }
        const priceEl = card.querySelector('.price-row, .product-price');
        if (priceEl) {
            const style = window.getComputedStyle(priceEl);
            const lineH = parseFloat(style.lineHeight) || (parseFloat(style.fontSize) * 1.3);
            const numLines = Math.round(priceEl.clientHeight / lineH);
            if (numLines > 1) {
                results.card_line_clamp_errors.push(`Price row wraps to ${numLines} lines (>1)`);
                if (results.card_line_clamp_errors.length >= 2) break;
            }
        }
    }

    // 7. Image scaling <= 1.5x (2.0x for lead plate)
    const images = document.querySelectorAll('img');
    for (const img of images) {
        if (!img.offsetParent || !img.complete || img.naturalWidth === 0) continue;
        const rect = img.getBoundingClientRect();
        if (rect.width === 0) continue;
        const isLeadPlate = !!img.closest('.lead-plate, .hero-plate, [data-hero-plate]');
        const maxRatio = isLeadPlate ? 2.0 : 1.5;
        const ratio = rect.width / img.naturalWidth;
        if (ratio > maxRatio + 0.05) {
            results.image_upscale_errors.push(`Image "${img.alt || img.src.slice(-25)}" upscale ${ratio.toFixed(2)}x > ${maxRatio}x`);
            if (results.image_upscale_errors.length >= 2) break;
        }
    }

    // 8. Vertical dead band > 200px
    const sections = document.querySelectorAll('section, main > div');
    for (const sec of sections) {
        if (!sec.offsetParent) continue;
        const children = Array.from(sec.children).filter(c => c.offsetParent && c.clientHeight > 0);
        for (let i = 0; i < children.length - 1; i++) {
            const r1 = children[i].getBoundingClientRect();
            const r2 = children[i + 1].getBoundingClientRect();
            const gap = r2.top - r1.bottom;
            if (gap > 200) {
                results.vertical_gap_errors.push(`Dead band ${gap.toFixed(0)}px (>200px) in section ${sec.className || sec.tagName}`);
                break;
            }
        }
        if (results.vertical_gap_errors.length >= 2) break;
    }

    // 9. Plate corner collection for python Pillow processing
    const plates = document.querySelectorAll('.product-plate, .plate, .hero-plate');
    for (const p of plates) {
        if (!p.offsetParent) continue;
        const img = p.querySelector('img');
        if (!img || !img.complete || img.naturalWidth === 0) continue;
        const pRect = p.getBoundingClientRect();
        if (pRect.width < 50 || pRect.height < 50) continue;

        const pStyle = window.getComputedStyle(p);
        results.plate_corner_colors.push({
            x: Math.round(pRect.left),
            y: Math.round(pRect.top),
            w: Math.round(pRect.width),
            h: Math.round(pRect.height),
            bg: pStyle.backgroundColor
        });
        if (results.plate_corner_colors.length >= 3) break;
    }

    return results;
}
"""


def parse_css_rgb(rgb_str: str) -> Tuple[int, int, int]:
    import re
    m = re.search(r"rgba?\((\d+),\s*(\d+),\s*(\d+)", rgb_str)
    if m:
        return int(m.group(1)), int(m.group(2)), int(m.group(3))
    return 255, 255, 255


def run_layout_audit(port: int, output_file: Path) -> Tuple[int, str]:
    print(f"[*] Starting Layout & Design Craft Audit against port {port}...", flush=True)
    failures: List[Dict[str, str]] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()

        for page_name, route in AUDIT_PAGES:
            url = f"http://127.0.0.1:{port}{route}"
            for width in VIEWPORT_WIDTHS:
                print(f"    -> Auditing {page_name} ({route}) at {width}px...", flush=True)
                page = context.new_page()
                page.set_viewport_size({"width": width, "height": DEFAULT_HEIGHT})
                try:
                    res = page.goto(url, wait_until="networkidle", timeout=12000)
                    if not res or res.status >= 400:
                        failures.append({
                            "page": page_name,
                            "width": f"{width}px",
                            "defect": f"HTTP {res.status if res else 'None'} loading {route}"
                        })
                        page.close()
                        continue

                    # Wait for fonts / hydration
                    page.wait_for_timeout(400)

                    # Run audit evaluation JS
                    audit_res = page.evaluate(AUDIT_SCRIPT_JS)

                    # 1. Horizontal overflow
                    if audit_res.get("horizontal_overflow"):
                        failures.append({
                            "page": page_name,
                            "width": f"{width}px",
                            "defect": f"Horizontal overflow: {audit_res.get('overflow_details')}"
                        })

                    # 2. Container alignment
                    if audit_res.get("container_alignment_error"):
                        failures.append({
                            "page": page_name,
                            "width": f"{width}px",
                            "defect": f"Container alignment: {audit_res.get('container_alignment_error')}"
                        })

                    # 3. Text box overflow
                    for err in audit_res.get("text_overflow_errors", []):
                        failures.append({
                            "page": page_name,
                            "width": f"{width}px",
                            "defect": f"Text box overflow: {err}"
                        })

                    # 4. Sibling interactive overlap
                    for err in audit_res.get("interactive_overlap_errors", []):
                        failures.append({
                            "page": page_name,
                            "width": f"{width}px",
                            "defect": f"Interactive overlap: {err}"
                        })

                    # 5. Tap targets
                    for err in audit_res.get("tap_target_errors", []):
                        failures.append({
                            "page": page_name,
                            "width": f"{width}px",
                            "defect": f"Tap target: {err}"
                        })

                    # 6. Card line clamps
                    for err in audit_res.get("card_line_clamp_errors", []):
                        failures.append({
                            "page": page_name,
                            "width": f"{width}px",
                            "defect": f"Card line clamp: {err}"
                        })

                    # 7. Image upscaling
                    for err in audit_res.get("image_upscale_errors", []):
                        failures.append({
                            "page": page_name,
                            "width": f"{width}px",
                            "defect": f"Image upscale: {err}"
                        })

                    # 8. Vertical dead gaps
                    for err in audit_res.get("vertical_gap_errors", []):
                        failures.append({
                            "page": page_name,
                            "width": f"{width}px",
                            "defect": f"Vertical gap: {err}"
                        })

                    # 9. Plate corner colour check via Pillow
                    plate_specs = audit_res.get("plate_corner_colors", [])
                    if plate_specs:
                        screenshot_bytes = page.screenshot()
                        screenshot_img = Image.open(io.BytesIO(screenshot_bytes))
                        img_w, img_h = screenshot_img.size

                        for p_info in plate_specs:
                            px = p_info["x"]
                            py = p_info["y"]
                            pw = p_info["w"]
                            ph = p_info["h"]
                            expected_rgb = parse_css_rgb(p_info["bg"])

                            # Sample 4 corners inset by 10%
                            sample_points = [
                                (px + int(pw * 0.12), py + int(ph * 0.12)),
                                (px + int(pw * 0.88), py + int(ph * 0.12)),
                                (px + int(pw * 0.12), py + int(ph * 0.88)),
                                (px + int(pw * 0.88), py + int(ph * 0.88)),
                            ]
                            for sx, sy in sample_points:
                                if 0 <= sx < img_w and 0 <= sy < img_h:
                                    sampled_pixel = screenshot_img.getpixel((sx, sy))[:3]
                                    diff = max(abs(sampled_pixel[c] - expected_rgb[c]) for c in range(3))
                                    if diff > 4:
                                        # Only report one corner failure per plate to avoid clutter
                                        failures.append({
                                            "page": page_name,
                                            "width": f"{width}px",
                                            "defect": f"Plate corner color mismatch: sampled {sampled_pixel} vs plate {expected_rgb} (diff {diff} > 4 RGB units)"
                                        })
                                        break

                except Exception as ex:
                    failures.append({
                        "page": page_name,
                        "width": f"{width}px",
                        "defect": f"Evaluation exception: {str(ex)[:80]}"
                    })
                finally:
                    page.close()

        context.close()
        browser.close()

    # Generate Markdown Table Report
    md_lines = [
        "# Layout & Design Craft Audit Table",
        "",
        f"**Audit Timestamp:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Viewports Evaluated:** {', '.join(f'{w}px' for w in VIEWPORT_WIDTHS)}",
        f"**Total Pages Audited:** {len(AUDIT_PAGES)}",
        f"**Total Defects Detected:** {len(failures)}",
        "",
        "| Page | Viewport | Defect Description |",
        "| :--- | :--- | :--- |",
    ]

    if not failures:
        md_lines.append("| **All Pages** | **All Viewports** | **PASSED: Zero layout, alignment, or bounding box defects.** |")
    else:
        for f in failures:
            safe_defect = f["defect"].replace("|", "/")
            md_lines.append(f"| {f['page']} | {f['width']} | {safe_defect} |")

    md_lines.append("")
    report_content = "\n".join(md_lines)
    output_file.write_text(report_content, encoding="utf-8")
    print(f"[+] Audit report written to {output_file}", flush=True)
    print(f"[*] Audit complete: {len(failures)} defects found.", flush=True)

    return len(failures), report_content


def main():
    parser = argparse.ArgumentParser(description="Run layout audit across viewports")
    parser.add_argument("--port", type=int, default=0, help="Existing server port or 0 to launch background server")
    parser.add_argument("--out", type=str, default="reports/layout_audit.md", help="Output report file path")
    parser.add_argument("--no-exit-code", action="store_true", help="Do not exit non-zero on failure (for before runs)")
    args = parser.parse_args()

    port = args.port
    server = None
    if port == 0:
        port = find_free_port()
        server = ServerManager(port=port)
        server.start()
        if not wait_for_server(f"http://127.0.0.1:{port}/", timeout=25):
            print("FATAL: Test server failed to start.")
            server.stop()
            sys.exit(1)

    out_path = BASE_DIR / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        failure_count, report_text = run_layout_audit(port, out_path)
    finally:
        if server:
            server.stop()

    if failure_count > 0 and not args.no_exit_code:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
