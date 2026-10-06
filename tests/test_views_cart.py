"""
Shopping cart and promotion view tests.
Tests cart detail, item additions, quantity updates, removals, and coupon lifecycle.
"""

from decimal import Decimal
from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import Category, Product
from apps.inventory.models import Inventory
from apps.promotions.models import Coupon


class CartViewsTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Audio",
            slug="audio",
            accent_key="earphones-headphones",
            gst_rate=Decimal("18.00"),
        )
        self.product = Product.objects.create(
            category=self.category,
            sku="SKU-CART-001",
            slug="test-earphones",
            raw_name="Test In-Ear Earphones High Fidelity",
            display_name="Test Hi-Fi Earphones",
            selling_price=Decimal("400.00"),
            mrp=Decimal("500.00"),
            is_available=True,
        )
        self.inventory = Inventory.objects.create(product=self.product, quantity=10)

        # Coupons
        self.coupon_valid = Coupon.objects.create(
            code="SAVE50",
            discount_type="fixed",
            discount_value=Decimal("50.00"),
            min_order_amount=Decimal("300.00"),
            valid_from=timezone.now() - timedelta(days=1),
            valid_until=timezone.now() + timedelta(days=5),
            is_active=True,
        )

    def test_empty_cart_detail(self):
        response = self.client.get(reverse("cart_detail"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your Shopping Cart is Empty")

    def test_cart_add_and_detail(self):
        url = reverse("cart_add", kwargs={"product_id": self.product.id})
        response = self.client.post(url, {"quantity": 1}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Hi-Fi Earphones")
        self.assertContains(response, "₹400")

    def test_cart_add_clamped_to_available_stock(self):
        url = reverse("cart_add", kwargs={"product_id": self.product.id})
        # Try to add 50 units when only 10 available
        self.client.post(url, {"quantity": 50}, follow=True)
        resp = self.client.get(reverse("cart_detail"))
        # Must be clamped to 10
        self.assertContains(resp, 'value="10"')

    def test_cart_update_quantity(self):
        # Add item
        self.client.post(reverse("cart_add", kwargs={"product_id": self.product.id}), {"quantity": 1})

        # Update to 3
        update_url = reverse("cart_update", kwargs={"product_id": self.product.id})
        self.client.post(update_url, {"quantity": 3}, follow=True)
        resp = self.client.get(reverse("cart_detail"))
        self.assertContains(resp, 'value="3"')
        self.assertContains(resp, "₹1,200")

        # Update to 0 removes item
        self.client.post(update_url, {"quantity": 0}, follow=True)
        resp_after = self.client.get(reverse("cart_detail"))
        self.assertContains(resp_after, "Your Shopping Cart is Empty")

    def test_cart_remove_and_clear(self):
        self.client.post(reverse("cart_add", kwargs={"product_id": self.product.id}), {"quantity": 2})

        # Remove item
        remove_url = reverse("cart_remove", kwargs={"product_id": self.product.id})
        self.client.post(remove_url, follow=True)
        resp = self.client.get(reverse("cart_detail"))
        self.assertContains(resp, "Your Shopping Cart is Empty")

        # Re-add and clear
        self.client.post(reverse("cart_add", kwargs={"product_id": self.product.id}), {"quantity": 1})
        self.client.post(reverse("cart_clear"), follow=True)
        resp_cleared = self.client.get(reverse("cart_detail"))
        self.assertContains(resp_cleared, "Your Shopping Cart is Empty")

    def test_coupon_apply_and_remove(self):
        # Add item (subtotal ₹400)
        self.client.post(reverse("cart_add", kwargs={"product_id": self.product.id}), {"quantity": 1})

        # Apply valid coupon
        resp_coupon = self.client.post(reverse("coupon_apply"), {"code": "SAVE50"}, follow=True)
        self.assertEqual(resp_coupon.status_code, 200)
        self.assertContains(resp_coupon, "SAVE50")
        self.assertContains(resp_coupon, "applied!")
        self.assertContains(resp_coupon, "-₹50")

        # Remove coupon
        resp_remove = self.client.post(reverse("coupon_remove"), follow=True)
        self.assertEqual(resp_remove.status_code, 200)
        self.assertContains(resp_remove, "Coupon removed")

    def test_coupon_invalid_code_rejected(self):
        self.client.post(reverse("cart_add", kwargs={"product_id": self.product.id}), {"quantity": 1})
        resp = self.client.post(reverse("coupon_apply"), {"code": "NONEXISTENT"}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "was not recognized")
