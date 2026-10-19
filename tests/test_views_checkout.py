"""
Checkout workflow view tests.
Tests guest checkout start, address validation with PIN serviceability, review, and order placement.
"""

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import Category, Product
from apps.inventory.models import Inventory
from apps.orders.models import Order
from apps.shipping.models import PincodeServiceability

User = get_user_model()


class CheckoutViewsTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Audio",
            slug="audio",
            accent_key="earphones-headphones",
            gst_rate=Decimal("18.00"),
        )
        self.product = Product.objects.create(
            category=self.category,
            sku="SKU-CHK-001",
            slug="studio-monitors",
            raw_name="Studio Nearfield Monitors Pair",
            display_name="Studio Monitors Pair",
            selling_price=Decimal("15000.00"),
            mrp=Decimal("18000.00"),
            is_available=True,
        )
        self.inventory = Inventory.objects.create(product=self.product, quantity=5)

        # Serviceable PIN code
        PincodeServiceability.objects.create(
            pincode="560001",
            state="Gujarat",
            is_serviceable=True,
            est_days_min=2,
            est_days_max=3,
            cod_allowed=True,
        )

        # Unserviceable PIN code
        PincodeServiceability.objects.create(
            pincode="999999",
            state="Remote",
            is_serviceable=False,
            cod_allowed=False,
        )

    def test_checkout_start_guest_and_authenticated(self):
        # Add item to cart
        self.client.post(reverse("cart_add", kwargs={"product_id": self.product.id}), {"quantity": 1})

        # Anonymous user sees guest start page
        resp_anon = self.client.get(reverse("checkout_start"))
        self.assertEqual(resp_anon.status_code, 200)
        self.assertContains(resp_anon, "Guest Checkout")
        self.assertContains(resp_anon, "Existing Member")

        # Authenticated user is redirected directly to address
        user = User.objects.create_user(email="buyer@electrocart.local", password="testpassword123")
        self.client.force_login(user)
        resp_auth = self.client.get(reverse("checkout_start"))
        self.assertRedirects(resp_auth, reverse("checkout_address"))

    def test_checkout_guest_contact_submission(self):
        self.client.post(reverse("cart_add", kwargs={"product_id": self.product.id}), {"quantity": 1})

        post_data = {
            "full_name": "Arun Kumar",
            "email": "arun@example.com",
            "phone": "9876543210",
        }
        resp = self.client.post(reverse("checkout_guest"), post_data)
        self.assertRedirects(resp, reverse("checkout_address"))

        session = self.client.session
        self.assertEqual(session["checkout_guest"]["email"], "arun@example.com")
        self.assertEqual(session["checkout_guest"]["phone"], "9876543210")

    def test_checkout_address_unserviceable_pincode_rejected(self):
        self.client.post(reverse("cart_add", kwargs={"product_id": self.product.id}), {"quantity": 1})
        self.client.post(reverse("checkout_guest"), {
            "full_name": "Arun Kumar",
            "email": "arun@example.com",
            "phone": "9876543210",
        })

        invalid_addr_data = {
            "full_name": "Arun Kumar",
            "phone": "9876543210",
            "line1": "Flat 402, Highrise",
            "city": "Remote City",
            "state": "Gujarat",
            "pincode": "999999",  # unserviceable
        }
        resp = self.client.post(reverse("checkout_address"), invalid_addr_data)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Delivery to this PIN code is currently suspended")

    def test_checkout_full_placement_flow_cod(self):
        # 1. Add item to cart
        self.client.post(reverse("cart_add", kwargs={"product_id": self.product.id}), {"quantity": 1})

        # 2. Guest details
        self.client.post(reverse("checkout_guest"), {
            "full_name": "Deepa Rao",
            "email": "deepa@example.com",
            "phone": "9845098450",
        })

        # 3. Valid address
        valid_addr_data = {
            "full_name": "Deepa Rao",
            "phone": "9845098450",
            "line1": "12 Residency Road",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "pincode": "560001",
        }
        resp_addr = self.client.post(reverse("checkout_address"), valid_addr_data)
        self.assertRedirects(resp_addr, reverse("checkout_review"))

        # 4. Review page
        resp_review = self.client.get(reverse("checkout_review"))
        self.assertEqual(resp_review.status_code, 200)
        self.assertContains(resp_review, "Cash on Delivery (COD)")
        self.assertContains(resp_review, "Online Payment (Razorpay)")
        self.assertContains(resp_review, "Stock Hold Active")

        # 5. Place order COD
        resp_place = self.client.post(reverse("checkout_place"), {"payment_method": "cod"})
        self.assertEqual(resp_place.status_code, 302)

        # Confirm Order created
        order = Order.objects.filter(guest_email="deepa@example.com").first()
        self.assertIsNotNone(order)
        self.assertEqual(order.payment_method, "cod")
        self.assertEqual(order.status, Order.STATUS_CONFIRMED)
        self.assertEqual(order.total_amount, Decimal("15000.00"))

        # Cart must be cleared
        resp_cart = self.client.get(reverse("cart_detail"))
        self.assertContains(resp_cart, "Your Shopping Cart is Empty")

    def test_guest_checkout_flow_with_strict_csrf_enforcement(self):
        """
        Regression test for F-01: Verifies guest checkout end-to-end under strict CSRF enforcement.
        Follows the exact shopper click path with cookies and CSRF tokens.
        """
        from django.test import Client
        csrf_client = Client(enforce_csrf_checks=True)

        # 1. Add product to cart
        resp_prod = csrf_client.get(f"/p/{self.product.slug}/")
        csrf_token = csrf_client.cookies["csrftoken"].value
        resp_add = csrf_client.post(
            f"/cart/add/{self.product.id}/",
            {"quantity": 1, "csrfmiddlewaretoken": csrf_token},
            HTTP_REFERER=f"http://testserver/p/{self.product.slug}/",
            follow=True,
        )
        self.assertEqual(resp_add.status_code, 200)

        # 2. View cart and proceed to checkout
        resp_cart = csrf_client.get("/cart/")
        self.assertEqual(resp_cart.status_code, 200)

        resp_chk = csrf_client.get("/checkout/")
        self.assertEqual(resp_chk.status_code, 200)
        self.assertContains(resp_chk, "Guest Checkout")
        csrf_token = csrf_client.cookies["csrftoken"].value

        # 3. Submit guest form - MUST NOT return 403 Forbidden
        guest_data = {
            "full_name": "Arun Kumar",
            "email": "arun.guest@example.com",
            "phone": "9876543210",
            "csrfmiddlewaretoken": csrf_token,
        }
        resp_guest = csrf_client.post(
            "/checkout/guest/",
            guest_data,
            HTTP_REFERER="http://testserver/checkout/",
            follow=True,
        )
        self.assertEqual(resp_guest.status_code, 200)
        self.assertTemplateUsed(resp_guest, "orders/checkout_address.html")

        # 4. Submit address form
        csrf_token = csrf_client.cookies["csrftoken"].value
        addr_data = {
            "full_name": "Arun Kumar",
            "phone": "9876543210",
            "line1": "Flat 101, Palm Avenue",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "pincode": "560001",
            "csrfmiddlewaretoken": csrf_token,
        }
        resp_addr = csrf_client.post(
            "/checkout/address/",
            addr_data,
            HTTP_REFERER="http://testserver/checkout/address/",
            follow=True,
        )
        self.assertEqual(resp_addr.status_code, 200)
        self.assertTemplateUsed(resp_addr, "orders/checkout_review.html")

        # 5. Place order COD
        csrf_token = csrf_client.cookies["csrftoken"].value
        resp_place = csrf_client.post(
            "/checkout/place/",
            {"payment_method": "cod", "csrfmiddlewaretoken": csrf_token},
            HTTP_REFERER="http://testserver/checkout/review/",
            follow=True,
        )
        self.assertEqual(resp_place.status_code, 200)
        self.assertTemplateUsed(resp_place, "orders/order_success.html")
        order = Order.objects.filter(guest_email="arun.guest@example.com").first()
        self.assertIsNotNone(order)
        self.assertEqual(order.status, Order.STATUS_CONFIRMED)

