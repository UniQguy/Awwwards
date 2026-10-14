"""
ELECTROCART Idempotent First-Run Setup Command (WP1.4).
Orchestrates a complete, clean, idempotent store initialization:
1. python manage.py migrate
2. python manage.py seed_categories
3. python manage.py import_products (if data/electronics_product.csv exists)
4. python manage.py seed_demo
5. python manage.py rebuild_search_text
6. python manage.py create_demo_admin (if DEMO_ADMIN_EMAIL & DEMO_ADMIN_PASSWORD env vars are present)
"""

import os
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Idempotently prepares database, seeds categories/coupons/shipping, imports catalog, and configures demo accounts."

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-import",
            action="store_true",
            help="Skip importing product catalog CSV even if it exists.",
        )
        parser.add_argument(
            "--admin-email",
            type=str,
            help="Administrator email (overrides DEMO_ADMIN_EMAIL env var).",
        )
        parser.add_argument(
            "--admin-password",
            type=str,
            help="Administrator password (overrides DEMO_ADMIN_PASSWORD env var).",
        )

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write("ELECTROCART DEMO SETUP: INITIATING IDEMPOTENT FIRST-RUN")
        self.stdout.write("=" * 80)

        # 1. Database Migrations
        self.stdout.write("\n[1/6] Running database migrations...")
        call_command("migrate", interactive=False)

        # 2. Seed Categories
        self.stdout.write("\n[2/6] Seeding 10 monograph product categories...")
        call_command("seed_categories")

        # 3. Import Catalog CSV if available
        if not options["skip_import"]:
            csv_path = settings.BASE_DIR / "data" / "electronics_product.csv"
            if csv_path.exists():
                self.stdout.write(f"\n[3/6] Found catalog CSV at {csv_path}. Importing products...")
                call_command("import_products", csv=str(csv_path))
            else:
                self.stdout.write(
                    f"\n[3/6] No catalog CSV found at {csv_path}. Skipping CSV import."
                )
        else:
            self.stdout.write("\n[3/6] Skipping product import (--skip-import passed).")

        # 4. Seed Demo Subsystems (inventory, zones, coupons, collections)
        self.stdout.write("\n[4/6] Seeding sample demo data (coupons, zones, inventory, collections)...")
        call_command("seed_demo")

        # 5. Rebuild Search Vectors
        self.stdout.write("\n[5/6] Rebuilding search vector representations...")
        call_command("rebuild_search_text")

        # 6. Create Demo Admin and Staff Accounts
        if options.get("admin_email"):
            os.environ["DEMO_ADMIN_EMAIL"] = options["admin_email"]
        if options.get("admin_password"):
            os.environ["DEMO_ADMIN_PASSWORD"] = options["admin_password"]

        admin_email = os.environ.get("DEMO_ADMIN_EMAIL")
        admin_password = os.environ.get("DEMO_ADMIN_PASSWORD")

        self.stdout.write("\n[6/6] Checking demo administrator setup...")
        if admin_email and admin_password:
            call_command("create_demo_admin")
        else:
            self.stdout.write(
                self.style.WARNING(
                    "Notice: DEMO_ADMIN_EMAIL and DEMO_ADMIN_PASSWORD not set in environment. "
                    "Skipping automatic demo admin creation. Run create_demo_admin or createsuperuser when needed."
                )
            )

        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS("ELECTROCART DEMO SETUP COMPLETE AND READY FOR BROWSING"))
        self.stdout.write("=" * 80)
