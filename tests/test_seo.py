"""
Comprehensive test suite for SEO, Metadata, Robots, Open Graph, and Sitemaps (WP3).
Verifies:
- Unique <title> and unique <meta name="description"> across storefront routes
- Canonical URLs on indexable pages
- Open Graph tags on editorial, category, and product sheets
- robots meta tags: noindex, nofollow on private/checkout/search flows
- JSON-LD structured data on product sheets without review/aggregateRating
- /robots.txt serving correct Disallow directives and Sitemap URL
- /sitemap.xml contains homepage, active categories, purchasable products, legal, and about
- Every URL referenced in /sitemap.xml returns HTTP 200 OK
"""

import json
import re
import xml.etree.ElementTree as ET
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from apps.catalog.models import Category, Product

User = get_user_model()


class SEOMetadataTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(
            name="Planar Headphones",
            slug="planar-headphones",
            accent_key="earphones-headphones",
            description="Precision planar-magnetic open back headphones for critical listening.",
            is_active=True,
            display_order=1,
        )
        self.product = Product.objects.create(
            raw_name="Hifiman Edition XS Planar Magnetic Headphones",
            display_name="Hifiman Edition XS Planar Magnetic Headphones",
            slug="hifiman-edition-xs",
            sku="HIF-EDITION-XS",
            source_asin="B09PH1N1M4",
            category=self.category,
            parsed_brand="Hifiman",
            selling_price=Decimal("26999.00"),
            mrp=Decimal("34999.00"),
            is_available=True,
            description="Open back planar magnetic headphones with stealth magnets and NEO supernano diaphragm.",
        )

    def test_robots_txt_content(self):
        """Verify /robots.txt disallows sensitive paths and provides sitemap."""
        resp = self.client.get("/robots.txt")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers["Content-Type"], "text/plain; charset=utf-8")
        content = resp.content.decode("utf-8")

        self.assertIn("User-agent: *", content)
        self.assertIn("Disallow: /cart/", content)
        self.assertIn("Disallow: /checkout/", content)
        self.assertIn("Disallow: /account/", content)
        self.assertIn("Disallow: /orders/", content)
        self.assertIn("Disallow: /search/", content)
        self.assertIn("Sitemap:", content)
        self.assertIn("/sitemap.xml", content)

    def test_sitemap_xml_and_all_urls_return_200(self):
        """Verify /sitemap.xml generates valid XML and all listed URLs return 200."""
        resp = self.client.get("/sitemap.xml")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("application/xml", resp.headers["Content-Type"])

        # Parse XML
        root = ET.fromstring(resp.content)
        namespace = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        loc_elements = root.findall("ns:url/ns:loc", namespace)
        self.assertGreater(len(loc_elements), 0)

        urls = [loc.text for loc in loc_elements]

        # Verify key required URLs are in sitemap
        joined = " ".join(urls)
        self.assertTrue(any(u.endswith("/") or u.endswith(":8000/") for u in urls), "Home URL should be present")
        self.assertIn("/about/", joined)
        self.assertIn("/categories/", joined)
        self.assertIn("/legal/terms/", joined)
        self.assertIn("/legal/privacy/", joined)
        self.assertIn("/legal/shipping/", joined)
        self.assertIn("/legal/refunds/", joined)
        self.assertIn(f"/c/{self.category.slug}/", joined)
        self.assertIn(f"/p/{self.product.slug}/", joined)

        # Check every URL returns 200
        for full_url in urls:
            path = re.sub(r"^https?://[^/]+", "", full_url)
            with self.subTest(path=path):
                page_resp = self.client.get(path)
                self.assertEqual(
                    page_resp.status_code,
                    200,
                    f"Sitemap URL {path} returned status {page_resp.status_code}",
                )

    def test_robots_meta_tags_on_private_pages(self):
        """Verify noindex, nofollow is present on utility and private pages."""
        private_paths = [
            "/cart/",
            "/checkout/",
            "/orders/track/",
            "/search/?q=headphones",
            "/accounts/login/",
            "/accounts/signup/",
        ]
        for path in private_paths:
            with self.subTest(path=path):
                resp = self.client.get(path)
                self.assertIn(resp.status_code, [200, 302])
                if resp.status_code == 200:
                    html = resp.content.decode("utf-8")
                    self.assertIn(
                        'name="robots" content="noindex, nofollow"',
                        html,
                        f"Expected noindex, nofollow in {path}",
                    )

    def test_open_graph_tags_on_catalog_pages(self):
        """Verify Open Graph tags exist on editorial, category, and product pages."""
        paths = [
            "/",
            f"/c/{self.category.slug}/",
            f"/p/{self.product.slug}/",
            "/about/",
        ]
        for path in paths:
            with self.subTest(path=path):
                resp = self.client.get(path)
                self.assertEqual(resp.status_code, 200)
                html = resp.content.decode("utf-8")
                self.assertIn('property="og:title"', html)
                self.assertIn('property="og:description"', html)
                self.assertIn('property="og:url"', html)
                self.assertIn('property="og:type"', html)

    def test_json_ld_on_product_page_no_reviews(self):
        """
        Verify JSON-LD on product sheet conforms to schema.org/Product
        and contains NO review or aggregateRating.
        """
        resp = self.client.get(f"/p/{self.product.slug}/")
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode("utf-8")

        # Extract JSON-LD script block
        match = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
        self.assertIsNotNone(match, "JSON-LD script block missing on product detail page")

        ld_data = json.loads(match.group(1))
        self.assertEqual(ld_data.get("@type"), "Product")
        self.assertEqual(ld_data.get("name"), self.product.display_name)
        self.assertEqual(ld_data.get("sku"), self.product.sku)
        self.assertEqual(ld_data.get("offers", {}).get("priceCurrency"), "INR")
        self.assertEqual(ld_data.get("offers", {}).get("price"), str(self.product.selling_price))

        # Strictly assert NO review or aggregateRating (Honesty Rule)
        self.assertNotIn("aggregateRating", ld_data)
        self.assertNotIn("review", ld_data)

    def test_canonical_urls_without_query_parameters(self):
        """Verify canonical URLs strip transient query strings."""
        resp = self.client.get(f"/c/{self.category.slug}/?sort=price_asc&page=1")
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode("utf-8")
        canonical_match = re.search(r'<link rel="canonical" href="([^"]+)">', html)
        self.assertIsNotNone(canonical_match)
        canonical_url = canonical_match.group(1)
        self.assertNotIn("sort=", canonical_url)
        self.assertNotIn("page=", canonical_url)
        self.assertTrue(canonical_url.endswith(f"/c/{self.category.slug}/"))

    def test_unique_title_and_meta_description_across_storefront_routes(self):
        """Crawl key public pages and verify each has unique title and meta description."""
        public_routes = [
            "/",
            "/about/",
            "/categories/",
            "/brands/",
            f"/c/{self.category.slug}/",
            f"/p/{self.product.slug}/",
            "/legal/terms/",
            "/legal/privacy/",
            "/legal/shipping/",
            "/legal/refunds/",
        ]

        titles = set()
        descriptions = set()

        for route in public_routes:
            with self.subTest(route=route):
                resp = self.client.get(route)
                self.assertEqual(resp.status_code, 200)
                html = resp.content.decode("utf-8")

                title_match = re.search(r"<title>(.*?)</title>", html)
                self.assertIsNotNone(title_match, f"Missing <title> on {route}")
                title = title_match.group(1).strip()
                self.assertNotIn(title, titles, f"Duplicate <title> '{title}' on {route}")
                titles.add(title)

                desc_match = re.search(r'<meta name="description" content="([^"]+)"', html)
                self.assertIsNotNone(desc_match, f"Missing <meta name='description'> on {route}")
                desc = desc_match.group(1).strip()
                self.assertNotIn(desc, descriptions, f"Duplicate meta description on {route}")
                descriptions.add(desc)
