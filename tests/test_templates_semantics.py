"""
Semantic HTML, Accessibility, Design System Tokens, and Markup Quality Verification Test Suite.
Enforces Phase 4 Design System Quality Gates:
- Exactly one <h1> per page.
- Mandatory landmarks (<header>, <main id="main-content">, <footer>).
- Accessible skip-to-content link targeting #main-content.
- All <img> elements have alt, width, and height attributes.
- No inline JavaScript event handlers (onclick, onsubmit, onchange, etc.).
- No placeholder "TODO" or "lorem ipsum" text.
- Heading hierarchy sanity (no skipped levels like h1 -> h3).
- No hardcoded hex/rgb colors or pixel font-sizes in template style attributes.
- 100% synchronization between database Category accent keys and CSS [data-world] tokens.
"""

from decimal import Decimal
from html.parser import HTMLParser
from pathlib import Path
import re
from typing import List, Tuple, Set

from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import Category, Product
from apps.inventory.models import Inventory


HEX_COLOR_PATTERN = re.compile(r'#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b')
RGB_COLOR_PATTERN = re.compile(r'\b(?:rgb|rgba|hsl|hsla)\s*\(')
PX_FONT_SIZE_PATTERN = re.compile(r'font-size\s*:\s*\d+px\b', re.IGNORECASE)
DATA_WORLD_PATTERN = re.compile(r'\[data-world="([^"]+)"\]')


class PageSemanticParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.h1_count = 0
        self.headings: List[int] = []
        self.has_skip_link = False
        self.has_header = False
        self.has_main = False
        self.main_id_valid = False
        self.has_footer = False
        self.images: List[dict] = []
        self.inline_event_handlers: List[Tuple[str, str]] = []
        self.form_inputs: List[dict] = []
        self.labels_for: Set[str] = set()

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)

        if tag == "h1":
            self.h1_count += 1
            self.headings.append(1)
        elif tag in ("h2", "h3", "h4", "h5", "h6"):
            self.headings.append(int(tag[1]))
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
        elif tag == "label" and "for" in attr_dict:
            self.labels_for.add(attr_dict["for"])
        elif tag in ("input", "select", "textarea"):
            input_type = attr_dict.get("type", "text").lower()
            if input_type not in ("hidden", "submit", "button"):
                self.form_inputs.append({
                    "tag": tag,
                    "type": input_type,
                    "id": attr_dict.get("id"),
                    "name": attr_dict.get("name"),
                    "has_label": bool(attr_dict.get("aria-label") or attr_dict.get("aria-labelledby")),
                })

        for k, v in attrs:
            if k.lower().startswith("on"):
                self.inline_event_handlers.append((k, v))


class SemanticHTMLComplianceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create all 10 frozen monograph categories for test fidelity
        cls.categories = []
        frozen_worlds = [
            ("Earphones & Headphones", "earphones-headphones"),
            ("Speakers", "speakers"),
            ("Smartphones", "smartphones"),
            ("Smartwatches & Bands", "smartwatches-bands"),
            ("Cameras", "cameras"),
            ("TVs & Displays", "tvs"),
            ("Keyboards & Mice", "keyboards-mice"),
            ("Cables & Chargers", "cables-chargers-powerbanks"),
            ("Cases & Protectors", "cases-protectors"),
            ("Other Accessories", "other"),
        ]
        for idx, (name, slug) in enumerate(frozen_worlds, start=1):
            cat = Category.objects.create(
                name=name,
                slug=slug,
                accent_key=slug,
                gst_rate=Decimal("18.00"),
                display_order=idx,
                description=f"Specialized {name} world.",
            )
            cls.categories.append(cat)

        cls.category = cls.categories[0]
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

        # 3. Heading hierarchy: no skipped levels
        for i in range(len(parser.headings) - 1):
            curr_lvl = parser.headings[i]
            next_lvl = parser.headings[i + 1]
            if next_lvl > curr_lvl:
                self.assertLessEqual(
                    next_lvl,
                    curr_lvl + 1,
                    f"Page {path} skips heading level from h{curr_lvl} to h{next_lvl}",
                )

        # 4. Core landmarks & skip link
        self.assertTrue(parser.has_skip_link, f"Page {path} missing skip link targeting #main-content")
        self.assertTrue(parser.has_header, f"Page {path} missing <header> landmark")
        self.assertTrue(parser.has_main, f"Page {path} missing <main> landmark")
        self.assertTrue(parser.main_id_valid, f"Page {path} <main> element missing id='main-content'")
        self.assertTrue(parser.has_footer, f"Page {path} missing <footer> landmark")

        # 5. Images have alt, width, height
        for img in parser.images:
            self.assertTrue(img["has_alt"], f"Page {path} has <img> missing alt attribute: {img['src']}")
            self.assertTrue(img["has_width"], f"Page {path} has <img> missing width attribute: {img['src']}")
            self.assertTrue(img["has_height"], f"Page {path} has <img> missing height attribute: {img['src']}")

        # 6. No inline event handlers
        self.assertEqual(
            len(parser.inline_event_handlers),
            0,
            f"Page {path} contains inline event handlers: {parser.inline_event_handlers}",
        )

        # 7. Form inputs have accessible labels
        for inp in parser.form_inputs:
            has_explicit_label = inp["id"] in parser.labels_for if inp["id"] else False
            has_aria = inp["has_label"]
            self.assertTrue(
                has_explicit_label or has_aria,
                f"Page {path} has form control without accessible label: {inp}",
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

    def test_no_hardcoded_styles_in_templates(self):
        """
        Enforce that template files do not contain hardcoded hex colors, rgb/hsl,
        or inline pixel font-sizes in style attributes.
        """
        base_dir = Path(__file__).resolve().parent.parent
        templates_dir = base_dir / "templates"
        style_pattern = re.compile(r'style\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)

        violations = []
        for template_file in templates_dir.rglob("*.html"):
            # Email templates require inline styles for email client compatibility; admin & internal dev tools use custom UI
            if (
                "emails" in template_file.parts
                or ("account" in template_file.parts and "email" in template_file.parts)
                or "admin" in template_file.parts
                or "dev_outbox.html" in template_file.name
            ):
                continue
            content = template_file.read_text(encoding="utf-8")
            for match in style_pattern.finditer(content):
                style_value = match.group(1)
                if HEX_COLOR_PATTERN.search(style_value):
                    violations.append(f"{template_file.name}: hardcoded hex color in style '{style_value}'")
                if RGB_COLOR_PATTERN.search(style_value):
                    violations.append(f"{template_file.name}: functional rgb/hsl in style '{style_value}'")
                if PX_FONT_SIZE_PATTERN.search(style_value):
                    violations.append(f"{template_file.name}: inline pixel font-size in style '{style_value}'")

        self.assertEqual(
            len(violations),
            0,
            f"Templates contain illegal hardcoded styles: {violations}",
        )

    def test_data_world_tokens_sync(self):
        """
        Assert every [data-world] slug in CSS matches a Category accent key
        in the database and vice versa.
        """
        base_dir = Path(__file__).resolve().parent.parent
        tokens_file = base_dir / "frontend" / "css" / "tokens.css"
        self.assertTrue(tokens_file.exists(), "tokens.css not found")

        content = tokens_file.read_text(encoding="utf-8")
        css_worlds = set(DATA_WORLD_PATTERN.findall(content))

        db_worlds = set(Category.objects.values_list("accent_key", flat=True).distinct())

        self.assertEqual(
            css_worlds,
            db_worlds,
            f"Mismatch between CSS [data-world] slugs {css_worlds} and Category accent keys {db_worlds}",
        )
