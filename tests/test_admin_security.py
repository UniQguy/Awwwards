"""
Tests for Django Admin access control, role permissions, and operational features.
"""

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import Client, TestCase
from django.urls import reverse

from apps.catalog.models import Category, Product
from apps.inventory.models import Inventory
from apps.orders.models import Order

User = get_user_model()


class AdminSecurityAndAccessTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Regular customer user (non-staff)
        self.customer = User.objects.create_user(
            email="customer@example.com",
            password="customerpassword123",
            full_name="Regular Customer",
            is_staff=False,
            is_superuser=False,
        )

        # Catalogue-only staff user
        self.catalog_staff = User.objects.create_user(
            email="catalogstaff@example.com",
            password="staffpassword123",
            full_name="Catalog Specialist",
            is_staff=True,
            is_superuser=False,
        )
        catalog_ct = ContentType.objects.get_for_model(Product)
        perms = Permission.objects.filter(
            content_type=catalog_ct,
            codename__in=["view_product", "change_product", "add_product"],
        )
        self.catalog_staff.user_permissions.set(perms)

        # Superuser
        self.admin = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpassword123",
            full_name="System Admin",
        )

        # Test Category and Product
        self.category = Category.objects.create(
            name="Audio Test",
            slug="audio-test",
            accent_key="amber",
            gst_rate=18,
            is_active=True,
        )
        self.product = Product.objects.create(
            sku="AUD-TST-001",
            display_name="Test Headphones",
            raw_name="Test Headphones Raw",
            category=self.category,
            selling_price=Decimal("4999.00"),
            mrp=Decimal("7999.00"),
            is_available=True,
        )
        self.inventory = Inventory.objects.create(
            product=self.product,
            quantity=3,
            low_stock_threshold=5,
            is_sample_data=False,
        )

        # Test Order
        self.order = Order.objects.create(
            order_number="ORD-TEST-9999",
            user=self.customer,
            status=Order.STATUS_CONFIRMED,
            payment_method=Order.PAYMENT_METHOD_RAZORPAY,
            payment_status=Order.PAYMENT_STATUS_CAPTURED,
            subtotal=Decimal("4999.00"),
            shipping_fee=Decimal("0.00"),
            discount_amount=Decimal("0.00"),
            tax_amount=Decimal("762.56"),
            total_amount=Decimal("4999.00"),
        )

    def test_anonymous_user_redirected_to_admin_login(self):
        resp = self.client.get("/admin/")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/admin/login/", resp.url)

    def test_non_staff_user_denied_admin_access(self):
        self.client.force_login(self.customer)
        resp = self.client.get("/admin/")
        # Django admin redirects non-staff users to login with ?next=/admin/
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/admin/login/", resp.url)

    def test_catalog_staff_can_view_product_admin(self):
        self.client.force_login(self.catalog_staff)
        resp = self.client.get("/admin/catalog/product/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Test Headphones")

    def test_catalog_staff_cannot_view_orders_admin(self):
        self.client.force_login(self.catalog_staff)
        resp = self.client.get("/admin/orders/order/")
        # Without order permissions, access is redirected or returns 403
        self.assertIn(resp.status_code, [302, 403])

    def test_catalog_staff_cannot_modify_order(self):
        self.client.force_login(self.catalog_staff)
        resp = self.client.post(
            f"/admin/orders/order/{self.order.pk}/change/",
            {"status": Order.STATUS_CANCELLED},
        )
        self.assertIn(resp.status_code, [302, 403])
        # Ensure order was not modified
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.STATUS_CONFIRMED)

    def test_order_financial_fields_readonly_on_existing_order(self):
        from apps.orders.admin import OrderAdmin
        from django.contrib.admin.sites import AdminSite

        site = AdminSite()
        order_admin = OrderAdmin(Order, site)
        readonly = order_admin.get_readonly_fields(None, obj=self.order)
        for field in ["subtotal", "shipping_fee", "discount_amount", "tax_amount", "total_amount"]:
            self.assertIn(field, readonly)

    def test_order_csv_export_action(self):
        from apps.orders.admin import OrderAdmin
        from django.contrib.admin.sites import AdminSite

        site = AdminSite()
        order_admin = OrderAdmin(Order, site)
        qs = Order.objects.filter(id=self.order.id)
        response = order_admin.export_orders_to_csv(None, qs)

        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn("attachment; filename=", response["Content-Disposition"])
        content = response.content.decode("utf-8")
        self.assertIn("Order Number", content)
        self.assertIn("ORD-TEST-9999", content)
        self.assertIn("4999.00", content)

    def test_admin_dashboard_metrics_render_for_superuser(self):
        self.client.force_login(self.admin)
        resp = self.client.get("/admin/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Store Operations Snapshot")
        self.assertContains(resp, "Orders Today")
        self.assertContains(resp, "Low Stock Alert")
        self.assertContains(resp, "Electrocart administration")
