"""
Tests for apps.shipping: ShippingConfig, zones, pincode serviceability, and fee calculations.
"""

from decimal import Decimal
import datetime
from django.core.management import call_command
from django.test import TestCase

from apps.shipping.models import PincodeServiceability, ShippingConfig, ShippingZone
from apps.shipping.services.estimator import estimate
from apps.shipping.services.fees import quote


class ShippingFeeQuoteTests(TestCase):
    """Test suite for shipping fees and free delivery threshold boundaries."""

    def setUp(self):
        self.config = ShippingConfig.get_solo()
        self.config.free_shipping_threshold = Decimal("499.00")
        self.config.standard_fee = Decimal("40.00")
        self.config.cod_fee = Decimal("30.00")
        self.config.save()

    def test_boundary_free_shipping_exact_499(self):
        """₹499.00 qualifies for free delivery (₹0.00 fee)."""
        q = quote(Decimal("499.00"), payment_method="razorpay", config=self.config)
        self.assertTrue(q.is_free)
        self.assertEqual(q.delivery_fee, Decimal("0.00"))
        self.assertEqual(q.amount_to_free, Decimal("0.00"))
        self.assertEqual(q.total_shipping_charges, Decimal("0.00"))

    def test_boundary_standard_shipping_498_99(self):
        """₹498.99 incurs the standard shipping fee of ₹40.00."""
        q = quote(Decimal("498.99"), payment_method="razorpay", config=self.config)
        self.assertFalse(q.is_free)
        self.assertEqual(q.delivery_fee, Decimal("40.00"))
        self.assertEqual(q.amount_to_free, Decimal("0.01"))
        self.assertEqual(q.total_shipping_charges, Decimal("40.00"))

    def test_discount_dropping_subtotal_below_threshold(self):
        """A discount dropping the cart total from ₹520 to ₹470 restores the shipping fee."""
        subtotal_before = Decimal("520.00")
        discount = Decimal("50.00")
        net_after = subtotal_before - discount  # ₹470.00

        q = quote(net_after, payment_method="razorpay", config=self.config)
        self.assertFalse(q.is_free)
        self.assertEqual(q.delivery_fee, Decimal("40.00"))
        self.assertEqual(q.amount_to_free, Decimal("29.00"))

    def test_cod_fee_applied_only_for_cod_payment_method(self):
        """COD payment adds cod_fee on top of shipping charges."""
        # Order eligible for free shipping
        q_free_cod = quote(Decimal("500.00"), payment_method="cod", config=self.config)
        self.assertTrue(q_free_cod.is_free)
        self.assertEqual(q_free_cod.delivery_fee, Decimal("0.00"))
        self.assertEqual(q_free_cod.cod_fee, Decimal("30.00"))
        self.assertEqual(q_free_cod.total_shipping_charges, Decimal("30.00"))

        # Order paying standard delivery fee
        q_paid_cod = quote(Decimal("300.00"), payment_method="cod", config=self.config)
        self.assertFalse(q_paid_cod.is_free)
        self.assertEqual(q_paid_cod.delivery_fee, Decimal("40.00"))
        self.assertEqual(q_paid_cod.cod_fee, Decimal("30.00"))
        self.assertEqual(q_paid_cod.total_shipping_charges, Decimal("70.00"))

    def test_singleton_pk1_enforcement(self):
        """Attempting to create another ShippingConfig row updates pk=1."""
        c2 = ShippingConfig(free_shipping_threshold=Decimal("999.00"))
        c2.save()
        self.assertEqual(c2.pk, 1)
        self.assertEqual(ShippingConfig.objects.count(), 1)


class DeliveryEstimatorTests(TestCase):
    """Test suite for PIN code serviceability and shipping zone prefix matching."""

    def setUp(self):
        # 1-digit national fallback zone
        ShippingZone.objects.create(
            name="Zone 5 National",
            pin_prefix="5",
            est_days_min=4,
            est_days_max=6,
            cod_allowed=True,
            is_active=True,
            source="sample",
        )
        # 2-digit regional zone
        ShippingZone.objects.create(
            name="Zone 56 Regional",
            pin_prefix="56",
            est_days_min=3,
            est_days_max=5,
            cod_allowed=True,
            is_active=True,
            source="sample",
        )
        # 3-digit city zone (Metro)
        ShippingZone.objects.create(
            name="Zone 560 Metro",
            pin_prefix="560",
            est_days_min=2,
            est_days_max=3,
            cod_allowed=True,
            is_active=True,
            source="sample",
        )

    def test_longest_prefix_wins(self):
        """Prefix 560 beats 56 and 5 for pincode 560038."""
        today = datetime.date(2026, 10, 10)
        est = estimate("560038", today=today)

        self.assertTrue(est.serviceable)
        self.assertEqual(est.matched_by, "zone_prefix")
        self.assertEqual(est.est_days_min, 2)
        self.assertEqual(est.est_days_max, 3)
        self.assertEqual(est.date_min, datetime.date(2026, 10, 12))
        self.assertEqual(est.date_max, datetime.date(2026, 10, 13))

    def test_intermediate_prefix_fallback(self):
        """Pincode 569001 (prefix 56) falls back to 56 zone when 569 doesn't exist."""
        est = estimate("569001")
        self.assertTrue(est.serviceable)
        self.assertEqual(est.est_days_min, 3)
        self.assertEqual(est.est_days_max, 5)

    def test_exact_pincode_override_beats_zone(self):
        """Exact PincodeServiceability record takes absolute precedence over zones."""
        PincodeServiceability.objects.create(
            pincode="560038",
            state="Gujarat",
            is_serviceable=True,
            est_days_min=1,
            est_days_max=1,
            cod_allowed=False,
            source="imported",
        )

        est = estimate("560038")
        self.assertTrue(est.serviceable)
        self.assertEqual(est.matched_by, "exact")
        self.assertEqual(est.est_days_min, 1)
        self.assertFalse(est.cod_allowed)
        self.assertFalse(est.is_sample)

    def test_unserviceable_exact_pincode_returns_unavailable(self):
        """Suspended PIN code returns serviceable=False and never a date."""
        PincodeServiceability.objects.create(
            pincode="560099",
            state="Gujarat",
            is_serviceable=False,
            source="imported",
        )

        est = estimate("560099")
        self.assertFalse(est.serviceable)
        self.assertIsNone(est.date_min)
        self.assertIsNone(est.date_max)

    def test_unknown_pincode_outside_zones_returns_unavailable(self):
        """PIN code with no matching prefix returns unavailable with no dates."""
        est = estimate("110001")  # No zone 1 configured in setUp
        self.assertFalse(est.serviceable)
        self.assertIsNone(est.date_min)
        self.assertIsNone(est.date_max)

    def test_invalid_pincode_format(self):
        """Non-numeric or non-6 digit codes fail immediately."""
        self.assertFalse(estimate("012345").serviceable)
        self.assertFalse(estimate("56003").serviceable)
        self.assertFalse(estimate("ABCDEF").serviceable)

    def test_seed_pincodes_command(self):
        """Command seeds 9 sample zones and creates ShippingConfig."""
        ShippingZone.objects.all().delete()
        call_command("seed_pincodes", sample=True)
        self.assertEqual(ShippingZone.objects.filter(source="sample").count(), 9)
        self.assertTrue(ShippingConfig.objects.filter(pk=1).exists())
