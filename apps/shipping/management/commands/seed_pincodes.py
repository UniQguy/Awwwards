"""
Management command to seed delivery zones and serviceability records.
"""

import csv
from pathlib import Path
from django.core.management.base import BaseCommand

from ...models import PincodeServiceability, ShippingConfig, ShippingZone


class Command(BaseCommand):
    help = "Seed delivery zones and PIN code serviceability data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--sample",
            action="store_true",
            help="Seed 9 national sample delivery zones based on leading digit (1-9).",
        )
        parser.add_argument(
            "--csv",
            type=str,
            help="Path to CSV file with real PIN code serviceability data.",
        )

    def handle(self, *args, **options):
        # 1. Guarantee ShippingConfig singleton exists
        config = ShippingConfig.get_solo()
        self.stdout.write(
            self.style.SUCCESS(
                f"ShippingConfig initialized: Free threshold INR {config.free_shipping_threshold}, Standard fee INR {config.standard_fee}"
            )
        )

        # 2. Seed 9 sample zones if --sample or default
        if options["sample"] or not options["csv"]:
            sample_zones = [
                ("1", "Northern Zone (Delhi/Punjab/Haryana/HP/JK)", 3, 5),
                ("2", "Northern Plains (UP/Uttarakhand)", 3, 5),
                ("3", "Western Zone (Rajasthan/Gujarat)", 3, 5),
                ("4", "West-Central Zone (Maharashtra/Goa/MP/CG)", 3, 5),
                ("5", "Southern Zone 1 (Andhra/Telangana/Karnataka)", 2, 4),
                ("6", "Southern Zone 2 (Tamil Nadu/Kerala)", 2, 4),
                ("7", "Eastern Zone (WB/Odisha/Bihar/Jharkhand)", 4, 6),
                ("8", "North-Eastern Zone (Assam/NE States)", 5, 7),
                ("9", "Army Postal / Special Territory", 5, 7),
            ]

            created_count = 0
            for prefix, name, days_min, days_max in sample_zones:
                _, created = ShippingZone.objects.update_or_create(
                    pin_prefix=prefix,
                    defaults={
                        "name": f"SAMPLE {name}",
                        "est_days_min": days_min,
                        "est_days_max": days_max,
                        "cod_allowed": True,
                        "is_active": True,
                        "source": "sample",
                    },
                )
                if created:
                    created_count += 1

            self.stdout.write(
                self.style.WARNING(
                    "NOTICE: Seeded 9 SAMPLE delivery zones. This is mock/development data, not real carrier serviceability."
                )
            )
            self.stdout.write(self.style.SUCCESS(f"Seeded {created_count} new sample zones."))

        # 3. Import CSV if supplied
        if options["csv"]:
            csv_path = Path(options["csv"])
            if not csv_path.exists():
                self.stderr.write(f"File not found: {csv_path}")
                return

            imported_count = 0
            with open(csv_path, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    pincode = row.get("pincode", "").strip()
                    if not pincode:
                        continue
                    PincodeServiceability.objects.update_or_create(
                        pincode=pincode,
                        defaults={
                            "state": row.get("state", "").strip(),
                            "is_serviceable": row.get("is_serviceable", "true").lower() in ("true", "1", "yes"),
                            "est_days_min": int(row.get("est_days_min", 3)),
                            "est_days_max": int(row.get("est_days_max", 5)),
                            "cod_allowed": row.get("cod_allowed", "true").lower() in ("true", "1", "yes"),
                            "source": "imported",
                        },
                    )
                    imported_count += 1

            self.stdout.write(self.style.SUCCESS(f"Imported/updated {imported_count} PIN serviceability records."))
