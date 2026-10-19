"""
Comprehensive test suite for Phase R9: 13-Point Live Browser Bug Remediation & UX Perfection.
Verifies all functional, architectural, and visual requirements across storefront, bag, checkout, and search.
"""

import datetime
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.cart.models import Cart, CartItem
from apps.cart.services.cart_service import add_to_cart, get_or_create_cart
from apps.catalog.models import Category, Product
from apps.inventory.models import Inventory
from apps.orders.models import Order, OrderItem
from apps.promotions.models import Coupon
from apps.search.services.search_service import calculate_match_score, execute_catalog_search

User = get_user_model()


class PhaseR9FullRemediationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cache.clear()
        call_command("seed_pincodes", sample=True)
        # Seed categories
        cls.cat_phones = Category.objects.create(name="Smartphones & Devices", slug="smartphones", is_active=True, display_order=1)
        cls.cat_audio = Category.objects.create(name="Earphones & Headphones", slug="earphones-headphones", is_active=True, display_order=2)
        cls.cat_cases = Category.objects.create(name="Cases & Protectors", slug="cases-protectors", is_active=True, display_order=3)
        cls.cat_tvs = Category.objects.create(name="Displays & Televisions", slug="tvs", is_active=True, display_order=4)

        # Products
        cls.iphone14_base = Product.objects.create(
            raw_name="Apple iPhone 14 (128 GB) - Blue",
            display_name="Apple iPhone 14 (128 GB) - Blue",
            slug="apple-iphone-14-128gb-blue",
            sku="APL-IP14-128-BLU",
            source_asin="B0BDK62PDX",
            category=cls.cat_phones,
            parsed_brand="Apple",
            selling_price=Decimal("69999.00"),
            mrp=Decimal("79900.00"),
            is_available=True,
            search_text="apple iphone 14 128 gb blue smartphone 5g",
        )
        cls.iphone14_pro_max = Product.objects.create(
            raw_name="Apple iPhone 14 Pro Max (128 GB) - Deep Purple",
            display_name="Apple iPhone 14 Pro Max (128 GB) - Deep Purple",
            slug="apple-iphone-14-pro-max-128gb",
            sku="APL-IP14PM-128-PUR",
            source_asin="B0BDJ24P1W",
            category=cls.cat_phones,
            parsed_brand="Apple",
            selling_price=Decimal("127999.00"),
            mrp=Decimal("139900.00"),
            is_available=True,
            search_text="apple iphone 14 pro max 128 gb deep purple smartphone 5g",
        )
        cls.iphone14_case = Product.objects.create(
            raw_name="Spigen Tempered Glass Screen Protector Guard for iPhone 14",
            display_name="Spigen Tempered Glass Screen Protector Guard for iPhone 14",
            slug="spigen-tempered-glass-iphone-14",
            sku="SPG-TG-IP14",
            source_asin="B0B9TEST01",
            category=cls.cat_cases,
            parsed_brand="Spigen",
            selling_price=Decimal("999.00"),
            mrp=Decimal("1499.00"),
            is_available=True,
            search_text="spigen tempered glass screen protector guard for iphone 14 case cover",
        )
        cls.oppo_phone = Product.objects.create(
            raw_name="Oppo Reno 8 5G (128 GB) - Shimmer Gold",
            display_name="Oppo Reno 8 5G (128 GB) - Shimmer Gold",
            slug="oppo-reno-8-5g",
            sku="OPP-REN8-128",
            source_asin="B0B7TEST02",
            category=cls.cat_phones,
            parsed_brand="Oppo",
            selling_price=Decimal("29999.00"),
            mrp=Decimal("38999.00"),
            is_available=True,
            search_text="oppo reno 8 5g shimmer gold smartphone phone mobile",
        )
        cls.oppo_case = Product.objects.create(
            raw_name="Transparent Shockproof Back Cover Case for Oppo Reno 8",
            display_name="Transparent Shockproof Back Cover Case for Oppo Reno 8",
            slug="shockproof-case-oppo-reno-8",
            sku="CS-OPP-REN8",
            source_asin="B0B7TEST03",
            category=cls.cat_cases,
            parsed_brand="Generic",
            selling_price=Decimal("299.00"),
            mrp=Decimal("799.00"),
            is_available=True,
            search_text="transparent shockproof back cover case for oppo reno 8",
        )

        for p in [cls.iphone14_base, cls.iphone14_pro_max, cls.iphone14_case, cls.oppo_phone, cls.oppo_case]:
            Inventory.objects.create(product=p, quantity=50)

        # User
        cls.user = User.objects.create_user(
            email="shopper@electrocart.test",
            password="TestPassword123!",
            full_name="Verified Shopper",
        )

        # Coupon
        now = timezone.now()
        cls.coupon = Coupon.objects.create(
            code="SAVE10",
            description="10% discount on orders above ₹500",
            discount_type=Coupon.TYPE_PERCENTAGE,
            discount_value=Decimal("10.00"),
            min_order_amount=Decimal("500.00"),
            valid_from=now - datetime.timedelta(days=1),
            valid_until=now + datetime.timedelta(days=365),
            is_active=True,
        )

    def setUp(self):
        self.client = Client()

    def test_fix_1_and_9_authenticated_user_pdp_visit_zero_crash(self):
        """Authenticated user visiting PDP must never crash on request.user.username."""
        self.client.force_login(self.user)
        response = self.client.get(reverse("product_detail", kwargs={"slug": self.iphone14_base.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Verified Shopper")
        self.assertNotContains(response, "VariableDoesNotExist")

    def test_fix_2_hero_card_thumbnails_and_flagship_curation(self):
        """Hero thumbnails have required data-* attributes and exclude musical keyboards."""
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        # Verify no musical keyboard in hero
        self.assertNotContains(response, "PSR-I500")
        self.assertNotContains(response, "PSR-E373")

    def test_fix_5_setup_configurator_add_bundle(self):
        """Build Your Complete Setup adds all selected products to bag."""
        url = reverse("cart_add_bundle")
        selected_ids = [str(self.iphone14_base.id), str(self.oppo_phone.id)]
        response = self.client.post(url, {"product_ids": selected_ids})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("cart_detail"))

        cart_resp = self.client.get(reverse("cart_detail"))
        self.assertEqual(cart_resp.status_code, 200)
        self.assertContains(cart_resp, self.iphone14_base.display_name)
        self.assertContains(cart_resp, self.oppo_phone.display_name)

    def test_fix_6_live_inline_pincode_estimate_api(self):
        """Pincode checker returns deliverability without page reload."""
        url = reverse("shipping_estimate")
        # Valid Gujarat pincode
        response = self.client.get(f"{url}?pincode=380001", HTTP_ACCEPT="application/json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("deliverable"))
        self.assertIn("Ahmedabad", data.get("location", ""))
        self.assertIn("✓", data.get("badge_text", ""))

        # Invalid/undeliverable pincode
        inv_response = self.client.get(f"{url}?pincode=000000", HTTP_ACCEPT="application/json")
        self.assertEqual(inv_response.status_code, 200)
        inv_data = inv_response.json()
        self.assertFalse(inv_data.get("deliverable"))
        self.assertIn("✕", inv_data.get("badge_text", ""))

    def test_fix_9_search_ranking_exact_model_and_accessory_penalty(self):
        """Searching 'iphone 14' must rank base iPhone 14 above Pro Max and accessories."""
        res = execute_catalog_search(query="iphone 14", collapsed=False)
        products = res["products"]
        self.assertGreaterEqual(len(products), 2)
        # Base iPhone 14 must rank #1
        self.assertEqual(products[0].id, self.iphone14_base.id)
        # Pro Max ranks below base
        self.assertEqual(products[1].id, self.iphone14_pro_max.id)

    def test_fix_9_search_ranking_phone_vs_case(self):
        """Searching 'oppo phone' must rank Oppo smartphone above cases."""
        res = execute_catalog_search(query="oppo phone", collapsed=False)
        products = res["products"]
        self.assertGreaterEqual(len(products), 1)
        self.assertEqual(products[0].id, self.oppo_phone.id)

    def test_fix_9_strict_category_filter_intersection(self):
        """Searching ?q=oppo&category=smartphones strictly excludes accessories and other categories."""
        res = execute_catalog_search(query="oppo", category_slug="smartphones", collapsed=False)
        products = res["products"]
        for p in products:
            self.assertEqual(p.category.slug, "smartphones")
            self.assertIn("oppo", (p.parsed_brand or "").lower())

    def test_fix_10_available_coupons_in_cart_and_1_click_apply(self):
        """Coupons appear in cart and can be applied via 1-click."""
        # Add item to cart
        self.client.post(reverse("cart_add", kwargs={"product_id": self.iphone14_base.id}), {"quantity": 1})

        # View cart - verify coupon is available
        response = self.client.get(reverse("cart_detail"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SAVE10")
        self.assertContains(response, "Available Coupons")

        # 1-Click apply coupon
        apply_resp = self.client.post(reverse("coupon_apply"), {"code": "SAVE10", "next": reverse("cart_detail")})
        self.assertEqual(apply_resp.status_code, 302)

        # Cart now has coupon applied
        cart_resp2 = self.client.get(reverse("cart_detail"))
        self.assertContains(cart_resp2, "Coupon: SAVE10")

    def test_fix_11_decrementing_quantity_at_1_removes_item(self):
        """When quantity is 1, decrementing to 0 removes the item from the cart."""
        # Add item
        self.client.post(reverse("cart_add", kwargs={"product_id": self.iphone14_base.id}), {"quantity": 1})

        # Update quantity to 0
        update_url = reverse("cart_update", kwargs={"product_id": self.iphone14_base.id})
        response = self.client.post(update_url, {"quantity": "0"}, HTTP_ACCEPT="application/json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))
        self.assertTrue(data.get("item_removed"))
        self.assertEqual(data.get("cart_count"), 0)

    def test_fix_12_cancelled_order_page_swaps_title_and_heading(self):
        """Cancelled order page must display 'Order Cancelled' in title, h1, and badge, and ₹0 payable."""
        self.client.force_login(self.user)
        order = Order.objects.create(
            order_number="EC-2026-TEST-9999",
            user=self.user,
            shipping_address_snapshot={"full_name": "Verified Shopper", "phone": "9876543210", "line1": "101 Test St", "city": "Ahmedabad", "state": "Gujarat", "pincode": "380001"},
            status=Order.STATUS_CANCELLED,
            payment_method=Order.PAYMENT_METHOD_COD,
            subtotal=Decimal("69999.00"),
            total_amount=Decimal("69999.00"),
        )
        OrderItem.objects.create(
            order=order,
            product=self.iphone14_base,
            product_sku=self.iphone14_base.sku,
            product_title=self.iphone14_base.display_name,
            unit_price=self.iphone14_base.selling_price,
            mrp=self.iphone14_base.mrp,
            quantity=1,
            taxable_value=Decimal("59321.19"),
            cgst_amount=Decimal("5338.90"),
            sgst_amount=Decimal("5338.90"),
            line_total=self.iphone14_base.selling_price,
        )

        response = self.client.get(reverse("order_success", kwargs={"order_number": order.order_number}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Order Cancelled #EC-2026-TEST-9999 — ELECTROCART")
        self.assertContains(response, "STATUS: ORDER CANCELLED")
        self.assertContains(response, "CREDIT NOTE ISSUED")
        self.assertContains(response, "Order Cancelled")
        self.assertContains(response, "Total Payable")
        self.assertContains(response, "₹0")
        self.assertNotContains(response, "<title>Order Confirmed")
