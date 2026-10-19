"""
Tests for Tax Mode (F-05) and Cart/Checkout Summary Arithmetic Footing (F-06).
Verifies:
- Four footing scenarios (no coupon, coupon, free delivery, COD)
- Rendered HTML numbers strictly add up to Grand Total
- MRP savings rendered outside the sum
- Strict absence of GST / tax mentions in bill_of_supply mode
- Presence of GST breakdown in gst mode
- Promo code placeholder honesty
"""

from decimal import Decimal
import re
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.cart.models import Cart, CartItem
from apps.cart.services.cart_calculator import calculate_cart_summary
from apps.catalog.models import Category, Product
from apps.promotions.models import Coupon
from apps.shipping.models import ShippingConfig


def _parse_inr(text: str) -> Decimal:
    """Parses '₹1,234.50' or '₹439' into Decimal."""
    clean = re.sub(r"[^\d.]", "", text)
    return Decimal(clean) if clean else Decimal("0.00")


class TaxModeAndCartFootingTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Configure shipping: free above 500, standard 40, cod 50
        cls.ship_cfg = ShippingConfig.get_solo()
        cls.ship_cfg.free_shipping_threshold = Decimal("500.00")
        cls.ship_cfg.standard_fee = Decimal("40.00")
        cls.ship_cfg.cod_fee = Decimal("50.00")
        cls.ship_cfg.is_standard_fee_confirmed = True
        cls.ship_cfg.save()

        cls.category = Category.objects.create(
            name="Audio",
            slug="audio",
            accent_key="earphones-headphones",
            hsn_code="8518",
            gst_rate=Decimal("18.00"),
            is_gst_rate_verified=True,
            is_active=True,
        )

        # Product 1: Below free shipping, has MRP savings
        cls.prod_low = Product.objects.create(
            category=cls.category,
            sku="AUD-LOW-1",
            source_asin="B00TAXLOW1",
            slug="aud-low-1",
            raw_name="Wired Earbuds Black",
            display_name="Wired Earbuds",
            selling_price=Decimal("399.00"),
            mrp=Decimal("999.00"),
            is_available=True,
        )

        # Product 2: Above free shipping
        cls.prod_high = Product.objects.create(
            category=cls.category,
            sku="AUD-HIGH-1",
            source_asin="B00TAXHIGH1",
            slug="aud-high-1",
            raw_name="Studio Wireless Headphones",
            display_name="Studio Wireless Headphones",
            selling_price=Decimal("1200.00"),
            mrp=Decimal("1500.00"),
            is_available=True,
        )

        now = timezone.now()
        cls.coupon = Coupon.objects.create(
            code="SAVE100",
            discount_type="fixed",
            discount_value=Decimal("100.00"),
            min_order_amount=Decimal("300.00"),
            valid_from=now - timezone.timedelta(days=1),
            valid_until=now + timezone.timedelta(days=30),
            is_active=True,
        )

    def setUp(self):
        self.guest_token = "test-guest-token-12345"
        self.client.cookies["electrocart_guest_token"] = self.guest_token
        self.cart = Cart.objects.create(guest_token=self.guest_token)

    def test_scenario_a_no_coupon_below_threshold(self):
        """Scenario A: Subtotal < 500 -> Items (399) + Delivery (40) = Total (439)."""
        CartItem.objects.create(cart=self.cart, product=self.prod_low, quantity=1)

        resp = self.client.get(reverse("cart_detail"))
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode("utf-8")

        # Check footing from rendered HTML
        items_match = re.search(r"<dt>Items</dt>\s*<dd>(₹[\d,]+(?:\.\d+)?)</dd>", content)
        delivery_match = re.search(r"<dt>Delivery</dt>\s*<dd>\s*(₹[\d,]+(?:\.\d+)?)\s*</dd>", content)
        total_match = re.search(r"<span class=\"total-label\">Total</span>\s*<span class=\"total-amount\">(₹[\d,]+(?:\.\d+)?)</span>", content)

        self.assertIsNotNone(items_match, "Items row missing in cart")
        self.assertIsNotNone(delivery_match, "Delivery row missing in cart")
        self.assertIsNotNone(total_match, "Total row missing in cart")

        items_val = _parse_inr(items_match.group(1))
        delivery_val = _parse_inr(delivery_match.group(1))
        total_val = _parse_inr(total_match.group(1))

        self.assertEqual(items_val, Decimal("399.00"))
        self.assertEqual(delivery_val, Decimal("40.00"))
        self.assertEqual(total_val, Decimal("439.00"))
        self.assertEqual(items_val + delivery_val, total_val)

        # MRP savings rendered outside the sum
        self.assertIn("You save ₹600 compared with the listed MRP.", content)

    def test_scenario_b_coupon_applied(self):
        """Scenario B: Items (399) - Coupon (100) + Delivery (40) = Total (339)."""
        CartItem.objects.create(cart=self.cart, product=self.prod_low, quantity=1)
        session = self.client.session
        session["applied_coupon_code"] = "SAVE100"
        session.save()

        resp = self.client.get(reverse("cart_detail"))
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode("utf-8")

        items_val = _parse_inr(re.search(r"<dt>Items</dt>\s*<dd>(₹[\d,]+(?:\.\d+)?)</dd>", content).group(1))
        coupon_val = _parse_inr(re.search(r"<dt[^>]*>Coupon</dt>\s*<dd[^>]*>-(₹[\d,]+(?:\.\d+)?)</dd>", content).group(1))
        delivery_val = _parse_inr(re.search(r"<dt>Delivery</dt>\s*<dd>\s*(₹[\d,]+(?:\.\d+)?)\s*</dd>", content).group(1))
        total_val = _parse_inr(re.search(r"<span class=\"total-label\">Total</span>\s*<span class=\"total-amount\">(₹[\d,]+(?:\.\d+)?)</span>", content).group(1))

        self.assertEqual(items_val, Decimal("399.00"))
        self.assertEqual(coupon_val, Decimal("100.00"))
        self.assertEqual(delivery_val, Decimal("40.00"))
        self.assertEqual(total_val, Decimal("339.00"))
        self.assertEqual(items_val - coupon_val + delivery_val, total_val)

    def test_scenario_c_free_delivery_above_threshold(self):
        """Scenario C: Items (1200) -> Delivery FREE -> Total (1200)."""
        CartItem.objects.create(cart=self.cart, product=self.prod_high, quantity=1)

        resp = self.client.get(reverse("cart_detail"))
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode("utf-8")

        items_val = _parse_inr(re.search(r"<dt>Items</dt>\s*<dd>(₹[\d,]+(?:\.\d+)?)</dd>", content).group(1))
        total_val = _parse_inr(re.search(r"<span class=\"total-label\">Total</span>\s*<span class=\"total-amount\">(₹[\d,]+(?:\.\d+)?)</span>", content).group(1))

        self.assertEqual(items_val, Decimal("1200.00"))
        self.assertEqual(total_val, Decimal("1200.00"))
        self.assertIn("FREE", content)

    def test_scenario_d_cod_fee(self):
        """Scenario D: COD calculation in checkout review."""
        CartItem.objects.create(cart=self.cart, product=self.prod_low, quantity=1)
        session = self.client.session
        session["checkout_address"] = {
            "full_name": "Test Buyer",
            "phone": "9876543210",
            "line1": "123 Main St",
            "city": "Ahmedabad",
            "state": "GJ",
            "pincode": "560001",
        }
        session.save()

        summary = calculate_cart_summary(
            cart=self.cart,
            buyer_state="GJ",
            payment_method="cod",
        )
        self.assertEqual(summary["subtotal"], Decimal("399.00"))
        self.assertEqual(summary["shipping_fee"], Decimal("40.00"))
        self.assertEqual(summary["cod_fee"], Decimal("50.00"))
        self.assertEqual(summary["grand_total"], Decimal("489.00"))
        self.assertEqual(
            summary["subtotal"] + summary["shipping_fee"] + summary["cod_fee"],
            summary["grand_total"],
        )

    @override_settings(SELLER_GSTIN="")
    def test_bill_of_supply_mode_hides_all_gst_mentions(self):
        """In bill_of_supply mode, no shopper-facing page mentions GST, tax, inclusive, or HSN."""
        CartItem.objects.create(cart=self.cart, product=self.prod_low, quantity=1)

        resp = self.client.get(reverse("cart_detail"))
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode("utf-8")

        # Assert zero GST or tax in summary
        self.assertNotIn("Taxes (GST)", content)
        self.assertNotIn("Includes GST", content)
        self.assertNotIn("inclusive of applicable GST", content)
        self.assertNotIn("HSN", content)

        # Footer compliance copy
        self.assertIn("Bills of supply are issued. No GST is charged.", content)
        self.assertNotIn("Composition Dealer", content)
        self.assertNotIn("Unregistered", content)

    @override_settings(SELLER_GSTIN="29ABCDE1234F1Z5")
    def test_gst_mode_shows_tax_inclusion(self):
        """In GST mode, cart shows tax line and GSTIN in footer."""
        CartItem.objects.create(cart=self.cart, product=self.prod_low, quantity=1)

        resp = self.client.get(reverse("cart_detail"))
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode("utf-8")

        self.assertIn("Includes GST", content)
        self.assertIn("Prices include GST.", content)
        self.assertIn("GSTIN: 29ABCDE1234F1Z5", content)

    def test_promo_code_placeholder_honesty(self):
        """Promo code field has label 'Promo code' and placeholder 'Enter code' without example code."""
        CartItem.objects.create(cart=self.cart, product=self.prod_low, quantity=1)
        resp = self.client.get(reverse("cart_detail"))
        content = resp.content.decode("utf-8")

        self.assertIn('placeholder="Enter code"', content)
        self.assertNotIn("WELCOME10", content)
