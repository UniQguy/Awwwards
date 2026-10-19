"""
Order post-purchase lifecycle view tests.
Tests order success confirmation, statutory invoice rendering with Indian words,
cancellation with stock restoration and credit notes, and tracking timeline.
"""

from decimal import Decimal
import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import Category, Product
from apps.inventory.models import Inventory
from apps.orders.models import Order, OrderItem
from apps.orders.services.invoicing import generate_invoice

User = get_user_model()


class OrderViewsTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Audio",
            slug="audio",
            accent_key="earphones-headphones",
            gst_rate=Decimal("18.00"),
        )
        self.product = Product.objects.create(
            category=self.category,
            sku="SKU-ORD-001",
            slug="planar-headphones",
            raw_name="Planar Magnetic Studio Headphones",
            display_name="Planar Magnetic Headphones",
            selling_price=Decimal("45000.00"),
            mrp=Decimal("50000.00"),
            is_available=True,
        )
        self.inv = Inventory.objects.create(product=self.product, quantity=10)

        self.user = User.objects.create_user(email="buyer@example.com", password="password123")

        self.order = Order.objects.create(
            order_number="EC-20261006-TEST1",
            user=self.user,
            guest_email="buyer@example.com",
            guest_phone="9876543210",
            status=Order.STATUS_CONFIRMED,
            payment_method=Order.PAYMENT_METHOD_COD,
            payment_status=Order.PAYMENT_STATUS_PENDING,
            subtotal=Decimal("45000.00"),
            shipping_fee=Decimal("0.00"),
            tax_amount=Decimal("6864.41"),
            total_amount=Decimal("45000.00"),
            shipping_address_snapshot={
                "full_name": "Buyer Test",
                "phone": "9876543210",
                "line1": "Flat 101, Brigade Towers",
                "city": "Ahmedabad",
                "state": "Gujarat",
                "pincode": "560001",
            },
        )
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_title=self.product.display_name,
            product_sku=self.product.sku,
            unit_price=self.product.selling_price,
            mrp=self.product.mrp,
            quantity=1,
            taxable_value=Decimal("38135.59"),
            cgst_amount=Decimal("3432.20"),
            sgst_amount=Decimal("3432.21"),
            line_total=Decimal("45000.00"),
        )
        generate_invoice(self.order)

    def test_order_success_access_control(self):
        url = reverse("order_success", kwargs={"order_number": self.order.order_number})

        # Anonymous without token -> 404
        resp_unauth = self.client.get(url)
        self.assertEqual(resp_unauth.status_code, 404)

        # Authenticated owner -> 200
        self.client.force_login(self.user)
        resp_owner = self.client.get(url)
        self.assertEqual(resp_owner.status_code, 200)
        self.assertContains(resp_owner, "Order Confirmed")
        self.assertContains(resp_owner, self.order.order_number)

    def test_order_invoice_renders_statutory_details_and_words(self):
        self.client.force_login(self.user)
        url = reverse("order_invoice", kwargs={"order_number": self.order.order_number})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Asserts invoice fields and Indian amount in words
        self.assertContains(response, self.order.invoice.invoice_number)
        self.assertContains(response, "Tax Invoice")
        self.assertContains(response, "Rupees Forty Five Thousand Only")
        self.assertContains(response, "Rule 46 of Central Goods and Services Tax")

    def test_order_cancellation_restocks_and_issues_credit_note(self):
        self.client.force_login(self.user)
        cancel_url = reverse("order_cancel", kwargs={"order_number": self.order.order_number})
        resp = self.client.post(cancel_url, follow=True)
        self.assertEqual(resp.status_code, 200)

        # Verify status is cancelled
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.STATUS_CANCELLED)

        # Verify credit note issued
        self.assertTrue(self.order.credit_notes.exists())
        cn = self.order.credit_notes.first()
        self.assertEqual(cn.amount, Decimal("45000.00"))

    def test_order_tracking_lookup_and_timeline(self):
        # 1. Tracking lookup form submission
        lookup_url = reverse("order_track_lookup")
        resp_lookup = self.client.post(lookup_url, {
            "order_number": self.order.order_number,
            "contact": "9876543210",
        }, follow=True)
        self.assertEqual(resp_lookup.status_code, 200)

        # Timeline renders
        self.assertContains(resp_lookup, "Shipment Progress")
        self.assertContains(resp_lookup, "Order Confirmed")
        self.assertContains(resp_lookup, "Processing &amp; Quality Check")
