#!/usr/bin/env python3
"""
Audits product classification across the 10 canonical categories in the database.
Outputs reports/classification_audit.md with:
- Category distribution counts
- 60 seeded-random titles per category
- Conflict titles matching multiple category rules and their winning classification
"""

import os
import random
import sys
from pathlib import Path

# Setup Django environment
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

import django
django.setup()

from apps.catalog.models import Category, Product
from apps.catalog.services.category_rules import CLASSIFICATION_RULES, classify_category

REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_FILE = REPORTS_DIR / "classification_audit.md"


def run_audit():
    print("[*] Running classification audit...")
    categories = list(Category.objects.all().order_by("display_order"))
    total_products = Product.objects.count()

    lines = [
        "# Catalog Classification Audit Report",
        "",
        f"**Total Catalog SKUs:** {total_products}",
        "",
        "## 1. Category Distribution Summary",
        "",
        "| Slug | Category Name | SKU Count | Share (%) |",
        "| :--- | :--- | :--- | :--- |",
    ]

    cat_products = {}
    for cat in categories:
        prods = list(Product.objects.filter(category=cat).values_list("raw_name", flat=True))
        cat_products[cat.slug] = prods
        share = (len(prods) / total_products * 100) if total_products else 0
        lines.append(f"| `{cat.slug}` | {cat.name} | {len(prods)} | {share:.1f}% |")

    lines.extend([
        "",
        "---",
        "",
        "## 2. Multi-Category Rule Conflicts Audit",
        "",
        "Titles matching keyword patterns across two or more categories:",
        "",
        "| Product Title | Matching Rules | Assigned Winner |",
        "| :--- | :--- | :--- |",
    ])

    # Sample conflicts
    all_prods = list(Product.objects.all().values_list("raw_name", "category__slug")[:3000])
    conflict_count = 0
    for title, current_slug in all_prods:
        matches = []
        for slug, pattern in CLASSIFICATION_RULES:
            if pattern.search(title):
                matches.append(slug)
        if len(matches) >= 2:
            conflict_count += 1
            if conflict_count <= 100:  # Cap table at 100 examples for readability
                rules_str = ", ".join(f"`{m}`" for m in matches)
                safe_title = title.replace("|", "/").strip()
                lines.append(f"| {safe_title} | {rules_str} | `{current_slug}` |")

    lines.extend([
        "",
        f"Total conflict candidates evaluated in sample: {conflict_count}",
        "",
        "---",
        "",
        "## 3. Seeded Random Samples (60 Titles per Category)",
        "",
    ])

    rng = random.Random(42)  # Seeded for deterministic output
    for cat in categories:
        prods = cat_products[cat.slug]
        sample_size = min(60, len(prods))
        sample = rng.sample(prods, sample_size) if prods else []
        lines.extend([
            f"### Category: {cat.name} (`{cat.slug}` - {len(prods)} total)",
            "",
        ])
        for idx, title in enumerate(sample, 1):
            lines.append(f"{idx}. {title}")
        lines.append("")

    content = "\n".join(lines)
    AUDIT_FILE.write_text(content, encoding="utf-8")
    print(f"[+] Audit written to {AUDIT_FILE}")


if __name__ == "__main__":
    run_audit()
