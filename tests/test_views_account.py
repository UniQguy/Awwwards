"""
Customer account management view tests.
Tests dashboard, order history, address CRUD with default management, and profile editing.
"""

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Address
from apps.orders.models import Order
from apps.shipping.models import PincodeServiceability

User = get_user_model()


class AccountViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="member@electrocart.local",
            password="testpassword123",
            full_name="Meera Sen",
        )
        self.client.force_login(self.user)

        PincodeServiceability.objects.create(
            pincode="560001",
            state="Gujarat",
            is_serviceable=True,
            cod_allowed=True,
        )

        self.address = Address.objects.create(
            user=self.user,
            full_name="Meera Sen",
            phone="9876543210",
            line1="45 M.G. Road",
            city="Ahmedabad",
            state="Gujarat",
            pincode="560001",
            is_default=True,
        )

    def test_account_dashboard_authenticated(self):
        resp = self.client.get(reverse("account_dashboard"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Meera Sen")
        self.assertContains(resp, "45 M.G. Road")

    def test_account_order_list(self):
        Order.objects.create(
            order_number="EC-20261006-ACCT1",
            user=self.user,
            status=Order.STATUS_CONFIRMED,
            payment_method="cod",
            payment_status="pending",
            subtotal=Decimal("1200.00"),
            total_amount=Decimal("1200.00"),
        )
        resp = self.client.get(reverse("account_order_list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "EC-20261006-ACCT1")

    def test_account_address_crud_and_default(self):
        # 1. Address List
        resp_list = self.client.get(reverse("account_address_list"))
        self.assertEqual(resp_list.status_code, 200)
        self.assertContains(resp_list, "45 M.G. Road")
        self.assertContains(resp_list, "Default")

        # 2. Create second address
        create_data = {
            "full_name": "Meera Sen Office",
            "phone": "9876543210",
            "line1": "Level 6, Tech Park",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "pincode": "560001",
            "is_default": "0",
        }
        self.client.post(reverse("account_address_create"), create_data, follow=True)
        self.assertEqual(self.user.addresses.count(), 2)

        new_addr = self.user.addresses.get(full_name="Meera Sen Office")

        # 3. Set second address as default
        self.client.post(reverse("account_address_set_default", kwargs={"uuid": new_addr.uuid}), follow=True)
        new_addr.refresh_from_db()
        self.address.refresh_from_db()
        self.assertTrue(new_addr.is_default)
        self.assertFalse(self.address.is_default)

        # 4. Delete address
        self.client.post(reverse("account_address_delete", kwargs={"uuid": self.address.uuid}), follow=True)
        self.assertEqual(self.user.addresses.count(), 1)

    def test_account_profile_update(self):
        resp = self.client.post(reverse("account_profile"), {
            "full_name": "Meera Sen Gupta",
        }, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, "Meera Sen Gupta")
