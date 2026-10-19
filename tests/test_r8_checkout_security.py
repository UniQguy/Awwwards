"""
Tests for Phase R8 Task 2: Guest COD Verification Gate (OTP),
Tiered COD Limits, Velocity Guard, and Payment Sandbox Fallback.
"""

from decimal import Decimal
import json
import secrets
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import Client, TestCase
from django.utils import timezone

from apps.accounts.models import Address
from apps.cart.models import Cart, CartItem
from apps.catalog.models import Category, Product
from apps.orders.models import Order
from apps.payments.providers import RazorpayProvider

User = get_user_model()


class CheckoutSecurityAndSandboxTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(
            name="Cables, Chargers & Power",
            slug="cables-chargers-powerbanks",
            display_order=1,
            is_active=True,
        )
        self.affordable_product = Product.objects.create(
            raw_name="Premium USB Cable",
            display_name="Premium USB Cable",
            slug="cable-test-001",
            sku="CABLE-TEST-001",
            source_asin="B00TESTCABLE",
            category=self.category,
            selling_price=Decimal("499.00"),
            mrp=Decimal("999.00"),
            is_available=True,
        )
        self.expensive_product = Product.objects.create(
            raw_name="Flagship Laptop Station",
            display_name="Flagship Laptop Station",
            slug="laptop-test-001",
            sku="LAPTOP-TEST-001",
            source_asin="B00TESTLAPTOP",
            category=self.category,
            selling_price=Decimal("18000.00"),
            mrp=Decimal("24000.00"),
            is_available=True,
        )
        self.ultra_product = Product.objects.create(
            raw_name="Ultra Workstation Pro",
            display_name="Ultra Workstation Pro",
            slug="ultra-test-001",
            sku="ULTRA-TEST-001",
            source_asin="B00TESTULTRA",
            category=self.category,
            selling_price=Decimal("40000.00"),
            mrp=Decimal("50000.00"),
            is_available=True,
        )

        from apps.inventory.models import Inventory
        from apps.shipping.models import PincodeServiceability

        Inventory.objects.create(product=self.affordable_product, quantity=50)
        Inventory.objects.create(product=self.expensive_product, quantity=50)
        Inventory.objects.create(product=self.ultra_product, quantity=50)

        PincodeServiceability.objects.create(
            pincode="380009",
            state="Gujarat",
            is_serviceable=True,
            cod_allowed=True,
            est_days_min=1,
            est_days_max=2,
        )

    def _setup_guest_checkout(self, product, quantity=1):
        # 1. Add to cart
        self.client.post(f"/cart/add/{product.id}/", {"quantity": quantity})
        # 2. Guest signup step
        self.client.post("/checkout/guest/", {
            "full_name": "Arjun Sharma",
            "email": "arjun.guest@example.com",
            "phone": "9876543210",
        })
        # 3. Address step
        self.client.post("/checkout/address/", {
            "full_name": "Arjun Sharma",
            "phone": "9876543210",
            "line1": "404 CG Road",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "pincode": "380009",
        })

    def test_guest_cod_otp_flow(self):
        self._setup_guest_checkout(self.affordable_product, quantity=1)

        # First checkout_place attempt without OTP triggers OTP dispatch and renders OTP template
        resp1 = self.client.post("/checkout/place/", {"payment_method": "cod", "notes": ""})
        self.assertEqual(resp1.status_code, 200)
        self.assertContains(resp1, "Verify Cash on Delivery")
        self.assertContains(resp1, "View OTP in Local Outbox")

        # OTP should be stored in session
        session = self.client.session
        otp = session.get("guest_cod_otp")
        self.assertTrue(otp)
        self.assertEqual(len(otp), 6)

        # Invalid OTP submission fails
        resp_invalid = self.client.post("/checkout/place/", {
            "payment_method": "cod",
            "guest_cod_otp": "000000",
            "notes": "",
        })
        self.assertEqual(resp_invalid.status_code, 200)
        self.assertContains(resp_invalid, "Invalid or expired verification code")

        # Valid OTP submission succeeds and places order
        resp_valid = self.client.post("/checkout/place/", {
            "payment_method": "cod",
            "guest_cod_otp": otp,
            "notes": "",
        })
        self.assertEqual(resp_valid.status_code, 302)
        self.assertIn("/orders/EC-", resp_valid.url)
        self.assertIn("/success/", resp_valid.url)

        order = Order.objects.filter(guest_email="arjun.guest@example.com").first()
        self.assertIsNotNone(order)
        self.assertEqual(order.payment_method, "cod")
        self.assertEqual(order.status, Order.STATUS_CONFIRMED)

    def test_tiered_cod_limit_for_guest(self):
        # Product is ₹18,000 (> ₹15,000 cap for guests)
        self._setup_guest_checkout(self.expensive_product, quantity=1)

        # Review page shows COD disabled with clear explanation
        resp = self.client.get("/checkout/review/")
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.context["can_cod"])
        self.assertIn("Orders above ₹15,000 require Online Payment", resp.context["cod_disabled_reason"])

        # Attempting to place COD anyway is blocked
        resp_place = self.client.post("/checkout/place/", {"payment_method": "cod"})
        self.assertEqual(resp_place.status_code, 302)
        self.assertEqual(resp_place.url, "/checkout/review/")

    def test_tiered_cod_limit_for_authenticated_user(self):
        user = User.objects.create_user(
            email="member@electrocart.local",
            password="MemberPass123",
        )
        self.client.force_login(user)

        # Authenticated user with ₹18,000 (< ₹35,000 limit) CAN use COD
        self.client.post(f"/cart/add/{self.expensive_product.id}/", {"quantity": 1})
        self.client.post("/checkout/address/", {
            "full_name": "Member User",
            "phone": "9876543211",
            "line1": "101 Ashram Road",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "pincode": "380009",
        })
        resp = self.client.get("/checkout/review/")
        self.assertTrue(resp.context["can_cod"])

        # But above ₹35,000 (e.g. ₹40,000), COD is disabled
        self.client.post(f"/cart/add/{self.ultra_product.id}/", {"quantity": 1})
        resp2 = self.client.get("/checkout/review/")
        self.assertFalse(resp2.context["can_cod"])
        self.assertIn("Orders above ₹35,000 require Online Payment", resp2.context["cod_disabled_reason"])

    def test_velocity_guard_blocks_more_than_two_cod_orders_in_24h(self):
        self._setup_guest_checkout(self.affordable_product, quantity=1)

        # Place order 1
        self.client.post("/checkout/place/", {"payment_method": "cod"})
        otp1 = self.client.session.get("guest_cod_otp")
        self.client.post("/checkout/place/", {"payment_method": "cod", "guest_cod_otp": otp1})

        # Place order 2
        self._setup_guest_checkout(self.affordable_product, quantity=1)
        self.client.post("/checkout/place/", {"payment_method": "cod"})
        otp2 = self.client.session.get("guest_cod_otp")
        self.client.post("/checkout/place/", {"payment_method": "cod", "guest_cod_otp": otp2})

        self.assertEqual(Order.objects.filter(guest_email="arjun.guest@example.com").count(), 2)

        # Place order 3: should be blocked by velocity guard
        self._setup_guest_checkout(self.affordable_product, quantity=1)
        resp_review = self.client.get("/checkout/review/")
        self.assertFalse(resp_review.context["can_cod"])
        self.assertIn("Maximum 2 active Cash on Delivery orders allowed", resp_review.context["cod_disabled_reason"])

    def test_payment_sandbox_verification_captures_online_order(self):
        self._setup_guest_checkout(self.affordable_product, quantity=1)

        # Select online razorpay payment
        resp_place = self.client.post("/checkout/place/", {"payment_method": "razorpay"})
        self.assertEqual(resp_place.status_code, 302)
        self.assertIn("/payments/razorpay/checkout/", resp_place.url)

        order = Order.objects.filter(guest_email="arjun.guest@example.com").first()
        self.assertIsNotNone(order)
        self.assertEqual(order.status, Order.STATUS_PENDING)
        self.assertEqual(order.payment_status, Order.PAYMENT_STATUS_PENDING)

        # Checkout page displays the sandbox interface
        resp_page = self.client.get(resp_place.url)
        self.assertEqual(resp_page.status_code, 200)
        self.assertContains(resp_page, "ElectroCart Secure Payment Sandbox (UPI / Card / NetBanking)")

        # Simulate sandbox verification callback with valid HMAC signature
        sandbox_order_id = resp_page.context["sandbox_order_id"]
        sandbox_payment_id = resp_page.context["sandbox_payment_id"]
        sandbox_signature = resp_page.context["sandbox_signature"]

        resp_verify = self.client.post("/payments/razorpay/verify/", {
            "order_number": order.order_number,
            "razorpay_order_id": sandbox_order_id,
            "razorpay_payment_id": sandbox_payment_id,
            "razorpay_signature": sandbox_signature,
        })
        self.assertEqual(resp_verify.status_code, 302)
        self.assertIn("/success/", resp_verify.url)

        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_CONFIRMED)
        self.assertEqual(order.payment_status, Order.PAYMENT_STATUS_CAPTURED)
        self.assertEqual(order.payment_method, "razorpay")
