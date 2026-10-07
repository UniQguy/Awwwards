"""
Tests for Phase 6 motion infrastructure, MOTION_DEBUG parameter stripping,
editorial data-layer markers, json_script data blocks, and /c/<slug>/count/ endpoint.
"""

from decimal import Decimal
import json

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.catalog.models import Category, Product
from apps.inventory.models import Inventory


class CategoryPriceCountEndpointTests(TestCase):
    """
    Tests for /c/<slug>/count/ endpoint used by the progressive-enhancement dual-thumb price range.
    """

    def setUp(self):
        cache.clear()
        self.category = Category.objects.create(
            name="Audio & Monitors",
            slug="audio-monitors",
            accent_key="earphones-headphones",
            is_active=True,
        )
        self.p1 = Product.objects.create(
            category=self.category,
            sku="SKU-AUD-001",
            slug="pro-monitor-headphones-001",
            source_asin="B00TEST001",
            raw_name="Pro Monitor Headphones",
            display_name="Pro Monitor Headphones Black",
            parsed_brand="AudioCraft",
            selling_price=Decimal("1200.00"),
            mrp=Decimal("1500.00"),
            is_available=True,
            source_rating_count=50,
        )
        Inventory.objects.create(product=self.p1, quantity=10)

        self.p2 = Product.objects.create(
            category=self.category,
            sku="SKU-AUD-002",
            slug="pro-monitor-headphones-002",
            source_asin="B00TEST002",
            raw_name="Pro Monitor Headphones",
            display_name="Pro Monitor Headphones Silver",
            parsed_brand="AudioCraft",
            selling_price=Decimal("1400.00"),
            mrp=Decimal("1800.00"),
            is_available=True,
            source_rating_count=20,
        )
        Inventory.objects.create(product=self.p2, quantity=5)

        self.p3 = Product.objects.create(
            category=self.category,
            sku="SKU-AUD-003",
            slug="budget-earbuds-003",
            source_asin="B00TEST003",
            raw_name="Budget Earbuds",
            display_name="Budget Earbuds White",
            parsed_brand="SoundZen",
            selling_price=Decimal("450.00"),
            mrp=Decimal("599.00"),
            is_available=True,
            source_rating_count=100,
        )
        Inventory.objects.create(product=self.p3, quantity=15)

    def tearDown(self):
        cache.clear()

    def test_price_count_basic_response_shape(self):
        url = reverse("category_price_count", kwargs={"slug": self.category.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("count", data)
        self.assertIn("category", data)
        self.assertEqual(data["category"], "audio-monitors")
        self.assertEqual(data["count"], 3)

    def test_price_count_min_max_filters(self):
        url = reverse("category_price_count", kwargs={"slug": self.category.slug})
        # Filter for under 500
        res = self.client.get(url, {"max_price": "500"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["count"], 1)

        # Filter for >= 1000 and <= 1300
        res = self.client.get(url, {"min_price": "1000", "max_price": "1300"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["count"], 1)

    def test_price_count_brand_filter(self):
        url = reverse("category_price_count", kwargs={"slug": self.category.slug})
        res = self.client.get(url, {"brand": "AudioCraft"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["count"], 2)

        res_other = self.client.get(url, {"brand": "SoundZen"})
        self.assertEqual(res_other.status_code, 200)
        self.assertEqual(res_other.json()["count"], 1)

    def test_price_count_collapsed(self):
        url = reverse("category_price_count", kwargs={"slug": self.category.slug})
        # Without collapse: 3 products
        res_uncollapsed = self.client.get(url)
        self.assertEqual(res_uncollapsed.json()["count"], 3)

        # With collapse: Pro Monitor Headphones (2 variants) collapses into 1 card, so total 2
        res_collapsed = self.client.get(url, {"collapsed": "1"})
        self.assertEqual(res_collapsed.status_code, 200)
        self.assertEqual(res_collapsed.json()["count"], 2)

    def test_price_count_404_for_missing_category(self):
        url = reverse("category_price_count", kwargs={"slug": "non-existent-category"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_price_count_rate_limiting(self):
        url = reverse("category_price_count", kwargs={"slug": self.category.slug})
        cache_key = "rl_price_count_127.0.0.1"
        cache.set(cache_key, 120, timeout=60)
        response = self.client.get(url, REMOTE_ADDR="127.0.0.1")
        self.assertEqual(response.status_code, 429)
        self.assertIn("Rate limit exceeded", response.json()["error"])


class MotionDebugMiddlewareTests(TestCase):
    """
    Tests asserting that ?motion= query parameter is stripped in production
    and allowed when MOTION_DEBUG is True.
    """

    @override_settings(MOTION_DEBUG=False)
    def test_motion_debug_stripped_in_production(self):
        response = self.client.get("/?motion=1")
        # Should redirect stripping the query param
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")

    @override_settings(MOTION_DEBUG=False)
    def test_motion_debug_stripped_preserving_other_params(self):
        response = self.client.get("/?q=cable&motion=2")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/?q=cable")

    @override_settings(MOTION_DEBUG=True)
    def test_motion_debug_allowed_in_development(self):
        response = self.client.get("/?motion=1")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-motion-debug="true"')


class EditorialDataLayerTests(TestCase):
    """
    Tests ensuring editorial pages carry data-layer="editorial" and utility pages do not.
    """

    def setUp(self):
        self.category = Category.objects.create(
            name="Audio & Monitors",
            slug="audio-monitors",
            accent_key="earphones-headphones",
            is_active=True,
        )
        self.product = Product.objects.create(
            category=self.category,
            sku="SKU-ED-001",
            slug="editorial-product-001",
            source_asin="B00ED001",
            raw_name="Editorial Product",
            display_name="Editorial Product Masterpiece",
            parsed_brand="AudioCraft",
            selling_price=Decimal("1200.00"),
            mrp=Decimal("1500.00"),
            is_available=True,
            source_rating_count=50,
        )
        Inventory.objects.create(product=self.product, quantity=10)

    def test_home_page_carries_editorial_data_layer(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-layer="editorial"')

    def test_category_list_carries_editorial_data_layer(self):
        response = self.client.get(reverse("category_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-layer="editorial"')

    def test_category_marquee_carries_editorial_data_layer(self):
        response = self.client.get(reverse("category_detail", kwargs={"slug": self.category.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-layer="editorial"')

    def test_product_detail_carries_editorial_data_layer(self):
        response = self.client.get(reverse("product_detail", kwargs={"slug": self.product.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-layer="editorial"')

    def test_utility_pages_do_not_carry_editorial_data_layer(self):
        # Cart
        res_cart = self.client.get(reverse("cart_detail"))
        self.assertNotContains(res_cart, 'data-layer="editorial"')

        # Login page
        res_login = self.client.get(reverse("account_login"))
        self.assertNotContains(res_login, 'data-layer="editorial"')

        # Track order lookup
        res_track = self.client.get(reverse("order_track_lookup"))
        self.assertNotContains(res_track, 'data-layer="editorial"')


class JsonScriptDataBlockTests(TestCase):
    """
    Tests ensuring templates render valid json_script blocks.
    """

    def setUp(self):
        self.category = Category.objects.create(
            name="Audio & Monitors",
            slug="audio-monitors",
            accent_key="earphones-headphones",
            is_active=True,
        )
        self.product = Product.objects.create(
            category=self.category,
            sku="SKU-JSON-001",
            slug="json-product-001",
            source_asin="B00JSON001",
            raw_name="JSON Product",
            display_name="JSON Product Masterpiece",
            parsed_brand="AudioCraft",
            selling_price=Decimal("1200.00"),
            mrp=Decimal("1500.00"),
            is_available=True,
            source_rating_count=50,
        )
        Inventory.objects.create(product=self.product, quantity=10)

    def test_home_renders_hero_cutouts_data_json_script(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<script id="hero-cutouts-data" type="application/json">')

    def test_category_detail_renders_price_brackets_data_json_script(self):
        response = self.client.get(reverse("category_detail", kwargs={"slug": self.category.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<script id="price-brackets-data" type="application/json">')
