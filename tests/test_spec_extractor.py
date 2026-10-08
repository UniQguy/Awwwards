"""
Unit tests for specification extraction service (Regression test for F-03).
"""

from django.test import SimpleTestCase
from apps.catalog.services.spec_extractor import (
    extract_specifications,
    parse_screen_size,
    parse_ram_and_storage,
)


class SpecExtractorTests(SimpleTestCase):
    def test_screen_size_prefers_explicit_inches(self):
        # Defect cases from F-03
        title1 = "Redmi 80 cm (32 inches) Android 11 Series HD Ready Smart LED TV"
        res1 = parse_screen_size(title1, category_slug="tvs")
        self.assertIsNotNone(res1)
        self.assertEqual(res1[2], '32"')

        title2 = "Sony Bravia 108 cm (43 inches) 4K Ultra HD Smart LED Google TV"
        res2 = parse_screen_size(title2, category_slug="tvs")
        self.assertIsNotNone(res2)
        self.assertEqual(res2[2], '43"')

        title3 = "OnePlus 126 cm (50 inches) Y Series 4K Ultra HD Smart Android LED TV"
        res3 = parse_screen_size(title3, category_slug="tvs")
        self.assertIsNotNone(res3)
        self.assertEqual(res3[2], '50"')

        title4 = 'Noise ColorFit Pulse Smartwatch 1.69" (4.29cm) HD Display'
        res4 = parse_screen_size(title4, category_slug="smartwatches-bands")
        self.assertIsNotNone(res4)
        self.assertEqual(res4[2], '1.69"')

    def test_screen_size_mixed_cases(self):
        self.assertEqual(parse_screen_size("43 inch Smart TV", "tvs")[2], '43"')
        self.assertEqual(parse_screen_size("43-inch LED TV", "tvs")[2], '43"')
        self.assertEqual(parse_screen_size('43" 4K TV', "tvs")[2], '43"')
        self.assertEqual(parse_screen_size("6.5 inch display phone", "smartphones")[2], '6.5"')
        self.assertEqual(parse_screen_size('1.69" display watch', "smartwatches-bands")[2], '1.69"')

    def test_screen_size_converts_cm_only_when_no_inches(self):
        # 108 cm converted: 108 / 2.54 = 42.519... -> 42.5"
        res = parse_screen_size("Sony Bravia 108 cm 4K Smart TV", category_slug="tvs")
        self.assertIsNotNone(res)
        self.assertEqual(res[2], '42.5"')

        # Never emit a cm number directly as inches
        self.assertNotEqual(res[2], '108"')

    def test_screen_size_range_sanity_drops_implausible_values(self):
        # TV screen size sanity: 15 to 120 in
        self.assertIsNone(parse_screen_size("Tiny 10 inch Pocket TV", category_slug="tvs"))
        self.assertIsNone(parse_screen_size("Huge 150 inch Stadium TV", category_slug="tvs"))

        # Phone screen size sanity: 3 to 8 in
        self.assertIsNone(parse_screen_size("Tiny 2.2 inch phone", category_slug="smartphones"))
        self.assertIsNone(parse_screen_size("Huge 12 inch phone", category_slug="smartphones"))

        # Watch display size sanity: 0.9 to 2.5 in
        self.assertIsNone(parse_screen_size("Huge 5 inch watch", category_slug="smartwatches-bands"))

    def test_ram_and_storage_disambiguation(self):
        title1 = "Redmi Note 10S (Cosmic Purple, 2GB RAM, 32GB Storage)"
        specs1 = {key: val for key, label, val in parse_ram_and_storage(title1, "smartphones")}
        self.assertEqual(specs1.get("ram"), "2 GB")
        self.assertEqual(specs1.get("storage"), "32 GB")

        title2 = "OnePlus Nord 2 (6GB + 128GB, Gray Sierra)"
        specs2 = {key: val for key, label, val in parse_ram_and_storage(title2, "smartphones")}
        self.assertEqual(specs2.get("ram"), "6 GB")
        self.assertEqual(specs2.get("storage"), "128 GB")

    def test_full_extract_specifications_dictionary(self):
        title = "Redmi 80 cm (32 inches) Android 11 Series HD Ready Smart LED TV"
        specs = extract_specifications(title, category_slug="tvs")
        self.assertIn("screen_size", specs)
        self.assertEqual(specs["screen_size"]["value"], '32"')
        self.assertIn("resolution", specs)
        self.assertEqual(specs["resolution"]["value"], "HD Ready")
