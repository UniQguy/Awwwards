#!/usr/bin/env python3
"""
WCAG 2.1 Contrast Ratio Verification Script for Electrocart Category Worlds.

Standard library only. Asserts color contrast ratios across all 10 category
monograph palettes according to W3C WCAG 2.1 specifications:
  - Body text: >= 4.5:1 (Level AA)
  - Large text & UI components: >= 3.0:1 (Level AA)

IMPORTANT:
This palette dictionary serves as the initial programmatic ground truth.
Once `frontend/css/tokens.css` is authored in Tier 2B, these color tokens must
remain identical across both files to maintain systemic synchronization.
"""

import sys

# Canonical 10 Category Monograph Worlds
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
        return True
    else:
        print("FINAL RESULT: CONTRAST AUDIT FAILED (Violations Detected)")
        print("=" * 94 + "\n")
        return False


if __name__ == "__main__":
    success = verify_all_palettes()
    sys.exit(0 if success else 1)
