"""
Management command to reclassify all catalog products using evidence-based category rules.
Outputs a before/after count matrix and writes reports/reclassification.md.
"""

from collections import Counter
from pathlib import Path
from typing import Dict

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import Category, Product
from apps.catalog.services.category_rules import classify_category


class Command(BaseCommand):
    help = "Reclassifies all catalog products based on evidence-based category rules."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Simulate reclassification without committing changes to the database.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        mode_str = "DRY RUN (no database changes)" if dry_run else "LIVE EXECUTION (updating database)"
        self.stdout.write(self.style.NOTICE(f"[*] Starting catalog reclassification: {mode_str}..."))

        categories = {c.slug: c for c in Category.objects.all()}
        total_products = Product.objects.count()
        self.stdout.write(f"[*] Total catalog products to inspect: {total_products}")

        before_counts = Counter()
        after_counts = Counter()
        transitions = Counter()
        updates = []

        products = list(Product.objects.select_related("category").only("id", "raw_name", "category__slug"))

        for prod in products:
            old_slug = prod.category.slug
            before_counts[old_slug] += 1

            new_slug = classify_category(prod.raw_name)
            after_counts[new_slug] += 1

            if old_slug != new_slug:
                transitions[(old_slug, new_slug)] += 1
                if not dry_run:
                    prod.category = categories[new_slug]
                    updates.append(prod)

        if not dry_run and updates:
            self.stdout.write(f"[*] Persisting {len(updates)} reclassified products...")
            with transaction.atomic():
                Product.objects.bulk_update(updates, ["category"], batch_size=500)
            self.stdout.write(self.style.SUCCESS(f"[+] Successfully updated {len(updates)} products in the database."))
        elif dry_run:
            self.stdout.write(self.style.WARNING(f"[!] Dry run: {len(transitions)} transition types detected ({sum(transitions.values())} products would change)."))

        # Build report
        reports_dir = Path("reports")
        reports_dir.mkdir(parents=True, exist_ok=True)
        report_path = reports_dir / "reclassification.md"

        report_lines = [
            "# Catalog Reclassification Report",
            "",
            f"**Execution Mode:** {mode_str}",
            f"**Total SKUs Processed:** {total_products}",
            f"**Total SKUs Reclassified:** {sum(transitions.values())}",
            "",
            "## 1. Category Distribution: Before vs After",
            "",
            "| Slug | Category Name | Before Count | Before Share | After Count | After Share | Net Shift |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ]

        for slug, cat in sorted(categories.items(), key=lambda x: x[1].display_order):
            b_cnt = before_counts[slug]
            a_cnt = after_counts[slug]
            b_pct = (b_cnt / total_products * 100) if total_products else 0
            a_pct = (a_cnt / total_products * 100) if total_products else 0
            diff = a_cnt - b_cnt
            sign = "+" if diff > 0 else ""
            report_lines.append(
                f"| `{slug}` | {cat.name} | {b_cnt} | {b_pct:.1f}% | {a_cnt} | {a_pct:.1f}% | {sign}{diff} |"
            )

        report_lines.extend([
            "",
            "---",
            "",
            "## 2. Key Category Transition Shifts",
            "",
            "| Origin Category | Destination Category | Reclassified Count |",
            "| :--- | :--- | :--- |",
        ])

        for (from_slug, to_slug), count in transitions.most_common(25):
            report_lines.append(f"| `{from_slug}` | `{to_slug}` | {count} |")

        report_lines.extend([
            "",
            "---",
            "",
            "## 3. Specific Defect Verifications (F-02)",
            "",
        ])

        # Query verification
        cameras_redmi = Product.objects.filter(category__slug="cameras", raw_name__icontains="Redmi").count()
        cameras_sandisk = Product.objects.filter(category__slug="cameras", raw_name__icontains="SanDisk").count()
        cameras_sd = Product.objects.filter(category__slug="cameras", raw_name__icontains="SD Card").count()
        tvs_stick = Product.objects.filter(category__slug="tvs", raw_name__icontains="Fire TV Stick").count()

        report_lines.extend([
            f"- Titles in Cameras containing 'Redmi': **{cameras_redmi}** (Target: 0)",
            f"- Titles in Cameras containing 'SanDisk': **{cameras_sandisk}** (Target: 0)",
            f"- Titles in Cameras containing 'SD Card': **{cameras_sd}** (Target: 0)",
            f"- Titles in TVs containing 'Fire TV Stick': **{tvs_stick}** (Target: 0)",
            "",
        ])

        content = "\n".join(report_lines)
        report_path.write_text(content, encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"[+] Reclassification report written to {report_path}"))

        # Print summary to console
        self.stdout.write("\n=================== RECLASSIFICATION SUMMARY ===================")
        self.stdout.write(f"Total Products: {total_products}")
        self.stdout.write(f"Total Reclassified: {sum(transitions.values())}")
        self.stdout.write(f"Other Share: {after_counts['other']} / {total_products} ({(after_counts['other']/total_products*100):.1f}%)")
        self.stdout.write(f"Cameras with 'Redmi': {cameras_redmi}")
        self.stdout.write(f"Cameras with 'SanDisk': {cameras_sandisk}")
        self.stdout.write(f"Cameras with 'SD Card': {cameras_sd}")
        self.stdout.write(f"TVs with 'Fire TV Stick': {tvs_stick}")
        self.stdout.write("================================================================\n")
