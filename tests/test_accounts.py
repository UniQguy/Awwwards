"""
Tests for apps.accounts: User, UserManager, and Address models.
Covers email-only auth, case-insensitive normalization, superuser validation,
Indian GST address rules, PIN/phone validators, and single-default constraint.
"""

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.accounts.models import Address, IndianState

User = get_user_model()


class UserModelTests(TestCase):
    """Test suite for the custom email-only User model and UserManager."""

    def test_create_user_successful(self):
        """User is created with lowercase email and correctly hashed password."""
        user = User.objects.create_user(
            email="Arjun.Sharma@Example.COM",
            password="StrongPassword123!",
            full_name="Arjun Sharma",
        )
        self.assertEqual(user.email, "arjun.sharma@example.com")
        self.assertTrue(user.check_password("StrongPassword123!"))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_active)
        self.assertIsNotNone(user.uuid)
        self.assertIsNotNone(user.created_at)
        self.assertIsNotNone(user.updated_at)
        self.assertEqual(str(user), "arjun.sharma@example.com")
        self.assertEqual(user.get_full_name(), "Arjun Sharma")
        self.assertEqual(user.get_short_name(), "Arjun")

    def test_create_user_without_email_raises_error(self):
        """Creating a user without an email address raises ValueError."""
        with self.assertRaisesMessage(ValueError, "An email address must be provided."):
            User.objects.create_user(email="", password="password123")

    def test_create_superuser_successful(self):
        """Superuser is created with is_staff=True and is_superuser=True."""
        admin = User.objects.create_superuser(
            email="admin@electrocart.in",
            password="AdminPassword123!",
        )
        self.assertEqual(admin.email, "admin@electrocart.in")
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_active)

    def test_create_superuser_invalid_flags_raises_error(self):
        """Attempting to create superuser with false permissions raises ValueError."""
        with self.assertRaisesMessage(ValueError, "Superuser must have is_staff=True."):
            User.objects.create_superuser(
                email="badadmin1@electrocart.in",
                password="password123",
                is_staff=False,
            )

        with self.assertRaisesMessage(ValueError, "Superuser must have is_superuser=True."):
            User.objects.create_superuser(
                email="badadmin2@electrocart.in",
                password="password123",
                is_superuser=False,
            )

    def test_case_insensitive_email_uniqueness(self):
        """Duplicate emails differing only in casing are rejected by database constraint."""
        User.objects.create_user(email="buyer@electrocart.in", password="password123")

        # Database unique constraint on lower(email) or manager lookup
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                # Direct raw save attempting duplicate lower email
                u2 = User(email="BUYER@ELECTROCART.IN")
                u2.set_password("password123")
                u2.save()


class AddressModelTests(TestCase):
    """Test suite for the Address model and Indian compliance validators."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="priya@electrocart.in",
            password="SecurePassword456!",
            full_name="Priya Patel",
        )

    def test_create_valid_address(self):
        """Address creates successfully with valid Indian fields and choices."""
        address = Address.objects.create(
            user=self.user,
            full_name="Priya Patel",
            phone="+919876543210",
            line1="Flat 402, Green Heights",
            line2="100 Feet Road, Indiranagar",
            landmark="Near Metro Station",
            city="Ahmedabad",
            state=IndianState.GUJARAT,
            pincode="560038",
            is_default=True,
        )
        self.assertEqual(address.state, "Gujarat")
        self.assertTrue(address.is_default)
        self.assertIsNotNone(address.uuid)
        self.assertIn("560038", str(address))

    def test_invalid_pincode_fails_validation(self):
        """Invalid PIN codes (starting with 0, letters, non-6 digits) fail validation."""
        invalid_pincodes = ["012345", "56003", "5600388", "560 038", "ABCDEF"]
        for pin in invalid_pincodes:
            address = Address(
                user=self.user,
                full_name="Priya Patel",
                phone="9876543210",
                line1="Some street",
                city="Ahmedabad",
                state=IndianState.GUJARAT,
                pincode=pin,
            )
            with self.assertRaises(ValidationError, msg=f"Pincode '{pin}' should fail validation"):
                address.full_clean()

    def test_invalid_phone_fails_validation(self):
        """Invalid phone numbers (less than 10 digits, invalid prefix) fail validation."""
        invalid_phones = ["12345", "1234567890", "5987654321", "abcdefghij"]
        for ph in invalid_phones:
            address = Address(
                user=self.user,
                full_name="Priya Patel",
                phone=ph,
                line1="Some street",
                city="Ahmedabad",
                state=IndianState.GUJARAT,
                pincode="560038",
            )
            with self.assertRaises(ValidationError, msg=f"Phone '{ph}' should fail validation"):
                address.full_clean()

    def test_single_default_address_switch(self):
        """Setting a new address as default automatically unsets the previous default."""
        addr1 = Address.objects.create(
            user=self.user,
            full_name="Priya Patel",
            phone="9876543210",
            line1="Address 1",
            city="Ahmedabad",
            state=IndianState.GUJARAT,
            pincode="560038",
            is_default=True,
        )
        self.assertTrue(addr1.is_default)

        # Create second default address
        addr2 = Address.objects.create(
            user=self.user,
            full_name="Priya Patel",
            phone="9876543210",
            line1="Address 2",
            city="Mumbai",
            state=IndianState.MAHARASHTRA,
            pincode="400001",
            is_default=True,
        )

        addr1.refresh_from_db()
        addr2.refresh_from_db()
        self.assertFalse(addr1.is_default)
        self.assertTrue(addr2.is_default)

    def test_multiple_non_default_addresses_permitted(self):
        """Multiple addresses with is_default=False can coexist for the same user."""
        Address.objects.create(
            user=self.user,
            full_name="Priya Patel",
            phone="9876543210",
            line1="Office 1",
            city="Ahmedabad",
            state=IndianState.GUJARAT,
            pincode="560038",
            is_default=False,
        )
        Address.objects.create(
            user=self.user,
            full_name="Priya Patel",
            phone="9876543210",
            line1="Office 2",
            city="Ahmedabad",
            state=IndianState.GUJARAT,
            pincode="560001",
            is_default=False,
        )
        self.assertEqual(Address.objects.filter(user=self.user).count(), 2)

    def test_state_list_size_36(self):
        """Controlled roster contains exactly 28 states and 8 Union Territories (36 total)."""
        self.assertEqual(len(IndianState.choices), 36)


class AllauthViewsTests(TestCase):
    """Verify allauth authentication endpoints, inputs, and status codes."""

    def setUp(self):
        from django.test import Client

        self.client = Client()

    def test_login_view_status_code(self):
        response = self.client.get("/accounts/login/")
        self.assertEqual(response.status_code, 200)

    def test_signup_view_renders_email_and_password_inputs(self):
        response = self.client.get("/accounts/signup/")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertIn('name="email"', content)
        self.assertIn('name="password1"', content)
        self.assertIn('name="password2"', content)

