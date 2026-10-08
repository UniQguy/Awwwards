"""
Tests for product families (F-12) and clean display names (F-11).
"""

from decimal import Decimal
from django.test import TestCase

from apps.catalog.models import Category, Product
from apps.catalog.services.editorial import category_spread, home_chapters
from apps.catalog.services.families import family_key
from apps.catalog.services.parsing import TRAILING_CONNECTORS, clean_display_name


class FamilyKeyAndDisplayNameTests(TestCase):
    def test_family_key_redmi_9a_sport_variants(self):
        v1 = "Redmi 9A Sport (Carbon Black, 2GB RAM, 32GB Storage) | 2GHz Octa-core Helio G25"
        v2 = "Redmi 9A Sport (Coral Green, 3GB RAM, 32GB Storage) | 2GHz Octa-core Helio G25"
        v3 = "Redmi 9A Sport (Metallic Blue, 2GB RAM, 32GB Storage)"
        k1 = family_key(v1)
        k2 = family_key(v2)
        k3 = family_key(v3)
        self.assertEqual(k1, k2)
        self.assertEqual(k2, k3)
        self.assertIn("redmi 9a sport", k1)

    def test_family_key_boat_bassheads_100_colours(self):
        b1 = "boAt BassHeads 100 in-Ear Wired Headphones with Mic (Black)"
        b2 = "boAt BassHeads 100 in-Ear Wired Headphones with Mic (White)"
        b3 = "boAt Bassheads 100 in Ear Wired Earphones with Mic(Furious Red)"
        k1 = family_key(b1)
        k2 = family_key(b2)
        k3 = family_key(b3)
        self.assertEqual(k1, k2)
        self.assertEqual(k2, k3)
        self.assertIn("boat bassheads 100", k1)

    def test_family_key_fitbit_versa_2_colourways(self):
        f1 = "Fitbit FB507BKBK Versa 2 Health & Fitness Smartwatch with Heart Rate, Music, Alexa Built-in, Sleep & Swim Tracking, Black/Carbon"
        f2 = "Fitbit FB507RGPK Versa 2 Health & Fitness Smartwatch with Heart Rate, Music, Alexa Built-in, Sleep & Swim Tracking, Petal/Copper Rose"
        k1 = family_key(f1)
        k2 = family_key(f2)
        self.assertEqual(k1, k2)
        self.assertIn("fitbit", k1)
        self.assertIn("versa 2", k1)

    def test_family_key_distinguishes_different_models(self):
        rn10s = "Redmi Note 10S (Deep Sea Blue, 6GB RAM, 64GB Storage) - Super Amoled Display"
        r9a = "Redmi 9A (Midnight Black, 2GB RAM, 32GB Storage)"
        self.assertNotEqual(family_key(rn10s), family_key(r9a))

    def test_clean_display_name_fixes_f11_examples(self):
        cases = [
            (
                "Portronics Konnect L 1.2M POR-1401 Fast Charging 3A Type-C Cable with Vibrant Colors with",
                "Portronics Konnect L 1.2M POR-1401 Fast Charging 3A Type-C Cable with Vibrant Colors",
            ),
            (
                "boAt Rockerz 450 Bluetooth On Ear Headphones with Mic with",
                "boAt Rockerz 450 Bluetooth On Ear Headphones with Mic",
            ),
            (
                "Wayona Nylon Braided 3A Lightning to USB A Cable, Fast Charging Cord Compatible for",
                "Wayona Nylon Braided 3A Lightning to USB A Cable, Fast Charging Cord",
            ),
        ]
        for raw, expected in cases:
            cleaned = clean_display_name(raw)
            self.assertEqual(cleaned, expected)
            self.assertLessEqual(len(cleaned), 90)
            words = cleaned.lower().split()
            self.assertNotIn(words[-1], TRAILING_CONNECTORS)
            self.assertEqual(cleaned.count("("), cleaned.count(")"))
            self.assertEqual(cleaned.count('"') % 2, 0)

    def test_clean_display_name_dataset_invariants(self):
        products = Product.objects.all()[:50]
        for p in products:
            cleaned = clean_display_name(p.raw_name, p.parsed_brand)
            self.assertLessEqual(len(cleaned), 90, f"Title exceeds 90 chars: {cleaned}")
            words = cleaned.lower().split()
            if words:
                self.assertNotIn(
                    words[-1],
                    TRAILING_CONNECTORS,
                    f"Title ends in connector word '{words[-1]}': {cleaned}",
                )
            self.assertEqual(
                cleaned.count("("),
                cleaned.count(")"),
                f"Unbalanced parentheses in: {cleaned}",
            )
            self.assertEqual(
                cleaned.count('"') % 2,
                0,
                f"Unbalanced quotes in: {cleaned}",
            )

    def test_editorial_deduplicates_by_family(self):
        cat = Category.objects.create(name="Audio", slug="audio-test", accent_key="audio")
        # Create 3 products from the same family and 1 from a different family
        p1 = Product.objects.create(
            category=cat,
            sku="BOAT-100-BLK",
            slug="boat-100-blk",
            raw_name="boAt BassHeads 100 in-Ear Wired Headphones with Mic (Black)",
            display_name="boAt BassHeads 100 Headphones (Black)",
            source_asin="B001111111",
            selling_price=Decimal("399.00"),
            mrp=Decimal("999.00"),
            source_rating=Decimal("4.2"),
            source_rating_count=5000,
            is_available=True,
        )
        p2 = Product.objects.create(
            category=cat,
            sku="BOAT-100-WHT",
            slug="boat-100-wht",
            raw_name="boAt BassHeads 100 in-Ear Wired Headphones with Mic (White)",
            display_name="boAt BassHeads 100 Headphones (White)",
            source_asin="B002222222",
            selling_price=Decimal("399.00"),
            mrp=Decimal("999.00"),
            source_rating=Decimal("4.3"),
            source_rating_count=4000,
            is_available=True,
        )
        p3 = Product.objects.create(
            category=cat,
            sku="BOAT-100-RED",
            slug="boat-100-red",
            raw_name="boAt Bassheads 100 in Ear Wired Earphones with Mic(Furious Red)",
            display_name="boAt Bassheads 100 Earphones (Red)",
            source_asin="B003333333",
            selling_price=Decimal("399.00"),
            mrp=Decimal("999.00"),
            source_rating=Decimal("4.1"),
            source_rating_count=3000,
            is_available=True,
        )
        p4 = Product.objects.create(
            category=cat,
            sku="SONY-WH1000",
            slug="sony-wh1000",
            raw_name="Sony WH-1000XM4 Wireless Noise Cancelling Headphones",
            display_name="Sony WH-1000XM4 Headphones",
            source_asin="B004444444",
            selling_price=Decimal("22990.00"),
            mrp=Decimal("29990.00"),
            source_rating=Decimal("4.7"),
            source_rating_count=1000,
            is_available=True,
        )

        spread = category_spread(cat)
        spread_skus = [p.sku for p in spread.picks]
        # Should contain at most 1 boAt BassHeads 100 variant, not all 3
        boat_count = sum(1 for sku in spread_skus if sku in {"BOAT-100-BLK", "BOAT-100-WHT", "BOAT-100-RED"})
        self.assertEqual(boat_count, 1)
