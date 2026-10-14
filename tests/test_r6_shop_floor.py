"""
Unit and regression tests for Phase R6: The Shop Floor.
Validates all changed behaviors per WP8.2:
1. Brand parsing (multi-token, canonical casing, leading symbols stripped, model preservation).
2. display_name (clean model preservation, brand never duplicated).
3. Budget search and price bracket filter.
4. Filter inputs reflecting URL parameters and autocomplete="off".
5. Stock badge rule (only "Only N left" and "Out of stock"; "In stock" removed).
6. Shelf markup and honest attribution.
7. No pinned stage scroll-hijack classes.
8. Distinct admin app verbose names.
9. SRI and crossorigin attributes on CDN scripts.
10. Strict host allowlist in CSP script-src.
11. Local vendored fallback loader presence.
12. INR currency formatting on admin revenue.
"""

from decimal import Decimal
from pathlib import Path
import re
from django.apps import apps
from django.conf import settings
from django.template import Context, Template
from django.test import TestCase, Client
from django.urls import reverse

from apps.catalog.models import Category, Product
from apps.catalog.services.brands import detect_brand
from apps.catalog.services.parsing import clean_display_name
from apps.inventory.models import Inventory


class R6ShopFloorRegressionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(
            name="Smartphones",
            slug="smartphones",
            accent_key="smartphones",
            display_order=1,
            is_active=True,
        )
        cls.p1 = Product.objects.create(
            category=cls.category,
            sku="R6-PHONE-01",
            slug="redmi-9-sporty-orange-64gb",
            source_asin="B08696ZPHF",
            raw_name="Redmi 9 (Sporty Orange, 64 GB) (4 GB RAM)",
            display_name="Redmi 9 (Sporty Orange, 64 GB)",
            parsed_brand="Redmi",
            selling_price=Decimal("8999.00"),
            mrp=Decimal("10999.00"),
            is_available=True,
        )
        cls.inv1 = Inventory.objects.create(
            product=cls.p1,
            quantity=3,
            low_stock_threshold=5,
        )

        cls.p2 = Product.objects.create(
            category=cls.category,
            sku="R6-PHONE-02",
            slug="cp-plus-4mp-smart-security-camera",
            source_asin="B08R6R7890",
            raw_name="CP PLUS 4MP Smart Security Camera with 360 Pan Tilt",
            display_name="CP PLUS 4MP Smart Security Camera",
            parsed_brand="CP PLUS",
            selling_price=Decimal("2499.00"),
            mrp=Decimal("3500.00"),
            is_available=True,
        )
        cls.inv2 = Inventory.objects.create(
            product=cls.p2,
            quantity=50,
            low_stock_threshold=5,
        )

        cls.p3 = Product.objects.create(
            category=cls.category,
            sku="R6-PHONE-03",
            slug="boat-rockerz-450-bluetooth-on-ear-headphones",
            source_asin="B07XVMG123",
            raw_name="boAt Rockerz 450 Bluetooth On Ear Headphones",
            display_name="boAt Rockerz 450 Bluetooth On Ear Headphones",
            parsed_brand="boAt",
            selling_price=Decimal("1299.00"),
            mrp=Decimal("3990.00"),
            is_available=False,
        )
        cls.inv3 = Inventory.objects.create(
            product=cls.p3,
            quantity=0,
            low_stock_threshold=5,
        )

    # 1. Brand parsing
    def test_brand_parsing_multi_token_canonical_casing(self):
        self.assertEqual(detect_brand("CP PLUS 4MP Smart Wi-Fi Camera"), "CP PLUS")
        self.assertEqual(detect_brand("Echo Dot (4th Gen) Smart speaker with Alexa"), "Echo")
        self.assertEqual(detect_brand("JBL Go 3 Wireless Ultra Portable Bluetooth Speaker"), "JBL")

    def test_brand_parsing_strips_leading_symbols(self):
        self.assertEqual(detect_brand("®Redmi 9A Sport (Carbon Black)"), "Redmi")
        self.assertEqual(detect_brand("™Sony WH-1000XM4 Noise Cancelling"), "Sony")
        self.assertEqual(detect_brand('"boAt" Bassheads 100 in-Ear'), "boAt")
        self.assertEqual(detect_brand("•JBL Tune 510BT Wireless"), "JBL")

    # 2. display_name clean model preservation
    def test_display_name_preserves_model_without_brand_duplication(self):
        cleaned = clean_display_name("Redmi 9 (Sporty Orange, 64 GB) (4 GB RAM)", "Redmi")
        self.assertIn("Redmi 9", cleaned)
        # Template filter strip_brand should preserve "Redmi 9" so the model is not reduced to a naked digit
        t = Template("{% load core_tags %}{{ name|strip_brand:brand }}")
        rendered = t.render(Context({"name": cleaned, "brand": "Redmi"})).strip()
        self.assertEqual(rendered, cleaned)
        self.assertNotIn("Redmi Redmi", rendered)

    # 3. Budget search filter
    def test_budget_search_filter(self):
        client = Client()
        # Filter for products between 1000 and 3000 (should return CP PLUS and boAt)
        response = client.get(reverse("category_detail", kwargs={"slug": self.category.slug}), {
            "min_price": "1000",
            "max_price": "3000",
        })
        self.assertEqual(response.status_code, 200)
        products = response.context["page_obj"].object_list
        for p in products:
            self.assertGreaterEqual(p.selling_price, Decimal("1000"))
            self.assertLessEqual(p.selling_price, Decimal("3000"))

    # 4. Filters reflecting the URL and autocomplete="off"
    def test_filters_reflect_url_and_autocomplete_off(self):
        client = Client()
        response = client.get(reverse("category_detail", kwargs={"slug": self.category.slug}), {
            "min_price": "1500",
            "max_price": "9000",
            "brand": "Redmi",
        })
        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8")
        # Filter inputs must have autocomplete="off"
        self.assertIn('name="min_price" id="filter-min-price" class="form-control" value="1500" autocomplete="off"', html)
        self.assertIn('name="max_price" id="filter-max-price" class="form-control" value="9000" autocomplete="off"', html)
        self.assertIn('id="filter-brand" class="form-control" autocomplete="off"', html)

    # 5. Stock badge rule
    def test_stock_badge_rule(self):
        t = Template('{% include "includes/stock_badge.html" with product=product %}')

        # Low stock: "Only 3 left"
        low_html = t.render(Context({"product": self.p1}))
        self.assertIn("Only 3 left", low_html)
        self.assertNotIn("In Stock", low_html)

        # High stock (50): no badge rendered, specifically NO "In Stock"
        high_html = t.render(Context({"product": self.p2}))
        self.assertEqual(high_html.strip(), "")
        self.assertNotIn("In Stock", high_html)

        # Out of stock (0): "Out of Stock"
        out_html = t.render(Context({"product": self.p3}))
        self.assertIn("Out of Stock", out_html)
        self.assertNotIn("In Stock", out_html)

    # 6. Shelf markup and honest attribution
    def test_shelf_markup_and_honest_attribution(self):
        client = Client()
        response = client.get(reverse("category_detail", kwargs={"slug": self.category.slug}))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8")
        # Category page shows honest attribution for most-rated picks
        self.assertIn("Selected by number of ratings on Amazon", html)

    # 7. No pinned classes on storefront
    def test_no_pinned_stage_classes_on_storefront(self):
        client = Client()
        response = client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8")
        # Zero pinned stage scroll-hijack classes
        self.assertNotIn("pinned-stage", html)
        self.assertNotIn("scroll-trap", html)
        self.assertNotIn("hero-pin-container", html)

    # 8. Admin distinct verbose names
    def test_admin_app_distinct_verbose_names(self):
        allauth_app = apps.get_app_config("account")
        accounts_app = apps.get_app_config("accounts")
        self.assertNotEqual(allauth_app.verbose_name, accounts_app.verbose_name)
        self.assertIn("Allauth", allauth_app.verbose_name)
        self.assertIn("Customer Accounts", accounts_app.verbose_name)

    # 9. SRI attributes on CDN scripts
    def test_sri_and_crossorigin_on_cdn_scripts(self):
        base_html = (Path(settings.BASE_DIR) / "templates" / "base.html").read_text(encoding="utf-8")
        # Any script tag with cdnjs or jsdelivr must have integrity="sha384-..." and crossorigin="anonymous"
        cdn_scripts = re.findall(r'<script[^>]+src=["\'](https?://(?:cdnjs\.cloudflare\.com|cdn\.jsdelivr\.net)[^"\']+)["\'][^>]*>', base_html)
        self.assertGreater(len(cdn_scripts), 0, "Expected at least one CDN script tag in base.html")
        for tag_match in re.finditer(r'<script[^>]+src=["\']https?://(?:cdnjs\.cloudflare\.com|cdn\.jsdelivr\.net)[^"\']+["\'][^>]*>', base_html):
            tag = tag_match.group(0)
            self.assertIn('integrity="sha384-', tag, f"Missing integrity attribute in: {tag}")
            self.assertIn('crossorigin="anonymous"', tag, f"Missing crossorigin attribute in: {tag}")
            self.assertIn("defer", tag, f"Missing defer attribute in: {tag}")

    # 10. CSP lists only the two CDN hosts
    def test_csp_lists_only_allowed_cdn_hosts(self):
        csp_scripts = settings.CONTENT_SECURITY_POLICY["DIRECTIVES"]["script-src"]
        allowed_hosts = {
            "'self'",
            "https://checkout.razorpay.com",
            "https://cdnjs.cloudflare.com",
            "https://cdn.jsdelivr.net",
            "http://localhost:5173",  # Local Vite development server
        }
        for item in csp_scripts:
            self.assertIn(item, allowed_hosts, f"Unauthorized script host in CSP: {item}")
        # Rule F.1: exactly these two CDN hosts and no others
        cdn_hosts = {h for h in csp_scripts if "cdn" in h}
        self.assertEqual(cdn_hosts, {"https://cdnjs.cloudflare.com", "https://cdn.jsdelivr.net"})

    # 11. Local vendored fallback loader presence
    def test_cdn_fallback_loader_presence(self):
        fallback_js = Path(settings.BASE_DIR) / "static" / "vendor" / "gsap" / "cdn_fallback.js"
        self.assertTrue(fallback_js.exists(), "static/vendor/gsap/cdn_fallback.js must exist")
        content = fallback_js.read_text(encoding="utf-8")
        self.assertIn("2500", content, "Fallback loader must check after 2500ms")
        self.assertIn("window.gsap", content)
        self.assertIn("/static/vendor/gsap/gsap.min.js", content)
        self.assertIn("/static/vendor/gsap/ScrollTrigger.min.js", content)

    # 12. INR formatting in admin revenue
    def test_admin_revenue_inr_formatting(self):
        admin_index = (Path(settings.BASE_DIR) / "templates" / "admin" / "index.html").read_text(encoding="utf-8")
        self.assertIn("{{ dashboard.revenue_today|inr }}", admin_index)
