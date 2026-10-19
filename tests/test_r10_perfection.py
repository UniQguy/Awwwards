"""
Comprehensive test suite for Phase R10: Synchronized Hero/Anatomy, Sub-Type Comparison,
24-Category Taxonomy Grid, Vector Search, AI Concierge & UI Collision Remediation.
"""

import json
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import Category, Product, ProductSpecification
from apps.catalog.services.category_nav import (
    GRANULAR_24_TAXONOMY,
    get_24_granular_categories,
    get_sub_category_filter,
)
from apps.catalog.services.editorial import (
    get_flagship_anatomy_layers,
    hero_products,
)
from apps.catalog.services.spec_extractor import (
    classify_product_subtype,
    synthesize_category_specs,
)
from apps.core.services.ai_concierge import process_concierge_message
from apps.core.templatetags.core_tags import best_coupon_offer
from apps.inventory.models import Inventory
from apps.orders.models import Order, OrderItem
from apps.promotions.models import Coupon
from apps.search.services.search_service import (
    extract_natural_price_bounds,
)
from apps.search.services.vector_search import (
    invalidate_vector_index,
    vector_rank_products,
)

User = get_user_model()


class PhaseR10PerfectionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cache.clear()
        invalidate_vector_index()
        call_command("seed_pincodes", sample=True)

        # Seed categories
        cls.cat_cameras = Category.objects.create(name="Cameras & Optics", slug="cameras", is_active=True, display_order=1)
        cls.cat_phones = Category.objects.create(name="Smartphones & Devices", slug="smartphones", is_active=True, display_order=2)
        cls.cat_audio = Category.objects.create(name="Earphones & Headphones", slug="earphones-headphones", is_active=True, display_order=3)
        cls.cat_tvs = Category.objects.create(name="Displays & Televisions", slug="tvs", is_active=True, display_order=4)

        # 1. DSLR Photography Camera
        cls.dslr_cam = Product.objects.create(
            raw_name="Canon EOS 200D II DSLR Camera with EF-S 18-55mm IS STM Lens",
            display_name="Canon EOS 200D II DSLR Camera (Black)",
            slug="canon-eos-200d-ii-dslr",
            sku="CAM-CAN-200D",
            source_asin="B07RJWB548",
            category=cls.cat_cameras,
            parsed_brand="Canon",
            selling_price=Decimal("56990.00"),
            mrp=Decimal("62995.00"),
            is_available=True,
            search_text="canon eos 200d ii dslr camera 24 mp aps-c optical viewfinder 4k video",
        )

        # 2. Rival Mirrorless Camera in same price bracket (0.45x - 1.85x of ₹56,990)
        cls.mirrorless_cam = Product.objects.create(
            raw_name="Sony Alpha ILCE-6100L 24.2 MP Mirrorless Camera with 16-50mm Lens",
            display_name="Sony Alpha ILCE-6100L Mirrorless Camera",
            slug="sony-alpha-ilce-6100l",
            sku="CAM-SNY-A6100",
            source_asin="B07X64L82D",
            category=cls.cat_cameras,
            parsed_brand="Sony",
            selling_price=Decimal("61490.00"),
            mrp=Decimal("75990.00"),
            is_available=True,
            search_text="sony alpha 6100 mirrorless camera 24 mp real time eye af 4k video",
        )

        # 3. CCTV Security Camera (Sub-type: security camera, ₹2,960 - wildly different price and sub-type)
        cls.cctv_cam = Product.objects.create(
            raw_name="TP-Link Tapo C200 360 2MP 1080p Full HD Pan/Tilt Home Security Wi-Fi Smart Camera",
            display_name="TP-Link Tapo C200 Security Wi-Fi Camera",
            slug="tp-link-tapo-c200-cctv",
            sku="CAM-TPL-C200",
            source_asin="B07XLML2YS",
            category=cls.cat_cameras,
            parsed_brand="TP-Link",
            selling_price=Decimal("2960.00"),
            mrp=Decimal("3299.00"),
            is_available=True,
            search_text="tp-link tapo c200 cctv pan tilt 1080p full hd night vision surveillance security camera",
        )

        # 4. Premium Smartphone (Flagship)
        cls.phone_flagship = Product.objects.create(
            raw_name="Samsung Galaxy S23 Ultra 5G (Phantom Black, 256 GB)",
            display_name="Samsung Galaxy S23 Ultra 5G",
            slug="samsung-galaxy-s23-ultra-5g",
            sku="PHN-SAM-S23U",
            source_asin="B0BT9CXXXX",
            category=cls.cat_phones,
            parsed_brand="Samsung",
            selling_price=Decimal("124999.00"),
            mrp=Decimal("149999.00"),
            is_available=True,
            search_text="samsung galaxy s23 ultra 5g dynamic amoled 200 mp snapdragon 8 gen 2 spen",
        )

        # 5. Mid-range Smartphone
        cls.phone_mid = Product.objects.create(
            raw_name="OnePlus Nord CE 3 Lite 5G (Pastel Lime, 128 GB)",
            display_name="OnePlus Nord CE 3 Lite 5G",
            slug="oneplus-nord-ce-3-lite-5g",
            sku="PHN-OP-NORD3L",
            source_asin="B0BY8MC59S",
            category=cls.cat_phones,
            parsed_brand="OnePlus",
            selling_price=Decimal("19999.00"),
            mrp=Decimal("21999.00"),
            is_available=True,
            search_text="oneplus nord ce 3 lite 5g 108 mp 5000 mah 67w supervooc smartphone",
        )

        # 6. Flagship Over-Ear ANC Headphone
        cls.headphone_flagship = Product.objects.create(
            raw_name="Sony WH-1000XM5 Wireless Industry Leading Noise Cancelling Headphones",
            display_name="Sony WH-1000XM5 Wireless ANC Headphones",
            slug="sony-wh-1000xm5-headphones",
            sku="AUD-SNY-WH1000XM5",
            source_asin="B09XS7JWHH",
            category=cls.cat_audio,
            parsed_brand="Sony",
            selling_price=Decimal("28990.00"),
            mrp=Decimal("34990.00"),
            is_available=True,
            search_text="sony wh 1000xm5 wireless anc active noise cancelling bluetooth headphones ldac 30 hr battery",
        )

        # 7. TWS Earbuds
        cls.earbuds_tws = Product.objects.create(
            raw_name="OnePlus Nord Buds 2 TWS in-Ear Earbuds with 25dB Active Noise Cancellation",
            display_name="OnePlus Nord Buds 2 TWS Earbuds",
            slug="oneplus-nord-buds-2",
            sku="AUD-OP-NBUDS2",
            source_asin="B0BY8PYM22",
            category=cls.cat_audio,
            parsed_brand="OnePlus",
            selling_price=Decimal("2799.00"),
            mrp=Decimal("3299.00"),
            is_available=True,
            search_text="oneplus nord buds 2 tws wireless bluetooth in ear earbuds anc basswave",
        )

        # 8. 4K Television
        cls.tv_flagship = Product.objects.create(
            raw_name="LG 139 cm (55 inches) 4K Ultra HD Smart OLED TV 55C2PSC",
            display_name="LG 55-inch 4K Ultra HD Smart OLED TV",
            slug="lg-55-inch-oled-4k-tv",
            sku="TV-LG-OLED55C2",
            source_asin="B09YV4C89P",
            category=cls.cat_tvs,
            parsed_brand="LG",
            selling_price=Decimal("119990.00"),
            mrp=Decimal("189990.00"),
            is_available=True,
            search_text="lg 55 inch oled 4k ultra hd smart tv dolby vision atmos gen5 ai processor 120hz",
        )

        for p in [
            cls.dslr_cam, cls.mirrorless_cam, cls.cctv_cam,
            cls.phone_flagship, cls.phone_mid, cls.headphone_flagship,
            cls.earbuds_tws, cls.tv_flagship,
        ]:
            Inventory.objects.create(product=p, quantity=25)

        # Seed coupon
        now = timezone.now()
        cls.coupon = Coupon.objects.create(
            code="ELECTRO10",
            description="Flat 10% off on all electronics",
            discount_type=Coupon.TYPE_PERCENTAGE,
            discount_value=Decimal("10.00"),
            min_order_amount=Decimal("1000.00"),
            valid_from=now - timezone.timedelta(days=1),
            valid_until=now + timezone.timedelta(days=30),
            is_active=True,
        )

        # Seed test user & order for concierge tracking
        cls.user = User.objects.create_user(
            email="techbuyer@electrocart.test",
            password="TestPassword123!",
            full_name="Priya Sharma",
        )
        cls.order = Order.objects.create(
            order_number="ORD-20261020-TEST",
            user=cls.user,
            shipping_address_snapshot={
                "full_name": cls.user.full_name,
                "phone": "9876543210",
                "line1": "12 Tech Park Avenue",
                "city": "Ahmedabad",
                "state": "Gujarat",
                "pincode": "380001",
            },
            status=Order.STATUS_CONFIRMED,
            payment_status=Order.PAYMENT_STATUS_CAPTURED,
            subtotal=Decimal("56990.00"),
            tax_amount=Decimal("10258.20"),
            total_amount=Decimal("67248.20"),
        )
        OrderItem.objects.create(
            order=cls.order,
            product=cls.dslr_cam,
            product_title=cls.dslr_cam.display_name,
            product_sku=cls.dslr_cam.sku,
            quantity=1,
            unit_price=cls.dslr_cam.selling_price,
            mrp=cls.dslr_cam.mrp,
            taxable_value=Decimal("48296.61"),
            line_total=cls.dslr_cam.selling_price,
            hsn_code="852580",
            gst_rate=Decimal("18.00"),
        )

    def setUp(self):
        self.client = Client()

    # --- PILLAR 1: SYNCHRONIZED HERO / ANATOMY ---
    def test_pillar_1_flagship_curation_and_anatomy_layers(self):
        """Editorial hero_products must curate flagships >= 15000 and provide distinct anatomy layers."""
        flagships = hero_products(n=4)
        self.assertGreaterEqual(len(flagships), 1)
        for prod in flagships:
            self.assertGreaterEqual(prod.selling_price, Decimal("15000.00"))
            layers = get_flagship_anatomy_layers(prod)
            self.assertEqual(len(layers), 4)
            for layer in layers:
                self.assertIn("num", layer)
                self.assertIn("title", layer)
                self.assertIn("desc", layer)

    def test_pillar_1_homepage_renders_anatomy_and_flagship_picker(self):
        """Homepage renders 4 flagship selector pills and Chapter 02 anatomy stage."""
        resp = self.client.get(reverse("home"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Flagship Engineering Anatomy")
        self.assertContains(resp, "hero-flagships-data")

    # --- PILLAR 2: SUB-TYPE COMPARISON & CCTV SPEC FIX ---
    def test_pillar_2_subtype_classification(self):
        """Camera sub-types distinguish photography vs security cameras."""
        self.assertEqual(classify_product_subtype(self.dslr_cam), "camera_dslr_mirrorless")
        self.assertEqual(classify_product_subtype(self.mirrorless_cam), "camera_dslr_mirrorless")
        self.assertEqual(classify_product_subtype(self.cctv_cam), "camera_cctv_security")
        self.assertEqual(classify_product_subtype(self.headphone_flagship), "audio_over_ear")
        self.assertEqual(classify_product_subtype(self.earbuds_tws), "audio_tws")

    def test_pillar_2_cctv_never_receives_apsc_sensor(self):
        """Synthesized specs for CCTV cameras must never include APS-C sensor."""
        specs = synthesize_category_specs(
            {},
            title=self.cctv_cam.display_name,
            category_slug="cameras",
            price=self.cctv_cam.selling_price,
            brand=self.cctv_cam.parsed_brand,
        )
        sensor_spec = str(specs.get("sensor", ""))
        self.assertNotIn("APS-C", sensor_spec)
        self.assertIn("Night Vision", str(specs.get("night_vision", "")))

    def test_pillar_2_pdp_compare_excludes_cctv_from_dslr(self):
        """Viewing DSLR camera PDP must never suggest CCTV camera in comparable rivals."""
        resp = self.client.get(reverse("product_detail", kwargs={"slug": self.dslr_cam.slug}))
        self.assertEqual(resp.status_code, 200)
        # Sony mirrorless may appear as rival, but TP-Link Tapo CCTV camera must never appear
        self.assertNotContains(resp, "TP-Link Tapo C200")

    def test_pillar_2_compare_picker_workflow(self):
        """Adding products to compare list via /compare/add/<id>/ updates session compare list up to 4 items."""
        # Add 1st product
        resp = self.client.post(reverse("compare_add", kwargs={"product_id": self.dslr_cam.id}))
        self.assertEqual(resp.status_code, 302)
        compare_list = self.client.session.get("compare_tray", [])
        self.assertEqual(compare_list, [self.dslr_cam.id])

        # Add 2nd product
        resp2 = self.client.post(reverse("compare_add", kwargs={"product_id": self.mirrorless_cam.id}))
        self.assertEqual(resp2.status_code, 302)
        compare_list2 = self.client.session.get("compare_tray", [])
        self.assertEqual(compare_list2, [self.dslr_cam.id, self.mirrorless_cam.id])

        # View comparison page with 2 products
        comp_resp = self.client.get(reverse("compare_tray"))
        self.assertEqual(comp_resp.status_code, 200)
        self.assertContains(comp_resp, self.dslr_cam.display_name)
        self.assertContains(comp_resp, self.mirrorless_cam.display_name)

    # --- PILLAR 3: 24-CATEGORY TAXONOMY GRID & ROUTING ---
    def test_pillar_3_taxonomy_grid_and_sub_slug_filtering(self):
        """Category directory displays 24-category visual grid and /c/<slug>/?sub=<sub_slug> filters items."""
        cats = get_24_granular_categories()
        self.assertEqual(len(cats), 24)

        resp = self.client.get(reverse("category_list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "taxonomy-grid")
        self.assertContains(resp, "taxonomy-card")

        # Test subcategory filter on smartphones
        cat_resp = self.client.get(f"{reverse('category_detail', kwargs={'slug': 'smartphones'})}?sub=flagship-phones")
        self.assertEqual(cat_resp.status_code, 200)

    # --- PILLAR 4: PINCODE LOCAL CHECK & TOAST STACK ---
    def test_pillar_4_pincode_zero_messages_pollution(self):
        """Pincode checker returns JSON deliverability without adding to django messages."""
        resp = self.client.get(f"{reverse('shipping_estimate')}?pincode=380001", HTTP_ACCEPT="application/json")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("deliverable"))
        # Verify no messages in session
        messages = list(resp.wsgi_request._messages) if hasattr(resp.wsgi_request, "_messages") else []
        self.assertEqual(len(messages), 0)

    # --- PILLAR 5: VECTOR SEARCH & NATURAL PRICE INTENT ---
    def test_pillar_5_natural_price_intent_parser(self):
        """extract_natural_price_bounds correctly parses natural price bounds."""
        q1, min1, max1 = extract_natural_price_bounds("smartphones under 20000")
        self.assertEqual(max1, Decimal("20000"))
        self.assertIsNone(min1)
        self.assertEqual(q1, "smartphones")

        q2, min2, max2 = extract_natural_price_bounds("headphones between 5k and 15k")
        self.assertEqual(min2, Decimal("5000"))
        self.assertEqual(max2, Decimal("15000"))
        self.assertEqual(q2, "headphones")

    def test_pillar_5_vector_search_returns_ranked_products(self):
        """vector_rank_products returns non-empty similarity scores for relevant query."""
        scores = vector_rank_products("dslr camera 4k video", top_k=5)
        self.assertIn(self.dslr_cam.id, scores)

    # --- PILLAR 6: AI CONCIERGE & TECHNICAL ASSISTANT ---
    def test_pillar_6_ai_concierge_recommendation(self):
        """AI Concierge responds with product recommendations."""
        res = process_concierge_message("recommend best camera for photography")
        self.assertIn("reply", res)
        self.assertGreaterEqual(len(res.get("products", [])), 1)

    def test_pillar_6_ai_concierge_order_lookup(self):
        """AI Concierge looks up order status by order number."""
        res = process_concierge_message("where is order ORD-20261020-TEST")
        self.assertIn("ORD-20261020-TEST", res["reply"])
        self.assertIn("confirmed", res["reply"].lower())

    def test_pillar_6_ai_concierge_api_endpoint(self):
        """POST to /api/assistant/chat/ returns valid JSON response."""
        resp = self.client.post(
            reverse("assistant_chat_api"),
            data=json.dumps({"message": "what is your return policy"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("reply", data)
        self.assertIn("7-Day Replacement", data.get("reply", ""))

    # --- PILLAR 8: COUPON PRICE MICRO-BADGES ---
    def test_pillar_8_best_coupon_micro_badge(self):
        """best_coupon_offer template filter computes correct discounted price."""
        offer = best_coupon_offer(self.phone_mid)
        self.assertIsNotNone(offer)
        self.assertEqual(offer["code"], "ELECTRO10")
        # 10% off on 19999 = 17999.10 -> 17999
        self.assertEqual(offer["effective_price"], Decimal("17999.10"))
