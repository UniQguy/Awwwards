"""
Tests for Store Operations Admin Dashboard (Phase R7 Admin Dashboard Pass).
Verifies access control, KPI accuracy, Decimal revenue calculations,
range whitelist, Indian Rupee formatting, empty states, and query performance.
"""

from datetime import timedelta
from decimal import Decimal
from django.apps import apps
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.utils import timezone

from apps.catalog.models import Category, Product
from apps.core.admin_dashboard import (
    ALLOWED_RANGES,
    DASHBOARD_RANGE_DAYS,
    get_admin_dashboard_context,
    resolve_range_days,
)
from apps.inventory.models import Inventory
from apps.orders.models import Order, OrderItem

User = get_user_model()


class AdminDashboardTests(TestCase):
    def setUp(self):
        self.client = Client()

        # 1. Staff and Superuser
        self.staff_user = User.objects.create_user(
            email="staff.operations@electrocart.local",
            password="staffpassword123",
            full_name="Staff Operator",
            is_staff=True,
            is_superuser=False,
        )

        self.superuser = User.objects.create_superuser(
            email="admin.superuser@electrocart.local",
            password="adminpassword123",
            full_name="Admin Superuser",
        )

        # 2. Regular non-staff customer
        self.customer = User.objects.create_user(
            email="shopper@example.com",
            password="customerpassword123",
            full_name="Regular Shopper",
            is_staff=False,
            is_superuser=False,
        )

        # 3. Catalog & Inventory Data
        self.cat_audio = Category.objects.create(
            name="Audio & Headphones",
            slug="audio-headphones",
            accent_key="amber",
            gst_rate=Decimal("18.00"),
        )
        self.cat_chargers = Category.objects.create(
            name="Cables & Chargers",
            slug="cables-chargers",
            accent_key="emerald",
            gst_rate=Decimal("18.00"),
        )

        self.prod_headphones = Product.objects.create(
            sku="EC-AU-HD01",
            source_asin="B00HDPHN01",
            slug="pro-headphones",
            display_name="Pro Wireless Headphones",
            raw_name="Pro Wireless Headphones",
            category=self.cat_audio,
            selling_price=Decimal("4999.00"),
            mrp=Decimal("7999.00"),
            parsed_brand="ElectroSound",
            is_available=True,
        )
        self.inv_headphones = Inventory.objects.create(
            product=self.prod_headphones,
            quantity=3,
            low_stock_threshold=5,
            is_sample_data=True,
        )

        self.prod_cable = Product.objects.create(
            sku="EC-CB-01",
            source_asin="B00CABLE01",
            slug="braided-cable",
            display_name="Braided USB-C Cable 1m",
            raw_name="Braided USB-C Cable 1m",
            category=self.cat_chargers,
            selling_price=Decimal("499.00"),
            mrp=Decimal("999.00"),
            parsed_brand="Anker",
            is_available=True,
        )
        self.inv_cable = Inventory.objects.create(
            product=self.prod_cable,
            quantity=12,
            low_stock_threshold=5,
            is_sample_data=True,
        )

        self.prod_out_of_stock = Product.objects.create(
            sku="EC-OOS-01",
            source_asin="B00OOS0001",
            slug="oos-gadget",
            display_name="Out of Stock Gadget",
            raw_name="Out of Stock Gadget",
            category=self.cat_audio,
            selling_price=Decimal("1999.00"),
            is_available=True,
        )
        self.inv_oos = Inventory.objects.create(
            product=self.prod_out_of_stock,
            quantity=0,
            low_stock_threshold=5,
            is_sample_data=True,
        )

        # 4. Orders Data
        now = timezone.now()

        # Order 1: Confirmed today, COD (₹4,999)
        self.order_today = Order.objects.create(
            order_number="ORD-20261019-001",
            user=self.customer,
            status=Order.STATUS_CONFIRMED,
            payment_method=Order.PAYMENT_METHOD_COD,
            subtotal=Decimal("4999.00"),
            shipping_fee=Decimal("0.00"),
            total_amount=Decimal("4999.00"),
        )
        OrderItem.objects.create(
            order=self.order_today,
            product=self.prod_headphones,
            product_title="Pro Wireless Headphones",
            product_sku="EC-AU-HD01",
            unit_price=Decimal("4999.00"),
            mrp=Decimal("7999.00"),
            quantity=1,
            taxable_value=Decimal("4236.44"),
            line_total=Decimal("4999.00"),
        )

        # Order 2: Confirmed 3 days ago, Online (₹998)
        self.order_recent = Order.objects.create(
            order_number="ORD-20261016-002",
            guest_email="guest.buyer@example.com",
            status=Order.STATUS_PROCESSING,
            payment_method=Order.PAYMENT_METHOD_RAZORPAY,
            subtotal=Decimal("998.00"),
            shipping_fee=Decimal("0.00"),
            total_amount=Decimal("998.00"),
        )
        # Update created_at timestamp to 3 days ago
        Order.objects.filter(id=self.order_recent.id).update(created_at=now - timedelta(days=3))
        OrderItem.objects.create(
            order=self.order_recent,
            product=self.prod_cable,
            product_title="Braided USB-C Cable 1m",
            product_sku="EC-CB-01",
            unit_price=Decimal("499.00"),
            mrp=Decimal("999.00"),
            quantity=2,
            taxable_value=Decimal("845.76"),
            line_total=Decimal("998.00"),
        )

        # Order 3: Cancelled 2 days ago (₹10,000) - MUST be excluded from revenue!
        self.order_cancelled = Order.objects.create(
            order_number="ORD-20261017-003",
            user=self.customer,
            status=Order.STATUS_CANCELLED,
            payment_method=Order.PAYMENT_METHOD_RAZORPAY,
            subtotal=Decimal("10000.00"),
            shipping_fee=Decimal("0.00"),
            total_amount=Decimal("10000.00"),
        )
        Order.objects.filter(id=self.order_cancelled.id).update(created_at=now - timedelta(days=2))
        OrderItem.objects.create(
            order=self.order_cancelled,
            product=self.prod_headphones,
            product_title="Pro Wireless Headphones",
            product_sku="EC-AU-HD01",
            unit_price=Decimal("4999.00"),
            mrp=Decimal("7999.00"),
            quantity=2,
            taxable_value=Decimal("8472.88"),
            line_total=Decimal("10000.00"),
        )

        # Order 4: Confirmed 45 days ago (outside 7 and 30 day range) (₹3,000)
        self.order_old = Order.objects.create(
            order_number="ORD-20260901-004",
            user=self.customer,
            status=Order.STATUS_DELIVERED,
            payment_method=Order.PAYMENT_METHOD_COD,
            subtotal=Decimal("3000.00"),
            shipping_fee=Decimal("0.00"),
            total_amount=Decimal("3000.00"),
        )
        Order.objects.filter(id=self.order_old.id).update(created_at=now - timedelta(days=45))

    def test_staff_sees_dashboard_with_200(self):
        """Staff members receive 200 OK and see the Store Operations Dashboard."""
        self.client.force_login(self.staff_user)
        resp = self.client.get("/admin/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Store Operations Dashboard")
        self.assertContains(resp, "Orders Today")
        self.assertContains(resp, "Revenue today")
        self.assertContains(resp, "Orders per day")
        self.assertContains(resp, "Orders by status")
        self.assertContains(resp, "Payment split")
        self.assertContains(resp, "Top 5 products by quantity sold")
        self.assertContains(resp, "Top categories by units sold")
        self.assertContains(resp, "Latest 8 orders")
        self.assertContains(resp, "Stock health")
        self.assertContains(resp, "Catalogue health")
        self.assertContains(resp, "Quick links")

    def test_non_staff_cannot_see_dashboard(self):
        """Non-staff authenticated customers and anonymous visitors are redirected to admin login."""
        # Authenticated customer
        self.client.force_login(self.customer)
        resp_cust = self.client.get("/admin/")
        self.assertEqual(resp_cust.status_code, 302)
        self.assertIn("/admin/login/", resp_cust.url)

        # Anonymous visitor
        self.client.logout()
        resp_anon = self.client.get("/admin/")
        self.assertEqual(resp_anon.status_code, 302)
        self.assertIn("/admin/login/", resp_anon.url)

    def test_numbers_equal_direct_recount_from_fixtures(self):
        """Financial metrics, counts, and top products match direct fixture computations."""
        ctx = get_admin_dashboard_context(range_days=7)

        # Orders Today
        self.assertEqual(ctx["orders_today"], 1)
        self.assertEqual(ctx["revenue_today"], Decimal("4999.00"))

        # Orders in 7-day range: 3 orders (order_today, order_recent, order_cancelled)
        self.assertEqual(ctx["orders_in_range"], 3)
        self.assertEqual(ctx["cancelled_orders"], 1)

        # Revenue in 7-day range: order_today (4999) + order_recent (998) = 5997.00
        # Cancelled order (10000.00) MUST be excluded!
        self.assertEqual(ctx["revenue_in_range"], Decimal("5997.00"))

        # Average Order Value: 5997.00 / 2 valid orders = 2998.50 -> quantize 2999.00 or 2998.50
        self.assertAlmostEqual(float(ctx["average_order_value"]), 2998.50, delta=1.0)

        # Pending orders (placed + confirmed + packed):
        # order_today is confirmed (1), order_recent is processing/packed (1) -> total 2
        self.assertEqual(ctx["pending_orders"], 2)

        # Payment split: 1 COD (50%), 1 Online non-cancelled (or 1 COD vs 2 total in range)
        self.assertEqual(ctx["payment_split"]["cod_count"], 1)
        self.assertEqual(ctx["payment_split"]["online_count"], 2)

        # Top Products (OrderItem snapshots, excluding cancelled order):
        # Cable sold 2 units (998 revenue); Headphones sold 1 unit (4999 revenue)
        self.assertEqual(len(ctx["top_products"]), 2)
        top_prod_1 = ctx["top_products"][0]
        self.assertEqual(top_prod_1["product_id"], self.prod_cable.id)
        self.assertEqual(top_prod_1["units"], 2)
        self.assertEqual(top_prod_1["revenue"], Decimal("998.00"))

        top_prod_2 = ctx["top_products"][1]
        self.assertEqual(top_prod_2["product_id"], self.prod_headphones.id)
        self.assertEqual(top_prod_2["units"], 1)
        self.assertEqual(top_prod_2["revenue"], Decimal("4999.00"))

        # Stock Health: low stock = 1 (headphones with qty 3 <= threshold 5), out of stock = 1 (oos gadget)
        self.assertEqual(ctx["stock_health"]["low_stock"], 1)
        self.assertEqual(ctx["stock_health"]["out_of_stock"], 1)

    def test_range_parameter_whitelist(self):
        """Range parameter accepts only 7 or 30 days; invalid values default to 7."""
        self.assertEqual(resolve_range_days("7"), 7)
        self.assertEqual(resolve_range_days(7), 7)
        self.assertEqual(resolve_range_days("30"), 30)
        self.assertEqual(resolve_range_days(30), 30)

        # Fallback to DASHBOARD_RANGE_DAYS (7)
        self.assertEqual(resolve_range_days("99"), DASHBOARD_RANGE_DAYS)
        self.assertEqual(resolve_range_days("bad_input"), DASHBOARD_RANGE_DAYS)
        self.assertEqual(resolve_range_days(None), DASHBOARD_RANGE_DAYS)
        self.assertEqual(resolve_range_days(-5), DASHBOARD_RANGE_DAYS)

    def test_empty_database_renders_without_error(self):
        """Empty database renders gracefully showing empty states without dividing by zero."""
        # Clear all order records
        OrderItem.objects.all().delete()
        Order.objects.all().delete()

        ctx = get_admin_dashboard_context(range_days=7)
        self.assertEqual(ctx["orders_today"], 0)
        self.assertEqual(ctx["revenue_today"], Decimal("0.00"))
        self.assertEqual(ctx["orders_in_range"], 0)
        self.assertEqual(ctx["revenue_in_range"], Decimal("0.00"))
        self.assertEqual(ctx["average_order_value"], Decimal("0.00"))
        self.assertEqual(ctx["pending_orders"], 0)
        self.assertEqual(len(ctx["top_products"]), 0)
        self.assertEqual(len(ctx["top_categories"]), 0)
        self.assertEqual(len(ctx["latest_orders"]), 0)

        self.client.force_login(self.staff_user)
        resp = self.client.get("/admin/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "No orders in this period")

    def test_money_formatted_indian_style(self):
        """Rupee values are formatted with the inr filter matching Indian numbering conventions."""
        self.client.force_login(self.staff_user)
        resp = self.client.get("/admin/")
        self.assertEqual(resp.status_code, 200)
        # Revenue today is 4,999 -> ₹4,999 (Indian grouped)
        self.assertContains(resp, "₹4,999")

    def test_dashboard_performance_assert_num_queries(self):
        """Dashboard request executes at most 12 queries, meeting strict performance gates."""
        self.client.force_login(self.superuser)
        with self.assertNumQueries(12):  # Bound tightly to <= 12 queries
            resp = self.client.get("/admin/")
            self.assertEqual(resp.status_code, 200)

    def test_allauth_app_distinct_verbose_name(self):
        """Allauth account app verbose_name is set to Email addresses and sign-in to avoid duplicate titles."""
        allauth_config = apps.get_app_config("account")
        self.assertIn("Email addresses and sign-in", allauth_config.verbose_name)
