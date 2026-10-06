"""
Unified demo seeding orchestration command.
Runs all seeding routines in logical dependency order:
Categories -> Inventory -> Delivery Pincodes -> Coupons -> Curated Collections.
"""

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Orchestrates all demo seeding routines to bootstrap the commerce database."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("=" * 60))
        self.stdout.write(self.style.NOTICE("BOOTSTRAPPING ELECTROCART DEMO COMMERCE ENVIRONMENT"))
        self.stdout.write(self.style.NOTICE("=" * 60))

        # 1. Categories
        self.stdout.write("\n[1/5] Seeding Categories & Tax Rules...")
        call_command("seed_categories")

        # 2. Inventory
        self.stdout.write("\n[2/5] Seeding Physical Inventory...")
        call_command("seed_inventory")

        # 3. Pincodes
        self.stdout.write("\n[3/5] Seeding Delivery Zones & Pincodes...")
        call_command("seed_pincodes", sample=True)

        # 4. Coupons
        self.stdout.write("\n[4/5] Seeding Promotional Coupons...")
        call_command("seed_coupons")

        # 5. Collections
        self.stdout.write("\n[5/5] Seeding Editorial Collections...")
        call_command("seed_collections")

        self.stdout.write(self.style.NOTICE("\n" + "=" * 60))
        self.stdout.write(self.style.SUCCESS("DEMO COMMERCE SEEDING COMPLETE!"))
        self.stdout.write(self.style.NOTICE("=" * 60))
