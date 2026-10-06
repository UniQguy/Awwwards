"""
Category classification rules for Electrocart catalog.

Applies ordered regex patterns ensuring accessories match before primary devices:
Cases/Protectors -> Cables/Chargers/Powerbanks -> Smartwatches/Bands ->
Keyboards/Mice -> Earphones/Headphones -> Speakers -> Smartphones -> Cameras -> TVs -> Other.
"""

from decimal import Decimal
import re
from typing import Dict, List, Tuple

CATEGORY_DEFINITIONS: List[Dict] = [
    {
        "slug": "cases-protectors",
        "name": "Cases & Protectors",
        "accent_key": "cases-protectors",
        "hsn_code": "3926",
        "gst_rate": Decimal("18.00"),
        "is_gst_rate_verified": True,
        "display_order": 9,
        "description": "Protective shells, tempered glass, ergonomic sleeves, and precision bumpers.",
    },
    {
        "slug": "cables-chargers-powerbanks",
        "name": "Cables, Chargers & Power",
        "accent_key": "cables-chargers-powerbanks",
        "hsn_code": "8504",
        "gst_rate": Decimal("18.00"),
        "is_gst_rate_verified": True,
        "display_order": 8,
        "description": "GaN fast chargers, braided USB-C cables, magnetic powerbanks, and power hubs.",
    },
    {
        "slug": "smartwatches-bands",
        "name": "Smartwatches & Wearables",
        "accent_key": "smartwatches-bands",
        "hsn_code": "9102",
        "gst_rate": Decimal("18.00"),
        "is_gst_rate_verified": True,
        "display_order": 4,
        "description": "Smart watches, fitness bands, sensory health monitors, and replacement bands.",
    },
    {
        "slug": "keyboards-mice",
        "name": "Keyboards & Pointers",
        "accent_key": "keyboards-mice",
        "hsn_code": "8471",
        "gst_rate": Decimal("18.00"),
        "is_gst_rate_verified": True,
        "display_order": 7,
        "description": "Mechanical tactile keyboards, ergonomic mice, desk mats, and wireless pointers.",
    },
    {
        "slug": "earphones-headphones",
        "name": "Earphones & Headphones",
        "accent_key": "earphones-headphones",
        "hsn_code": "8518",
        "gst_rate": Decimal("18.00"),
        "is_gst_rate_verified": True,
        "display_order": 1,
        "description": "High-fidelity studio monitors, active noise-cancelling headphones, and wireless earbuds.",
    },
    {
        "slug": "speakers",
        "name": "Acoustics & Speakers",
        "accent_key": "speakers",
        "hsn_code": "8518",
        "gst_rate": Decimal("18.00"),
        "is_gst_rate_verified": True,
        "display_order": 2,
        "description": "Architectural bookshelf speakers, Dolby Atmos soundbars, and portable acoustic units.",
    },
    {
        "slug": "smartphones",
        "name": "Smartphones & Devices",
        "accent_key": "smartphones",
        "hsn_code": "8517",
        "gst_rate": Decimal("18.00"),
        "is_gst_rate_verified": True,
        "display_order": 3,
        "description": "Flagship smartphones, cellular computing devices, and pocket communicators.",
    },
    {
        "slug": "cameras",
        "name": "Cameras & Optics",
        "accent_key": "cameras",
        "hsn_code": "8525",
        "gst_rate": Decimal("18.00"),
        "is_gst_rate_verified": True,
        "display_order": 5,
        "description": "Mirrorless camera bodies, cinema prime lenses, gimbals, and visual capture gear.",
    },
    {
        "slug": "tvs",
        "name": "Displays & Televisions",
        "accent_key": "tvs",
        "hsn_code": "8528",
        "gst_rate": Decimal("18.00"),
        "is_gst_rate_verified": True,
        "display_order": 6,
        "description": "OLED cinema panels, ultra-wide studio monitors, and 4K HDR home theatre screens.",
    },
    {
        "slug": "other",
        "name": "Sundry Electronics",
        "accent_key": "other",
        "hsn_code": "8543",
        "gst_rate": Decimal("18.00"),
        "is_gst_rate_verified": True,
        "display_order": 10,
        "description": "Calculated accessories, smart home peripherals, adaptors, and electronic sundries.",
    },
]

# Ordered regex classifiers. Earlier rules supersede later rules.
CLASSIFICATION_RULES: List[Tuple[str, re.Pattern]] = [
    (
        "cases-protectors",
        re.compile(
            r"\b(case|cover|protector|screen guard|tempered glass|sleeve|pouch|skin|back cover|flip cover|bumper|holster)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "cables-chargers-powerbanks",
        re.compile(
            r"\b(cable|charger|power\s*bank|powerbank|adapter|adaptor|charging\s*pad|magsafe|dock|surge\s*protector|extension\s*cord|lightning\s*cable|type-c\s*cable|micro\s*usb|fast\s*charging|battery\s*pack)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "smartwatches-bands",
        re.compile(
            r"\b(smartwatch|smart\s*watch|smart\s*band|fitness\s*tracker|watch\s*strap|watch\s*band|galaxy\s*watch|apple\s*watch|fitbit|amazfit)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "keyboards-mice",
        re.compile(
            r"\b(keyboard|keypad|mouse|mice|trackpad|mousepad|mouse\s*pad|keycaps|wireless\s*mouse|gaming\s*mouse|mechanical\s*keyboard)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "earphones-headphones",
        re.compile(
            r"\b(earphone|earphones|headphone|headphones|earbud|earbuds|tws|neckband|airpods|headset|in-ear|over-ear|on-ear|true\s*wireless|ear\s*buds)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "speakers",
        re.compile(
            r"\b(speaker|speakers|soundbar|sound\s*bar|subwoofer|woofer|boombox|home\s*theatre|home\s*theater|bluetooth\s*speaker)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "cameras",
        re.compile(
            r"\b(camera|cameras|dslr|mirrorless|camcorder|webcam|dashcam|action\s*camera|gopro|tripod|camera\s*lens|security\s*camera)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "tvs",
        re.compile(
            r"\b(television|smart\s*tv|led\s*tv|oled\s*tv|qled\s*tv|\b4k\s*tv\b|\btv\b|monitor|monitors|projector)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "smartphones",
        re.compile(
            r"\b(smartphone|smartphones|mobile\s*phone|cellular\s*phone|iphone|galaxy\s*s\d+|galaxy\s*z|oneplus|redmi|realme|xiaomi|poco|vivo|oppo|pixel\s*\d+|motorola|moto\s*g\d*)\b",
            re.IGNORECASE,
        ),
    ),
]


def classify_category(title: str, sub_category: str = "") -> str:
    """
    Classify a product title and optional sub_category into one of the 10 canonical slugs.
    """
    text = f"{title} {sub_category}".strip()
    for slug, pattern in CLASSIFICATION_RULES:
        if pattern.search(text):
            return slug
    return "other"
