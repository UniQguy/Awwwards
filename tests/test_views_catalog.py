"""
Storefront catalog and search view integration tests.
Tests home, category listing, category detail with facets, product detail with JSON-LD,
brand directory, and comparison tray logic.
"""

from decimal import Decimal
import json

from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import Category, Collection, FeaturedProduct, Product, ProductSpecification
from apps.inventory.models import Inventory


class CatalogViewsTests(TestCase):
    def setUp(self):
        self.category_audio = Category.objects.create(
            name="Earphones & Headphones",
            slug="earphones-headphones",
            accent_key="earphones-headphones",
            gst_rate=Decimal("18.00"),
            is_gst_rate_verified=True,
            display_order=1,
            description="Personal acoustic monitoring equipment.",
        )
        self.category_keys = Category.objects.create(
            name="Keyboards & Mice",
            slug="keyboards-mice",
            accent_key="keyboards-mice",
            gst_rate=Decimal("18.00"),
            is_gst_rate_verified=True,
            display_order=2,
        )

        self.prod1 = Product.objects.create(
            category=self.category_audio,
            sku="SKU-AUD-001",
            slug="sennheiser-hd650",
            raw_name="Sennheiser HD 650 Open Back Professional Studio Monitor Headphones",
            display_name="Sennheiser HD 650 Studio Headphones",
            source_asin="B00018MSNI",
            parsed_brand="Sennheiser",
            selling_price=Decimal("29990.00"),
            mrp=Decimal("34990.00"),
            is_available=True,
            source_rating=Decimal("4.80"),
            source_rating_count=1240,
        )
        Inventory.objects.create(product=self.prod1, quantity=15)

        ProductSpecification.objects.create(
            product=self.prod1,
            key="Transducer Principle",
            value="Dynamic, Open-Air",
        )
        ProductSpecification.objects.create(
            product=self.prod1,
            key="Impedance",
            value="300 Ohms",
        )

        self.prod2 = Product.objects.create(
            category=self.category_audio,
            sku="SKU-AUD-002",
            slug="audio-technica-m50x",
            raw_name="Audio-Technica ATH-M50x Professional Studio Monitor Headphones Black",
            display_name="Audio-Technica ATH-M50x Monitor Headphones",
            source_asin="B00HVLUR86",
            parsed_brand="Audio-Technica",
            selling_price=Decimal("12999.00"),
            mrp=Decimal("15999.00"),
            is_available=True,
            source_rating=Decimal("4.60"),
            source_rating_count=3500,
        )
        Inventory.objects.create(product=self.prod2, quantity=25)

        self.prod_key = Product.objects.create(
            category=self.category_keys,
            sku="SKU-KEY-001",
            slug="keychron-q1-pro",
            raw_name="Keychron Q1 Pro Wireless Custom Mechanical Keyboard",
            display_name="Keychron Q1 Pro Wireless Mechanical Keyboard",
            source_asin="B0BKEYQ1PR",
            parsed_brand="Keychron",
            selling_price=Decimal("18999.00"),
            mrp=Decimal("21999.00"),
            is_available=True,
        )
        Inventory.objects.create(product=self.prod_key, quantity=8)

        # Editorial collection
        self.collection = Collection.objects.create(
            title="Studio Acoustic Reference",
            slug="studio-acoustic-reference",
            intro="Critically engineered transducers for audio mastering.",
        )
        FeaturedProduct.objects.create(
            collection=self.collection,
            product=self.prod1,
            display_order=1,
            is_hero=True,
        )

    def test_home_page_renders_successfully(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ELECTROCART")
        self.assertContains(response, "Studio Acoustic Reference")
        self.assertContains(response, "Sennheiser HD 650")
        self.assertContains(response, "Earphones &amp; Headphones")

    def test_category_list_renders_categories(self):
        response = self.client.get(reverse("category_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Earphones &amp; Headphones")
        self.assertContains(response, "Keyboards &amp; Mice")

    def test_category_detail_filtering_and_facets(self):
        url = reverse("category_detail", kwargs={"slug": self.category_audio.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sennheiser HD 650")
        self.assertContains(response, "Audio-Technica ATH-M50x")

        # Brand filter
        response_brand = self.client.get(url, {"brand": "Sennheiser"})
        self.assertEqual(response_brand.status_code, 200)
        self.assertContains(response_brand, "Sennheiser HD 650")
        self.assertNotContains(response_brand, "Audio-Technica ATH-M50x")

        # Price range filter
        response_price = self.client.get(url, {"min_price": "20000", "max_price": "35000"})
        self.assertEqual(response_price.status_code, 200)
        self.assertContains(response_price, "Sennheiser HD 650")
        self.assertNotContains(response_price, "Audio-Technica ATH-M50x")

    def test_product_detail_page_includes_json_ld_schema(self):
        url = reverse("product_detail", kwargs={"slug": self.prod1.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sennheiser HD 650")
        self.assertContains(response, "Transducer Principle")
        self.assertContains(response, "Dynamic, Open-Air")
        self.assertContains(response, "Marketplace Rating:")
        self.assertContains(response, "4.8")

        # JSON-LD Schema assertion
        content = response.content.decode("utf-8")
        self.assertIn('application/ld+json', content)
        self.assertIn('"@type": "Product"', content)
        self.assertIn('"priceCurrency": "INR"', content)

    def test_brand_list_displays_grouped_brands(self):
        response = self.client.get(reverse("brand_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sennheiser")
        self.assertContains(response, "Audio-Technica")
        self.assertContains(response, "Keychron")

    def test_compare_tray_workflow_and_constraints(self):
        # 1. Add first product
        resp = self.client.post(reverse("compare_add", kwargs={"product_id": self.prod1.id}), follow=True)
        self.assertEqual(resp.status_code, 200)
        session = self.client.session
        self.assertEqual(session["compare_tray"], [self.prod1.id])

        # 2. Add second product in same category
        resp = self.client.post(reverse("compare_add", kwargs={"product_id": self.prod2.id}), follow=True)
        self.assertEqual(resp.status_code, 200)
        session = self.client.session
        self.assertEqual(session["compare_tray"], [self.prod1.id, self.prod2.id])

        # 3. Add product in different category -> rejected with error message
        resp = self.client.post(reverse("compare_add", kwargs={"product_id": self.prod_key.id}), follow=True)
        self.assertEqual(resp.status_code, 200)
        session = self.client.session
        self.assertEqual(len(session["compare_tray"]), 2)
        self.assertContains(resp, "restricted to products in the same category")

        # 4. View compare tray
        resp_tray = self.client.get(reverse("compare_tray"))
        self.assertEqual(resp_tray.status_code, 200)
        self.assertContains(resp_tray, "Sennheiser HD 650")
        self.assertContains(resp_tray, "Audio-Technica ATH-M50x")
        self.assertContains(resp_tray, "Transducer Principle")

        # 5. Remove an item
        self.client.post(reverse("compare_remove", kwargs={"product_id": self.prod1.id}))
        session = self.client.session
        self.assertEqual(session["compare_tray"], [self.prod2.id])

        # 6. Clear compare tray
        self.client.post(reverse("compare_clear"))
        session = self.client.session
        self.assertEqual(session["compare_tray"], [])
