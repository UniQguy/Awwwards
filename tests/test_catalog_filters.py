"""
Tests for category catalog filtering, form autocomplete attributes, and URL synchronization (WP1.7).
"""

from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from apps.catalog.models import Category, Product


class CategoryFilterFormTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(
            name="Cameras",
            slug="cameras",
            display_order=1,
            is_active=True,
        )
        # Create products to populate pagination and filtering
        for i in range(30):
            Product.objects.create(
                category=self.category,
                sku=f"CAM-{i:03d}",
                slug=f"camera-item-{i:03d}",
                raw_name=f"Camera Model {i:03d} with Zoom Lens",
                display_name=f"Camera Model {i:03d}",
                source_asin=f"B000CAM{i:03d}",
                parsed_brand="Canon" if i % 2 == 0 else "Nikon",
                selling_price=Decimal(f"{(i + 1) * 1000}.00"),
                is_available=True,
            )

    def test_filter_form_has_autocomplete_off(self):
        """Filter form and its input/select fields must carry autocomplete='off' to prevent browser form restore bugs."""
        url = reverse("category_detail", kwargs={"slug": self.category.slug})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode("utf-8")

        self.assertIn('autocomplete="off"', content)
        self.assertIn('name="min_price" id="filter-min-price" class="form-control" value="" autocomplete="off"', content)
        self.assertIn('name="max_price" id="filter-max-price" class="form-control" value="" autocomplete="off"', content)
        self.assertIn('name="sort" id="filter-sort" class="form-control" autocomplete="off"', content)

    def test_page_2_without_params_has_empty_price_inputs(self):
        """Visiting page 2 without price query parameters must render empty min_price and max_price inputs."""
        url = reverse("category_detail", kwargs={"slug": self.category.slug})
        resp = self.client.get(url, {"page": "2"})
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode("utf-8")

        self.assertIn('name="min_price" id="filter-min-price" class="form-control" value="" autocomplete="off"', content)
        self.assertIn('name="max_price" id="filter-max-price" class="form-control" value="" autocomplete="off"', content)

    def test_explicit_price_filter_reflects_in_inputs(self):
        """When query parameters contain price bounds, inputs must reflect exact values."""
        url = reverse("category_detail", kwargs={"slug": self.category.slug})
        resp = self.client.get(url, {"min_price": "5000", "max_price": "15000"})
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode("utf-8")

        self.assertIn('name="min_price" id="filter-min-price" class="form-control" value="5000" autocomplete="off"', content)
        self.assertIn('name="max_price" id="filter-max-price" class="form-control" value="15000" autocomplete="off"', content)
