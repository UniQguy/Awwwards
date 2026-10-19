"""
Tests for search service, multi-tier ranking, synonym & plural handling,
typo correction, zero-result fallback, and family_key deduplication (R7 Item 3).
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
            search_text="apple iphone 14 128gb midnight smartphone mobile",
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
            search_text="sony wh-1000xm5 wireless headphones xm5 noise cancelling",
            is_available=True,
        )

        # Product 3: boAt Bassheads Earphones (for brand+model and synonym tests)
        self.boat_earbuds = Product.objects.create(
            category=self.cat_audio,
            sku="EC-BOAT-BH100-BLK",
            slug="boat-bassheads-100-black",
            raw_name="boAt BassHeads 100 in-Ear Wired Headphones with Mic (Black)",
            display_name="boAt BassHeads 100",
            source_asin="B00BOAT100B",
            parsed_brand="boAt",
            selling_price=Decimal("399.00"),
            source_rating=Decimal("4.30"),
            source_rating_count=85000,
            search_text="boat bassheads 100 wired earphones headphones bass in-ear",
            is_available=True,
        )

        # Product 4: boAt Bassheads color variant (for family_key deduplication)
        self.boat_earbuds_white = Product.objects.create(
            category=self.cat_audio,
            sku="EC-BOAT-BH100-WHT",
            slug="boat-bassheads-100-white",
            raw_name="boAt BassHeads 100 in-Ear Wired Headphones with Mic (White)",
            display_name="boAt BassHeads 100 White",
            source_asin="B00BOAT100W",
            parsed_brand="boAt",
            selling_price=Decimal("449.00"),
            source_rating=Decimal("4.30"),
            source_rating_count=12000,
            search_text="boat bassheads 100 wired earphones headphones bass in-ear white",
            is_available=True,
        )

        # Products 5 & 6: Cable variants
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
            search_text="anker braided usb-c cable 1m",
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
            search_text="anker braided usb-c cable 2m",
            is_available=True,
        )

    def test_search_by_brand_and_keyword(self):
        res = execute_catalog_search(query="iPhone")
        self.assertGreaterEqual(res["total_count"], 1)
        self.assertEqual(res["products"][0].id, self.phone.id)

        res_sony = execute_catalog_search(query="Sony")
        self.assertGreaterEqual(res_sony["total_count"], 1)
        self.assertEqual(res_sony["products"][0].id, self.headphones.id)

    def test_search_filter_by_category(self):
        res = execute_catalog_search(category_slug="smartphones")
        self.assertEqual(res["total_count"], 1)
        self.assertEqual(res["products"][0].id, self.phone.id)

    def test_search_price_bounds(self):
        res = execute_catalog_search(min_price=Decimal("50000.00"))
        self.assertEqual(res["total_count"], 1)
        self.assertEqual(res["products"][0].id, self.phone.id)

        res_low = execute_catalog_search(max_price=Decimal("1000.00"))
        # Cable family (1 collapsed) + boat family (1 collapsed) = 2
        self.assertEqual(res_low["total_count"], 2)

    def test_synonym_search(self):
        """Searching 'earbuds' finds boAt Bassheads and Sony Headphones via synonym group."""
        res = execute_catalog_search(query="earbuds")
        self.assertGreaterEqual(res["total_count"], 1)
        result_ids = [p.id for p in res["products"]]
        self.assertIn(self.boat_earbuds.id, result_ids)

    def test_plural_and_singular_search(self):
        """Searching 'smartphone' (singular) finds phone tagged with smartphones (plural)."""
        res_sing = execute_catalog_search(query="smartphone")
        self.assertGreaterEqual(res_sing["total_count"], 1)
        self.assertEqual(res_sing["products"][0].id, self.phone.id)

        res_plur = execute_catalog_search(query="smartphones")
        self.assertGreaterEqual(res_plur["total_count"], 1)
        self.assertEqual(res_plur["products"][0].id, self.phone.id)

    def test_brand_plus_model_match(self):
        """Searching 'boat bass' matches boAt brand + Bassheads model."""
        res = execute_catalog_search(query="boat bass")
        self.assertGreaterEqual(res["total_count"], 1)
        self.assertEqual(res["products"][0].id, self.boat_earbuds.id)

    def test_typo_fuzzy_match(self):
        """Searching with typos like 'hedphones' finds headphones."""
        res = execute_catalog_search(query="hedphones")
        self.assertGreaterEqual(res["total_count"], 1)
        result_ids = [p.id for p in res["products"]]
        self.assertTrue(
            self.headphones.id in result_ids or self.boat_earbuds.id in result_ids,
            "Typo 'hedphones' should match headphones products.",
        )

    def test_zero_result_fallback_and_did_you_mean(self):
        """Queries with no exact matches return closest matches with is_fallback=True and did_you_mean."""
        res = execute_catalog_search(query="aplle")
        self.assertTrue(res["is_fallback"])
        self.assertIn("Closest matches for", res["fallback_label"])
        self.assertEqual(res["did_you_mean"], "Apple")
        self.assertGreater(len(res["products"]), 0, "Zero results must never show empty void.")

    def test_family_key_deduplication_and_option_count(self):
        """Near-duplicate variants collapse into 1 card showing option_count."""
        res = execute_catalog_search(query="boAt")
        # Both black and white variants exist in DB, but collapse to 1 family
        boat_cards = [p for p in res["products"] if p.parsed_brand == "boAt"]
        self.assertEqual(len(boat_cards), 1, "boAt variants must collapse to single representative.")
        self.assertEqual(boat_cards[0].option_count, 2, "Option count must reflect 2 variants.")

    def test_tie_breaking_order(self):
        """Equal score ties are broken by source_rating_count desc, then price asc."""
        # Query 'cable' matches cable_v1 (100 ratings, 799) and cable_v2 (200 ratings, 999)
        # When uncollapsed, cable_v2 has 200 ratings vs cable_v1 100 ratings
        res = execute_catalog_search(query="cable", collapsed=False)
        self.assertEqual(res["products"][0].id, self.cable_v2.id)

    def test_rebuild_search_text_command(self):
        call_command("rebuild_search_text")
        self.phone.refresh_from_db()
        self.assertIn("apple", self.phone.search_text)
        self.assertIn("midnight", self.phone.search_text)
