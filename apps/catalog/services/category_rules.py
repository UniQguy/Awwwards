"""
Evidence-based Category Classification Engine for ELECTROCART.

Rule Architecture (Scored Approach):
------------------------------------
1. Primary Device vs Accessory Disambiguation:
   - Negative filters run first: Memory cards (SD, microSD, CF), card readers, TV streaming sticks
     (Fire TV Stick, Chromecast), TV remotes, wall mounts, and camera bags/tripods are NOT core devices;
     they are classified into 'other'.
   - Dedicated accessory categories (cases-protectors, cables-chargers) take precedence when the title
     starts with or is dominated by the accessory noun.
   - Genuine televisions (Redmi TV, Sony TV) and earphones (OnePlus Bullets, realme Buds) are matched
     BEFORE smartphones so devices manufactured by smartphone brands are assigned to their true hardware category.
   - Camera bodies/optics match genuine camera terms (DSLR, Digital SLR, mirrorless, camcorder, action camera)
     while camera bags, lens caps, and tripods go to 'other'.

2. Category Hierarchy:
   1. Negative Filters (SD Cards / Readers / TV Sticks / Camera Bags -> 'other')
   2. Cases & Protectors (Phone cases, covers, tempered glass, watch replacement straps)
   3. Cables, Chargers & Power (Cables, wall chargers, GaN power, power banks)
   4. Televisions & Displays (Smart TVs, LED/OLED/QLED TVs, monitors)
   5. Earphones & Headphones (Earphones, earbuds, TWS, headphones, neckbands, Bullets)
   6. Speakers & Soundbars (Speakers, soundbars, subwoofers, party speakers)
   7. Smartwatches & Wearables (Smartwatches, fitness bands, Apple Watch, Galaxy Watch)
   8. Keyboards & Pointers (Keyboards, mice, combos, trackpads, mousepads)
   9. Cameras & Optics (DSLR, SLR, mirrorless, camcorders, action cameras, lenses)
   10. Smartphones & Devices (Smartphones, mobile phones, iPhone, Galaxy, Redmi, OnePlus)
   11. Fallback -> 'other' (Sundry electronics)

Documented in docs/DECISIONS.md per Standing Orders Section 2.
"""

from decimal import Decimal
import re
from typing import Dict, List, Tuple

CATEGORY_DEFINITIONS: List[Dict] = [
    {
        "slug": "earphones-headphones",
        "name": "Earphones & Headphones",
        "accent_key": "earphones-headphones",
        "hsn_code": "8518",
        "gst_rate": Decimal("18.00"),
        "is_gst_rate_verified": True,
        "display_order": 1,
        "description": "",
    },
    {
        "slug": "speakers",
        "name": "Acoustics & Speakers",
        "accent_key": "speakers",
        "hsn_code": "8518",
        "gst_rate": Decimal("18.00"),
        "is_gst_rate_verified": True,
        "display_order": 2,
        "description": "",
    },
    {
        "slug": "smartphones",
        "name": "Smartphones & Devices",
        "accent_key": "smartphones",
        "hsn_code": "8517",
        "gst_rate": Decimal("18.00"),
        "is_gst_rate_verified": True,
        "display_order": 3,
        "description": "",
    },
    {
        "slug": "smartwatches-bands",
        "name": "Smartwatches & Wearables",
        "accent_key": "smartwatches-bands",
        "hsn_code": "9102",
        "gst_rate": Decimal("18.00"),
        "is_gst_rate_verified": True,
        "display_order": 4,
        "description": "",
    },
    {
        "slug": "cameras",
        "name": "Cameras & Optics",
        "accent_key": "cameras",
        "hsn_code": "8525",
        "gst_rate": Decimal("18.00"),
        "is_gst_rate_verified": True,
        "display_order": 5,
        "description": "",
    },
    {
        "slug": "tvs",
        "name": "Displays & Televisions",
        "accent_key": "tvs",
        "hsn_code": "8528",
        "gst_rate": Decimal("18.00"),
        "is_gst_rate_verified": True,
        "display_order": 6,
        "description": "",
    },
    {
        "slug": "keyboards-mice",
        "name": "Keyboards & Pointers",
        "accent_key": "keyboards-mice",
        "hsn_code": "8471",
        "gst_rate": Decimal("18.00"),
        "is_gst_rate_verified": True,
        "display_order": 7,
        "description": "",
    },
    {
        "slug": "cables-chargers-powerbanks",
        "name": "Cables, Chargers & Power",
        "accent_key": "cables-chargers-powerbanks",
        "hsn_code": "8504",
        "gst_rate": Decimal("18.00"),
        "is_gst_rate_verified": True,
        "display_order": 8,
        "description": "",
    },
    {
        "slug": "cases-protectors",
        "name": "Cases & Protectors",
        "accent_key": "cases-protectors",
        "hsn_code": "3926",
        "gst_rate": Decimal("18.00"),
        "is_gst_rate_verified": True,
        "display_order": 9,
        "description": "",
    },
    {
        "slug": "other",
        "name": "Sundry Electronics",
        "accent_key": "other",
        "hsn_code": "8543",
        "gst_rate": Decimal("18.00"),
        "is_gst_rate_verified": True,
        "display_order": 10,
        "description": "",
    },
]

# ----------------------------------------------------------------------
# 1. Negative Filters & Accessory Catchers
# ----------------------------------------------------------------------

RE_STORAGE_MEMORY_CARD = re.compile(
    r"\b(?:micro\s*sd|microsd|sd\s*card|sdxc|sdhc|memory\s*card|compact\s*flash|cfexpress|card\s*reader|flash\s*drive|pendrive|pen\s*drive|sd\s+uhs|\buhs-?[iI12]\b|\d+GB\s+card)\b",
    re.IGNORECASE,
)

RE_TV_STREAMING_OR_ACCESSORY = re.compile(
    r"\b(?:fire\s*tv\s*stick|chromecast|streaming\s*stick|tv\s*stick|tv\s*box|apple\s*tv|tv\s*remote|remote\s*control|wall\s*mount|tv\s*mount|tv\s*bracket|tv\s*stand)\b",
    re.IGNORECASE,
)

RE_CAMERA_ACCESSORY = re.compile(
    r"\b(?:camera\s*(?:\w+\s+)?bag|camera\s*(?:\w+\s+)?case|camera\s*strap|lens\s*cap|lens\s*hood|tripod|monopod|camera\s*battery|camera\s*mount|lens\s*cleaning|shoulder\s*bag\s*for\s*(?:dslr|camera)|battery\s+for\s+(?:canon|nikon|sony|dslr)|rechargeable\s+lithium-ion\s+battery|laptop|notebook|macbook)\b",
    re.IGNORECASE,
)

# ----------------------------------------------------------------------
# 2. Cases, Straps & Protectors
# ----------------------------------------------------------------------

RE_CASE_ACCESSORY_PREFIX = re.compile(
    r"^(?:spigen|ringke|elago|dailyobjects|solimo)?\s*(?:case|cover|back\s+cover|flip\s+cover|tempered\s+glass|screen\s+protector|screen\s+guard|pouch|sleeve|bumper|skin|strap|watch\s+strap|watch\s+band)\b",
    re.IGNORECASE,
)

RE_CASE_ACCESSORY_TERMS = re.compile(
    r"\b(?:back\s+cover|flip\s+cover|phone\s+case|protective\s+case|hybrid\s+case|silicone\s+case|tempered\s+glass|screen\s+protector|screen\s+guard|lens\s+protector|watch\s+strap|watch\s+band|replacement\s+band|replacement\s+(?:silicone\s+)?strap)\b",
    re.IGNORECASE,
)

# ----------------------------------------------------------------------
# 3. Cables, Chargers & Power
# ----------------------------------------------------------------------

RE_CABLE_CHARGER_PREFIX = re.compile(
    r"^(?:amazon\s+basics|boat|anker|portronics|ptron|ambrane)?\s*(?:cable|charger|power\s*bank|powerbank|adapter|adaptor|charging\s+cable|usb\s+cable|type-c\s+cable|lightning\s+cable|fast\s+charger|gan\s+charger|dual\s+port\s+charger|wall\s+charger)\b",
    re.IGNORECASE,
)

RE_POWER_BANK = re.compile(
    r"\b(?:power\s*bank|powerbank|battery\s+pack|portable\s+charger)\b",
    re.IGNORECASE,
)

# ----------------------------------------------------------------------
# 4. Televisions & Monitors
# ----------------------------------------------------------------------

RE_TELEVISION = re.compile(
    r"\b(?:smart\s*(?:(?:android|google|led|oled|qled)\s*)*tv|led\s*tv|oled\s*tv|qled\s*tv|android\s*tv|google\s*tv|\btelevision\b|4k\s*(?:ultra\s*hd\s*)?tv|hd\s*ready\s*tv|full\s*hd\s*tv)\b"
    r"|(?:\b\d{2,3}\s*(?:cm|inch|inches|\")\b.*?\b(?:tv|television)\b)"
    r"|\b(?:gaming\s+monitor|curved\s+monitor|studio\s+monitor|ultrawide\s+monitor|led\s+monitor|lcd\s+monitor)\b",
    re.IGNORECASE,
)

# ----------------------------------------------------------------------
# 5. Audio: Earphones & Headphones vs Speakers
# ----------------------------------------------------------------------

RE_EARPHONES = re.compile(
    r"\b(?:earphone|earphones|headphone|headphones|earbud|earbuds|tws|neckband|airpods|headset|in-ear|over-ear|on-ear|true\s+wireless|ear\s+buds|bullets\s+z\d*)\b",
    re.IGNORECASE,
)

RE_SPEAKERS = re.compile(
    r"\b(?:speaker|speakers|soundbar|sound\s*bar|subwoofer|party\s*speaker|bookshelf\s*speaker|bluetooth\s*speaker|echo\s*dot|desktop\s*speakers)\b",
    re.IGNORECASE,
)

# ----------------------------------------------------------------------
# 6. Smartwatches & Wearables
# ----------------------------------------------------------------------

RE_SMARTWATCH = re.compile(
    r"\b(?:smartwatch|smart\s*watch|fitness\s*tracker|activity\s*tracker|galaxy\s*watch|apple\s*watch|fitbit|amazfit|colorfit|noise\s+pulse|watch\s+with\s+(?:spo2|heart\s+rate))\b",
    re.IGNORECASE,
)

# ----------------------------------------------------------------------
# 7. Keyboards & Mice
# ----------------------------------------------------------------------

RE_KEYBOARDS_MICE = re.compile(
    r"\b(?:keyboard|keypad|mouse|mice|trackpad|mousepad|mouse\s*pad|desk\s*mat|keycaps|mechanical\s+keyboard|wireless\s+mouse|gaming\s+mouse|combo\s+keyboard|keyboard\s+and\s+mouse)\b",
    re.IGNORECASE,
)

# ----------------------------------------------------------------------
# 8. Cameras & Optics
# ----------------------------------------------------------------------

RE_CAMERA_DEVICE = re.compile(
    r"\b(?:dslr|digital\s+slr|slr(?:\s+camera)?|mirrorless(?:\s+camera)?|camcorder|action\s+camera|gopro|instant\s+camera|digital\s+camera|camera\s+body|cinema\s+camera|webcam|dashcam|security\s+camera|cctv|lens\s+for\s+(?:canon|nikon|sony)|telephoto\s+lens|zoom\s+lens|prime\s+lens)\b",
    re.IGNORECASE,
)

# ----------------------------------------------------------------------
# 9. Smartphones & Devices
# ----------------------------------------------------------------------

RE_PHONE_PREFIX = re.compile(
    r"^(?:redmi|realme|samsung\s+galaxy|oneplus|apple\s+iphone|iphone|xiaomi|poco|vivo|oppo|google\s+pixel|pixel\s+\d|motorola|moto\s+[ge]\d*|iqoo|nokia)\b",
    re.IGNORECASE,
)

RE_PHONE_SPECS = re.compile(
    r"\b(?:\d+GB\s+RAM|\d+GB\s+Storage|\d+TB\s+Storage|\d+mAh|\d+MP\s+(?:Quad|Dual|Triple|Rear|Front|AI)?\s*Camera|Super\s+Amoled|5G\s+Mobile|Smartphone)\b",
    re.IGNORECASE,
)

# Backward compatibility
CLASSIFICATION_RULES: List[Tuple[str, re.Pattern]] = [
    ("cases-protectors", RE_CASE_ACCESSORY_TERMS),
    ("cables-chargers-powerbanks", re.compile(r"\b(cable|charger|power\s*bank|powerbank|adapter|adaptor)\b", re.I)),
    ("smartwatches-bands", RE_SMARTWATCH),
    ("keyboards-mice", RE_KEYBOARDS_MICE),
    ("earphones-headphones", RE_EARPHONES),
    ("speakers", RE_SPEAKERS),
    ("cameras", RE_CAMERA_DEVICE),
    ("tvs", RE_TELEVISION),
    ("smartphones", RE_PHONE_PREFIX),
]


def classify_category(title: str, sub_category: str = "") -> str:
    """
    Classifies a product title using evidence-based scoring and domain precedence rules.
    Returns one of the 10 canonical slugs.
    """
    text = f"{title} {sub_category}".strip()

    # 1. HARD EXCLUSIONS & DISAMBIGUATIONS
    # Storage & Memory Cards -> NOT cameras -> 'other'
    if RE_STORAGE_MEMORY_CARD.search(text):
        return "other"

    # Streaming sticks (Fire TV Stick, Chromecast), TV remotes, wall mounts -> NOT TVs -> 'other'
    if RE_TV_STREAMING_OR_ACCESSORY.search(text):
        return "other"

    # Camera bags, tripods, lens caps -> NOT cameras -> 'other'
    if RE_CAMERA_ACCESSORY.search(text):
        return "other"

    # Watch replacement bands/straps -> 'cases-protectors'
    if re.search(r"\b(?:strap|band)\s+(?:for|compatible with)\b", text, re.I) or re.search(r"\b(?:replacement\s+band|replacement\s+strap|silicone\s+strap|metal\s+strap|mesh\s+strap|watch\s+strap|watch\s+band)\b", text, re.I):
        if not re.search(r"\b(?:smartwatch|smart\s*watch|fitness\s*tracker|activity\s*tracker|spo2|heart\s*rate|bluetooth\s*calling)\b", text, re.I):
            return "cases-protectors"


    # 2. CASES & PROTECTORS PRECEDENCE
    if RE_CASE_ACCESSORY_PREFIX.search(text) or RE_CASE_ACCESSORY_TERMS.search(text):
        if not (RE_PHONE_PREFIX.search(text) and RE_PHONE_SPECS.search(text) and not re.search(r"\b(?:cover|case|glass)\s+for\b", text, re.I)):
            return "cases-protectors"

    # 3. CABLES, CHARGERS & POWER PRECEDENCE
    if RE_CABLE_CHARGER_PREFIX.search(text):
        return "cables-chargers-powerbanks"

    if RE_POWER_BANK.search(text) and not re.search(r"\b(?:smartphone|mobile\s+phone)\b", text, re.I):
        return "cables-chargers-powerbanks"

    # 4. TELEVISIONS & MONITORS (checked before smartphones so Redmi TV is a TV)
    if RE_TELEVISION.search(text):
        return "tvs"

    # 5. AUDIO: EARPHONES & HEADPHONES (checked before smartphones so OnePlus Bullets is earphones)
    if RE_EARPHONES.search(text):
        return "earphones-headphones"

    # 6. SPEAKERS & SOUNDBARS
    if RE_SPEAKERS.search(text):
        return "speakers"

    # 7. SMARTWATCHES & WEARABLES
    if RE_SMARTWATCH.search(text):
        return "smartwatches-bands"

    # 8. KEYBOARDS & MICE
    if RE_KEYBOARDS_MICE.search(text):
        return "keyboards-mice"

    # 9. CAMERAS & OPTICS
    if RE_CAMERA_DEVICE.search(text):
        return "cameras"

    # 10. SMARTPHONES & DEVICES
    if RE_PHONE_PREFIX.search(text):
        if not re.search(r"\b(?:cable|charger|adapter|case|cover|glass)\b", text, re.I) or RE_PHONE_SPECS.search(text):
            return "smartphones"

    if re.search(r"\b(?:smartphone|smartphones|mobile\s+phone|cellular\s+phone)\b", text, re.I):
        return "smartphones"

    # 11. SECONDARY CABLES / CHARGERS CATCH-ALL
    if re.search(r"\b(?:charger|charging\s+cable|usb\s+cable|type-c\s+cable|lightning\s+cable|power\s+adapter|gan\s+fast\s+charger|wall\s+charger)\b", text, re.I):
        return "cables-chargers-powerbanks"

    return "other"


def merge_duplicate_categories() -> Dict[str, int]:
    """
    Finds and merges duplicate Category records into their canonical Category
    defined in CATEGORY_DEFINITIONS.
    Reassigns all Product, Collection, and Coupon foreign keys before deleting duplicate categories.
    Returns summary dict of actions taken.
    """
    from apps.catalog.models import Category, Collection, Product
    from apps.promotions.models import Coupon

    canonical_by_slug = {}
    for item in CATEGORY_DEFINITIONS:
        cat, _ = Category.objects.update_or_create(
            slug=item["slug"],
            defaults={
                "name": item["name"],
                "accent_key": item["accent_key"],
                "hsn_code": item["hsn_code"],
                "gst_rate": item["gst_rate"],
                "is_gst_rate_verified": item["is_gst_rate_verified"],
                "display_order": item["display_order"],
                "description": item["description"],
                "is_active": True,
            },
        )
        canonical_by_slug[item["slug"]] = cat

    canonical_slugs = set(canonical_by_slug.keys())
    canonical_by_name = {c.name.strip().lower(): c for c in canonical_by_slug.values()}

    reassigned_products = 0
    deleted_categories = 0

    all_categories = list(Category.objects.all())
    for cat in all_categories:
        if cat.slug in canonical_slugs:
            continue

        # Find target canonical category
        target = None
        cat_name_clean = cat.name.strip().lower()
        if cat_name_clean in canonical_by_name:
            target = canonical_by_name[cat_name_clean]
        else:
            for c_slug, c_cat in canonical_by_slug.items():
                if cat.slug.startswith(c_slug):
                    target = c_cat
                    break

        if not target:
            target = canonical_by_slug["other"]

        # Reassign products
        prod_count = Product.objects.filter(category=cat).update(category=target)
        reassigned_products += prod_count

        # Reassign collections
        Collection.objects.filter(category=cat).update(category=target)

        # Reassign coupons
        for coupon in Coupon.objects.filter(applicable_categories=cat):
            coupon.applicable_categories.remove(cat)
            coupon.applicable_categories.add(target)

        cat.delete()
        deleted_categories += 1

    return {
        "reassigned_products": reassigned_products,
        "deleted_categories": deleted_categories,
    }
