"""
Semantic HTML, Accessibility, and Markup Quality Verification Test Suite.
Uses standard library HTMLParser to strictly enforce:
- Exactly one <h1> per page.
- Mandatory landmarks (<header>, <main id="main-content">, <footer>).
- Accessible skip-to-content link targeting #main-content.
- All <img> elements have alt, width, and height attributes.
- No inline JavaScript event handlers (onclick, onsubmit, onchange, etc.).
- No placeholder "TODO" or "lorem ipsum" text.
"""

from decimal import Decimal
from html.parser import HTMLParser
from typing import List, Tuple

from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import Category, Product
from apps.inventory.models import Inventory


class PageSemanticParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.h1_count = 0
        self.has_skip_link = False
        self.has_header = False
        self.has_main = False
        self.main_id_valid = False
        self.has_footer = False
        self.images: List[dict] = []
        self.inline_event_handlers: List[Tuple[str, str]] = []

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)

        if tag == "h1":
            self.h1_count += 1
        elif tag == "header":
            self.has_header = True
        elif tag == "main":
            self.has_main = True
            if attr_dict.get("id") == "main-content":
                self.main_id_valid = True
        elif tag == "footer":
            self.has_footer = True
        elif tag == "a" and attr_dict.get("href") == "#main-content":
            self.has_skip_link = True
        elif tag == "img":
            self.images.append({
                "src": attr_dict.get("src", ""),
                "has_alt": "alt" in attr_dict,
                "alt": attr_dict.get("alt", ""),
                "has_width": "width" in attr_dict,
                "has_height": "height" in attr_dict,
            })

        for k, v in attrs:
            if k.lower().startswith("on"):
                self.inline_event_handlers.append((k, v))


class SemanticHTMLComplianceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(
            name="Earphones & Headphones",
            slug="earphones-headphones",
            accent_key="earphones-headphones",
            gst_rate=Decimal("18.00"),
            display_order=1,
            description="High fidelity acoustic monitors.",
        )
        cls.product = Product.objects.create(
            category=cls.category,
            sku="SKU-SEM-001",
            slug="hd650-semantic",
            raw_name="Sennheiser HD 650 Audiophile Open Back Dynamic Headphones",
            display_name="Sennheiser HD 650 Audiophile Headphones",
            selling_price=Decimal("29990.00"),
            mrp=Decimal("34990.00"),
            is_available=True,
        )
        Inventory.objects.create(product=cls.product, quantity=5)

    def _parse_and_verify_page(self, path: str):
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200, f"Page {path} returned status {response.status_code}")

        html_content = response.content.decode("utf-8")

        # 1. No placeholder text
        self.assertNotIn("TODO", html_content, f"Page {path} contains 'TODO'")
        self.assertNotIn("lorem ipsum", html_content.lower(), f"Page {path} contains 'lorem ipsum'")

        parser = PageSemanticParser()
        parser.feed(html_content)

        # 2. Exactly one <h1>
        self.assertEqual(parser.h1_count, 1, f"Page {path} must have exactly one <h1>, found {parser.h1_count}")

        # 3. Core landmarks & skip link
        self.assertTrue(parser.has_skip_link, f"Page {path} missing skip link targeting #main-content")
        self.assertTrue(parser.has_header, f"Page {path} missing <header> landmark")
        self.assertTrue(parser.has_main, f"Page {path} missing <main> landmark")
        self.assertTrue(parser.main_id_valid, f"Page {path} <main> element missing id='main-content'")
        self.assertTrue(parser.has_footer, f"Page {path} missing <footer> landmark")

        # 4. Images have alt, width, height
        for img in parser.images:
            self.assertTrue(img["has_alt"], f"Page {path} has <img> missing alt attribute: {img['src']}")
            self.assertTrue(img["has_width"], f"Page {path} has <img> missing width attribute: {img['src']}")
            self.assertTrue(img["has_height"], f"Page {path} has <img> missing height attribute: {img['src']}")

        # 5. No inline event handlers
        self.assertEqual(
            len(parser.inline_event_handlers),
            0,
            f"Page {path} contains inline event handlers: {parser.inline_event_handlers}",
        )

    def test_semantic_compliance_across_public_storefront(self):
        paths_to_verify = [
            "/",
            "/categories/",
            f"/c/{self.category.slug}/",
            f"/p/{self.product.slug}/",
            "/brands/",
            "/cart/",
            "/legal/terms/",
            "/legal/privacy/",
            "/legal/shipping/",
            "/legal/refunds/",
            "/orders/track/",
            "/accounts/login/",
            "/accounts/signup/",
        ]
        for path in paths_to_verify:
            with self.subTest(path=path):
                self._parse_and_verify_page(path)
