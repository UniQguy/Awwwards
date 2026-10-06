"""
Unit tests for catalog services: category rules, brand detection, title parsing,
spec extraction, price distribution, and catalog model properties.
"""

from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from apps.catalog.models import Category, Product, ProductSpecification
from apps.catalog.services.brands import detect_brand
from apps.catalog.services.category_rules import CATEGORY_DEFINITIONS, classify_category
from apps.catalog.services.parsing import (
    build_unique_slug,
    clean_display_name,
    extract_asin,
    parse_count,
    parse_price,
    parse_rating,
)
from apps.catalog.services.price_distribution import calculate_price_distribution
from apps.catalog.services.spec_extractor import extract_specifications


class CategoryRulesAndClassificationTests(TestCase):
    def test_ten_canonical_categories_defined(self):
        self.assertEqual(len(CATEGORY_DEFINITIONS), 10)
        slugs = [c["slug"] for c in CATEGORY_DEFINITIONS]
        self.assertIn("cases-protectors", slugs)
        self.assertIn("cables-chargers-powerbanks", slugs)
        self.assertIn("smartphones", slugs)
        self.assertIn("other", slugs)

    def test_accessory_precedence_over_devices(self):
        # Cases & Protectors must match before smartphones
        slug = classify_category("Apple iPhone 14 Pro Max silicone case cover")
        self.assertEqual(slug, "cases-protectors")

        # Screen protector
        slug = classify_category("Samsung Galaxy S23 Ultra tempered glass screen protector")
        self.assertEqual(slug, "cases-protectors")

        # Cables & chargers must match before smartphones
        slug = classify_category("OnePlus 65W Warp Charger Type-C Cable")
        self.assertEqual(slug, "cables-chargers-powerbanks")

        # Power bank
        slug = classify_category("Xiaomi 20000mAh Power Bank 3i with fast charging")
        self.assertEqual(slug, "cables-chargers-powerbanks")

        # Smartwatch band must match before smartwatch or phone
        slug = classify_category("Apple Watch Series 8 replacement silicone watch strap band")
        self.assertEqual(slug, "smartwatches-bands")

    def test_audio_and_peripherals_classification(self):
        self.assertEqual(classify_category("boAt Airdopes 141 Bluetooth Earbuds TWS"), "earphones-headphones")
        self.assertEqual(classify_category("Sony WH-1000XM5 Wireless Noise Cancelling Headphones"), "earphones-headphones")
        self.assertEqual(classify_category("JBL Flip 6 Portable Bluetooth Speaker"), "speakers")
        self.assertEqual(classify_category("Logitech MX Master 3S Wireless Performance Mouse"), "keyboards-mice")
        self.assertEqual(classify_category("Keychron K2 Mechanical Keyboard"), "keyboards-mice")
        self.assertEqual(classify_category("Canon EOS R6 Mark II Mirrorless Camera"), "cameras")
        self.assertEqual(classify_category("Sony Bravia 55 inch 4K Ultra HD Smart LED Google TV"), "tvs")
        self.assertEqual(classify_category("Apple iPhone 14 (128 GB, Midnight)"), "smartphones")
        self.assertEqual(classify_category("Unbranded USB Desktop Desk Fan"), "other")


class BrandDetectionTests(TestCase):
    def test_leading_brand_detection(self):
        self.assertEqual(detect_brand("Apple iPhone 14 Pro"), "Apple")
        self.assertEqual(detect_brand("Samsung Galaxy S23"), "Samsung")
        self.assertEqual(detect_brand("boAt Airdopes 141"), "boAt")
        self.assertEqual(detect_brand("Fire-Boltt Ninja Call Pro Plus"), "Fire-Boltt")

    def test_mid_title_brand_detection(self):
        self.assertEqual(detect_brand("Leather Sleeve for Dell XPS 13"), "Dell")
        self.assertEqual(detect_brand("Silicone Case for OnePlus 11"), "OnePlus")

    def test_fallback_brand(self):
        self.assertEqual(detect_brand("Widgetmaster 5000 Multi Tool"), "Widgetmaster")
        self.assertEqual(detect_brand(""), "Unknown")


class ParsingUtilitiesTests(TestCase):
    def test_parse_price(self):
        self.assertEqual(parse_price("₹10,999"), Decimal("10999.00"))
        self.assertEqual(parse_price("₹ 1,499.50"), Decimal("1499.50"))
        self.assertEqual(parse_price("Rs. 499"), Decimal("499.00"))
        self.assertEqual(parse_price(""), None)
        self.assertEqual(parse_price("Free"), None)
        self.assertEqual(parse_price("-100"), None)

    def test_parse_rating(self):
        self.assertEqual(parse_rating("4.3"), Decimal("4.30"))
        self.assertEqual(parse_rating("4.0 out of 5 stars"), Decimal("4.00"))
        self.assertEqual(parse_rating("3,9"), Decimal("3.90"))
        self.assertEqual(parse_rating("5.8"), None)  # out of bounds
        self.assertEqual(parse_rating("N/A"), None)

    def test_parse_count(self):
        self.assertEqual(parse_count("113,956"), 113956)
        self.assertEqual(parse_count("965"), 965)
        self.assertEqual(parse_count("1.5k"), 1500)
        self.assertEqual(parse_count(""), None)

    def test_extract_asin(self):
        url = "https://www.amazon.in/Redmi-Power-Black-128GB-Storage/dp/B09Y64H8VS/ref=sr_1_4"
        self.assertEqual(extract_asin(url), "B09Y64H8VS")
        self.assertEqual(extract_asin("Standalone B0BF57RN3K text"), "B0BF57RN3K")
        self.assertIsNone(extract_asin("invalid text without asin"))

    def test_clean_display_name(self):
        raw = "Redmi 10 Power (Power Black, 8GB RAM, 128GB Storage) | 6000mAh Battery | Upto 12GB RAM with RAM Plus (Renewed)"
        cleaned = clean_display_name(raw, brand="Redmi")
        self.assertNotIn("(Renewed)", cleaned)
        self.assertNotIn("|", cleaned)
        self.assertTrue(len(cleaned) <= 90)

    def test_build_unique_slug(self):
        slug = build_unique_slug("Redmi 10 Power Black", "B09Y64H8VS")
        self.assertEqual(slug, "redmi-10-power-black-b09y64h8vs")


class SpecificationExtractorTests(TestCase):
    def test_extract_specifications(self):
        title = "Redmi 10 Power (Power Black, 8GB RAM, 128GB Storage) | 6000mAh Battery | 65W Fast Charging | 6.5 inch Display"
        specs = extract_specifications(title)
        self.assertEqual(specs.get("RAM"), "8GB")
        self.assertEqual(specs.get("Internal Storage"), "128GB")
        self.assertEqual(specs.get("Battery Capacity"), "6000mAh")
        self.assertEqual(specs.get("Power / Wattage"), "65W")
        self.assertEqual(specs.get("Display Size"), '6.5"')
        self.assertEqual(specs.get("Color"), "Black")


class PriceDistributionTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(
            name="Audio",
            slug="audio-test",
            accent_key="earphones-headphones",
            gst_rate=Decimal("18.00"),
        )
        Product.objects.create(
            category=self.cat,
            sku="EC-TEST-1",
            slug="ec-test-1",
            raw_name="Cheap Earbuds",
            display_name="Cheap Earbuds",
            source_asin="B000TEST01",
            selling_price=Decimal("299.00"),
            is_available=True,
        )
        Product.objects.create(
            category=self.cat,
            sku="EC-TEST-2",
            slug="ec-test-2",
            raw_name="Mid Earbuds",
            display_name="Mid Earbuds",
            source_asin="B000TEST02",
            selling_price=Decimal("1499.00"),
            is_available=True,
        )
        Product.objects.create(
            category=self.cat,
            sku="EC-TEST-3",
            slug="ec-test-3",
            raw_name="High-end Headphones",
            display_name="High-end Headphones",
            source_asin="B000TEST03",
            selling_price=Decimal("24999.00"),
            is_available=True,
        )

    def test_calculate_distribution(self):
        bars = calculate_price_distribution(Product.objects.filter(selling_price__isnull=False))
        self.assertEqual(len(bars), 9)
        # Bracket 0: Under INR 500
        self.assertEqual(bars[0]["count"], 1)
        # Bracket 2: INR 1000 - 2499
        self.assertEqual(bars[2]["count"], 1)
        # Bracket 6: INR 20000 - 39999
        self.assertEqual(bars[6]["count"], 1)
        # Bracket 8: INR 80000+
        self.assertEqual(bars[8]["count"], 0)
        self.assertTrue(bars[0]["height_percent"] > 0)


class ProductModelIntegrityTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(
            name="Smartphones",
            slug="smartphones-test",
            accent_key="smartphones",
            hsn_code="8517",
            gst_rate=Decimal("18.00"),
            is_gst_rate_verified=True,
        )

    def test_effective_properties_and_search_vector(self):
        prod = Product.objects.create(
            category=self.cat,
            sku="EC-B012345678",
            slug="phone-test-asin",
            raw_name="Awesome Flagship 5G Smartphone",
            display_name="Awesome Flagship Phone",
            source_asin="B012345678",
            parsed_brand="Apple",
            selling_price=Decimal("69999.00"),
            mrp=Decimal("79999.00"),
            is_available=True,
        )
        self.assertEqual(prod.effective_hsn, "8517")
        self.assertEqual(prod.effective_gst_rate, Decimal("18.00"))
        self.assertTrue(prod.effective_gst_verified)
        self.assertTrue(prod.is_purchasable)
        self.assertIn("awesome", prod.search_text)
        self.assertIn("apple", prod.search_text)
        self.assertIn("smartphones", prod.search_text)

    def test_product_negative_price_constraint(self):
        with self.assertRaises(IntegrityError):
            Product.objects.create(
                category=self.cat,
                sku="EC-FAIL-1",
                slug="ec-fail-1",
                raw_name="Invalid Item",
                display_name="Invalid Item",
                source_asin="B00FAIL001",
                selling_price=Decimal("-10.00"),
            )
