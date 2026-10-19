"""
Unit tests for apps.catalog.services.editorial.
Tests curation, fallback auto-selection, determinism, aggregate correctness,
empty-state safety, cutout eligibility, and query efficiency.
"""

from decimal import Decimal
from django.test import TestCase

from apps.catalog.models import (
    Category,
    Collection,
    FeaturedProduct,
    Product,
    ProductMedia,
    ProductSpecification,
)
from apps.catalog.services.editorial import (
    brand_list,
    category_spread,
    eligible_cutout_products,
    hero_products,
    home_chapters,
    index_rows,
)
from apps.inventory.models import Inventory


class EditorialServicesTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create categories
        cls.cat_audio = Category.objects.create(
            name="Audio & Monitors",
            slug="earphones-headphones",
            accent_key="earphones-headphones",
            description="Precision acoustic instruments and studio reference gear.",
            display_order=1,
        )
        cls.cat_keyboards = Category.objects.create(
            name="Keyboards & Input",
            slug="keyboards-mice",
            accent_key="keyboards-mice",
            description="Milled mechanical peripherals and tactile switches.",
            display_order=2,
        )
        cls.cat_empty = Category.objects.create(
            name="Sparse Category",
            slug="other",
            accent_key="other",
            description="",
            display_order=3,
        )

        # Products for audio (5 products)
        cls.audio_prods = []
        for i in range(5):
            p = Product.objects.create(
                category=cls.cat_audio,
                sku=f"AUD-{i+1}",
                slug=f"audio-prod-{i+1}",
                source_asin=f"B00TESTAUD{i+1}",
                raw_name=f"Audio Specimen {i+1} Black",
                display_name=f"Audio Specimen {i+1}",
                parsed_brand="boAt",
                selling_price=Decimal(f"{(i+1)*500}.00"),
                mrp=Decimal(f"{(i+1)*800}.00"),
                is_available=True,
                source_rating=4.5,
                source_rating_count=(i + 1) * 100,
            )
            ProductMedia.objects.create(
                product=p,
                media_type="image",
                external_image_url=f"https://m.media-amazon.com/images/I/audio_{i+1}.jpg",
                display_order=0,
            )
            ProductSpecification.objects.create(
                product=p,
                key="Driver",
                value="10mm Beryllium",
                is_highlight=True,
                display_order=1,
            )
            Inventory.objects.create(product=p, quantity=10, is_sample_data=True)
            cls.audio_prods.append(p)

        # Products for keyboards (4 products)
        cls.kb_prods = []
        for i in range(4):
            p = Product.objects.create(
                category=cls.cat_keyboards,
                sku=f"KB-{i+1}",
                slug=f"kb-prod-{i+1}",
                source_asin=f"B00TESTKB{i+1}",
                raw_name=f"Mechanical Keyboard {i+1}",
                display_name=f"Mechanical Keyboard {i+1}",
                parsed_brand="Logitech",
                selling_price=Decimal(f"{(i+1)*1200}.00"),
                mrp=Decimal(f"{(i+1)*1500}.00"),
                is_available=True,
                source_rating=4.8,
                source_rating_count=(i + 1) * 50,
            )
            ProductMedia.objects.create(
                product=p,
                media_type="image",
                external_image_url=f"https://m.media-amazon.com/images/I/kb_{i+1}.jpg",
                display_order=0,
            )
            Inventory.objects.create(product=p, quantity=5, is_sample_data=True)
            cls.kb_prods.append(p)

    def test_hero_products_auto_select_fallback(self):
        """When no curated home_hero collection exists, auto-selects 1 per category by rating desc."""
        hero = hero_products(n=2)
        self.assertTrue(hero.is_auto)
        self.assertEqual(len(hero.products), 2)
        # Unique categories among selections
        cat_ids = [p.category_id for p in hero.products]
        self.assertEqual(len(cat_ids), len(set(cat_ids)))
        # Top audio product is Audio Specimen 5 (rating count 500), top kb product is KB-4 (rating count 200)
        self.assertEqual({p.sku for p in hero.products}, {"AUD-5", "KB-4"})

    def test_hero_products_curated_collection(self):
        """When a home_hero collection exists, returns curated products and is_auto=False."""
        col = Collection.objects.create(
            title="Curated Audio Exhibition",
            slug="curated-audio-hero",
            placement=Collection.PLACEMENT_HOME_HERO,
            is_active=True,
        )
        FeaturedProduct.objects.create(collection=col, product=self.audio_prods[0], display_order=1)
        FeaturedProduct.objects.create(collection=col, product=self.audio_prods[1], display_order=2)

        hero = hero_products(n=2)
        self.assertFalse(hero.is_auto)
        self.assertEqual(len(hero.products), 2)
        self.assertEqual(hero.products[0], self.audio_prods[0])
        self.assertEqual(hero.products[1], self.audio_prods[1])

    def test_home_chapters_filtering_and_stats(self):
        """home_chapters only returns categories with >= 4 purchasable items with real database stats."""
        chapters = home_chapters(max_chapters=6)
        self.assertEqual(len(chapters), 2)  # Audio and Keyboards have >= 4, Sparse has 0

        # Audio chapter
        ch_audio = chapters[0]
        self.assertEqual(ch_audio.category, self.cat_audio)
        self.assertEqual(ch_audio.product_count, 5)
        self.assertEqual(ch_audio.price_min, Decimal("500.00"))
        self.assertEqual(ch_audio.price_max, Decimal("2500.00"))
        self.assertEqual(ch_audio.editorial_line, "Precision acoustic instruments and studio reference gear.")
        self.assertEqual(len(ch_audio.picks), 3)

        # Keyboards chapter
        ch_kb = chapters[1]
        self.assertEqual(ch_kb.category, self.cat_keyboards)
        self.assertEqual(ch_kb.product_count, 4)
        self.assertEqual(ch_kb.price_min, Decimal("1200.00"))
        self.assertEqual(ch_kb.price_max, Decimal("4800.00"))

    def test_category_spread_stats_accuracy(self):
        """category_spread stats match real database counts and aggregations."""
        spread = category_spread(self.cat_audio)
        self.assertEqual(spread.category, self.cat_audio)
        self.assertEqual(spread.stats.listing_count, 5)
        self.assertEqual(spread.stats.distinct_raw_name_count, 5)
        self.assertEqual(spread.stats.brand_count, 1)  # boAt is allow-listed
        self.assertEqual(spread.stats.price_min, Decimal("500.00"))
        self.assertEqual(spread.stats.price_max, Decimal("2500.00"))
        self.assertEqual(spread.stats.in_stock_count, 5)
        self.assertEqual(len(spread.picks), 4)

    def test_category_spread_fallback_editorial_line(self):
        """When category has no description, constructs a factual sentence from stats."""
        spread = category_spread(self.cat_empty)
        self.assertEqual(spread.stats.listing_count, 0)
        self.assertEqual(spread.editorial_line, "0 listings from ₹0.00 to ₹0.00.")

    def test_index_rows(self):
        """index_rows returns all active categories with price-from and a top pick."""
        rows = index_rows()
        self.assertEqual(len(rows), 3)
        row_audio = rows[0]
        self.assertEqual(row_audio.category, self.cat_audio)
        self.assertEqual(row_audio.count, 5)
        self.assertEqual(row_audio.price_from, Decimal("500.00"))
        self.assertIsNotNone(row_audio.pick)

    def test_brand_list(self):
        """brand_list returns allow-listed brands with real listing counts."""
        brands = brand_list(max_brands=10)
        brand_names = [b.name for b in brands]
        self.assertIn("boAt", brand_names)
        self.assertIn("Logitech", brand_names)
        boat_item = next(b for b in brands if b.name == "boAt")
        self.assertEqual(boat_item.product_count, 5)

    def test_eligible_cutout_products(self):
        """A product is eligible for headline cutout only if it has an image and is purchasable."""
        # Unpurchasable product
        unpurchasable = Product.objects.create(
            category=self.cat_audio,
            sku="NO-PRICE",
            slug="no-price",
            source_asin="B00UNPURCHASABLE",
            raw_name="Unpriced",
            display_name="Unpriced",
            selling_price=None,
            is_available=True,
        )
        ProductMedia.objects.create(
            product=unpurchasable,
            media_type="image",
            external_image_url="https://example.com/test.jpg",
        )

        # No image product
        no_img = Product.objects.create(
            category=self.cat_audio,
            sku="NO-IMG",
            slug="no-img",
            source_asin="B00NOIMG",
            raw_name="No Image",
            display_name="No Image",
            selling_price=Decimal("100.00"),
            is_available=True,
        )

        candidates = [unpurchasable, no_img, self.audio_prods[0], self.audio_prods[1]]
        cutouts = eligible_cutout_products(candidates, max_cutouts=3)
        self.assertEqual(len(cutouts), 2)
        self.assertEqual(cutouts[0], self.audio_prods[0])
        self.assertEqual(cutouts[1], self.audio_prods[1])

    def test_query_efficiency(self):
        """hero_products and home_chapters execute within small, fixed query budgets."""
        # hero_products query count = 4 (collection, products, prefetch media, prefetch specs)
        with self.assertNumQueries(4):
            hero = hero_products(n=3)
            self.assertTrue(len(hero.products) >= 2)

        # home_chapters query count = 8 (categories, collections, and 3 queries per category for picks/media/specs)
        with self.assertNumQueries(8):
            chapters = home_chapters(max_chapters=6)
            self.assertEqual(len(chapters), 2)
