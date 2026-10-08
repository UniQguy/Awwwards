"""
Unit tests for evidence-based category classification (Regression test for F-02).
"""

from django.test import SimpleTestCase
from apps.catalog.services.category_rules import classify_category


class CategoryRulesClassificationTests(SimpleTestCase):
    def test_phone_with_camera_and_display_specs_stays_smartphone(self):
        # Defect case from F-02: Redmi Note 10S with Super AMOLED and 64MP Camera
        title1 = "Redmi Note 10S (Cosmic Purple, 6GB RAM, 128GB Storage) - Super Amoled Display / 64 MP Quad Camera / 6 Month Free Screen Replacement"
        self.assertEqual(classify_category(title1), "smartphones")

        title2 = "Redmi Note 9 (Aqua Green, 4GB RAM, 64GB Storage) - 48MP Quad Camera & Full HD+ Display"
        self.assertEqual(classify_category(title2), "smartphones")

        title3 = "Redmi 8A Dual (Sea Blue, 2GB RAM, 32GB Storage) – Dual Cameras & 5,000 mAH Battery"
        self.assertEqual(classify_category(title3), "smartphones")

        title4 = "Samsung Galaxy M13 (Aqua Green, 6GB, 128GB Storage) | 6000mAh Battery | Upto 12GB RAM with RAM Plus"
        self.assertEqual(classify_category(title4), "smartphones")

        title5 = "OnePlus Nord CE 2 Lite 5G (Black Dusk, 6GB RAM, 128GB Storage)"
        self.assertEqual(classify_category(title5), "smartphones")

    def test_fire_tv_stick_and_tv_accessories_are_not_tvs(self):
        # Defect case from F-02: Fire TV Stick shown in Displays and Televisions
        title1 = "Fire TV Stick with Alexa Voice Remote (includes TV and app controls) | HD streaming device"
        self.assertEqual(classify_category(title1), "other")

        title2 = "Fire TV Stick 4K with Alexa Voice Remote"
        self.assertEqual(classify_category(title2), "other")

        title3 = "Google Chromecast 3 Media Streaming Device"
        self.assertEqual(classify_category(title3), "other")

        title4 = "Universal TV Wall Mount Bracket for 32 to 55 inch LED LCD TVs"
        self.assertEqual(classify_category(title4), "other")

        title5 = "Universal Remote Control for Samsung Smart TV"
        self.assertEqual(classify_category(title5), "other")

    def test_memory_cards_and_camera_accessories_are_not_cameras(self):
        # Defect case from F-02: SanDisk SD cards shown in Cameras
        title1 = "SanDisk 128GB Ultra microSDXC UHS-I Memory Card 120MB/s for Cameras"
        self.assertEqual(classify_category(title1), "other")

        title2 = "SanDisk Extreme PRO SDXC UHS-I Card 64GB for DSLR Cameras"
        self.assertEqual(classify_category(title2), "other")

        title3 = "USB 3.0 High Speed SD Card Reader"
        self.assertEqual(classify_category(title3), "other")

        title4 = "Professional Aluminium Tripod for DSLR Camera with Ball Head"
        self.assertEqual(classify_category(title4), "other")

        title5 = "Padded Camera Shoulder Bag for DSLR and Lens"
        self.assertEqual(classify_category(title5), "other")

    def test_genuine_televisions_match_tvs(self):
        title1 = "Redmi 80 cm (32 inches) Android 11 Series HD Ready Smart LED TV"
        self.assertEqual(classify_category(title1), "tvs")

        title2 = "Sony Bravia 108 cm (43 inches) 4K Ultra HD Smart LED Google TV"
        self.assertEqual(classify_category(title2), "tvs")

        title3 = "OnePlus 126 cm (50 inches) Y Series 4K Ultra HD Smart Android LED TV"
        self.assertEqual(classify_category(title3), "tvs")

        title4 = "LG 27 inch 4K-UHD IPS HDR Gaming Monitor"
        self.assertEqual(classify_category(title4), "tvs")

    def test_genuine_cameras_match_cameras(self):
        title1 = "Canon EOS 1500D 24.1 Digital SLR Camera (Black) with EF S18-55 is II Lens"
        self.assertEqual(classify_category(title1), "cameras")

        title2 = "Sony Alpha ILCE-6100L 24.2 MP Mirrorless Digital Camera with 16-50 mm Lens"
        self.assertEqual(classify_category(title2), "cameras")

        title3 = "GoPro HERO10 Black - Waterproof Action Camera with Front LCD"
        self.assertEqual(classify_category(title3), "cameras")

    def test_smartwatch_straps_are_accessories_not_smartwatches(self):
        title1 = "Replacement Silicone Strap Band for Apple Watch 44mm 42mm"
        self.assertEqual(classify_category(title1), "cases-protectors")

        title2 = "Stainless Steel Metal Mesh Strap for Samsung Galaxy Watch 4"
        self.assertEqual(classify_category(title2), "cases-protectors")

        # But genuine smartwatches match smartwatches-bands
        title3 = "Noise ColorFit Pulse Smartwatch with 1.4\" Full Touch HD Display"
        self.assertEqual(classify_category(title3), "smartwatches-bands")

        title4 = "boAt Wave Lite Smartwatch with 1.69\" HD Display"
        self.assertEqual(classify_category(title4), "smartwatches-bands")

    def test_keyboards_and_mice_combos(self):
        title1 = "Logitech MK215 Wireless Keyboard and Mouse Combo"
        self.assertEqual(classify_category(title1), "keyboards-mice")

        title2 = "Keychron K2 Wireless Mechanical Keyboard (Version 2)"
        self.assertEqual(classify_category(title2), "keyboards-mice")

    def test_earphones_with_charging_features_stay_earphones(self):
        title1 = "Boult Audio X1 Buds True Wireless in Ear Earbuds with 24H Playtime, Type-C Fast Charging"
        self.assertEqual(classify_category(title1), "earphones-headphones")

        title2 = "OnePlus Bullets Z2 Bluetooth Wireless in Ear Earphones with Mic, 10 Mins Charge"
        self.assertEqual(classify_category(title2), "earphones-headphones")

    def test_powerbanks_and_chargers_stay_cables_chargers(self):
        title1 = "Mi 10000mAH Li-Polymer Power Bank 3i with 18W Fast Charging"
        self.assertEqual(classify_category(title1), "cables-chargers-powerbanks")

        title2 = "Amazon Basics 65W GaN Dual Port Fast Wall Charger"
        self.assertEqual(classify_category(title2), "cables-chargers-powerbanks")
