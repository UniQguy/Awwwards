"""
Tests for Transactional Emails (Phase 7, WP1).
Verifies:
- Multipart rendering (HTML + TXT)
- Plain-language voice, no "lorem"
- No unrendered template tags
- Financial totals match order snapshot
- Links are absolute with SITE_URL
- Guest tokens included exactly once
- Idempotency guard via EmailLog
- Non-blocking error handling
"""

from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.mail import EmailMultiAlternatives
from django.test import TestCase, override_settings
from django.utils import timezone

User = get_user_model()
from apps.catalog.models import Category, Product
from apps.orders.models import CreditNote, EmailLog, Invoice, Order, OrderItem
from apps.orders.services.email_notifier import (
    _send_transactional_email,
    mask_email,
    mask_token,
    send_cancellation_refund,
    send_cod_placed,
    send_order_confirmation,
    send_payment_confirmation,
    send_status_update,
)


@override_settings(SITE_URL="https://electrocart.in")
class TransactionalEmailsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="aarav.sharma@example.com",
            full_name="Aarav Sharma",
            password="StrongPassword123!",
        )
        self.category = Category.objects.create(name="Headphones", slug="headphones", accent_key="earphones-headphones")
        self.product = Product.objects.create(
            display_name="Sony WH-1000XM5 Noise Cancelling Headphones",
            raw_name="Sony WH-1000XM5 Wireless Headphones Black",
            sku="SONY-XM5-BLK",
            slug="sony-wh-1000xm5-black",
            source_asin="B09XS7JWHH",
            category=self.category,
            selling_price=Decimal("29990.00"),
            mrp=Decimal("34990.00"),
            is_available=True,
        )
        self.order = Order.objects.create(
            order_number="EC-20261007-9911",
            user=self.user,
            guest_email="",
            status=Order.STATUS_CONFIRMED,
            payment_method=Order.PAYMENT_METHOD_RAZORPAY,
            payment_status=Order.PAYMENT_STATUS_CAPTURED,
            subtotal=Decimal("29990.00"),
            shipping_fee=Decimal("0.00"),
            discount_amount=Decimal("1500.00"),
            tax_amount=Decimal("4340.85"),
            total_amount=Decimal("28490.00"),
            shipping_address_snapshot={
                "full_name": "Aarav Sharma",
                "line1": "Flat 402, Shanti Heights",
                "line2": "Indiranagar",
                "city": "Ahmedabad",
                "state": "Gujarat",
                "pincode": "560038",
                "phone": "+91 98765 43210",
            },
        )
        self.item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_title=self.product.display_name,
            product_sku=self.product.sku,
            unit_price=self.product.selling_price,
            mrp=self.product.mrp,
            quantity=1,
            taxable_value=Decimal("24149.15"),
            cgst_amount=Decimal("2170.42"),
            sgst_amount=Decimal("2170.43"),
            line_total=Decimal("28490.00"),
        )

    def test_mask_email_and_token(self):
        self.assertEqual(mask_email("aarav.sharma@example.com"), "a***a@example.com")
        self.assertEqual(mask_email("a@b.com"), "a***@b.com")
        self.assertEqual(mask_email(""), "***")
        self.assertEqual(mask_token("securetoken12345"), "sec***")
        self.assertEqual(mask_token("abc"), "***")

    def test_order_confirmation_rendering_and_invariants(self):
        with self.captureOnCommitCallbacks(execute=True):
            send_order_confirmation(self.order)
        self.assertEqual(len(mail.outbox), 1)
        sent = mail.outbox[0]

        self.assertIn(self.order.order_number, sent.subject)
        self.assertEqual(sent.to, ["aarav.sharma@example.com"])

        # Check plain text content
        self.assertIn("Order Confirmed", sent.body)
        self.assertIn(self.order.order_number, sent.body)
        self.assertIn("28490.00", sent.body)
        self.assertNotIn("lorem", sent.body.lower())
        self.assertNotIn("{{", sent.body)
        self.assertNotIn("{%", sent.body)

        # Check HTML alternative
        self.assertEqual(len(sent.alternatives), 1)
        html_body, mimetype = sent.alternatives[0]
        self.assertEqual(mimetype, "text/html")
        self.assertIn(self.order.order_number, html_body)
        self.assertIn("28490.00", html_body)
        self.assertIn("https://electrocart.in", html_body)
        self.assertNotIn("lorem", html_body.lower())
        self.assertNotIn("{{", html_body)
        self.assertNotIn("{%", html_body)

        # Verify EmailLog created
        log = EmailLog.objects.get(order=self.order, event="order_confirmation")
        self.assertTrue(log.sent_successfully)
        self.assertIn("***", log.recipient_email)

    def test_guest_link_has_token_only_once(self):
        guest_order = Order.objects.create(
            order_number="EC-20261007-GUEST",
            user=None,
            guest_email="guest.shopper@example.com",
            status=Order.STATUS_CONFIRMED,
            total_amount=Decimal("999.00"),
            subtotal=Decimal("999.00"),
        )
        with self.captureOnCommitCallbacks(execute=True):
            send_order_confirmation(guest_order, guest_token="signed_guest_token_999")
        self.assertEqual(len(mail.outbox), 1)
        sent = mail.outbox[0]
        html_body, _ = sent.alternatives[0]

        expected_url = "https://electrocart.in/orders/EC-20261007-GUEST/?token=signed_guest_token_999"
        self.assertIn(expected_url, html_body)
        self.assertEqual(html_body.count("token="), 1)

    def test_email_idempotency_prevents_duplicate_sending(self):
        # First send
        with self.captureOnCommitCallbacks(execute=True):
            send_order_confirmation(self.order)
        self.assertEqual(len(mail.outbox), 1)

        # Second send attempt for same order & event
        with self.captureOnCommitCallbacks(execute=True):
            send_order_confirmation(self.order)
        # Length remains 1 due to EmailLog check
        self.assertEqual(len(mail.outbox), 1)

    def test_non_blocking_error_handling(self):
        with patch.object(EmailMultiAlternatives, "send", side_effect=Exception("SMTP Connection Refused")):
            # Must NOT raise exception
            success = _send_transactional_email(
                self.order,
                "failing_event",
                "Test Subject",
                "emails/order_confirmation",
                {"order": self.order, "order_url": "https://electrocart.in"},
            )
            self.assertFalse(success)

        # Verify failure recorded in EmailLog without breaking transaction
        log = EmailLog.objects.get(order=self.order, event="failing_event")
        self.assertFalse(log.sent_successfully)
        self.assertIn("SMTP Connection Refused", log.error_message)

    def test_payment_confirmation_email(self):
        with self.captureOnCommitCallbacks(execute=True):
            send_payment_confirmation(self.order, payment_id="pay_K99228811AA")
        self.assertEqual(len(mail.outbox), 1)
        sent = mail.outbox[0]
        self.assertIn("Payment Received", sent.subject)
        self.assertIn("pay_K99228811AA", sent.body)

    def test_status_update_email(self):
        with self.captureOnCommitCallbacks(execute=True):
            send_status_update(
                self.order,
                status=Order.STATUS_SHIPPED,
                tracking_number="BLUEDART-8899",
                carrier="Blue Dart",
                estimated_delivery="Thursday, 12 Oct",
            )
        self.assertEqual(len(mail.outbox), 1)
        sent = mail.outbox[0]
        self.assertIn("Shipped", sent.subject)
        self.assertIn("BLUEDART-8899", sent.body)
        self.assertIn("Blue Dart", sent.body)

    def test_cancellation_refund_email(self):
        invoice = Invoice.objects.create(
            invoice_number="EC-INV-2026-27-001",
            order=self.order,
            financial_year="2026-27",
            sequence_number=1,
            is_bill_of_supply=False,
        )
        credit_note = CreditNote.objects.create(
            credit_note_number="EC-CN-2026-27-001",
            invoice=invoice,
            order=self.order,
            financial_year="2026-27",
            sequence_number=1,
            amount=self.order.total_amount,
            tax_amount=Decimal("0.00"),
            reason="Customer request",
        )
        with self.captureOnCommitCallbacks(execute=True):
            send_cancellation_refund(
                self.order,
                credit_note=credit_note,
                refund_amount=self.order.total_amount,
                reason="Customer requested cancellation",
            )
        self.assertEqual(len(mail.outbox), 1)
        sent = mail.outbox[0]
        self.assertIn("Order Cancelled", sent.subject)
        self.assertIn("EC-CN-2026-27-001", sent.body)
        self.assertIn("28490.00", sent.body)

    def test_cod_placed_email(self):
        self.order.payment_method = Order.PAYMENT_METHOD_COD
        with self.captureOnCommitCallbacks(execute=True):
            send_cod_placed(self.order)
        self.assertEqual(len(mail.outbox), 1)
        sent = mail.outbox[0]
        self.assertIn("Cash on Delivery Scheduled", sent.subject)
        self.assertIn("Doorstep", sent.body)
        self.assertIn("28490.00", sent.body)
