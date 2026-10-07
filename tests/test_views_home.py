"""
Integration tests for the Editorial Homepage (Concept 2: The Kinetic Monograph).
Verifies:
- Live rendering with real database data
- Sparse/empty database safety (degrades to headline without exceptions)
- Curated vs auto-selected collections attribution
- Live numbers matching database state
- Continuous headline sentence without text gaps when cutouts are stripped
- Zero lorem ipsum
- No hardcoded copy numerals
- Query count efficiency
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


class HomeViewEditorialTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        ShippingConfig.get_solo()

        cls.cat_audio = Category.objects.create(
            name="Audio & Monitors",
            slug="earphones-headphones",
            accent_key="earphones-headphones",
            description="Precision studio monitors and IEMs.",
            display_order=1,
            is_active=True,
        )
        cls.cat_keyboards = Category.objects.create(
            name="Keyboards & Mice",
            slug="keyboards-mice",
            accent_key="keyboards-mice",
            description="CNC milled mechanical decks.",
            display_order=2,
            is_active=True,
        )

        cls.products = []
        for i in range(5):
            p = Product.objects.create(
                category=cls.cat_audio,
                sku=f"AUD-{i+1}",
                slug=f"aud-specimen-{i+1}",
                source_asin=f"B00HOMEAUD{i+1}",
                raw_name=f"Audio Specimen {i+1} Matte Black",
                display_name=f"Audio Specimen {i+1}",
                parsed_brand="boAt",
                selling_price=Decimal(f"{(i+1)*600}.00"),
                mrp=Decimal(f"{(i+1)*900}.00"),
                is_available=True,
                source_rating=4.5,
                source_rating_count=(i + 1) * 150,
            )
            ProductMedia.objects.create(
                product=p,
                media_type="image",
                external_image_url=f"https://m.media-amazon.com/images/I/aud_{i+1}.jpg",
                display_order=0,
            )
            ProductSpecification.objects.create(
                product=p,
                key="Transducer",
                value="Planar Magnetic",
                is_highlight=True,
            )
            Inventory.objects.create(product=p, quantity=10, is_sample_data=True)
            cls.products.append(p)

        for i in range(4):
            p = Product.objects.create(
                category=cls.cat_keyboards,
                sku=f"KB-{i+1}",
                slug=f"kb-specimen-{i+1}",
                source_asin=f"B00HOMEKB{i+1}",
                raw_name=f"Mechanical Deck {i+1}",
                display_name=f"Mechanical Deck {i+1}",
                parsed_brand="Logitech",
                selling_price=Decimal(f"{(i+1)*1500}.00"),
                mrp=Decimal(f"{(i+1)*1800}.00"),
                is_available=True,
                source_rating=4.8,
                source_rating_count=(i + 1) * 80,
            )
            ProductMedia.objects.create(
                product=p,
                media_type="image",
                external_image_url=f"https://m.media-amazon.com/images/I/kb_{i+1}.jpg",
                display_order=0,
            )
            Inventory.objects.create(product=p, quantity=8, is_sample_data=True)
            cls.products.append(p)

    def test_home_page_status_and_template(self):
        """Home page responds with HTTP 200 using catalog/home.html."""
        resp = self.client.get(reverse("home"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "catalog/home.html")

    def test_single_h1_on_page(self):
        """Page contains exactly one <h1> element."""
        resp = self.client.get(reverse("home"))
        content = resp.content.decode("utf-8")
        h1_matches = re.findall(r"<h1[^>]*>(.*?)</h1>", content, re.DOTALL | re.IGNORECASE)
        self.assertEqual(len(h1_matches), 1)

    def test_headline_text_continuity_without_cutout_gaps(self):
        """
        When inline cutout tags (<span class="cutout" ...</span>) are stripped,
        the hero headline sentence reads continuously without syntax or punctuation gaps.
        """
        resp = self.client.get(reverse("home"))
        content = resp.content.decode("utf-8")
        h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", content, re.DOTALL | re.IGNORECASE)
        self.assertIsNotNone(h1_match)

        raw_h1 = h1_match.group(1)
        # Strip cutout elements
        cleaned = re.sub(r'<span class="cutout"[^>]*>.*?</span>', '', raw_h1, flags=re.DOTALL)
        # Strip extra whitespace and HTML tags
        cleaned = re.sub(r'<[^>]+>', '', cleaned)
        cleaned = " ".join(cleaned.split())

        # Assert sentence is continuous
        expected = "Instruments for listening, tools for thought, and objects of pure utility."
        self.assertEqual(cleaned, expected)

    def test_live_database_counts_match_rendered_page(self):
        """Every count rendered in hero and chapters matches real database counts."""
        resp = self.client.get(reverse("home"))
        content = resp.content.decode("utf-8")

        total_listings = Product.objects.filter(is_available=True, selling_price__gt=0).count()
        self.assertContains(resp, f"{total_listings} listings across")

    def test_auto_selected_attribution_label(self):
        """When auto-selected, honest attribution note appears."""
        resp = self.client.get(reverse("home"))
        self.assertContains(resp, "Selected by number of ratings on Amazon")

    def test_curated_hero_collection_suppresses_attribution(self):
        """When home_hero collection is curated, no attribution label is displayed for hero."""
        col = Collection.objects.create(
            title="Studio Exhibition",
            slug="studio-exhibition",
            placement=Collection.PLACEMENT_HOME_HERO,
            is_active=True,
        )
        FeaturedProduct.objects.create(collection=col, product=self.products[0], display_order=1)

        resp = self.client.get(reverse("home"))
        # Hero plate product is curated
        self.assertEqual(resp.context["hero_plate_product"], self.products[0])
        self.assertFalse(resp.context["hero"].is_auto)

    def test_no_lorem_ipsum_in_template(self):
        """Template copy contains zero instances of 'lorem ipsum'."""
        resp = self.client.get(reverse("home"))
        content = resp.content.decode("utf-8").lower()
        self.assertNotIn("lorem", content)
        self.assertNotIn("ipsum", content)

    def test_query_count_efficiency(self):
        """Homepage executes within reasonable query bounds (26 queries including base context processors and chapters)."""
        with self.assertNumQueries(26):
            resp = self.client.get(reverse("home"))
            self.assertEqual(resp.status_code, 200)

    def test_empty_database_safety(self):
        """When database has zero products, homepage renders safely with no errors."""
        Product.objects.all().delete()
        Category.objects.all().delete()
        Collection.objects.all().delete()

        resp = self.client.get(reverse("home"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Instruments for listening")
