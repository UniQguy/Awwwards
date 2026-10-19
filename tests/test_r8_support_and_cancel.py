"""
Tests for Phase R8 Task 3: Guest Order Lookup, Self-Serve Cancellation,
Inventory Restock, and Support Concierge Ticket Flow.
"""

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import Client, TestCase
from django.utils import timezone

from apps.catalog.models import Category, Product
from apps.core.models import SupportTicket
from apps.inventory.models import Inventory
from apps.orders.models import Order, OrderItem, OrderStatusHistory

User = get_user_model()


class SupportAndCancellationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(
            name="Smartphones & Basic Mobiles",
            slug="smartphones-basic-mobiles",
            display_order=1,
            is_active=True,
        )
        self.product = Product.objects.create(
            raw_name="Galaxy S23 Test Phone",
            display_name="Galaxy S23 Test Phone",
            slug="galaxy-s23-test",
            sku="PHONE-S23-TEST",
            source_asin="B00TESTS23",
            category=self.category,
            selling_price=Decimal("49999.00"),
            mrp=Decimal("74999.00"),
            is_available=True,
        )
        self.inventory = Inventory.objects.create(
            product=self.product,
            quantity=8,
        )

        self.order = Order.objects.create(
            order_number="EC-20261019-TEST",
            guest_email="guestbuyer@example.com",
            guest_phone="9876543210",
            status=Order.STATUS_CONFIRMED,
            payment_method="cod",
            subtotal=Decimal("49999.00"),
            tax_amount=Decimal("8999.82"),
            shipping_fee=Decimal("0.00"),
            total_amount=Decimal("49999.00"),
            shipping_address_snapshot={
                "full_name": "Rohan Patel",
                "line1": "101 High Street",
                "city": "Ahmedabad",
                "state": "Gujarat",
                "pincode": "380009",
                "phone": "9876543210",
            },
            billing_address_snapshot={
                "full_name": "Rohan Patel",
                "line1": "101 High Street",
                "city": "Ahmedabad",
                "state": "Gujarat",
                "pincode": "380009",
                "phone": "9876543210",
                "email": "guestbuyer@example.com",
            },
        )
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_title="Galaxy S23 Test Phone",
            product_sku="PHONE-S23-TEST",
            mrp=Decimal("74999.00"),
            quantity=2,
            unit_price=Decimal("24999.50"),
            taxable_value=Decimal("40999.18"),
            line_total=Decimal("49999.00"),
            gst_rate=Decimal("18.00"),
            cgst_amount=Decimal("4499.91"),
            sgst_amount=Decimal("4499.91"),
        )

    def test_support_ticket_submission_and_email(self):
        """Customer submits support ticket; receives ticket ID and confirmation email."""
        resp = self.client.post("/support/", {
            "order_number": "EC-20261019-TEST",
            "email": "rohan@example.com",
            "issue_category": "7-Day Dead on Arrival (DOA) Claim",
            "message": "Screen flickers on first boot. Requesting DOA replacement.",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Support Ticket Registered: #TKT-2026-")

        ticket = SupportTicket.objects.filter(email="rohan@example.com").first()
        self.assertIsNotNone(ticket)
        self.assertTrue(ticket.ticket_id.startswith("TKT-2026-"))
        self.assertEqual(ticket.order_number, "EC-20261019-TEST")
        self.assertEqual(ticket.issue_category, "7-Day Dead on Arrival (DOA) Claim")

        # Confirm confirmation email dispatched
        self.assertTrue(len(mail.outbox) >= 1)
        sent = [m for m in mail.outbox if "Support Ticket Logged:" in m.subject]
        self.assertTrue(len(sent) >= 1)
        self.assertIn("rohan@example.com", sent[0].to)

    def test_guest_order_lookup_by_email_and_phone(self):
        """Guest looks up order with number and email or phone; gains timeline access."""
        # By email
        resp = self.client.post("/orders/track/", {
            "order_number": "EC-20261019-TEST",
            "contact": "guestbuyer@example.com",
        })
        self.assertRedirects(resp, "/orders/track/EC-20261019-TEST/verify/")

        # Follow redirect
        timeline_resp = self.client.get("/orders/track/EC-20261019-TEST/verify/")
        self.assertEqual(timeline_resp.status_code, 200)
        self.assertContains(timeline_resp, "EC-20261019-TEST")
        self.assertContains(timeline_resp, "Self-Serve Order Cancellation")
        self.assertContains(timeline_resp, "Itemized GST Breakdown")

        # By phone
        resp_phone = self.client.post("/orders/track/", {
            "order_number": "EC-20261019-TEST",
            "contact": "9876543210",
        })
        self.assertRedirects(resp_phone, "/orders/track/EC-20261019-TEST/verify/")

    def test_guest_self_serve_cancellation_restores_inventory(self):
        """Guest cancels active order via web; inventory is restored from 8 to 10."""
        # Look up order first to obtain track session authorization
        self.client.post("/orders/track/", {
            "order_number": "EC-20261019-TEST",
            "contact": "guestbuyer@example.com",
        })

        # Submit cancellation with reason
        resp = self.client.post("/orders/EC-20261019-TEST/cancel/", {
            "reason": "Ordered wrong model",
        })
        self.assertRedirects(resp, "/orders/track/EC-20261019-TEST/verify/")

        # Refresh order from db
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.STATUS_CANCELLED)

        # Refresh inventory from db
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity, 10)  # 8 + 2 restored

        # Check history recorded reason
        history = OrderStatusHistory.objects.filter(order=self.order, to_status=Order.STATUS_CANCELLED).first()
        self.assertIsNotNone(history)
        self.assertIn("Ordered wrong model", history.notes)
