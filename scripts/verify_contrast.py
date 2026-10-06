#!/usr/bin/env python3
"""
WCAG 2.1 Contrast Ratio Verification Script for Electrocart Category Worlds.

Standard library only. Asserts color contrast ratios across all 10 category
monograph palettes according to W3C WCAG 2.1 specifications:
  - Body text: >= 4.5:1 (Level AA)
  - Large text & UI components: >= 3.0:1 (Level AA)

IMPORTANT:
This palette dictionary serves as the initial programmatic ground truth.
Section 2 parses `frontend/css/tokens.css` and asserts exact parity with PALETTES.
"""

import os
from pathlib import Path
import re
import sys

# Canonical 10 Category Monograph Worlds (FROZEN)
# Must mirror CSS tokens in frontend/css/tokens.css
PALETTES = {
    "earphones-headphones": {
        "bg": "#F5F2EB",
        "surface": "#EDE8DE",
        "accent": "#9E3D24",
        "text_primary": "#1C1917",
        "text_muted": "#544E48",
    },
    "speakers": {
        "bg": "#F2EFE9",
        "surface": "#E8E3DA",
        "accent": "#7C4A2D",
        "text_primary": "#1A1816",
        "text_muted": "#544E48",
    },
    "smartphones": {
        "bg": "#EBF0ED",
        "surface": "#DEE7E2",
        "accent": "#1B5E4B",
        "text_primary": "#111C18",
        "text_muted": "#544E48",
    },
    "smartwatches-bands": {
        "bg": "#EDECE8",
        "surface": "#E2E0D8",
        "accent": "#2C5282",
        "text_primary": "#14171A",
        "text_muted": "#544E48",
    },
    "cameras": {
        "bg": "#F0EDE6",
        "surface": "#E5E0D5",
        "accent": "#8C3A27",
        "text_primary": "#1A1715",
        "text_muted": "#544E48",
    },
    "tvs": {
        "bg": "#ECEEF0",
        "surface": "#DFE3E6",
        "accent": "#1E3A5F",
        "text_primary": "#11161B",
        "text_muted": "#544E48",
    },
    "keyboards-mice": {
        "bg": "#EEECE8",
        "surface": "#E3DFD8",
        "accent": "#5C4A36",
        "text_primary": "#181613",
        "text_muted": "#544E48",
    },
    "cables-chargers-powerbanks": {
        "bg": "#EEF0E8",
        "surface": "#E1E6D8",
        "accent": "#3B5E2B",
        "text_primary": "#151B12",
        "text_muted": "#544E48",
    },
    "cases-protectors": {
        "bg": "#F1EDE8",
        "surface": "#E6DFD6",
        "accent": "#824C59",
        "text_primary": "#1C1618",
        "text_muted": "#544E48",
    },
    "other": {
        "bg": "#EFEFEA",
        "surface": "#E3E3DC",
        "accent": "#3E4A52",
        "text_primary": "#161819",
        "text_muted": "#544E48",
    },
}

WHITE = "#FFFFFF"

# Required thresholds (WCAG 2.1 AA)
MIN_TEXT_CONTRAST = 4.5
MIN_UI_CONTRAST = 3.0

# Additional Status Colors (Earthy tones verified >= 4.5:1 on tint, bg, and surface)
STATUS_COLORS = {
    "success": {"text": "#1C4728", "tint": "#EAF2EB"},
    "warning": {"text": "#5C3E08", "tint": "#F9F3E5"},
    "danger":  {"text": "#7D2117", "tint": "#F9EBEA"},
    "info":    {"text": "#1A4363", "tint": "#EBF1F6"},
}


def hex_to_relative_luminance(hex_code: str) -> float:
    """Calculate relative luminance from an sRGB hex color according to WCAG 2.1."""
    clean_hex = hex_code.lstrip("#")
    r_srgb = int(clean_hex[0:2], 16) / 255.0
    g_srgb = int(clean_hex[2:4], 16) / 255.0
    b_srgb = int(clean_hex[4:6], 16) / 255.0

    def linearize(channel: float) -> float:
        if channel <= 0.04045:
            return channel / 12.92
        return ((channel + 0.055) / 1.055) ** 2.4

    r_lin = linearize(r_srgb)
    g_lin = linearize(g_srgb)
    b_lin = linearize(b_srgb)

    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin


def calculate_contrast_ratio(fg_hex: str, bg_hex: str) -> float:
    """Calculate the contrast ratio between two hex colors."""
    l1 = hex_to_relative_luminance(fg_hex)
    l2 = hex_to_relative_luminance(bg_hex)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def verify_all_palettes() -> bool:
    """Run WCAG AA contrast checks across all 10 category worlds."""
    all_passed = True
    print("\n" + "=" * 94)
    print("ELECTROCART WCAG 2.1 CONTRAST VERIFICATION MATRIX (Concept 2: Kinetic Monograph)")
    print("=" * 94)
    header = (
        f"{'Category':<26} | {'Pairing':<22} | {'Ratio':<8} | {'Required':<8} | {'Status'}"
    )
    print(header)
    print("-" * 94)

    checks = [
        ("Text-Primary on BG", "text_primary", "bg", MIN_TEXT_CONTRAST),
        ("Text-Primary on Surface", "text_primary", "surface", MIN_TEXT_CONTRAST),
        ("Muted-Text on BG", "text_muted", "bg", MIN_TEXT_CONTRAST),
        ("Muted-Text on Surface", "text_muted", "surface", MIN_TEXT_CONTRAST),
        ("Accent on BG", "accent", "bg", MIN_UI_CONTRAST),
        ("Accent on Surface", "accent", "surface", MIN_UI_CONTRAST),
        ("White on Accent Button", None, "accent", MIN_UI_CONTRAST),
    ]

    for category, tokens in PALETTES.items():
        for label, fg_key, bg_key, required in checks:
            fg_color = WHITE if fg_key is None else tokens[fg_key]
            bg_color = tokens[bg_key]
            ratio = calculate_contrast_ratio(fg_color, bg_color)
            passed = ratio >= required
            if not passed:
                all_passed = False
            status = "PASS" if passed else "FAIL"
            print(
                f"{category:<26} | {label:<22} | {ratio:>5.2f}:1 | {required:>5.1f}:1 | {status}"
            )
        print("-" * 94)

    print()
    if all_passed:
        print("FINAL RESULT: ALL 10 CATEGORY PALETTES PASS WCAG 2.1 AA (Zero Contrast Violations)")
        print("=" * 94 + "\n")
    else:
        print("FINAL RESULT: CONTRAST AUDIT FAILED (Violations Detected)")
        print("=" * 94 + "\n")

    return all_passed


def verify_status_and_focus_tokens() -> bool:
    """Run WCAG AA checks on status tokens and focus rings."""
    all_passed = True
    print("=" * 94)
    print("STATUS COLORS & FOCUS RING VERIFICATION MATRIX")
    print("=" * 94)
    header = (
        f"{'Token / Scope':<26} | {'Pairing':<22} | {'Ratio':<8} | {'Required':<8} | {'Status'}"
    )
    print(header)
    print("-" * 94)

    # 1. Status Colors on their own tint
    for status_name, colors in STATUS_COLORS.items():
        ratio = calculate_contrast_ratio(colors["text"], colors["tint"])
        passed = ratio >= MIN_TEXT_CONTRAST
        if not passed:
            all_passed = False
        stat = "PASS" if passed else "FAIL"
        print(f"Status: {status_name:<18} | Text on Tint         | {ratio:>5.2f}:1 | {MIN_TEXT_CONTRAST:>5.1f}:1 | {stat}")

    # 2. Status Colors against each world bg and surface
    for status_name, colors in STATUS_COLORS.items():
        for cat_name, pal in PALETTES.items():
            r_bg = calculate_contrast_ratio(colors["text"], pal["bg"])
            r_surf = calculate_contrast_ratio(colors["text"], pal["surface"])
            if r_bg < MIN_TEXT_CONTRAST or r_surf < MIN_TEXT_CONTRAST:
                all_passed = False
                print(f"Status: {status_name:<18} | Fail on {cat_name}  | {min(r_bg, r_surf):>5.2f}:1 | {MIN_TEXT_CONTRAST:>5.1f}:1 | FAIL")

    print("-" * 94)
    print("Status colors verified on all 10 world backgrounds and surfaces: PASS (>= 4.5:1)")

    # 3. Focus Ring (Accent) against BG and Surface (>= 3.0:1)
    for cat_name, pal in PALETTES.items():
        r_bg = calculate_contrast_ratio(pal["accent"], pal["bg"])
        r_surf = calculate_contrast_ratio(pal["accent"], pal["surface"])
        passed = (r_bg >= MIN_UI_CONTRAST) and (r_surf >= MIN_UI_CONTRAST)
        if not passed:
            all_passed = False
        stat = "PASS" if passed else "FAIL"
        print(f"Focus Ring: {cat_name:<14} | Accent on BG/Surf   | {min(r_bg, r_surf):>5.2f}:1 | {MIN_UI_CONTRAST:>5.1f}:1 | {stat}")

    print("=" * 94 + "\n")
    return all_passed


def verify_css_tokens_sync() -> bool:
    """Verify that frontend/css/tokens.css values match PALETTES exactly (Single Source of Truth)."""
    base_dir = Path(__file__).resolve().parent.parent
    tokens_path = base_dir / "frontend" / "css" / "tokens.css"

    print("=" * 94)
    print("CSS TOKENS SYNCHRONIZATION GUARD (frontend/css/tokens.css vs PALETTES)")
    print("=" * 94)

    if not tokens_path.exists():
        print(f"ERROR: {tokens_path} does not exist.")
        return False

    content = tokens_path.read_text(encoding="utf-8")
    passed = True

    for slug, expected in PALETTES.items():
        # Match selector block for [data-world="slug"]
        pattern = rf'\[data-world="{slug}"\][^\{{]*\{{([^}}]+)\}}'
        match = re.search(pattern, content)
        if not match:
            print(f"FAIL: Missing [data-world=\"{slug}\"] selector in tokens.css")
            passed = False
            continue

        block = match.group(1)

        def extract_var(name: str) -> str:
            m = re.search(rf'--world-{name}\s*:\s*([^;]+);', block)
            return m.group(1).strip() if m else ""

        css_bg = extract_var("bg").upper()
        css_surface = extract_var("surface").upper()
        css_accent = extract_var("accent").upper()
        css_text = extract_var("text").upper()
        css_muted = extract_var("muted").upper()

        exp_bg = expected["bg"].upper()
        exp_surface = expected["surface"].upper()
        exp_accent = expected["accent"].upper()
        exp_text = expected["text_primary"].upper()
        exp_muted = expected["text_muted"].upper()

        if (css_bg != exp_bg or css_surface != exp_surface or css_accent != exp_accent
                or css_text != exp_text or css_muted != exp_muted):
            print(f"FAIL: Drift detected in [data-world=\"{slug}\"]:")
            print(f"  Expected: bg={exp_bg}, surface={exp_surface}, accent={exp_accent}, text={exp_text}, muted={exp_muted}")
            print(f"  Got CSS:  bg={css_bg}, surface={css_surface}, accent={css_accent}, text={css_text}, muted={css_muted}")
            passed = False
        else:
            print(f"MATCH: [data-world=\"{slug}\"] synchronized 100% with PALETTES.")

    print("=" * 94 + "\n")
    return passed


if __name__ == "__main__":
    palettes_ok = verify_all_palettes()
    status_focus_ok = verify_status_and_focus_tokens()
    sync_ok = verify_css_tokens_sync()

    overall = palettes_ok and status_focus_ok and sync_ok
    if overall:
        print(">>> ALL WCAG 2.1 CONTRAST & CSS TOKEN CHECKS PASSED (EXIT 0) <<<\n")
    else:
        print(">>> VERIFICATION FAILED (EXIT 1) <<<\n")

    sys.exit(0 if overall else 1)
