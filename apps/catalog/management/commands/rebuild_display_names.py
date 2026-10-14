"""
Management command to clean and rebuild display names and search text across all catalog products.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.catalog.models import Product
from apps.catalog.services.brands import detect_brand
from apps.catalog.services.parsing import clean_display_name


class Command(BaseCommand):
    help = "Rebuilds clean display names, parsed brands, and search text for all products in the database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch-size",
            type=int,
            default=1000,
            help="Batch size for updates (default: 1000)",
        )

    def handle(self, *args, **options):
        batch_size = options["batch_size"]
        self.stdout.write("Rebuilding product display names, brands, and search vectors...")

        products = list(Product.objects.select_related("category").all())
        updated = 0
        samples = []

        for idx, p in enumerate(products):
            old_brand = p.parsed_brand
            old_name = p.display_name
            p.parsed_brand = detect_brand(p.raw_name)
            p.display_name = clean_display_name(p.raw_name, p.parsed_brand)
            brand = p.parsed_brand or ""
            cat_name = p.category.name if p.category_id else ""
            p.search_text = f"{p.raw_name} {p.display_name} {brand} {cat_name} {p.sku} {p.source_asin}".lower()
            if idx < 20 or old_brand != p.parsed_brand:
                if len(samples) < 20:
                    samples.append((p.sku, old_brand, p.parsed_brand, old_name, p.display_name))

        with transaction.atomic():
            for i in range(0, len(products), batch_size):
                chunk = products[i : i + batch_size]
                Product.objects.bulk_update(chunk, ["parsed_brand", "display_name", "search_text"], batch_size=batch_size)
                updated += len(chunk)

        self.stdout.write("\nSample Cleaned Products (Before -> After):")
        for sku, ob, nb, on, nn in samples:
            self.stdout.write(f"  [{sku}] Brand: '{ob}' -> '{nb}'")
            self.stdout.write(f"        Title: '{on}' -> '{nn}'")

        self.stdout.write(
            self.style.SUCCESS(f"\nSuccessfully updated brands, display names and search vectors for {updated} products.")
        )
