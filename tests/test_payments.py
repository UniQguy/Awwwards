"""
Tests for Razorpay HMAC-SHA256 offline signature validation, webhook deduplication,
and stock expiration refund_required fallback.
"""

from datetime import timedelta
from decimal import Decimal
import json
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import Category, Product
from apps.inventory.models import Inventory, StockReservation
from apps.orders.models import Invoice, Order, OrderItem
from apps.orders.services.invoicing import generate_invoice
from apps.payments.models import PaymentTransaction, WebhookEvent
from apps.payments.providers import RazorpayProvider

User = get_user_model()


class RazorpayProviderSignatureTests(TestCase):
    def setUp(self):
        self.secret = "test_super_secret_key_123"
        self.webhook_secret = "test_webhook_secret_456"
        self.provider = RazorpayProvider(
            key_id="rzp_test_123",
            key_secret=self.secret,
            webhook_secret=self.webhook_secret,
        )

    def test_payment_signature_verification(self):
        order_id = "order_DBJOWzybf0sJbb"
        payment_id = "pay_29MoThyfdP3gah"
        valid_sig = RazorpayProvider.generate_test_payment_signature(order_id, payment_id, self.secret)

        self.assertTrue(
            self.provider.verify_payment_signature(order_id, payment_id, valid_sig)
        )
        self.assertFalse(
            self.provider.verify_payment_signature(order_id, payment_id, "invalid_sig_abc123")
        )

    def test_webhook_signature_verification(self):
        body = b'{"event":"payment.captured"}'
        valid_sig = RazorpayProvider.generate_test_webhook_signature(body, self.webhook_secret)

        self.assertTrue(self.provider.verify_webhook_signature(body, valid_sig))
        self.assertFalse(self.provider.verify_webhook_signature(body, "fake_sig_xyz"))


class PaymentVerificationAndWebhookEndpointTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.cat = Category.objects.create(
            name="Audio",
            slug="audio-pay",
            accent_key="earphones-headphones",
            gst_rate=Decimal("18.00"),
        )
        self.prod = Product.objects.create(
            category=self.cat,
            sku="EC-PAY-PROD-1",
            slug="ec-pay-prod-1",
            raw_name="Audio Gear",
            display_name="Audio Gear",
            source_asin="B00PAY0001",
            selling_price=Decimal("1000.00"),
            is_available=True,
        )
        self.inventory = Inventory.objects.create(product=self.prod, quantity=5)

        self.user = User.objects.create_user(email="payuser@example.com", password="SecurePassword123!")
        self.order = Order.objects.create(
            order_number="EC-2026-TEST-PAY1",
            user=self.user,
            status=Order.STATUS_PENDING,
            payment_method="razorpay",
            payment_status=Order.PAYMENT_STATUS_PENDING,
            subtotal=Decimal("1000.00"),
            shipping_fee=Decimal("0.00"),
            total_amount=Decimal("1000.00"),
        )
        self.reservation = StockReservation.objects.create(
            product=self.prod,
            order=self.order,
            quantity=1,
            status=StockReservation.STATUS_RESERVED,
            expires_at=timezone.now() + timedelta(minutes=30),
        )

        self.secret = getattr(settings, "RAZORPAY_KEY_SECRET", "rzp_test_mock_secret_key")
        self.webhook_secret = getattr(settings, "RAZORPAY_WEBHOOK_SECRET", "rzp_test_mock_webhook_secret")

    def test_verify_endpoint_valid_signature_confirms_order(self):
        order_id = "order_rzp_test_1"
        payment_id = "pay_rzp_test_1"
        valid_sig = RazorpayProvider.generate_test_payment_signature(order_id, payment_id, self.secret)

        url = reverse("payments:razorpay_verify")
        payload = {
            "order_number": self.order.order_number,
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": valid_sig,
        }

        response = self.client.post(url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 200)

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.STATUS_CONFIRMED)
        self.assertEqual(self.order.payment_status, Order.PAYMENT_STATUS_CAPTURED)

        # Inventory decremented
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity, 4)

        # Invoice generated
        self.assertTrue(Invoice.objects.filter(order=self.order).exists())

    def test_verify_endpoint_invalid_signature_rejected(self):
        url = reverse("payments:razorpay_verify")
        payload = {
            "order_number": self.order.order_number,
            "razorpay_order_id": "order_rzp_test_1",
            "razorpay_payment_id": "pay_rzp_test_1",
            "razorpay_signature": "bad_signature",
        }

        response = self.client.post(url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.STATUS_PENDING)

    def test_webhook_endpoint_deduplication_and_replay_protection(self):
        url = reverse("payments:razorpay_webhook")
        event_payload = {
            "event_id": "evt_test_dedup_001",
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_test_001",
                        "order_id": "order_test_001",
                        "notes": {"order_number": self.order.order_number},
                    }
                }
            },
        }
        body_bytes = json.dumps(event_payload).encode("utf-8")
        sig = RazorpayProvider.generate_test_webhook_signature(body_bytes, self.webhook_secret)

        # First delivery
        resp1 = self.client.post(
            url,
            data=body_bytes,
            content_type="application/json",
            HTTP_X_RAZORPAY_SIGNATURE=sig,
        )
        self.assertEqual(resp1.status_code, 200)
        data1 = resp1.json()
        self.assertEqual(data1["status"], "success")

        # Second delivery (replay)
        resp2 = self.client.post(
            url,
            data=body_bytes,
            content_type="application/json",
            HTTP_X_RAZORPAY_SIGNATURE=sig,
        )
        self.assertEqual(resp2.status_code, 200)
        data2 = resp2.json()
        self.assertEqual(data2["status"], "already_processed")

    def test_capture_when_reservation_expired_triggers_refund_required(self):
        # Expire reservation and deplete physical inventory
        self.reservation.expires_at = timezone.now() - timedelta(minutes=10)
        self.reservation.save()
        self.inventory.quantity = 0
        self.inventory.save()

        order_id = "order_rzp_expired_1"
        payment_id = "pay_rzp_expired_1"
        valid_sig = RazorpayProvider.generate_test_payment_signature(order_id, payment_id, self.secret)

        url = reverse("payments:razorpay_verify")
        payload = {
            "order_number": self.order.order_number,
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": valid_sig,
        }

        response = self.client.post(url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 400)

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.STATUS_REFUND_REQUIRED)
        self.assertEqual(self.order.payment_status, Order.PAYMENT_STATUS_CAPTURED)
