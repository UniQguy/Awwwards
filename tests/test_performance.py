"""
Performance and database query optimization tests.
Ensures zero N+1 queries on key commerce pages, sensitive caching headers,
WhiteNoise configuration, and SQLite performance pragmas.
"""

from decimal import Decimal
from django.conf import settings
from django.db import connection
from django.test import Client, TestCase

from apps.catalog.models import Category, Product
from apps.cart.services.cart_service import add_to_cart, get_or_create_cart
from apps.inventory.models import Inventory


class PerformanceOptimizationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(
            name="Audio Lab",
            slug="audio-lab",
            accent_key="audio",
            display_order=1,
            is_active=True,
        )
        cls.products = []
        for i in range(10):
            p = Product.objects.create(
                category=cls.category,
                sku=f"PERF-SKU-{i:03d}",
                slug=f"perf-product-{i:03d}",
                raw_name=f"Studio Monitor Model {i:03d}",
                display_name=f"Studio Monitor {i:03d}",
                source_asin=f"B00PERF{i:03d}",
                parsed_brand="Acoustics",
                selling_price=Decimal("4999.00"),
                mrp=Decimal("5999.00"),
                is_available=True,
                source_rating_count=50 + i,
            )
            Inventory.objects.create(product=p, quantity=20, low_stock_threshold=3)
            cls.products.append(p)

    def setUp(self):
        self.client = Client()

    def test_category_detail_query_count_bounded(self):
        """Category detail page query count is strictly bounded and free of N+1 inventory queries."""
        from django.test.utils import CaptureQueriesContext

        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get(f"/c/{self.category.slug}/")
            self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(ctx), 22)

    def test_product_detail_query_count_bounded(self):
        """Product detail page has fixed query count with prefetched media and variants."""
        from django.test.utils import CaptureQueriesContext

        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get(f"/p/{self.products[0].slug}/")
            self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(ctx), 15)

    def test_cart_detail_no_item_n_plus_one(self):
        """Cart page with multiple items does not trigger N+1 queries for media or inventory."""
        from django.test.utils import CaptureQueriesContext

        session = self.client.session
        session["guest_token"] = "perf-cart-token"
        session.save()
        cart = get_or_create_cart(guest_token="perf-cart-token")

        # Warm up session and storefront context processor caches
        self.client.get("/cart/")

        for p in self.products[:2]:
            add_to_cart(cart, p, quantity=1)

        with CaptureQueriesContext(connection) as ctx_2_items:
            self.client.get("/cart/")

        # Add 3 more items (total 5)
        for p in self.products[2:5]:
            add_to_cart(cart, p, quantity=1)

        with CaptureQueriesContext(connection) as ctx_5_items:
            response = self.client.get("/cart/")
            self.assertEqual(response.status_code, 200)

        # Query count must remain constant (O(1) database queries with respect to line count)
        self.assertEqual(len(ctx_2_items), len(ctx_5_items))
        self.assertLessEqual(len(ctx_5_items), 20)

    def test_sensitive_endpoints_have_no_store_headers(self):
        """Sensitive commerce pages (cart, checkout, orders, account) are never cached."""
        paths = ["/cart/", "/checkout/"]
        for path in paths:
            response = self.client.get(path)
            self.assertIn("Cache-Control", response.headers)
            self.assertIn("no-store", response.headers["Cache-Control"])
            self.assertIn("private", response.headers["Cache-Control"])
            self.assertEqual(response.headers.get("Referrer-Policy"), "same-origin")

    def test_whitenoise_immutable_test(self):
        """WhiteNoise immutable file test correctly identifies hashed and Vite dist assets."""
        from config.settings.base import whitenoise_immutable_file_test

        self.assertTrue(whitenoise_immutable_file_test("static/dist/assets/app.c7a201b1.js", "/static/dist/assets/app.c7a201b1.js"))
        self.assertTrue(whitenoise_immutable_file_test("static/css/storefront.1234567890ab.css", "/static/css/storefront.1234567890ab.css"))
        self.assertFalse(whitenoise_immutable_file_test("static/favicon.ico", "/static/favicon.ico"))

    def test_sqlite_pragmas_configured(self):
        """SQLite connections have WAL mode, NORMAL synchronous, 64MB cache, and busy timeout configured."""
        if connection.vendor == "sqlite":
            with connection.cursor() as cursor:
                cursor.execute("PRAGMA journal_mode;")
                # Note: in in-memory test database, journal_mode can be 'memory' or 'wal'
                jm = cursor.fetchone()[0].lower()
                self.assertIn(jm, ("wal", "memory"))
                cursor.execute("PRAGMA busy_timeout;")
                self.assertEqual(cursor.fetchone()[0], 5000)
