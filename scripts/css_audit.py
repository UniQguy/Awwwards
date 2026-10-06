#!/usr/bin/env python3
"""
CSS Quality & Token Discipline Auditor for ELECTROCART (Phase 4 Quality Gate).
Scans all CSS files in frontend/css/:
1. Enforces that only frontend/css/tokens.css contains raw hex/rgb/hsl color values;
   all other CSS files must strictly reference var(--world-...) or var(--color-...) tokens,
   or valid standard keywords (transparent, currentColor, inherit).
2. Enforces that '!important' is forbidden except in print rules or reduced-motion layers.
"""

from pathlib import Path
import re
import sys

HEX_COLOR_PATTERN = re.compile(r'#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b')
RGB_COLOR_PATTERN = re.compile(r'\b(?:rgb|rgba|hsl|hsla)\s*\(')
IMPORTANT_PATTERN = re.compile(r'!\s*important', re.IGNORECASE)


def audit_css_files() -> bool:
    base_dir = Path(__file__).resolve().parent.parent
    css_dir = base_dir / "frontend" / "css"

    if not css_dir.exists():
        print(f"Error: {css_dir} directory does not exist.")
        return False

    violations = []
    print("\n" + "=" * 80)
    print("ELECTROCART CSS DISCIPLINE & TOKEN COMPLIANCE AUDIT")
    print("=" * 80)

    for css_file in sorted(css_dir.rglob("*.css")):
        rel_path = css_file.relative_to(base_dir)
        is_tokens_file = (css_file.name == "tokens.css")
        is_print_file = (css_file.name == "print.css")

        content = css_file.read_text(encoding="utf-8")
        lines = content.splitlines()

        in_reduced_motion = False
        in_print_block = False

        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()

            # Track media block context
            if "@media (prefers-reduced-motion" in stripped:
                in_reduced_motion = True
            if "@media print" in stripped:
                in_print_block = True
            if stripped == "}" and (in_reduced_motion or in_print_block):
                in_reduced_motion = False
                in_print_block = False

            # Ignore comments
            if stripped.startswith("/*") or stripped.startswith("*"):
                continue

            # Check 1: Raw colors forbidden outside tokens.css
            if not is_tokens_file:
                # Disallow hex colors
                hex_matches = HEX_COLOR_PATTERN.findall(stripped)
                if hex_matches:
                    violations.append(
                        f"{rel_path}:{line_num}: Raw hex color {hex_matches} forbidden. Use var(--world-...) or var(--color-...)."
                    )

                # Disallow rgb/rgba/hsl outside url() or shadow tokens
                rgb_matches = RGB_COLOR_PATTERN.findall(stripped)
                if rgb_matches:
                    violations.append(
                        f"{rel_path}:{line_num}: Raw functional color {rgb_matches} forbidden. Use tokens."
                    )

            # Check 2: !important forbidden except in reduced-motion or print
            if IMPORTANT_PATTERN.search(stripped):
                allowed = is_print_file or in_reduced_motion or in_print_block
                if not allowed:
                    violations.append(
                        f"{rel_path}:{line_num}: '!important' forbidden outside print or reduced-motion layers."
                    )

    if violations:
        print(f"FAILED: Found {len(violations)} CSS token / styling violation(s):")
        for v in violations:
            print(f"  [VIOLATION] {v}")
        print("=" * 80 + "\n")
        return False
    else:
        print("PASSED: Zero hard-coded colors outside tokens.css. Zero illegal !important directives.")
        print("=" * 80 + "\n")
        return True


if __name__ == "__main__":
    success = audit_css_files()
    sys.exit(0 if success else 1)
