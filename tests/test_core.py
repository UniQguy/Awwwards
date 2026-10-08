"""
Tests for apps.core: tokens, identifiers, middleware, templatetags, and health check.
"""

from decimal import Decimal
import time
from django.test import Client, SimpleTestCase, TestCase
from django.urls import reverse

from apps.core.templatetags.core_tags import discount_percent, inr, savings
from apps.core.utils.identifiers import generate_order_number
from apps.core.utils.tokens import make_guest_token, verify_guest_token


class CoreTokensTests(SimpleTestCase):
    """Tests for guest token cryptographic creation and verification."""

    def test_valid_token_verifies(self):
        order_num = "EC-2026-F8K9-M4R2"
        raw_token, stored_hash = make_guest_token(order_num)

        self.assertTrue(verify_guest_token(raw_token, order_num, stored_hash))

    def test_tampered_token_fails(self):
        order_num = "EC-2026-F8K9-M4R2"
        raw_token, stored_hash = make_guest_token(order_num)
        tampered_token = raw_token + "tampered"

        self.assertFalse(verify_guest_token(tampered_token, order_num, stored_hash))

    def test_wrong_order_number_fails(self):
        order_num = "EC-2026-F8K9-M4R2"
        raw_token, stored_hash = make_guest_token(order_num)

        self.assertFalse(
            verify_guest_token(raw_token, "EC-2026-DIFFERENT", stored_hash)
        )

    def test_hash_mismatch_fails(self):
        order_num = "EC-2026-F8K9-M4R2"
        raw_token, _ = make_guest_token(order_num)
        bogus_hash = "0" * 64

        self.assertFalse(verify_guest_token(raw_token, order_num, bogus_hash))

    def test_empty_or_none_inputs_fail_safely(self):
        self.assertFalse(verify_guest_token("", "", ""))
        self.assertFalse(verify_guest_token("a", "b", ""))


class CoreIdentifiersTests(SimpleTestCase):
    """Tests for order number generation."""

    def test_order_number_format(self):
        num = generate_order_number(2026)
        self.assertTrue(num.startswith("EC-2026-"))
        parts = num.split("-")
        self.assertEqual(len(parts), 4)
        self.assertEqual(len(parts[2]), 4)
        self.assertEqual(len(parts[3]), 4)
        # Verify characters are unambiguous (no 0, O, 1, I, L)
        for char in parts[2] + parts[3]:
            self.assertNotIn(char, "0O1IL")

    def test_order_number_uniqueness(self):
        generated = {generate_order_number(2026) for _ in range(500)}
        self.assertEqual(len(generated), 500)


class CoreTemplateTagsTests(SimpleTestCase):
    """Tests for Indian currency grouping and savings helpers."""

    def test_inr_grouping_vectors(self):
        self.assertEqual(inr(10), "₹10")
        self.assertEqual(inr(1299), "₹1,299")
        self.assertEqual(inr(100000), "₹1,00,000")
        self.assertEqual(inr(134999), "₹1,34,999")
        self.assertEqual(inr(None), "")
        self.assertEqual(inr(""), "")

    def test_inr_decimal_values(self):
        self.assertEqual(inr(Decimal("1299.00")), "₹1,299")
        self.assertEqual(inr(Decimal("1299.50")), "₹1,299.50")
        self.assertEqual(inr(Decimal("100000.75")), "₹1,00,000.75")

    def test_discount_percent_and_savings(self):
        # MRP 2000, Selling 1500 -> 25% discount, ₹500 savings
        self.assertEqual(discount_percent(2000, 1500), 25)
        self.assertEqual(savings(2000, 1500), "₹500")

        # When MRP <= selling price, no discount or savings
        self.assertEqual(discount_percent(1500, 1500), 0)
        self.assertEqual(savings(1500, 1500), "")
        self.assertEqual(discount_percent(1000, 1500), 0)
        self.assertEqual(savings(1000, 1500), "")


class CoreViewsAndMiddlewareTests(TestCase):
    """Tests for health check and security headers middleware."""

    def setUp(self):
        self.client = Client()

    def test_health_check_endpoint(self):
        response = self.client.get(reverse("health_check"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("service"), "electrocart")

    def test_sensitive_headers_middleware_on_sensitive_paths(self):
        # Sensitive routes like /orders/
        response = self.client.get("/orders/track/")
        self.assertEqual(response.headers.get("Referrer-Policy"), "same-origin")
        self.assertIn("no-store", response.headers.get("Cache-Control", ""))

        response = self.client.get("/checkout/")
        self.assertEqual(response.headers.get("Referrer-Policy"), "same-origin")
        self.assertIn("no-store", response.headers.get("Cache-Control", ""))

    def test_public_path_not_burdened_by_no_store(self):
        response = self.client.get(reverse("health_check"))
        # Public health check should not have no-store forced by the middleware
        self.assertNotEqual(response.headers.get("Referrer-Policy"), "no-referrer")

    def test_db_backup_command(self):
        from pathlib import Path
        import tempfile
        from django.core.management import call_command

        with tempfile.TemporaryDirectory() as tmp_dir:
            call_command("db_backup", output_dir=tmp_dir, retention=2)
            files = list(Path(tmp_dir).glob("electrocart_backup_*.sqlite3"))
            self.assertGreaterEqual(len(files), 1)
