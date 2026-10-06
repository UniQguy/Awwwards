"""
Management command to import consumer electronics catalog from CSV with full audit reporting.
Supports --csv and --dry-run. Idempotent across multiple executions.
"""

import csv
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Set

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import Category, Product, ProductMedia, ProductSpecification
from apps.catalog.services.brands import detect_brand
from apps.catalog.services.category_rules import CATEGORY_DEFINITIONS, classify_category
from apps.catalog.services.parsing import (
    build_unique_slug,
    clean_display_name,
    extract_asin,
    parse_count,
    parse_price,
    parse_rating,
)
from apps.catalog.services.spec_extractor import extract_specifications


class Command(BaseCommand):
    help = "Imports electronics products from CSV dataset with validation and audit reporting."

    def add_arguments(self, parser):
        parser.add_argument(
            "--csv",
            type=str,
            default="data/electronics_product.csv",
            help="Path to CSV dataset file (default: data/electronics_product.csv)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Perform in-memory streaming audit without persisting any records to the database.",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=1000,
            help="Batch size for bulk database operations (default: 1000)",
        )

    def handle(self, *args, **options):
        csv_path = Path(options["csv"])
        dry_run = options["dry_run"]
        batch_size = options["batch_size"]

        if not csv_path.exists():
            self.stderr.write(self.style.ERROR(f"CSV file not found: {csv_path}"))
            return

        self.stdout.write(f"Starting catalog ingestion from {csv_path} (dry_run={dry_run})...")

        # Ensure categories exist
        category_map: Dict[str, Category] = {}
        for cat in Category.objects.all():
            category_map[cat.slug] = cat

        if not category_map and not dry_run:
            self.stdout.write("Categories missing; running automatic category seeding...")
            for item in CATEGORY_DEFINITIONS:
                c, _ = Category.objects.get_or_create(
                    slug=item["slug"],
                    defaults={
                        "name": item["name"],
                        "accent_key": item["accent_key"],
                        "hsn_code": item["hsn_code"],
                        "gst_rate": item["gst_rate"],
                        "is_gst_rate_verified": item["is_gst_rate_verified"],
                        "display_order": item["display_order"],
                        "description": item["description"],
                    },
                )
                category_map[c.slug] = c

        # In-memory tracking
        total_rows = 0
        skipped_no_asin = 0
        seen_asins_in_file: Set[str] = set()
        duplicate_asins_in_file = 0

        parsed_items: List[Dict] = []
        category_counts: Dict[str, int] = {c_slug: 0 for c_slug in [item["slug"] for item in CATEGORY_DEFINITIONS]}
        brand_counts: Dict[str, int] = {}
        price_bracket_counts = {i: 0 for i in range(9)}
        unpriced_count = 0

        # Read CSV
        with open(csv_path, mode="r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                total_rows += 1
                raw_name = (row.get("name") or "").strip()
                if not raw_name:
                    continue

                link = (row.get("link") or "").strip()
                asin = extract_asin(link)
                if not asin:
                    # Fallback check inside title or generate deterministic fallback
                    skipped_no_asin += 1
                    continue

                if asin in seen_asins_in_file:
                    duplicate_asins_in_file += 1
                    continue
                seen_asins_in_file.add(asin)

                sub_cat = (row.get("sub_category") or "").strip()
                cat_slug = classify_category(raw_name, sub_cat)
                category_counts[cat_slug] = category_counts.get(cat_slug, 0) + 1

                brand = detect_brand(raw_name)
                brand_counts[brand] = brand_counts.get(brand, 0) + 1

                selling_price = parse_price(row.get("discount_price"))
                mrp = parse_price(row.get("actual_price"))

                # Integrity: ensure MRP >= selling_price if both present
                if selling_price and mrp and mrp < selling_price:
                    mrp = selling_price
                elif selling_price and not mrp:
                    mrp = selling_price

                if selling_price is not None:
                    sp = float(selling_price)
                    if sp < 500:
                        price_bracket_counts[0] += 1
                    elif sp < 1000:
                        price_bracket_counts[1] += 1
                    elif sp < 2500:
                        price_bracket_counts[2] += 1
                    elif sp < 5000:
                        price_bracket_counts[3] += 1
                    elif sp < 10000:
                        price_bracket_counts[4] += 1
                    elif sp < 20000:
                        price_bracket_counts[5] += 1
                    elif sp < 40000:
                        price_bracket_counts[6] += 1
                    elif sp < 80000:
                        price_bracket_counts[7] += 1
                    else:
                        price_bracket_counts[8] += 1
                else:
                    unpriced_count += 1

                source_rating = parse_rating(row.get("ratings"))
                source_rating_count = parse_count(row.get("no_of_ratings"))
                image_url = (row.get("image") or "").strip()

                parsed_items.append({
                    "asin": asin,
                    "raw_name": raw_name,
                    "cat_slug": cat_slug,
                    "brand": brand,
                    "selling_price": selling_price,
                    "mrp": mrp,
                    "source_rating": source_rating,
                    "source_rating_count": source_rating_count,
                    "link": link,
                    "image_url": image_url,
                })

        # Generate report content
        report_md = f"""# Electrocart Catalog Ingestion Audit Report

- **Source File**: `{csv_path}`
- **Execution Mode**: `{'Dry Run (0 DB writes)' if dry_run else 'Production Database Ingestion'}`
- **Total CSV Rows Processed**: {total_rows:,}
- **Unique ASINs Extracted**: {len(seen_asins_in_file):,}
- **Duplicate ASINs Skipped in File**: {duplicate_asins_in_file:,}
- **Rows Skipped (No Valid ASIN)**: {skipped_no_asin:,}
- **Successfully Parsed Products**: {len(parsed_items):,}
- **Priced Products**: {len(parsed_items) - unpriced_count:,}
- **Unpriced Products**: {unpriced_count:,}

## Category Distribution
| Category Slug | Product Count |
| :--- | :--- |
"""
        for c_slug, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            report_md += f"| `{c_slug}` | {count:,} |\n"

        report_md += """
## Top 15 Brands Identified
| Brand | Product Count |
| :--- | :--- |
"""
        for b_name, count in sorted(brand_counts.items(), key=lambda x: x[1], reverse=True)[:15]:
            report_md += f"| **{b_name}** | {count:,} |\n"

        report_md += """
## Price Brackets Distribution (INR)
| Bracket | Range | Product Count |
| :--- | :--- | :--- |
| 0 | Under INR 500 | """ + f"{price_bracket_counts[0]:,} |\n"
        report_md += f"| 1 | INR 500 - 999 | {price_bracket_counts[1]:,} |\n"
        report_md += f"| 2 | INR 1,000 - 2,499 | {price_bracket_counts[2]:,} |\n"
        report_md += f"| 3 | INR 2,500 - 4,999 | {price_bracket_counts[3]:,} |\n"
        report_md += f"| 4 | INR 5,000 - 9,999 | {price_bracket_counts[4]:,} |\n"
        report_md += f"| 5 | INR 10,000 - 19,999 | {price_bracket_counts[5]:,} |\n"
        report_md += f"| 6 | INR 20,000 - 39,999 | {price_bracket_counts[6]:,} |\n"
        report_md += f"| 7 | INR 40,000 - 79,999 | {price_bracket_counts[7]:,} |\n"
        report_md += f"| 8 | INR 80,000+ | {price_bracket_counts[8]:,} |\n"

        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        report_file = reports_dir / "import_report.md"
        with open(report_file, "w", encoding="utf-8") as rf:
            rf.write(report_md)

        self.stdout.write(self.style.SUCCESS(f"Audit report written to {report_file}"))

        if dry_run:
            self.stdout.write(self.style.SUCCESS(f"DRY RUN COMPLETE: {len(parsed_items)} records audited. 0 DB writes."))
            return

        # Database persistence with idempotency
        self.stdout.write("Persisting catalog items to database...")
        existing_asins = set(Product.objects.values_list("source_asin", flat=True))

        products_to_create: List[Product] = []
        items_for_specs_and_media: List[Dict] = []

        for item in parsed_items:
            asin = item["asin"]
            if asin in existing_asins:
                # Already exists; skip creation
                continue

            cat = category_map.get(item["cat_slug"])
            if not cat:
                continue

            display_name = clean_display_name(item["raw_name"], item["brand"])
            slug = build_unique_slug(display_name, asin)
            sku = f"EC-{asin}"

            p = Product(
                category=cat,
                sku=sku,
                slug=slug,
                raw_name=item["raw_name"],
                display_name=display_name,
                source_asin=asin,
                source_url=item["link"],
                parsed_brand=item["brand"],
                selling_price=item["selling_price"],
                mrp=item["mrp"],
                is_available=(item["selling_price"] is not None and item["selling_price"] > Decimal("0.00")),
                source_rating=item["source_rating"],
                source_rating_count=item["source_rating_count"],
            )
            # Denormalized search vector
            p.search_text = f"{p.raw_name} {p.display_name} {p.parsed_brand} {cat.name} {p.sku} {p.source_asin}".lower()
            products_to_create.append(p)
            items_for_specs_and_media.append(item)

        created_count = 0
        if products_to_create:
            with transaction.atomic():
                # Bulk create products in batches
                for i in range(0, len(products_to_create), batch_size):
                    chunk = products_to_create[i : i + batch_size]
                    Product.objects.bulk_create(chunk, batch_size=batch_size)
                    created_count += len(chunk)

            # Re-fetch created products to attach media and specifications
            created_prod_map = {
                p.source_asin: p
                for p in Product.objects.filter(source_asin__in=[it["asin"] for it in items_for_specs_and_media])
            }

            media_to_create: List[ProductMedia] = []
            specs_to_create: List[ProductSpecification] = []

            for item in items_for_specs_and_media:
                asin = item["asin"]
                prod = created_prod_map.get(asin)
                if not prod:
                    continue

                if item["image_url"]:
                    media_to_create.append(
                        ProductMedia(
                            product=prod,
                            media_type="image",
                            external_image_url=item["image_url"],
                            alt_text=prod.display_name,
                            display_order=0,
                        )
                    )

                specs = extract_specifications(item["raw_name"])
                for s_key, s_val in specs.items():
                    specs_to_create.append(
                        ProductSpecification(
                            product=prod,
                            key=s_key,
                            value=s_val,
                            source="parsed_from_title",
                            is_highlight=True,
                        )
                    )

            if media_to_create:
                for i in range(0, len(media_to_create), batch_size):
                    ProductMedia.objects.bulk_create(media_to_create[i : i + batch_size], batch_size=batch_size)

            if specs_to_create:
                for i in range(0, len(specs_to_create), batch_size):
                    ProductSpecification.objects.bulk_create(specs_to_create[i : i + batch_size], batch_size=batch_size)

        self.stdout.write(
            self.style.SUCCESS(
                f"Ingestion finished: {created_count} products created, {len(existing_asins)} previously existed."
            )
        )
