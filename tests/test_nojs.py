"""
JavaScript-Disabled End-to-End Commerce Flow Test Suite.
Verifies that complete purchase, cart modification, and order placement flows
function seamlessly in a browser with JavaScript completely disabled.
"""

from decimal import Decimal
from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import Category, Product
from apps.inventory.models import Inventory
from apps.orders.models import Order
from apps.promotions.models import Coupon
from apps.shipping.models import PincodeServiceability
from django.utils import timezone
from datetime import timedelta


class NoJavaScriptCommerceFlowTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Keyboards",
            slug="keyboards",
            accent_key="keyboards-mice",
            gst_rate=Decimal("18.00"),
        )
        self.product = Product.objects.create(
            category=self.category,
            sku="SKU-NOJS-001",
            slug="mechanical-keyboard-nojs",
            raw_name="Tactile Custom Mechanical Keyboard",
            display_name="Tactile Mechanical Keyboard",
            selling_price=Decimal("12000.00"),
            mrp=Decimal("14000.00"),
            is_available=True,
        )
        self.inventory = Inventory.objects.create(product=self.product, quantity=10)

        self.coupon = Coupon.objects.create(
            code="TACTILE100",
            discount_type="fixed",
            discount_value=Decimal("100.00"),
            min_order_amount=Decimal("1000.00"),
            valid_from=timezone.now() - timedelta(days=1),
            valid_until=timezone.now() + timedelta(days=5),
            is_active=True,
        )

        PincodeServiceability.objects.create(
            pincode="560025",
            state="Karnataka",
            is_serviceable=True,
            est_days_min=1,
            est_days_max=3,
            cod_allowed=True,
        )

    def test_complete_nojs_clickthrough_to_cod_success(self):
        # 1. Browse Home
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)

        # 2. Browse Category
        resp = self.client.get(f"/c/{self.category.slug}/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Tactile Mechanical Keyboard")

        # 3. View Product Detail
        resp = self.client.get(f"/p/{self.product.slug}/")
        self.assertEqual(resp.status_code, 200)

        # 4. Standard POST Add to Cart (No AJAX, regular form submission)
        resp = self.client.post(
            f"/cart/add/{self.product.id}/",
            {"quantity": "1"},
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Tactile Mechanical Keyboard")

        # 5. Standard POST Apply Coupon
        resp = self.client.post("/cart/coupon/apply/", {"code": "TACTILE100"}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "TACTILE100")
        self.assertContains(resp, "applied!")

        # 6. Proceed to Checkout: Guest Contact Form
        resp = self.client.post("/checkout/guest/", {
            "full_name": "Kavita Rao",
            "email": "kavita@example.com",
            "phone": "9812345678",
        }, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "orders/checkout_address.html")

        # 7. Standard POST Delivery Address
        resp = self.client.post("/checkout/address/", {
            "full_name": "Kavita Rao",
            "phone": "9812345678",
            "line1": "Flat 304, Richmond Plaza",
            "city": "Bengaluru",
            "state": "Karnataka",
            "pincode": "560025",
        }, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "orders/checkout_review.html")
        self.assertContains(resp, "Cash on Delivery (COD)")

        # 8. Standard POST Place Order COD
        resp = self.client.post("/checkout/place/", {
            "payment_method": "cod",
            "notes": "Ring the bell upon delivery.",
        }, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "orders/order_success.html")
        self.assertContains(resp, "Order Placed Successfully")

        # 9. Verify Order Integrity in Database
        order = Order.objects.filter(guest_email="kavita@example.com").first()
        self.assertIsNotNone(order)
        self.assertEqual(order.payment_method, "cod")
        self.assertEqual(order.status, Order.STATUS_CONFIRMED)
        self.assertEqual(order.discount_amount, Decimal("100.00"))
        self.assertEqual(order.total_amount, Decimal("11900.00"))  # 12000 - 100
        self.assertTrue(hasattr(order, "invoice"))
        self.assertIsNotNone(order.invoice)

        # 10. View Printable Invoice via standard GET
        resp_inv = self.client.get(f"/orders/{order.order_number}/invoice/")
        self.assertEqual(resp_inv.status_code, 200)
        self.assertContains(resp_inv, order.invoice.invoice_number)
        self.assertContains(resp_inv, "Rupees Eleven Thousand Nine Hundred Only")
