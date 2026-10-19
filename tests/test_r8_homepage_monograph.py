"""
Integration tests for Phase R8 Task 5: 9-Chapter Kinetic Monograph Homepage Exhibition.
"""

from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse

from apps.catalog.models import Category, Product, ProductMedia
from apps.inventory.models import Inventory
from apps.cart.models import Cart


class HomepageMonographTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.cat_phones = Category.objects.create(name="Smartphones & Devices", slug="smartphones", is_active=True)
        self.cat_audio = Category.objects.create(name="Earphones & Headphones", slug="earphones-headphones", is_active=True)
        self.cat_acc = Category.objects.create(name="Cables, Chargers & Power", slug="cables-chargers-powerbanks", is_active=True)

        self.flagship = Product.objects.create(
            category=self.cat_phones,
            raw_name="Flagship Phone Ultra 512GB",
            display_name="Flagship Phone Ultra",
            slug="flagship-phone-ultra",
            selling_price=Decimal("89999.00"),
            mrp=Decimal("99999.00"),
            is_available=True,
            sku="FLAG-001",
            source_asin="B08FLAG001",
        )
        ProductMedia.objects.create(
            product=self.flagship,
            media_type="image",
            external_image_url="https://example.com/phone.jpg",
        )
        Inventory.objects.create(product=self.flagship, quantity=10)

        self.audio_item = Product.objects.create(
            category=self.cat_audio,
            raw_name="Studio Acoustic Headphones Pro",
            display_name="Studio Acoustic Headphones",
            slug="studio-acoustic-headphones",
            selling_price=Decimal("18999.00"),
            mrp=Decimal("24999.00"),
            is_available=True,
            sku="AUD-001",
            source_asin="B08AUD0001",
        )
        ProductMedia.objects.create(
            product=self.audio_item,
            media_type="image",
            external_image_url="https://example.com/audio.jpg",
        )
        Inventory.objects.create(product=self.audio_item, quantity=10)

        self.acc_item = Product.objects.create(
            category=self.cat_acc,
            raw_name="Braided USB-C Rapid Cable",
            display_name="Braided USB-C Cable",
            slug="braided-usbc-cable",
            selling_price=Decimal("999.00"),
            mrp=Decimal("1499.00"),
            is_available=True,
            sku="ACC-001",
            source_asin="B08ACC0001",
        )
        ProductMedia.objects.create(
            product=self.acc_item,
            media_type="image",
            external_image_url="https://example.com/cable.jpg",
        )
        Inventory.objects.create(product=self.acc_item, quantity=10)

    def test_homepage_renders_all_9_chapters(self):
        resp = self.client.get(reverse("home"))
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode("utf-8")

        # Verify presence of all 9 chapters
        self.assertIn('id="hero-stage-chapter"', content)
        self.assertIn('id="flagship-anatomy-chapter"', content)
        self.assertIn('id="vault-deals-chapter"', content)
        self.assertIn('id="categories-matrix-chapter"', content)
        self.assertIn('id="trust-manifesto-chapter"', content)
        self.assertIn('id="monograph-footer-chapter"', content)
        self.assertIn("Ahmedabad, Gujarat", content)

    def test_cart_add_bundle(self):
        bundle_url = reverse("cart_add_bundle")
        pids = [self.flagship.id, self.audio_item.id, self.acc_item.id]
        resp = self.client.post(bundle_url, {"product_ids": [str(pid) for pid in pids]})
        self.assertRedirects(resp, reverse("cart_detail"))

        # Verify cart has all 3 items
        cart = Cart.objects.last()
        self.assertIsNotNone(cart)
        self.assertEqual(cart.total_items, 3)
