"""
Integration tests for Category Spreads, Category Index, and Product Sheet.
Verifies:
- Editorial marquee display conditions (page 1 without params vs compact header)
- Product sheet single-image composition & secondary slot rules
- Other listings / finish swatches rendering
- Semantic standards: single <h1> per page, cutout aria-hidden and empty alt, max 2 display-xl elements
"""

from decimal import Decimal
import re
from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import (
    Category,
    Collection,
    FeaturedProduct,
    Product,
    ProductMedia,
    ProductSpecification,
)
from apps.inventory.models import Inventory
from apps.shipping.models import ShippingConfig


class CategorySpreadAndProductSheetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        ShippingConfig.get_solo()

        cls.category = Category.objects.create(
            name="Audio & Monitors",
            slug="earphones-headphones",
            accent_key="earphones-headphones",
            description="Precision acoustic instruments and studio reference gear.",
            display_order=1,
            is_active=True,
        )

        cls.products = []
        for i in range(6):
            p = Product.objects.create(
                category=cls.category,
                sku=f"SPREAD-AUD-{i+1}",
                slug=f"spread-aud-{i+1}",
                source_asin=f"B00SPREAD{i+1}",
                raw_name=f"Studio In-Ear Monitor {i+1} Space Black",
                display_name=f"Studio In-Ear Monitor {i+1}",
                parsed_brand="boAt",
                selling_price=Decimal(f"{(i+1)*800}.00"),
                mrp=Decimal(f"{(i+1)*1200}.00"),
                is_available=True,
                source_rating=4.7,
                source_rating_count=(i + 1) * 200,
            )
            ProductMedia.objects.create(
                product=p,
                media_type="image",
                external_image_url=f"https://m.media-amazon.com/images/I/spread_{i+1}.jpg",
                display_order=0,
            )
            ProductSpecification.objects.create(
                product=p,
                key="Frequency Response",
                value="20Hz - 20kHz",
                is_highlight=True,
            )
            Inventory.objects.create(product=p, quantity=15, is_sample_data=True)
            cls.products.append(p)

    def test_marquee_shows_on_page_1_without_filters(self):
        """Editorial marquee renders when visiting category on page 1 with no filters."""
        url = reverse("category_detail", kwargs={"slug": self.category.slug})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context["show_marquee"])
        self.assertContains(resp, "Monograph Marquee")
        self.assertContains(resp, "category-marquee")

    def test_marquee_hidden_when_filtering(self):
        """When query parameters (filter, sort, search) are present, marquee is hidden in favor of compact header."""
        url = reverse("category_detail", kwargs={"slug": self.category.slug}) + "?brand=boAt"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.context["show_marquee"])
        self.assertNotContains(resp, "Monograph Marquee")
        self.assertNotContains(resp, "category-marquee")

    def test_marquee_hidden_on_page_2(self):
        """Marquee is hidden on page 2 even if no filters are active."""
        url = reverse("category_detail", kwargs={"slug": self.category.slug}) + "?page=2"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.context["show_marquee"])

    def test_category_list_monograph_index(self):
        """Category index (/categories/) renders monograph spreads with live stats and picks."""
        resp = self.client.get(reverse("category_list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Category Monograph Index")
        self.assertContains(resp, "Audio &amp; Monitors")
        self.assertContains(resp, "Curated listings")

    def test_product_detail_single_image_composition(self):
        """Product page renders single image in exhibition frame without fake carousel thumbnails."""
        product = self.products[0]
        url = reverse("product_detail", kwargs={"slug": product.slug})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "product-frame-plate")
        self.assertContains(resp, "product-frame-mat")
        # Ensure fake thumbnail carousel is not rendered
        self.assertNotContains(resp, "product-thumbnails")

    def test_product_detail_absent_secondary_slot(self):
        """When product has no video/model media, secondary slot is absent."""
        product = self.products[0]
        url = reverse("product_detail", kwargs={"slug": product.slug})
        resp = self.client.get(url)
        self.assertNotContains(resp, "Exhibition Model: Video Slot")
        self.assertNotContains(resp, "Exhibition Model: 3D Model Slot")

    def test_product_detail_other_listings_row(self):
        """Other listings section renders hardware finish chips with links."""
        product = self.products[0]
        url = reverse("product_detail", kwargs={"slug": product.slug})
        resp = self.client.get(url)
        self.assertContains(resp, "Other Listings of This Item")
        self.assertContains(resp, "finish-swatch-list")
        self.assertContains(resp, "finish-swatch-item")

    def test_semantics_single_h1_per_page(self):
        """Pages contain exactly one <h1> element."""
        # 1. Category detail with marquee
        resp1 = self.client.get(reverse("category_detail", kwargs={"slug": self.category.slug}))
        h1s_1 = re.findall(r"<h1[^>]*>(.*?)</h1>", resp1.content.decode("utf-8"), re.DOTALL | re.IGNORECASE)
        self.assertEqual(len(h1s_1), 1)

        # 2. Category detail without marquee
        resp2 = self.client.get(reverse("category_detail", kwargs={"slug": self.category.slug}) + "?brand=boAt")
        h1s_2 = re.findall(r"<h1[^>]*>(.*?)</h1>", resp2.content.decode("utf-8"), re.DOTALL | re.IGNORECASE)
        self.assertEqual(len(h1s_2), 1)

        # 3. Product detail
        resp3 = self.client.get(reverse("product_detail", kwargs={"slug": self.products[0].slug}))
        h1s_3 = re.findall(r"<h1[^>]*>(.*?)</h1>", resp3.content.decode("utf-8"), re.DOTALL | re.IGNORECASE)
        self.assertEqual(len(h1s_3), 1)

    def test_max_two_display_xl_per_page(self):
        """No page contains more than two display-xl elements."""
        for url in [
            reverse("home"),
            reverse("category_list"),
            reverse("category_detail", kwargs={"slug": self.category.slug}),
            reverse("product_detail", kwargs={"slug": self.products[0].slug}),
        ]:
            resp = self.client.get(url)
            content = resp.content.decode("utf-8")
            display_xls = re.findall(r'class="[^"]*display-xl[^"]*"', content)
            self.assertLessEqual(len(display_xls), 2, f"Too many display-xl on {url}")

    def test_cutouts_have_aria_hidden_and_empty_alt(self):
        """All headline cutouts carry aria-hidden='true' and empty alt='' for screen reader transparency."""
        resp = self.client.get(reverse("home"))
        content = resp.content.decode("utf-8")
        cutouts = re.findall(r'<span class="cutout"[^>]*>.*?</span>', content, re.DOTALL)
        for cutout in cutouts:
            self.assertIn('aria-hidden="true"', cutout)
            self.assertIn('alt=""', cutout)
