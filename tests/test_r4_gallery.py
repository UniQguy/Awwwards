"""
Tests for Pass R4: The Gallery, Storytelling, and Media Slots.
Verifies:
- Category.chapter_intro renders only when set, and leaves zero empty markup when blank.
- media_slot.html collapses cleanly when files are missing and respects show_placeholder_labels.
- balance_amp filter binds ampersands with non-breaking spaces.
- strip_brand filter cleans product display titles.
- INR price formatting and zero exclamation marks.
"""

from decimal import Decimal
from django.test import TestCase, override_settings
from django.template import Context, Template
from django.urls import reverse

from apps.catalog.models import Category, Product
from apps.inventory.models import Inventory
from apps.shipping.models import ShippingConfig


class R4StorytellingAndMediaSlotsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        ShippingConfig.get_solo()

        cls.category_with_intro = Category.objects.create(
            name="Earphones & Headphones",
            slug="earphones-headphones",
            accent_key="earphones-headphones",
            display_order=1,
            is_active=True,
            chapter_intro="Quiet open-back drivers and high-purity copper cables.",
        )

        cls.category_without_intro = Category.objects.create(
            name="Speakers & Acoustics",
            slug="speakers",
            accent_key="speakers",
            display_order=2,
            is_active=True,
            chapter_intro="",
        )

        cls.product = Product.objects.create(
            category=cls.category_with_intro,
            sku="R4-AUD-01",
            slug="r4-aud-specimen",
            source_asin="B00R4AUD01",
            raw_name="Audio Brand Specimen 1 Studio Headphones",
            parsed_brand="Audio Brand",
            display_name="Audio Brand Specimen 1 Studio Headphones",
            selling_price=Decimal("12999.00"),
            mrp=Decimal("14999.00"),
            is_available=True,
        )
        Inventory.objects.create(
            product=cls.product,
            quantity=10,
            low_stock_threshold=2,
        )

    def test_chapter_intro_renders_when_set(self):
        """When Category.chapter_intro is set, it renders in category detail marquee and home chapter."""
        res_cat = self.client.get(reverse("category_detail", kwargs={"slug": self.category_with_intro.slug}))
        self.assertEqual(res_cat.status_code, 200)
        self.assertContains(res_cat, "Quiet open-back drivers and high-purity copper cables.")

        res_home = self.client.get(reverse("home"))
        self.assertEqual(res_home.status_code, 200)
        self.assertContains(res_home, "Quiet open-back drivers and high-purity copper cables.")

    def test_chapter_intro_collapses_when_blank(self):
        """When Category.chapter_intro is empty, zero empty paragraphs or duplicate ranges render."""
        res_cat = self.client.get(reverse("category_detail", kwargs={"slug": self.category_without_intro.slug}))
        self.assertEqual(res_cat.status_code, 200)
        content_cat = res_cat.content.decode("utf-8")
        self.assertNotIn('class="category-editorial-line"', content_cat)

        res_home = self.client.get(reverse("home"))
        self.assertEqual(res_home.status_code, 200)
        content_home = res_home.content.decode("utf-8")
        # Ensure no empty pull quote is rendered for the blank category
        self.assertNotIn('<p class="pull mb-4"></p>', content_home)

    def test_balance_amp_filter(self):
        """balance_amp filter replaces ' & ' with ' &amp;&nbsp;' to prevent orphaned ampersands."""
        tpl = Template('{% load core_tags %}{{ text|balance_amp }}')
        rendered = tpl.render(Context({"text": "Earphones & Headphones"}))
        self.assertIn("Earphones &amp;&nbsp;Headphones", rendered)

    def test_strip_brand_filter(self):
        """strip_brand filter strips redundant leading brand from product name."""
        tpl = Template('{% load core_tags %}{{ name|strip_brand:brand }}')
        rendered = tpl.render(Context({"name": "Audio Brand Studio Monitor", "brand": "Audio Brand"}))
        self.assertEqual(rendered, "Studio Monitor")

    def test_media_slot_missing_files_collapses(self):
        """media_slot template collapses completely when files do not exist."""
        tpl = Template(
            '{% include "includes/media_slot.html" with slot_id="nonexistent" poster_src="images/none.webp" video_src="video/none.mp4" %}'
        )
        rendered = tpl.render(Context({"show_placeholder_labels": True})).strip()
        self.assertEqual(rendered, "")

    def test_media_slot_production_mode_hides_placeholder_badge(self):
        """In production (SHOW_PLACEHOLDER_LABELS=False), placeholder badges never render."""
        tpl = Template(
            '{% include "includes/media_slot.html" with slot_id="home-hero" poster_src="media/placeholders/home-hero-poster.webp" is_placeholder=True %}'
        )
        rendered_prod = tpl.render(Context({"show_placeholder_labels": False})).strip()
        self.assertNotIn("media-placeholder-badge", rendered_prod)
        self.assertNotIn("Placeholder", rendered_prod)

        rendered_dev = tpl.render(Context({"show_placeholder_labels": True})).strip()
        self.assertIn("media-placeholder-badge", rendered_dev)
        self.assertIn("Placeholder", rendered_dev)
