"""
Management command to seed inventory levels across catalog products using deterministic ASIN hashing.
Creates a realistic retail mix:
80% healthy stock (15 - 100 units), 10% low stock (1 - 4 units), 5% out of stock (0 units), 5% unallocated.
"""

import hashlib
from typing import List

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import Product
from apps.inventory.models import Inventory


class Command(BaseCommand):
    help = "Seeds deterministic physical inventory quantities across catalog products."

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch-size",
            type=int,
            default=1000,
            help="Batch size for bulk insertion (default: 1000)",
        )

    def handle(self, *args, **options):
        batch_size = options["batch_size"]
        self.stdout.write("Seeding physical inventory records...")

        products = Product.objects.all().order_by("id")
        existing_inv_prod_ids = set(Inventory.objects.values_list("product_id", flat=True))

        to_create: List[Inventory] = []
        counts = {"healthy": 0, "low": 0, "out_of_stock": 0, "unallocated": 0}

        for prod in products:
            if prod.id in existing_inv_prod_ids:
                continue

            # Deterministic bucket from md5 hash of ASIN
            h_int = int(hashlib.md5(prod.source_asin.encode("utf-8")).hexdigest()[:8], 16)
            mod100 = h_int % 100

            if mod100 < 5:
                # 5% Unallocated (no inventory record created)
                counts["unallocated"] += 1
                continue
            elif mod100 < 10:
                # 5% Out of stock (quantity 0)
                qty = 0
                counts["out_of_stock"] += 1
            elif mod100 < 20:
                # 10% Low stock (1 - 4 units)
                qty = 1 + (h_int % 4)
                counts["low"] += 1
            else:
                # 80% Healthy stock (15 - 100 units)
                qty = 15 + (h_int % 86)
                counts["healthy"] += 1

            to_create.append(
                Inventory(
                    product=prod,
                    quantity=qty,
                    low_stock_threshold=5,
                    is_sample_data=True,
                )
            )

        created_count = 0
        if to_create:
            with transaction.atomic():
                for i in range(0, len(to_create), batch_size):
                    chunk = to_create[i : i + batch_size]
                    Inventory.objects.bulk_create(chunk, batch_size=batch_size)
                    created_count += len(chunk)

        self.stdout.write(
            self.style.SUCCESS(
                f"Inventory seeding finished: {created_count} records created.\n"
                f"Distribution: Healthy={counts['healthy']}, Low={counts['low']}, Out of Stock={counts['out_of_stock']}, Unallocated={counts['unallocated']}"
            )
        )
