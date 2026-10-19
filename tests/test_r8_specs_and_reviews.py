"""
Tests for Phase R8 Task 4: Deep Technical Spec Comparison Engine,
Price Delta Advisory, Spec Winners, and Customer Product Reviews with Verified Purchase Detection.
"""

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from apps.catalog.models import Category, Product, ProductReview, ProductSpecification
from apps.catalog.services.spec_extractor import extract_specifications
from apps.orders.models import Order, OrderItem

User = get_user_model()


class SpecsAndReviewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(
            name="Smartphones & Basic Mobiles",
            slug="smartphones",
            display_order=1,
            is_active=True,
        )

        self.flagship_phone = Product.objects.create(
            raw_name="Galaxy Ultra Flagship 5G",
            display_name="Galaxy Ultra Flagship 5G",
            slug="galaxy-ultra-flagship",
            sku="PHONE-ULTRA-FLAG",
            source_asin="B00ULTRAFLAG",
            category=self.category,
            selling_price=Decimal("80000.00"),
            mrp=Decimal("95000.00"),
            is_available=True,
        )

        self.budget_phone = Product.objects.create(
            raw_name="Galaxy Budget Essential 4G",
            display_name="Galaxy Budget Essential 4G",
            slug="galaxy-budget-essential",
            sku="PHONE-BUDGET-ESS",
            source_asin="B00BUDGETESS",
            category=self.category,
            selling_price=Decimal("10000.00"),
            mrp=Decimal("14000.00"),
            is_available=True,
        )

    def test_spec_extraction_and_synthesis(self):
        """Extracts and synthesizes rich technical specifications without empty comparison values."""
        flagship_specs = extract_specifications(
            self.flagship_phone.raw_name,
            category_slug=self.category.slug,
            price=self.flagship_phone.selling_price,
            brand="Samsung",
        )
        self.assertIn("ram", flagship_specs)
        self.assertIn("storage", flagship_specs)
        self.assertIn("processor", flagship_specs)
        self.assertIn("camera", flagship_specs)
        self.assertEqual(flagship_specs["ram"]["value"], "12GB")
        self.assertEqual(flagship_specs["storage"]["value"], "256GB")

        budget_specs = extract_specifications(
            self.budget_phone.raw_name,
            category_slug=self.category.slug,
            price=self.budget_phone.selling_price,
            brand="Samsung",
        )
        self.assertIn("ram", budget_specs)
        self.assertEqual(budget_specs["ram"]["value"], "4GB")

    def test_compare_matrix_with_delta_advisory_and_spec_winners(self):
        """Comparing flagship vs budget triggers 8.0x Delta Advisory, Spec Winners, and Identical Flags."""
        # Seed specs on both products
        f_specs = extract_specifications(
            self.flagship_phone.raw_name,
            category_slug="smartphones",
            price=self.flagship_phone.selling_price,
        )
        for idx, (k, v) in enumerate(f_specs.items(), 1):
            ProductSpecification.objects.create(
                product=self.flagship_phone,
                key=k,
                value=v["value"],
                display_order=idx,
            )

        b_specs = extract_specifications(
            self.budget_phone.raw_name,
            category_slug="smartphones",
            price=self.budget_phone.selling_price,
        )
        for idx, (k, v) in enumerate(b_specs.items(), 1):
            ProductSpecification.objects.create(
                product=self.budget_phone,
                key=k,
                value=v["value"],
                display_order=idx,
            )

        # Set session tray
        session = self.client.session
        session["compare_tray"] = [self.flagship_phone.id, self.budget_phone.id]
        session.save()

        resp = self.client.get("/compare/")
        self.assertEqual(resp.status_code, 200)

        # Delta Advisory checks
        self.assertContains(resp, "8.0x Price Delta")
        self.assertContains(resp, "Flagship vs Budget Tier")

        # Spec winners checks
        self.assertContains(resp, "Spec Winner")
        self.assertContains(resp, "Best Value")
        self.assertContains(resp, "row-identical")

    def test_customer_review_submission_with_verified_purchase(self):
        """Customer submits review; verified purchase badge is set if matching order exists."""
        # 1. Unverified submission
        resp1 = self.client.post(f"/p/{self.budget_phone.slug}/", {
            "submit_review": "1",
            "reviewer_name": "Aarav Sharma",
            "reviewer_email": "unverified@example.com",
            "rating": "4",
            "title": "Decent hardware for the price",
            "body": "Good battery life and snappy interface for everyday tasks.",
        }, follow=True)
        self.assertEqual(resp1.status_code, 200)
        review1 = ProductReview.objects.get(reviewer_email="unverified@example.com")
        self.assertFalse(review1.is_verified_purchase)
        self.assertContains(resp1, "Decent hardware for the price")

        # 2. Verified submission: Create confirmed order first
        order = Order.objects.create(
            order_number="EC-20261019-REVW",
            guest_email="verified@example.com",
            status=Order.STATUS_CONFIRMED,
            subtotal=Decimal("10000.00"),
            total_amount=Decimal("10000.00"),
        )
        OrderItem.objects.create(
            order=order,
            product=self.budget_phone,
            product_title=self.budget_phone.display_name,
            product_sku=self.budget_phone.sku,
            quantity=1,
            unit_price=Decimal("10000.00"),
            taxable_value=Decimal("8474.58"),
            line_total=Decimal("10000.00"),
            mrp=Decimal("14000.00"),
        )

        resp2 = self.client.post(f"/p/{self.budget_phone.slug}/", {
            "submit_review": "1",
            "reviewer_name": "Diya Patel",
            "reviewer_email": "verified@example.com",
            "rating": "5",
            "title": "Verified purchaser review",
            "body": "Everything worked right out of the box. Super smooth experience.",
        }, follow=True)
        self.assertEqual(resp2.status_code, 200)
        review2 = ProductReview.objects.get(reviewer_email="verified@example.com")
        self.assertTrue(review2.is_verified_purchase)
        self.assertContains(resp2, "Verified Purchase")
        self.assertContains(resp2, "Verified purchaser review")
