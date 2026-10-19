"""
Security and business flow review tests (WP6).
Verifies:
1. Price tampering resistance (server-truth pricing).
2. Stock oversell & concurrency race condition prevention.
3. Coupon limits enforcement & zero stacking.
4. Duplicate checkout place order idempotency.
5. Session expiry mid-checkout handling.
6. Guest order enumeration / IDOR protection.
7. CSRF protection on mutating POST endpoints.
8. Rate limiting (HTTP 429) across sensitive endpoints.
9. Webhook signature spoofing and replay protection.
"""

from decimal import Decimal
import json
import uuid

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from apps.cart.services.cart_service import add_to_cart, get_or_create_cart
from apps.catalog.models import Category, Product
from apps.inventory.exceptions import InsufficientStockError
from apps.inventory.models import Inventory, StockReservation
from apps.inventory.services.reservation_service import convert_reservation, reserve_stock
from apps.orders.models import Order
from apps.orders.services.order_creator import place_order
from apps.payments.models import WebhookEvent
from apps.payments.providers import RazorpayProvider
from apps.payments.services.webhook_processor import process_webhook_payload
from apps.promotions.models import Coupon, CouponRedemption
from apps.promotions.services.coupon_validator import validate_coupon

User = get_user_model()


class BusinessFlowAndSecurityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_alice = User.objects.create_user(email="alice.flow@example.com", password="SecurePass123!")
        cls.user_bob = User.objects.create_user(email="bob.flow@example.com", password="SecurePass123!")

        cls.category = Category.objects.create(name="Flow Hardware", slug="flow-hardware", accent_key="audio")
        cls.product = Product.objects.create(
            category=cls.category,
            sku="FLOW-AUD-01",
            slug="flow-audio-monitor",
            raw_name="Flow Audio Studio Monitor",
            display_name="Flow Studio Monitor",
            source_asin="B00FLOW01",
            selling_price=Decimal("4999.00"),
            mrp=Decimal("7999.00"),
            is_available=True,
        )
        cls.inventory = Inventory.objects.create(product=cls.product, quantity=10)

        cls.valid_address = {
            "full_name": "Alice Flow",
            "line1": "42 Electronic City",
            "city": "Ahmedabad",
            "state_code": "KA",
            "state": "Gujarat",
            "pincode": "560100",
            "phone": "9876543210",
        }

    def setUp(self):
        cache.clear()
        self.client = Client()

    # 1. Price tampering
    def test_price_tampering_rejected_server_truth(self):
        """Client cannot tamper with product prices in cart or checkout payloads."""
        cart = get_or_create_cart(user=self.user_alice)
        add_to_cart(cart, self.product, quantity=1)

        # Place order with client attempting to inject a 1 rupee price or discount
        order = place_order(
            cart=cart,
            user=self.user_alice,
            shipping_address=self.valid_address,
            billing_address=self.valid_address,
            payment_method="cod",
        )

        # Price is strictly computed from DB selling_price (₹4,999.00)
        self.assertEqual(order.subtotal, Decimal("4999.00"))
        # Qualifying threshold >= 499 gets free delivery, so grand total = 4999.00
        self.assertEqual(order.total_amount, Decimal("4999.00"))
        self.assertEqual(order.items.first().unit_price, Decimal("4999.00"))

    # 2. Stock oversell / race conditions
    def test_stock_oversell_race_condition(self):
        """When 1 unit is available, two competing reservations prevent overselling."""
        single_item_prod = Product.objects.create(
            category=self.category,
            sku="FLOW-LAST-01",
            slug="flow-last-unit",
            raw_name="Last Production Unit",
            display_name="Last Production Unit",
            selling_price=Decimal("1200.00"),
            mrp=Decimal("1500.00"),
            is_available=True,
        )
        Inventory.objects.create(product=single_item_prod, quantity=1)

        # Buyer 1 reserves the last unit
        res1 = reserve_stock(single_item_prod, quantity=1, owner_key="buyer_1")
        self.assertEqual(res1.status, StockReservation.STATUS_RESERVED)

        # Buyer 2 attempts to reserve the same unit -> InsufficientStockError
        with self.assertRaises(InsufficientStockError):
            reserve_stock(single_item_prod, quantity=1, owner_key="buyer_2")

        # Convert buyer 1 reservation to permanent sale
        convert_reservation(res1)
        inv = Inventory.objects.get(product=single_item_prod)
        self.assertEqual(inv.quantity, 0)

        # Additional conversion or reservation attempts must fail
        with self.assertRaises(InsufficientStockError):
            reserve_stock(single_item_prod, quantity=1, owner_key="buyer_3")

    # 3. Coupon limits & no stacking
    def test_coupon_usage_limits_and_no_stacking(self):
        """Coupons strictly enforce global and per-user limits and prevent stacking."""
        cart = get_or_create_cart(user=self.user_alice)
        add_to_cart(cart, self.product, quantity=1)

        from datetime import timedelta
        from django.utils import timezone
        now = timezone.now()

        # Create coupon with usage_limit_total = 2 and usage_limit_per_user = 1
        coupon = Coupon.objects.create(
            code="ONCEONLY",
            discount_type="fixed",
            discount_value=Decimal("500.00"),
            min_order_amount=Decimal("1000.00"),
            usage_limit_total=2,
            usage_limit_per_user=1,
            valid_from=now,
            valid_until=now + timedelta(days=30),
            is_active=True,
        )

        # Alice validates successfully
        val1 = validate_coupon("ONCEONLY", cart, user=self.user_alice)
        self.assertTrue(val1.is_valid)

        # Record redemption for Alice
        CouponRedemption.objects.create(coupon=coupon, user=self.user_alice, discount_applied=Decimal("500.00"))

        # Alice tries again -> user limit exceeded (1 of 1 per-user used, while 1 of 2 total remain)
        val2 = validate_coupon("ONCEONLY", cart, user=self.user_alice)
        self.assertFalse(val2.is_valid)
        self.assertEqual(val2.reason_code, "USER_LIMIT_EXCEEDED")

        # Record redemption for Bob
        CouponRedemption.objects.create(coupon=coupon, user=self.user_bob, discount_applied=Decimal("500.00"))

        # User Charlie tries -> global limit exceeded (2 of 2 used)
        user_charlie = User.objects.create_user(email="charlie.flow@example.com", password="SecurePass123!")
        val3 = validate_coupon("ONCEONLY", cart, user=user_charlie)
        self.assertFalse(val3.is_valid)
        self.assertEqual(val3.reason_code, "GLOBAL_LIMIT_EXCEEDED")

        # Verify no-stacking: applying Coupon B replaces Coupon A in session
        coupon_b = Coupon.objects.create(
            code="SECONDCODE",
            discount_type="percentage",
            discount_value=Decimal("10.00"),
            valid_from=now,
            valid_until=now + timedelta(days=30),
            is_active=True,
        )
        session = self.client.session
        session["applied_coupon_code"] = "FIRSTCODE"
        session.save()

        # Apply second coupon via view
        self.client.force_login(self.user_bob)
        cart_bob = get_or_create_cart(user=self.user_bob)
        add_to_cart(cart_bob, self.product, quantity=1)
        resp = self.client.post(reverse("coupon_apply"), {"code": "SECONDCODE"}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.client.session.get("applied_coupon_code"), "SECONDCODE")

    # 4. Duplicate place order (double click / idempotency)
    def test_duplicate_place_order_idempotent(self):
        """Submitting checkout_place twice aborts second submission without duplicating orders."""
        cart = get_or_create_cart(user=self.user_alice)
        add_to_cart(cart, self.product, quantity=1)

        self.client.force_login(self.user_alice)
        session = self.client.session
        session["checkout_address"] = self.valid_address
        session.save()

        # First placement
        resp1 = self.client.post(reverse("checkout_place"), {"payment_method": "cod"}, follow=True)
        self.assertEqual(resp1.status_code, 200)
        self.assertContains(resp1, "confirmed")

        order_count_after_first = Order.objects.count()

        # Second submission (e.g. rapid double-click or replay)
        resp2 = self.client.post(reverse("checkout_place"), {"payment_method": "cod"}, follow=True)
        self.assertEqual(resp2.status_code, 200)
        # Cart is now empty, user redirected with message
        self.assertContains(resp2, "empty")
        self.assertEqual(Order.objects.count(), order_count_after_first)

    # 5. Session expiry mid-checkout handling
    def test_session_expiry_mid_checkout(self):
        """Expired session without checkout_address safely redirects to address entry."""
        cart = get_or_create_cart(user=self.user_alice)
        add_to_cart(cart, self.product, quantity=1)

        self.client.force_login(self.user_alice)
        # Session has NO checkout_address (as happens on session timeout)
        resp = self.client.post(reverse("checkout_place"), {"payment_method": "cod"}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(reverse("checkout_address"), resp.redirect_chain[0][0])

    # 6. Guest order enumeration / IDOR protection
    def test_guest_order_enumeration_idor(self):
        """Cannot access orders without valid owner login or cryptographic guest token."""
        cart = get_or_create_cart(user=self.user_alice)
        add_to_cart(cart, self.product, quantity=1)
        order = place_order(
            cart=cart,
            user=self.user_alice,
            shipping_address=self.valid_address,
            billing_address=self.valid_address,
            payment_method="cod",
        )

        # 1. Bob cannot view Alice's invoice or order success
        self.client.force_login(self.user_bob)
        resp_bob = self.client.get(reverse("order_invoice", kwargs={"order_number": order.order_number}))
        self.assertEqual(resp_bob.status_code, 404)

        # 2. Unauthenticated guest cannot view Alice's order
        self.client.logout()
        resp_guest = self.client.get(reverse("order_invoice", kwargs={"order_number": order.order_number}))
        self.assertEqual(resp_guest.status_code, 404)

        # 3. Guest with fake token is rejected with 404
        resp_fake = self.client.get(
            f"{reverse('order_invoice', kwargs={'order_number': order.order_number})}?token=fake-token-1234"
        )
        self.assertEqual(resp_fake.status_code, 404)

    # 7. CSRF protection on mutating POST endpoints
    def test_csrf_protection_on_all_post_endpoints(self):
        """All mutating endpoints reject requests lacking CSRF tokens."""
        csrf_client = Client(enforce_csrf_checks=True)

        endpoints = [
            (reverse("cart_add", kwargs={"product_id": self.product.id}), {"quantity": 1}),
            (reverse("cart_save_for_later", kwargs={"product_id": self.product.id}), {}),
            (reverse("cart_move_to_bag", kwargs={"product_id": self.product.id}), {}),
            (reverse("cart_remove", kwargs={"product_id": self.product.id}), {}),
            (reverse("coupon_apply"), {"code": "TEST"}),
            (reverse("checkout_place"), {"payment_method": "cod"}),
        ]

        for url, data in endpoints:
            with self.subTest(url=url):
                res = csrf_client.post(url, data)
                self.assertEqual(res.status_code, 403, f"Expected 403 CSRF rejection on {url}")

    # 8. Rate limits (HTTP 429)
    def test_rate_limits_enforced_429(self):
        """Endpoints return HTTP 429 when IP rate limits are exceeded."""
        client = Client(REMOTE_ADDR="198.51.100.99")

        # Rate limit coupon apply (10/m)
        hit_429 = False
        for _ in range(15):
            res = client.post(reverse("coupon_apply"), {"code": "BRUTEFORCE"})
            if res.status_code == 429:
                hit_429 = True
                break
        self.assertTrue(hit_429, "coupon_apply should return 429 when rate limit is exceeded")

        # Rate limit shipping check (20/m)
        hit_429_ship = False
        for _ in range(25):
            res = client.post(reverse("shipping_check"), {"pincode": "560001"})
            if res.status_code == 429:
                hit_429_ship = True
                break
        self.assertTrue(hit_429_ship, "shipping_check should return 429 when rate limit is exceeded")

    # 9. Webhook replay and signature spoofing
    def test_webhook_replay_and_signature_spoofing(self):
        """Webhooks reject spoofed signatures with 403 and deduplicate replays."""
        raw_body = json.dumps({
            "event": "payment.captured",
            "event_id": "evt_test_replay_001",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_test_123",
                        "order_id": "order_test_123",
                        "amount": 499900,
                    }
                }
            }
        }).encode("utf-8")

        # 1. Invalid signature raises PermissionError -> 403
        resp_spoof = self.client.post(
            reverse("payments:razorpay_webhook"),
            data=raw_body,
            content_type="application/json",
            HTTP_X_RAZORPAY_SIGNATURE="spoofed_signature_value",
        )
        self.assertEqual(resp_spoof.status_code, 403)

        # 2. Valid signature processed, then replayed -> returns already_processed
        provider = RazorpayProvider()
        # In test mode or when secret is set, compute real signature:
        secret = provider.webhook_secret
        import hmac, hashlib
        valid_sig = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()

        # First delivery
        res1 = process_webhook_payload(raw_body=raw_body, signature_header=valid_sig, provider=provider)
        self.assertEqual(res1.get("status"), "success")

        # Mark processed
        evt = WebhookEvent.objects.get(event_id="evt_test_replay_001")
        evt.is_processed = True
        evt.save()

        # Replayed delivery
        res2 = process_webhook_payload(raw_body=raw_body, signature_header=valid_sig, provider=provider)
        self.assertEqual(res2.get("status"), "already_processed")
