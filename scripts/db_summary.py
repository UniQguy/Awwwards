#!/usr/bin/env python3
"""
Electrocart Database Summary Audit Script (WP1).
Audits and prints:
- Database engine, vendor, and file path
- PRAGMA integrity_check and PRAGMA foreign_key_check
- Exact row counts for every table in the SQLite database
- Migration status and unapplied migration check
- Seed status of catalogue, inventory, shipping zones, coupons, and collections
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

import django
django.setup()

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from apps.accounts.models import Address, User
from apps.catalog.models import Category, Collection, Product, ProductMedia, ProductSpecification
from apps.catalog.services.price_distribution import calculate_price_distribution
from apps.inventory.models import Inventory
from apps.orders.models import Order, Invoice
from apps.promotions.models import Coupon
from apps.shipping.models import PincodeServiceability, ShippingConfig, ShippingZone


def print_summary():
    print("=" * 80)
    print("ELECTROCART DATABASE ENGINE & METRICS AUDIT (WP1)")
    print("=" * 80)

    # 1. Engine, Vendor, and Path
    db_settings = connection.settings_dict
    vendor = connection.vendor
    engine = db_settings.get("ENGINE", "unknown")
    name = db_settings.get("NAME", "unknown")
    abs_path = Path(name).resolve() if name else "in-memory"

    print(f"\n[DATABASE CONFIGURATION]")
    print(f"  Engine:                  {engine}")
    print(f"  Vendor:                  {vendor}")
    print(f"  Database Path:           {abs_path}")
    print(f"  File Exists:             {abs_path.exists() if isinstance(abs_path, Path) else 'N/A'}")
    if isinstance(abs_path, Path) and abs_path.exists():
        size_mb = abs_path.stat().st_size / (1024 * 1024)
        print(f"  File Size:               {size_mb:.2f} MB")

    # 2. PRAGMA Integrity & Foreign Key Checks
    print(f"\n[PRAGMA HEALTH CHECKS]")
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA integrity_check;")
        integrity_res = cursor.fetchall()
        integrity_ok = len(integrity_res) == 1 and integrity_res[0][0] == "ok"
        print(f"  PRAGMA integrity_check:   {'PASS (ok)' if integrity_ok else f'FAIL ({integrity_res})'}")

        cursor.execute("PRAGMA foreign_key_check;")
        fk_res = cursor.fetchall()
        fk_ok = len(fk_res) == 0
        print(f"  PRAGMA foreign_key_check: {'PASS (0 violations)' if fk_ok else f'FAIL ({len(fk_res)} violations)'}")

    # 3. Migration Status
    print(f"\n[MIGRATION STATUS]")
    executor = MigrationExecutor(connection)
    targets = executor.loader.graph.leaf_nodes()
    unapplied = executor.migration_plan(targets)
    if not unapplied:
        print(f"  All migrations applied:  PASS (0 unapplied migrations)")
    else:
        print(f"  All migrations applied:  FAIL ({len(unapplied)} unapplied migrations)")
        for migration, _ in unapplied:
            print(f"    - {migration.app_label}: {migration.name}")

    # 4. Table Row Counts (Master inspection)
    print(f"\n[TABLE ROW COUNTS (ALL TABLES)]")
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
        tables = [row[0] for row in cursor.fetchall()]

        total_rows = 0
        print(f"  {'Table Name':<42} {'Row Count':>12}")
        print(f"  {'-'*42} {'-'*12}")
        for tbl in tables:
            # Table names come from sqlite_master, safe to format
            cursor.execute(f'SELECT COUNT(*) FROM "{tbl}";')
            count = cursor.fetchone()[0]
            total_rows += count
            print(f"  {tbl:<42} {count:>12,}")
        print(f"  {'-'*42} {'-'*12}")
        print(f"  {'TOTAL ENTITIES ACROSS ALL TABLES':<42} {total_rows:>12,}")

    # 5. Core Business Seed Status
    print(f"\n[CORE SUBSYSTEM SEED STATUS]")
    cat_count = Category.objects.count()
    prod_count = Product.objects.count()
    purchasable = Product.objects.filter(is_available=True, selling_price__gt=0).count()
    inv_count = Inventory.objects.count()
    zone_count = ShippingZone.objects.count()
    pin_count = PincodeServiceability.objects.count()
    coupon_count = Coupon.objects.count()
    col_count = Collection.objects.count()
    user_count = User.objects.count()
    order_count = Order.objects.count()
    invoice_count = Invoice.objects.count()

    print(f"  Catalogue (Categories):  {cat_count:>6} categories  [{'SEEDED' if cat_count >= 10 else 'NEEDS SEED'}]")
    print(f"  Catalogue (Products):    {prod_count:>6} products    [{'SEEDED' if prod_count > 0 else 'NEEDS SEED'}]")
    print(f"  Catalogue (Purchasable): {purchasable:>6} products")
    print(f"  Inventory Tracking:      {inv_count:>6} SKUs        [{'SEEDED' if inv_count > 0 else 'NEEDS SEED'}]")
    print(f"  Shipping (Zones):        {zone_count:>6} zones       [{'SEEDED' if zone_count > 0 else 'NEEDS SEED'}]")
    print(f"  Shipping (PIN Overrides):{pin_count:>6} pincodes")
    print(f"  Promotions (Coupons):    {coupon_count:>6} active      [{'SEEDED' if coupon_count > 0 else 'NEEDS SEED'}]")
    print(f"  Collections:             {col_count:>6} curated     [{'SEEDED' if col_count > 0 else 'NEEDS SEED'}]")
    print(f"  Registered Users:        {user_count:>6} users")
    print(f"  Customer Orders:         {order_count:>6} orders")
    print(f"  Invoices Generated:      {invoice_count:>6} invoices")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    print_summary()
