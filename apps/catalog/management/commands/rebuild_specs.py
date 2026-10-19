"""
Management command to rebuild parsed specifications for all catalog products.
Deletes only source='parsed_from_title' rows then recreates using validated spec extractor.
Prints and writes a min, median, max distribution table per category.
"""

from collections import defaultdict
import statistics
from pathlib import Path
import re
from typing import Dict, List

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import Category, Product, ProductSpecification
from apps.catalog.services.spec_extractor import extract_specifications


class Command(BaseCommand):
    help = "Rebuilds technical specifications parsed from titles with category range guards."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("[*] Rebuilding product specifications from titles..."))

        # 1. Idempotently delete only parsed_from_title specs
        deleted_count, _ = ProductSpecification.objects.filter(source="parsed_from_title").delete()
        self.stdout.write(f"[*] Cleared {deleted_count} existing parsed specifications.")

        # 2. Extract specs for all products
        products = list(
            Product.objects.select_related("category").only(
                "id", "raw_name", "category__slug", "selling_price", "parsed_brand", "description"
            )
        )
        specs_to_create: List[ProductSpecification] = []

        # Metric tracking per category: {category_slug: {spec_key: [numeric_values]}}
        metrics: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))

        for prod in products:
            cat_slug = prod.category.slug if prod.category else ""
            extracted = extract_specifications(
                prod.raw_name,
                category_slug=cat_slug,
                price=prod.selling_price,
                brand=prod.parsed_brand,
                description=prod.description,
            )

            for order_idx, (spec_key, spec_data) in enumerate(extracted.items(), start=1):
                val_str = spec_data["value"]
                specs_to_create.append(
                    ProductSpecification(
                        product=prod,
                        key=spec_key,
                        value=val_str,
                        source="parsed_from_title",
                        is_highlight=True,
                        display_order=order_idx,
                    )
                )

                # Extract numeric metric for distribution table
                num_val = None
                if spec_key == "screen_size":
                    m = re.search(r"(\d+(?:\.\d+)?)", val_str)
                    if m:
                        num_val = float(m.group(1))
                elif spec_key in ("ram", "storage"):
                    m = re.search(r"(\d+)", val_str)
                    if m:
                        num_val = float(m.group(1))
                        if "TB" in val_str:
                            num_val *= 1024
                elif spec_key == "battery":
                    m = re.search(r"(\d+)", val_str)
                    if m:
                        num_val = float(m.group(1))
                elif spec_key == "charging_wattage":
                    m = re.search(r"(\d+)", val_str)
                    if m:
                        num_val = float(m.group(1))
                elif spec_key == "playtime":
                    m = re.search(r"(\d+)", val_str)
                    if m:
                        num_val = float(m.group(1))

                if num_val is not None and cat_slug:
                    metrics[cat_slug][spec_key].append(num_val)

        # 3. Bulk create specifications
        batch_size = 1000
        with transaction.atomic():
            for i in range(0, len(specs_to_create), batch_size):
                ProductSpecification.objects.bulk_create(specs_to_create[i : i + batch_size], batch_size=batch_size)

        self.stdout.write(self.style.SUCCESS(f"[+] Successfully created {len(specs_to_create)} validated specifications."))

        # 4. Generate distribution table
        reports_dir = Path("reports")
        reports_dir.mkdir(parents=True, exist_ok=True)
        report_file = reports_dir / "specs_distribution.md"

        lines = [
            "# Product Specifications Distribution Table",
            "",
            f"**Total Parsed Specifications:** {len(specs_to_create)}",
            "",
            "| Category | Spec Key | Metric Unit | Min | Median | Max | Count |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ]

        categories = Category.objects.order_by("display_order")
        console_table = []
        for cat in categories:
            cat_slug = cat.slug
            cat_metrics = metrics.get(cat_slug, {})
            for spec_key, values in sorted(cat_metrics.items()):
                if not values:
                    continue
                min_v = min(values)
                med_v = statistics.median(values)
                max_v = max(values)
                cnt = len(values)

                unit = "in" if spec_key == "screen_size" else ("GB" if spec_key in ("ram", "storage") else ("mAh" if spec_key == "battery" else ("W" if spec_key == "charging_wattage" else "Hrs")))
                row_str = f"| `{cat_slug}` | `{spec_key}` | {unit} | {min_v:g} | {med_v:g} | {max_v:g} | {cnt} |"
                lines.append(row_str)
                console_table.append(f"{cat_slug:22} | {spec_key:15} | {min_v:6g} | {med_v:6g} | {max_v:6g} | ({cnt} SKUs)")

        report_file.write_text("\n".join(lines), encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"[+] Distribution table written to {report_file}"))

        self.stdout.write("\n=================== SPECIFICATION DISTRIBUTION MATRIX ===================")
        self.stdout.write("Category               | Spec Key        | Min    | Median | Max    | Sample")
        self.stdout.write("-------------------------------------------------------------------------")
        for row in console_table:
            self.stdout.write(row)
        self.stdout.write("=========================================================================\n")
