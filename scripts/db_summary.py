#!/usr/bin/env python3
"""
Electrocart Database Summary Audit Script.
Prints system entity counts, category breakdowns, price brackets, and tax/shipping configurations.
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

from apps.accounts.models import Address, User
from apps.catalog.models import Category, Collection, Product, ProductMedia, ProductSpecification
from apps.catalog.services.price_distribution import calculate_price_distribution
from apps.shipping.models import PincodeServiceability, ShippingConfig, ShippingZone


def print_summary():
    print("=" * 80)
    print("ELECTROCART DATABASE METRICS & AUDIT SUMMARY")
    print("=" * 80)

    # Accounts
    user_count = User.objects.count()
    staff_count = User.objects.filter(is_staff=True).count()
    addr_count = Address.objects.count()
    print(f"\n[ACCOUNTS]")
    print(f"  Total Users:             {user_count}")
    print(f"  Staff / Admin Users:     {staff_count}")
    print(f"  Customer Addresses:      {addr_count}")

    # Shipping
    cfg = ShippingConfig.get_solo()
    zone_count = ShippingZone.objects.count()
    pin_count = PincodeServiceability.objects.count()
    print(f"\n[SHIPPING ENGINE]")
    print(f"  Free Shipping Threshold: INR {cfg.free_shipping_threshold}")
    print(f"  Standard Shipping Fee:   INR {cfg.standard_fee}")
    print(f"  COD Fee:                 INR {cfg.cod_fee}")
    print(f"  Shipping Zones:          {zone_count}")
    print(f"  Pincode Overrides:       {pin_count}")

    # Catalog
    cat_count = Category.objects.count()
    prod_count = Product.objects.count()
    purchasable = Product.objects.filter(is_available=True, selling_price__gt=0).count()
    media_count = ProductMedia.objects.count()
    spec_count = ProductSpecification.objects.count()
    col_count = Collection.objects.count()

    print(f"\n[CATALOG & MERCHANDISE]")
    print(f"  Categories:              {cat_count}")
    print(f"  Total Products:          {prod_count}")
    print(f"  Purchasable Products:    {purchasable}")
    print(f"  Media Assets:            {media_count}")
    print(f"  Specifications Extracted:{spec_count}")
    print(f"  Curated Collections:     {col_count}")

    print("\n[PRODUCTS BY CATEGORY]")
    for cat in Category.objects.all():
        p_count = cat.products.count()
        avail_count = cat.products.filter(is_available=True).count()
        print(f"  - {cat.name:<28} ({cat.slug:<26}): {p_count:5} products ({avail_count:5} in stock) [HSN: {cat.hsn_code}, GST: {cat.gst_rate}%]")

    print("\n[PRICE BRACKET DISTRIBUTION]")
    distribution = calculate_price_distribution(Product.objects.filter(selling_price__isnull=False))
    for bar in distribution:
        bar_visual = "#" * int(bar["height_percent"] // 2)
        print(f"  Bracket {bar['index']} ({bar['label']:<16}): {bar['count']:5} items | {bar_visual} ({bar['height_percent']}%)")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    print_summary()
