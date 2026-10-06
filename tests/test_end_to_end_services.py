"""
End-to-End Acceptance Tests for Phase 2 Commerce Engine.
Tests the complete lifecycle:
Anonymous Browse -> Cart -> Coupon -> Delivery Estimate -> Login & Merge ->
Order Placement (COD vs Online) -> Invoicing -> Status Progression -> Cancellation Restock & Credit Note.
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
from apps.inventory.services.reservation_service import get_available_stock
from apps.cart.models import Cart
from apps.cart.services.cart_calculator import calculate_cart_summary
from apps.cart.services.cart_service import add_to_cart, get_or_create_cart, merge_carts
from apps.orders.models import CreditNote, Invoice, Order
from apps.orders.services.order_creator import place_order
from apps.orders.services.order_status import transition_order_status
from apps.orders.services.tracking import get_tracking_info
from apps.payments.providers import RazorpayProvider
from apps.promotions.models import Coupon
from apps.shipping.models import ShippingConfig, ShippingZone
from apps.shipping.services.estimator import estimate_delivery

User = get_user_model()


class EndToEndCommerceLifecycleTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Seed categories
        self.cat_audio = Category.objects.create(
            name="Audio & Headphones",
            slug="earphones-headphones",
            accent_key="earphones-headphones",
            hsn_code="8518",
            gst_rate=Decimal("18.00"),
            is_gst_rate_verified=True,
        )

        # Seed product & inventory
        self.headphones = Product.objects.create(
            category=self.cat_audio,
            sku="EC-E2E-AUDIO-01",
            slug="pro-sound-headphones",
            raw_name="Pro Sound Reference Studio Headphones",
            display_name="Pro Sound Reference Headphones",
            source_asin="B00E2EAUDIO1",
            selling_price=Decimal("4999.00"),
            mrp=Decimal("7999.00"),
            is_available=True,
        )
        self.inventory = Inventory.objects.create(product=self.headphones, quantity=10)

        # Seed shipping
        self.shipping_cfg = ShippingConfig.get_solo()
        self.shipping_cfg.free_shipping_threshold = Decimal("499.00")
        self.shipping_cfg.standard_fee = Decimal("40.00")
        self.shipping_cfg.cod_fee = Decimal("0.00")
        self.shipping_cfg.save()

        ShippingZone.objects.create(
            name="South Metros",
            pin_prefix="560",
            est_days_min=2,
            est_days_max=3,
            is_active=True,
        )

        # Seed sample coupon
        now = timezone.now()
        self.coupon = Coupon.objects.create(
            code="WELCOME10",
            discount_type=Coupon.TYPE_PERCENTAGE,
            discount_value=Decimal("10.00"),
            min_order_amount=Decimal("999.00"),
            max_discount_amount=Decimal("500.00"),
            valid_from=now - timedelta(days=1),
            valid_until=now + timedelta(days=365),
            is_active=True,
        )

    def test_complete_anonymous_to_cod_order_and_cancellation_flow(self):
        # 1. Anonymous user browses and adds item to cart
        guest_token = "cryptographic_guest_session_token_xyz"
        guest_cart = get_or_create_cart(guest_token=guest_token)
        add_to_cart(guest_cart, self.headphones, quantity=2)

        self.assertEqual(guest_cart.items.count(), 1)
        self.assertEqual(guest_cart.total_quantity, 2)

        # 2. Check delivery estimate for Bengaluru pincode
        estimate = estimate_delivery("560038")
        self.assertEqual(estimate.est_days_min, 2)
        self.assertEqual(estimate.est_days_max, 3)

        # 3. Apply promotional coupon WELCOME10
        summary_guest = calculate_cart_summary(guest_cart, buyer_state="KA", coupon_discount=Decimal("500.00"))
        # 2 x 4999 = 9998; discount 10% capped at 500 = 500; subtotal 9998 - 500 = 9498
        self.assertEqual(summary_guest["subtotal"], Decimal("9998.00"))
        self.assertEqual(summary_guest["coupon_discount"], Decimal("500.00"))
        self.assertEqual(summary_guest["shipping_fee"], Decimal("0.00"))  # >= 499 free shipping

        # 4. Customer registers and logs in -> guest cart is merged into user account
        user = User.objects.create_user(email="e2e_shopper@example.com", password="Password12345!")
        user_cart = get_or_create_cart(user=user)
        merged_cart = merge_carts(guest_cart, user_cart)

        self.assertEqual(merged_cart.items.count(), 1)
        self.assertEqual(merged_cart.total_quantity, 2)
        self.assertFalse(guest_cart.is_active)

        # 5. Place COD order
        shipping_addr = {
            "street": "100 Feet Road, HAL 2nd Stage",
            "city": "Bengaluru",
            "state": "KA",
            "pincode": "560038",
            "phone": "9876543210",
        }

        order = place_order(
            cart=merged_cart,
            user=user,
            shipping_address=shipping_addr,
            payment_method="cod",
            coupon_code="WELCOME10",
        )

        self.assertEqual(order.status, Order.STATUS_CONFIRMED)
        self.assertEqual(order.payment_method, "cod")
        self.assertEqual(order.discount_amount, Decimal("500.00"))
        self.assertEqual(order.total_amount, Decimal("9498.00"))

        # Inventory check: physical units decremented 10 - 2 = 8
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity, 8)
        self.assertEqual(get_available_stock(self.headphones), 8)

        # Sequential invoice check
        self.assertTrue(hasattr(order, "invoice"))
        inv = order.invoice
        self.assertTrue(inv.invoice_number.startswith("EC-INV-"))
        self.assertEqual(inv.sequence_number, 1)

        # 6. Check Tracking Information
        tracking = get_tracking_info(order)
        self.assertEqual(tracking["order_number"], order.order_number)
        self.assertTrue(tracking["steps"][0]["completed"])

        # 7. Progress order status: confirmed -> processing -> cancelled
        transition_order_status(order, Order.STATUS_PROCESSING, notes="Quality inspection passed")
        self.assertEqual(order.status, Order.STATUS_PROCESSING)

        transition_order_status(order, Order.STATUS_CANCELLED, notes="Buyer request before courier dispatch")
        self.assertEqual(order.status, Order.STATUS_CANCELLED)

        # Check physical inventory was restocked back to 10
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity, 10)

        # Check GST Credit Note was issued referencing the invoice
        cn = CreditNote.objects.filter(order=order).first()
        self.assertIsNotNone(cn)
        self.assertTrue(cn.credit_note_number.startswith("EC-CN-"))
        self.assertEqual(cn.amount, order.total_amount)

    def test_complete_razorpay_gateway_verification_and_webhook_replay(self):
        user = User.objects.create_user(email="rzp_shopper@example.com", password="Password12345!")
        cart = get_or_create_cart(user=user)
        add_to_cart(cart, self.headphones, quantity=1)

        shipping_addr = {"state": "MH", "pincode": "400001"}
        order = place_order(
            cart=cart,
            user=user,
            shipping_address=shipping_addr,
            payment_method="razorpay",
        )

        self.assertEqual(order.status, Order.STATUS_PENDING)
        # Inventory not decremented yet, but 1 unit reserved
        self.assertEqual(get_available_stock(self.headphones), 9)

        # Simulate Razorpay verify callback
        secret = getattr(settings, "RAZORPAY_KEY_SECRET", "rzp_test_mock_secret_key")
        rzp_order_id = "order_E2E_RZP_001"
        rzp_pay_id = "pay_E2E_RZP_001"
        valid_sig = RazorpayProvider.generate_test_payment_signature(rzp_order_id, rzp_pay_id, secret)

        verify_url = reverse("payments:razorpay_verify")
        resp = self.client.post(
            verify_url,
            data=json.dumps({
                "order_number": order.order_number,
                "razorpay_order_id": rzp_order_id,
                "razorpay_payment_id": rzp_pay_id,
                "razorpay_signature": valid_sig,
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)

        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_CONFIRMED)
        self.assertEqual(order.payment_status, Order.PAYMENT_STATUS_CAPTURED)

        # Physical inventory decremented
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity, 9)

        # Invoice generated
        self.assertTrue(Invoice.objects.filter(order=order).exists())

    def test_expired_reservation_triggers_refund_required(self):
        user = User.objects.create_user(email="late_buyer@example.com", password="Password12345!")
        cart = get_or_create_cart(user=user)
        add_to_cart(cart, self.headphones, quantity=1)

        shipping_addr = {"state": "DL", "pincode": "110001"}
        order = place_order(cart=cart, user=user, shipping_address=shipping_addr, payment_method="razorpay")

        # Simulate TTL expiration and complete stock exhaustion by another customer
        res = order.reservations.first()
        res.expires_at = timezone.now() - timedelta(minutes=5)
        res.save()

        self.inventory.quantity = 0
        self.inventory.save()

        secret = getattr(settings, "RAZORPAY_KEY_SECRET", "rzp_test_mock_secret_key")
        rzp_order_id = "order_E2E_LATE_001"
        rzp_pay_id = "pay_E2E_LATE_001"
        valid_sig = RazorpayProvider.generate_test_payment_signature(rzp_order_id, rzp_pay_id, secret)

        verify_url = reverse("payments:razorpay_verify")
        resp = self.client.post(
            verify_url,
            data=json.dumps({
                "order_number": order.order_number,
                "razorpay_order_id": rzp_order_id,
                "razorpay_payment_id": rzp_pay_id,
                "razorpay_signature": valid_sig,
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_REFUND_REQUIRED)
        self.assertEqual(order.payment_status, Order.PAYMENT_STATUS_CAPTURED)
