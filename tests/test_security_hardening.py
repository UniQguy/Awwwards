"""
Comprehensive security hardening tests.
Verifies logging redaction, upload validation, rate limits (HTTP 429),
security headers, price tampering prevention, IDOR protection, and CSRF protection.
"""

from decimal import Decimal
import io
import logging
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from PIL import Image

from apps.accounts.models import IndianState
from apps.cart.services.cart_service import add_to_cart, get_or_create_cart
from apps.catalog.models import Category, Product, ProductMedia, validate_product_image_upload
from apps.core.logging_filters import SensitiveDataFilter
from apps.inventory.exceptions import InsufficientStockError
from apps.inventory.models import Inventory
from apps.orders.models import Order
from apps.orders.services.order_creator import place_order

User = get_user_model()


class SecurityHardeningTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_a = User.objects.create_user(email="alice@example.com", password="SecurePassword123!")
        cls.user_b = User.objects.create_user(email="bob@example.com", password="SecurePassword123!")
        cls.category = Category.objects.create(name="Security Cat", slug="security-cat", accent_key="audio")
        cls.product = Product.objects.create(
            category=cls.category,
            sku="SEC-001",
            slug="sec-product-001",
            raw_name="Secure Audio Device",
            display_name="Secure Audio Device",
            source_asin="B00SEC001",
            selling_price=Decimal("1500.00"),
            mrp=Decimal("2000.00"),
            is_available=True,
        )
        cls.inventory = Inventory.objects.create(product=cls.product, quantity=5)

    def setUp(self):
        self.client = Client()

    def test_logging_redaction_filter(self):
        """SensitiveDataFilter redacts tokens, signatures, emails, and razorpay keys."""
        filter_instance = SensitiveDataFilter()
        logger = logging.getLogger("test_redaction_logger")
        log_stream = io.StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.addFilter(filter_instance)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        raw_msg = (
            "Requested /orders/EC-20261007-001/?token=super_secret_token_123&sig=sig456 "
            "for user alice@example.com with gateway rzp_test_1234567890abcdef"
        )
        logger.info(raw_msg)

        output = log_stream.getvalue()
        self.assertNotIn("super_secret_token_123", output)
        self.assertNotIn("alice@example.com", output)
        self.assertNotIn("rzp_test_1234567890abcdef", output)
        self.assertIn("token=[REDACTED]", output)
        self.assertIn("sig=[REDACTED]", output)
        self.assertIn("@example.com", output)
        self.assertIn("al***", output)
        self.assertIn("rzp_test_1234[REDACTED]", output)

    def test_upload_validation_rejects_non_image(self):
        """validate_product_image_upload rejects files that are not valid images."""
        bad_file = SimpleUploadedFile("malicious.php", b"<?php phpinfo(); ?>", content_type="text/plain")
        with self.assertRaises(ValidationError):
            validate_product_image_upload(bad_file)

    def test_upload_validation_accepts_valid_image(self):
        """validate_product_image_upload accepts valid image bytes."""
        img_io = io.BytesIO()
        img = Image.new("RGB", (100, 100), color="white")
        img.save(img_io, format="PNG")
        img_io.seek(0)
        good_file = SimpleUploadedFile("product.png", img_io.read(), content_type="image/png")
        # Should not raise
        validate_product_image_upload(good_file)

    def test_upload_validation_rejects_oversized_file(self):
        """validate_product_image_upload rejects files exceeding 5MB limit."""
        oversized = SimpleUploadedFile("huge.png", b"0" * (6 * 1024 * 1024), content_type="image/png")
        with self.assertRaises(ValidationError) as ctx:
            validate_product_image_upload(oversized)
        self.assertIn("exceeds 5MB limit", str(ctx.exception))

    def test_security_headers_present_on_all_responses(self):
        """Baseline security headers (Permissions-Policy, COOP, Referrer-Policy) are present."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Permissions-Policy", response.headers)
        self.assertIn("camera=()", response.headers["Permissions-Policy"])
        self.assertIn("microphone=()", response.headers["Permissions-Policy"])
        self.assertEqual(response.headers.get("Cross-Origin-Opener-Policy"), "same-origin")
        self.assertEqual(response.headers.get("Referrer-Policy"), "strict-origin-when-cross-origin")
        self.assertEqual(response.headers.get("X-Frame-Options"), "DENY")
        self.assertIn("Content-Security-Policy", response.headers)

    def test_idor_protection_on_orders(self):
        """User B cannot access User A's order without authorization."""
        cart_a = get_or_create_cart(user=self.user_a)
        add_to_cart(cart_a, self.product, quantity=1)
        addr = {
            "full_name": "Alice Customer",
            "line1": "100 MG Road",
            "city": "Bengaluru",
            "state_code": "KA",
            "pincode": "560001",
            "phone": "9876543210",
        }
        order_a = place_order(cart=cart_a, shipping_address=addr, billing_address=addr, payment_method="cod")

        # Authenticate as User B
        self.client.force_login(self.user_b)
        response = self.client.get(f"/orders/{order_a.order_number}/invoice/")
        # Must return 404 unauthorized
        self.assertEqual(response.status_code, 404)

        # Unauthenticated guest without token cannot view order
        self.client.logout()
        guest_response = self.client.get(f"/orders/{order_a.order_number}/invoice/")
        self.assertEqual(guest_response.status_code, 404)

    def test_price_tampering_impossible(self):
        """Order pricing is strictly computed from database Product.selling_price."""
        cart = get_or_create_cart(user=self.user_a)
        add_to_cart(cart, self.product, quantity=2)
        addr = {
            "full_name": "Tamper Test",
            "line1": "100 MG Road",
            "city": "Bengaluru",
            "state_code": "KA",
            "pincode": "560001",
            "phone": "9876543210",
        }
        order = place_order(cart=cart, shipping_address=addr, billing_address=addr, payment_method="cod")
        # Product price is 1500.00 * 2 = 3000.00 + free shipping = 3000.00
        self.assertEqual(order.subtotal, Decimal("3000.00"))
        self.assertEqual(order.total_amount, Decimal("3000.00"))

    def test_stock_overselling_prevented(self):
        """Attempting to reserve more than available physical inventory raises InsufficientStockError."""
        from apps.inventory.services.reservation_service import reserve_stock

        # Inventory quantity is 5, attempting to reserve 10 units
        with self.assertRaises(InsufficientStockError):
            reserve_stock(self.product, quantity=10, owner_key="test_overflow")

        # Zero stock product cannot be added to cart
        self.inventory.quantity = 0
        self.inventory.save()
        cart = get_or_create_cart(user=self.user_a)
        with self.assertRaises(InsufficientStockError):
            add_to_cart(cart, self.product, quantity=1)
        self.inventory.quantity = 5
        self.inventory.save()

    def test_csrf_protection_on_mutations(self):
        """POST requests without CSRF token are rejected when CSRF enforcement is active."""
        # Use a fresh test client with enforce_csrf_checks=True
        csrf_client = Client(enforce_csrf_checks=True)
        response = csrf_client.post(f"/cart/add/{self.product.id}/", {"quantity": 1})
        self.assertEqual(response.status_code, 403)

    def test_rate_limit_search_suggest_returns_429(self):
        """search_suggest returns HTTP 429 when rate limit is exceeded."""
        from django.core.cache import cache
        cache.clear()

        # Exceed rate limit (60/m)
        client = Client(REMOTE_ADDR="198.51.100.1")
        for _ in range(65):
            res = client.get("/search/suggest/?q=audio")
            if res.status_code == 429:
                break
        self.assertEqual(res.status_code, 429)

    def test_rate_limit_coupon_apply_returns_429(self):
        """coupon_apply returns HTTP 429 when rate limit is exceeded."""
        from django.core.cache import cache
        cache.clear()

        client = Client(REMOTE_ADDR="198.51.100.2")
        for _ in range(15):
            res = client.post("/cart/coupon/apply/", {"code": "TRYCODE"})
            if res.status_code == 429:
                break
        self.assertEqual(res.status_code, 429)
