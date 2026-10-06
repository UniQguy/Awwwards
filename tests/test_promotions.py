"""
Tests for Coupon validation service, discount math, and usage constraints.
"""

from datetime import timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.catalog.models import Category, Product
from apps.inventory.models import Inventory
from apps.cart.models import Cart
from apps.cart.services.cart_service import add_to_cart, get_or_create_cart
from apps.promotions.models import Coupon, CouponRedemption
from apps.promotions.services.coupon_validator import (
    REASON_CATEGORY_MISMATCH,
    REASON_EXPIRED,
    REASON_INACTIVE,
    REASON_INVALID_CODE,
    REASON_MIN_ORDER,
    REASON_USER_LIMIT,
    validate_coupon,
)

User = get_user_model()


class PromotionCouponValidationTests(TestCase):
    def setUp(self):
        self.cat_audio = Category.objects.create(
            name="Audio",
            slug="earphones-headphones",
            accent_key="earphones-headphones",
            gst_rate=Decimal("18.00"),
        )
        self.cat_phones = Category.objects.create(
            name="Phones",
            slug="smartphones",
            accent_key="smartphones",
            gst_rate=Decimal("18.00"),
        )

        self.headphone = Product.objects.create(
            category=self.cat_audio,
            sku="EC-PROMO-HP-1",
            slug="ec-promo-hp-1",
            raw_name="Studio Monitor Pro",
            display_name="Studio Monitor Pro",
            source_asin="B00PROMOHP1",
            selling_price=Decimal("2000.00"),
            is_available=True,
        )
        Inventory.objects.create(product=self.headphone, quantity=10)

        self.phone = Product.objects.create(
            category=self.cat_phones,
            sku="EC-PROMO-PH-1",
            slug="ec-promo-ph-1",
            raw_name="Speed Phone 5G",
            display_name="Speed Phone 5G",
            source_asin="B00PROMOPH1",
            selling_price=Decimal("15000.00"),
            is_available=True,
        )
        Inventory.objects.create(product=self.phone, quantity=5)

        self.user = User.objects.create_user(email="promouser@example.com", password="SecurePassword123!")
        self.cart = get_or_create_cart(user=self.user)

        now = timezone.now()
        self.coupon_pct = Coupon.objects.create(
            code="SAVE10",
            discount_type=Coupon.TYPE_PERCENTAGE,
            discount_value=Decimal("10.00"),
            min_order_amount=Decimal("1000.00"),
            max_discount_amount=Decimal("500.00"),
            valid_from=now - timedelta(days=1),
            valid_until=now + timedelta(days=30),
            is_active=True,
        )

    def test_case_insensitive_match(self):
        add_to_cart(self.cart, self.headphone, quantity=1)
        res = validate_coupon("save10", self.cart, user=self.user)
        self.assertTrue(res.is_valid)
        # 10% of 2000 = 200
        self.assertEqual(res.discount_amount, Decimal("200.00"))

    def test_invalid_coupon_code(self):
        add_to_cart(self.cart, self.headphone, quantity=1)
        res = validate_coupon("DOESNOTEXIST", self.cart, user=self.user)
        self.assertFalse(res.is_valid)
        self.assertEqual(res.reason_code, REASON_INVALID_CODE)

    def test_inactive_coupon(self):
        self.coupon_pct.is_active = False
        self.coupon_pct.save()

        add_to_cart(self.cart, self.headphone, quantity=1)
        res = validate_coupon("SAVE10", self.cart, user=self.user)
        self.assertFalse(res.is_valid)
        self.assertEqual(res.reason_code, REASON_INACTIVE)

    def test_expired_coupon(self):
        self.coupon_pct.valid_until = timezone.now() - timedelta(days=1)
        self.coupon_pct.save()

        add_to_cart(self.cart, self.headphone, quantity=1)
        res = validate_coupon("SAVE10", self.cart, user=self.user)
        self.assertFalse(res.is_valid)
        self.assertEqual(res.reason_code, REASON_EXPIRED)

    def test_min_order_amount_not_met(self):
        # Min order is 1000; create cheap item 500
        cheap = Product.objects.create(
            category=self.cat_audio,
            sku="EC-CHEAP-1",
            slug="ec-cheap-1",
            raw_name="Cheap Cable",
            display_name="Cheap Cable",
            source_asin="B00CHEAP001",
            selling_price=Decimal("500.00"),
            is_available=True,
        )
        Inventory.objects.create(product=cheap, quantity=10)
        add_to_cart(self.cart, cheap, quantity=1)

        res = validate_coupon("SAVE10", self.cart, user=self.user)
        self.assertFalse(res.is_valid)
        self.assertEqual(res.reason_code, REASON_MIN_ORDER)

    def test_percentage_discount_cap(self):
        # Buy phone for 15,000; 10% would be 1,500, but cap is 500
        add_to_cart(self.cart, self.phone, quantity=1)
        res = validate_coupon("SAVE10", self.cart, user=self.user)
        self.assertTrue(res.is_valid)
        self.assertEqual(res.discount_amount, Decimal("500.00"))

    def test_category_restriction(self):
        now = timezone.now()
        cat_coupon = Coupon.objects.create(
            code="AUDIOPRO",
            discount_type=Coupon.TYPE_FIXED,
            discount_value=Decimal("300.00"),
            min_order_amount=Decimal("1000.00"),
            valid_from=now - timedelta(days=1),
            valid_until=now + timedelta(days=30),
            is_active=True,
        )
        cat_coupon.applicable_categories.add(self.cat_audio)

        # Cart with phone only (different category)
        add_to_cart(self.cart, self.phone, quantity=1)
        res = validate_coupon("AUDIOPRO", self.cart, user=self.user)
        self.assertFalse(res.is_valid)
        self.assertEqual(res.reason_code, REASON_CATEGORY_MISMATCH)

        # Now add audio item
        add_to_cart(self.cart, self.headphone, quantity=1)
        res2 = validate_coupon("AUDIOPRO", self.cart, user=self.user)
        self.assertTrue(res2.is_valid)
        self.assertEqual(res2.discount_amount, Decimal("300.00"))

    def test_user_usage_limit(self):
        add_to_cart(self.cart, self.headphone, quantity=1)
        CouponRedemption.objects.create(
            coupon=self.coupon_pct,
            user=self.user,
            discount_applied=Decimal("200.00"),
        )
        res = validate_coupon("SAVE10", self.cart, user=self.user)
        self.assertFalse(res.is_valid)
        self.assertEqual(res.reason_code, REASON_USER_LIMIT)
