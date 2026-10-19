"""
Tests for Phase R8 Task 1: Mega-Menu Category Deduplication, Non-Zero Prices,
Flagship Image Cutouts, and Brand Pills.
"""

from decimal import Decimal
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase

from apps.catalog.models import Category, Product, ProductMedia
from apps.catalog.services.category_nav import get_mega_menu_categories
from apps.catalog.services.category_rules import CATEGORY_DEFINITIONS, merge_duplicate_categories


class MegaMenuCategoryNavTests(TestCase):
    def setUp(self):
        cache.clear()
        call_command("seed_categories")

    def test_merge_duplicate_categories_deduplicates_and_reassigns(self):
        canonical_cat = Category.objects.get(slug="earphones-headphones")
        dup_cat = Category.objects.create(
            name="Earphones & Headphones",
            slug="earphones-headphones-test-dup",
            display_order=99,
            is_active=True,
        )
        prod = Product.objects.create(
            raw_name="Test Headphones 999",
            display_name="Test Headphones 999",
            sku="TEST-HD-999",
            source_asin="B00TEST9999",
            category=dup_cat,
            selling_price=Decimal("1999.00"),
            mrp=Decimal("2499.00"),
            is_available=True,
        )

        res = merge_duplicate_categories()
        self.assertGreaterEqual(res["deleted_categories"], 1)

        # Check product reassigned to canonical category
        prod.refresh_from_db()
        self.assertEqual(prod.category_id, canonical_cat.id)

        # Duplicate category should no longer exist
        self.assertFalse(Category.objects.filter(slug="earphones-headphones-test-dup").exists())

    def test_mega_menu_categories_have_valid_images_and_nonzero_prices(self):
        for idx, cat in enumerate(Category.objects.all(), start=1):
            p = Product.objects.create(
                raw_name=f"Sample Product Unique {idx} {cat.slug}",
                display_name=f"Sample Product Unique {idx} {cat.slug}",
                slug=f"sample-product-unique-{idx}-{cat.slug}",
                sku=f"SKU-SAMPLE-{idx}",
                source_asin=f"B00TEST{idx:04d}",
                category=cat,
                selling_price=Decimal("1499.00"),
                mrp=Decimal("1999.00"),
                is_available=True,
                parsed_brand="ElectroBrand",
            )
            ProductMedia.objects.create(
                product=p,
                media_type="image",
                external_image_url=f"https://example.com/images/prod_{idx}.jpg",
                display_order=1,
            )

        cache.clear()
        cats = get_mega_menu_categories()
        self.assertEqual(len(cats), 10)

        slugs = [c.slug for c in cats]
        # Slugs must be unique (no duplicates in nav)
        self.assertEqual(len(slugs), len(set(slugs)))

        for cat in cats:
            self.assertGreater(cat.product_count, 0)
            self.assertGreater(cat.price_from, Decimal("0.00"))
            self.assertTrue(cat.cutout_url, f"Category {cat.slug} missing cutout_url")
            self.assertTrue(cat.top_brands, f"Category {cat.slug} missing top_brands")
            self.assertGreaterEqual(len(cat.top_brands), 1)

    def test_mega_menu_excludes_empty_categories(self):
        # Create an empty category with 0 active products
        empty_cat = Category.objects.create(
            name="Empty Ghost Category",
            slug="empty-ghost-category",
            is_active=True,
            display_order=999,
        )
        cache.clear()
        cats = get_mega_menu_categories()
        exposed_slugs = [c.slug for c in cats]
        self.assertNotIn("empty-ghost-category", exposed_slugs)
