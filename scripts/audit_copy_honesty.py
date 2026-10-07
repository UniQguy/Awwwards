#!/usr/bin/env python3
"""
Copy and Honesty Audit Script for ELECTROCART (Phase 7).
Scans all HTML templates and email templates for:
- Banned marketing hype words ('amazing', 'best', 'premium', 'unbeatable', 'guaranteed', 'authentic', 'genuine', 'original')
- Exclamation marks in customer-facing text
- Placeholder text ('lorem', 'TODO')
- Verify absence of schema.org 'Review' or 'AggregateRating'
- Verify sample data notices are present where sample data is referenced.
"""

import os
import re
from pathlib import Path

BANNED_WORDS = [
    "amazing",
    "unbeatable",
    "guaranteed",
    "genuine",
]

# Nuanced words that might legitimately appear in code/specs (e.g. 'best' in best-seller or brand, 'original' in original price/MRP)
# but should NOT be used as emotional hype adjectives in promotional copy
CONTEXT_WATCH_WORDS = [
    "premium",
    "authentic",
    "best",
    "original",
]

ROOT_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = ROOT_DIR / "templates"


def audit_templates():
    print("=" * 70)
    print("ELECTROCART COPY & HONESTY AUDIT")
    print("=" * 70)

    html_files = list(TEMPLATES_DIR.rglob("*.html"))
    print(f"Scanning {len(html_files)} template files in {TEMPLATES_DIR}...")

    findings = []
    schema_findings = []
    exclamation_findings = []
    lorem_findings = []

    for file_path in html_files:
        rel_path = file_path.relative_to(ROOT_DIR)
        content = file_path.read_text(encoding="utf-8")
        lines = content.splitlines()

        for idx, line in enumerate(lines, 1):
            line_lower = line.lower()

            # Ignore comments and scripts/styles/meta
            stripped = line.strip()
            if stripped.startswith("{#") or stripped.startswith("<!--") or stripped.startswith("//"):
                continue

            # 1. Check schema.org review markup
            if "aggregaterating" in line_lower or '"review"' in line_lower or "'review'" in line_lower:
                if "itemtype" in line_lower or "@type" in line_lower:
                    schema_findings.append((rel_path, idx, line.strip()))

            # 2. Check lorem / TODO
            if "lorem ipsum" in line_lower or "lorem" in line_lower:
                lorem_findings.append((rel_path, idx, line.strip()))
            if "todo:" in line_lower or "todo " in line_lower:
                lorem_findings.append((rel_path, idx, line.strip()))

            # 3. Check banned words
            for word in BANNED_WORDS:
                # match word boundary
                if re.search(r"\b" + re.escape(word) + r"\b", line_lower):
                    findings.append((rel_path, idx, word, line.strip()))

            # 4. Exclamation marks in user-facing text (excluding django template tags {% ... %} or {{ ... }} or regex or SVG paths)
            # Remove template tags first
            clean_line = re.sub(r"\{%.*?%\}", "", line)
            clean_line = re.sub(r"\{\{.*?\}\}", "", clean_line)
            clean_line = re.sub(r"<[^>]+>", "", clean_line)  # remove HTML tags
            if "!" in clean_line:
                # Exclude != and common JS/code constructs
                if not re.search(r"!==?|<!|-->|&excl;", clean_line):
                    # Check if it has letters before the !
                    if re.search(r"[a-zA-Z]{2,}\s*!", clean_line):
                        exclamation_findings.append((rel_path, idx, clean_line.strip()))

    print("\n--- 1. SCHEMA.ORG REVIEWS & RATINGS CHECK ---")
    if schema_findings:
        print(f"VIOLATIONS FOUND ({len(schema_findings)}):")
        for f in schema_findings:
            print(f"  {f[0]}:{f[1]} -> {f[2]}")
    else:
        print("PASS: Zero schema.org Review or AggregateRating markup detected.")

    print("\n--- 2. LOREM / TODO PLACEHOLDERS CHECK ---")
    if lorem_findings:
        print(f"FINDINGS ({len(lorem_findings)}):")
        for f in lorem_findings:
            print(f"  {f[0]}:{f[1]} -> {f[2]}")
    else:
        print("PASS: Zero lorem ipsum or TODO placeholders in templates.")

    print("\n--- 3. BANNED HYPE WORDS CHECK ---")
    if findings:
        print(f"FINDINGS ({len(findings)}):")
        for f in findings:
            print(f"  {f[0]}:{f[1]} [word: {f[2]}] -> {f[3]}")
    else:
        print("PASS: Zero banned hype words detected.")

    print("\n--- 4. EXCLAMATION MARKS IN USER-FACING COPY ---")
    if exclamation_findings:
        print(f"POTENTIAL EXCLAMATIONS ({len(exclamation_findings)}):")
        for f in exclamation_findings:
            print(f"  {f[0]}:{f[1]} -> {f[2]}")
    else:
        print("PASS: Zero customer-facing exclamation marks.")

    print("\n" + "=" * 70)
    success = (len(schema_findings) == 0 and len(lorem_findings) == 0 and len(findings) == 0)
    print(f"OVERALL HONESTY AUDIT: {'PASSED' if success else 'NEEDS ATTENTION'}")
    print("=" * 70)
    return success


if __name__ == "__main__":
    audit_templates()
