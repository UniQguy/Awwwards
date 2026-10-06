"""
Tests for search service, faceted filtering, 'did you mean' suggestions, and grid collapse.
"""

from decimal import Decimal
from django.core.management import call_command
from django.test import TestCase

from apps.catalog.models import Category, Product
from apps.catalog.queries.grid_collapse import get_collapsed_catalog_queryset
from apps.search.services.search_service import execute_catalog_search


class CatalogSearchAndCollapseTests(TestCase):
    def setUp(self):
        self.cat_audio = Category.objects.create(
            name="Audio & Headphones",
            slug="earphones-headphones",
            accent_key="earphones-headphones",
            gst_rate=Decimal("18.00"),
        )
        self.cat_phones = Category.objects.create(
            name="Smartphones",
            slug="smartphones",
            accent_key="smartphones",
            gst_rate=Decimal("18.00"),
        )

        # Product 1: Apple iPhone
        self.phone = Product.objects.create(
            category=self.cat_phones,
            sku="EC-IPHONE-14",
            slug="apple-iphone-14",
            raw_name="Apple iPhone 14 128GB Midnight",
            display_name="Apple iPhone 14",
            source_asin="B00IPHONE14",
            parsed_brand="Apple",
            selling_price=Decimal("69999.00"),
            source_rating=Decimal("4.60"),
            source_rating_count=5000,
            is_available=True,
        )

        # Product 2: Sony Headphones
        self.headphones = Product.objects.create(
            category=self.cat_audio,
            sku="EC-SONY-XM5",
            slug="sony-wh1000xm5",
            raw_name="Sony WH-1000XM5 Wireless Headphones",
            display_name="Sony WH-1000XM5",
            source_asin="B00SONYXM5",
            parsed_brand="Sony",
            selling_price=Decimal("26990.00"),
            source_rating=Decimal("4.50"),
            source_rating_count=3200,
            is_available=True,
        )

        # Products 3 & 4: Duplicate raw_name variants for grid collapse testing
        self.cable_v1 = Product.objects.create(
            category=self.cat_audio,
            sku="EC-CABLE-VAR-1",
            slug="anker-cable-1m",
            raw_name="Anker Braided USB-C Cable",
            display_name="Anker Braided USB-C Cable 1m",
            source_asin="B00ANKER01",
            parsed_brand="Anker",
            selling_price=Decimal("799.00"),
            source_rating_count=100,
            is_available=True,
        )
        self.cable_v2 = Product.objects.create(
            category=self.cat_audio,
            sku="EC-CABLE-VAR-2",
            slug="anker-cable-2m",
            raw_name="Anker Braided USB-C Cable",
            display_name="Anker Braided USB-C Cable 2m",
            source_asin="B00ANKER02",
            parsed_brand="Anker",
            selling_price=Decimal("999.00"),
            source_rating_count=200,
            is_available=True,
        )

    def test_search_by_brand_and_keyword(self):
        res = execute_catalog_search(query="iPhone")
        self.assertEqual(res["total_count"], 1)
        self.assertEqual(res["products"].first().id, self.phone.id)

        res_sony = execute_catalog_search(query="Sony")
        self.assertEqual(res_sony["total_count"], 1)
        self.assertEqual(res_sony["products"].first().id, self.headphones.id)

    def test_search_filter_by_category(self):
        res = execute_catalog_search(category_slug="smartphones")
        self.assertEqual(res["total_count"], 1)
        self.assertEqual(res["products"].first().id, self.phone.id)

    def test_search_price_bounds(self):
        res = execute_catalog_search(min_price=Decimal("50000.00"))
        self.assertEqual(res["total_count"], 1)
        self.assertEqual(res["products"].first().id, self.phone.id)

        res_low = execute_catalog_search(max_price=Decimal("1000.00"))
        self.assertEqual(res_low["total_count"], 2)

    def test_did_you_mean_suggestion(self):
        # Misspelling "Apple" -> "aplle"
        res = execute_catalog_search(query="aplle")
        self.assertEqual(res["total_count"], 0)
        self.assertEqual(res["did_you_mean"], "Apple")

    def test_grid_collapse_collapses_duplicate_raw_names(self):
        # 4 total products in DB (phone, headphones, cable_v1, cable_v2)
        # Grid collapse should yield 3 cards: cable_v1 (799) wins over cable_v2 (999)
        collapsed_qs = get_collapsed_catalog_queryset()
        self.assertEqual(collapsed_qs.count(), 3)
        collapsed_ids = set(collapsed_qs.values_list("id", flat=True))
        self.assertIn(self.cable_v1.id, collapsed_ids)
        self.assertNotIn(self.cable_v2.id, collapsed_ids)

    def test_rebuild_search_text_command(self):
        call_command("rebuild_search_text")
        self.phone.refresh_from_db()
        self.assertIn("apple", self.phone.search_text)
        self.assertIn("midnight", self.phone.search_text)
