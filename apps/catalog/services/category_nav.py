"""
Service to provide enriched, cached category navigation metadata for the header mega-menu.
Includes product counts, starting prices, top 5 brands, and representative thumbnail cutouts.
"""

from decimal import Decimal
from typing import List
from django.conf import settings
from django.core.cache import cache
from django.db.models import Count, Max, Min, Q

from apps.catalog.models import Category, Product
from apps.catalog.services.brands import get_known_brands

CACHE_KEY_NAV_PREVIEWS = "nav_categories_with_previews_r8"
CACHE_TTL = 900  # 15 minutes


def get_mega_menu_categories() -> List[Category]:
    """
    Returns the active canonical categories enriched with real starting price (> 0),
    top brands, and representative flagship product thumbnail cutout URL for the
    header mega-menu preview pane.
    Filters out any categories with 0 active listings.
    Cached for 15 minutes with graceful database fallback.
    """
    cached = cache.get(CACHE_KEY_NAV_PREVIEWS)
    if cached is not None:
        return cached

    categories = list(
        Category.objects.filter(is_active=True)
        .annotate(
            product_count=Count(
                "products",
                filter=Q(products__selling_price__gt=Decimal("0.00"), products__is_available=True),
            ),
            price_min_agg=Min(
                "products__selling_price",
                filter=Q(products__selling_price__gt=Decimal("0.00"), products__is_available=True),
            ),
        )
        .order_by("display_order", "name")
    )

    # Never expose categories with 0 active products in primary navigation
    categories = [cat for cat in categories if cat.product_count > 0]

    known_brands_set = set(get_known_brands())

    for cat in categories:
        # Guarantee non-zero starting price
        cat.price_from = cat.price_min_agg if (cat.price_min_agg and cat.price_min_agg > Decimal("0.00")) else Decimal("99.00")

        # Pick representative flagship product with valid image for thumbnail cutout
        top_prod = (
            Product.objects.filter(
                category=cat,
                is_available=True,
                selling_price__gt=Decimal("0.00"),
                media__media_type="image",
            )
            .prefetch_related("media")
            .order_by("-selling_price", "-source_rating_count", "id")
            .first()
        )
        if not top_prod:
            top_prod = (
                Product.objects.filter(
                    category=cat,
                    is_available=True,
                    selling_price__gt=Decimal("0.00"),
                )
                .prefetch_related("media")
                .order_by("-source_rating_count", "-selling_price", "id")
                .first()
            )

        cat.cutout_url = top_prod.primary_image_url if top_prod else ""
        cat.lead_title = top_prod.display_name if top_prod else cat.name

        # Top 3 to 5 brands
        brands_qs = (
            Product.objects.filter(
                category=cat,
                is_available=True,
                parsed_brand__in=known_brands_set,
            )
            .values("parsed_brand")
            .annotate(cnt=Count("id"))
            .order_by("-cnt")[:5]
        )
        top_brands_list = [b["parsed_brand"] for b in brands_qs]
        if len(top_brands_list) < 3:
            # Fallback to any distinct brands in this category if known brands filter yielded < 3
            fallback_brands = (
                Product.objects.filter(
                    category=cat,
                    is_available=True,
                )
                .exclude(parsed_brand="")
                .values_list("parsed_brand", flat=True)
                .distinct()[:5]
            )
            top_brands_list = list(dict.fromkeys(top_brands_list + list(fallback_brands)))[:5]

        cat.top_brands = top_brands_list
        cat.top_brands_str = ", ".join(cat.top_brands)

        # Budget shortcut
        if cat.price_from < Decimal("1000.00"):
            cat.budget_label = "Under ₹999"
            cat.budget_url = f"/c/{cat.slug}/?max_price=999"
        elif cat.price_from < Decimal("5000.00"):
            cat.budget_label = "Under ₹4,999"
            cat.budget_url = f"/c/{cat.slug}/?max_price=4999"
        else:
            cat.budget_label = "Under ₹19,999"
            cat.budget_url = f"/c/{cat.slug}/?max_price=19999"

    cache.set(CACHE_KEY_NAV_PREVIEWS, categories, timeout=CACHE_TTL)
    return categories


CATEGORY_CLUSTERS_MAP = {
    "earphones-headphones": [
        ("TWS Wireless Earbuds", "earbuds", r"\b(?:earbud|earbuds|tws|airpods|true\s+wireless)\b"),
        ("Over-Ear Headphones", "headphones", r"\b(?:over-ear|on-ear|headphone|headphones|headset)\b"),
        ("Neckbands", "neckband", r"\b(?:neckband|bullets)\b"),
        ("Wired IEMs & Earphones", "wired earphones", r"\b(?:wired|in-ear|earphone|earphones)\b"),
    ],
    "smartphones": [
        ("5G Flagships", "5G", r"\b(?:5g|ultra|pro\s+max)\b"),
        ("Mid-Range Smartphones", "smartphones", r"\b(?:redmi|realme|oppo|vivo|samsung|oneplus|poco|iqoo|motorola)\b"),
        ("Tablets & eReaders", "tablets", r"\b(?:tablet|tablets|ipad|tab|pad)\b"),
    ],
    "speakers": [
        ("Bluetooth Portable Speakers", "portable speaker", r"\b(?:portable|bluetooth\s+speaker|go\s*3|wireless\s+speaker)\b"),
        ("Soundbars & Home Theatre", "soundbar", r"\b(?:soundbar|sound\s*bar|subwoofer|home\s+theatre|dolby)\b"),
        ("Smart & Desktop Speakers", "desktop speaker", r"\b(?:echo|alexa|desktop|pebble|multimedia)\b"),
    ],
    "tvs": [
        ("4K Smart TVs", "4K TV", r"\b(?:4k|ultra\s+hd|smart\s+tv|google\s+tv|android\s+tv)\b"),
        ("QLED & OLED Panels", "QLED", r"\b(?:qled|oled)\b"),
        ("Desktop & Gaming Monitors", "monitor", r"\b(?:monitor|curved\s+monitor|gaming\s+monitor)\b"),
    ],
    "smartwatches-bands": [
        ("Advanced Smartwatches", "smartwatch", r"\b(?:apple\s+watch|galaxy\s+watch|bluetooth\s+calling|smartwatch|smart\s*watch)\b"),
        ("Fitness Trackers & Bands", "fitness band", r"\b(?:band|fitness\s*tracker|activity\s*tracker|pulse)\b"),
        ("Sport & Outdoor Wearables", "sport watch", r"\b(?:sport|gps|rugged|titan|amazfit)\b"),
    ],
    "cameras": [
        ("Mirrorless & DSLRs", "DSLR", r"\b(?:dslr|mirrorless|slr|eos|alpha)\b"),
        ("Security & Smart Cameras", "security camera", r"\b(?:cctv|security|pan/tilt|webcam|dashcam|tapo)\b"),
        ("Lenses & Precision Optics", "lens", r"\b(?:lens|telephoto|prime|zoom|optics)\b"),
    ],
    "keyboards-mice": [
        ("Mechanical Keyboards", "mechanical keyboard", r"\b(?:mechanical|keycaps|switch|backlit)\b"),
        ("Wireless Office Combos", "keyboard combo", r"\b(?:combo|wireless\s+keyboard|keyboard\s+and\s+mouse)\b"),
        ("Gaming & Ergonomic Mice", "mouse", r"\b(?:mouse|mice|gaming\s+mouse|mx\s+master|trackpad)\b"),
    ],
    "cables-chargers-powerbanks": [
        ("Powerbanks & Battery Packs", "powerbank", r"\b(?:power\s*bank|powerbank|battery\s+pack)\b"),
        ("Fast Wall Chargers & GaN", "charger", r"\b(?:charger|fast\s+charger|gan|adapter|wall\s+charger)\b"),
        ("USB-C & Lightning Cables", "cable", r"\b(?:cable|cord|usb-c|type-c|lightning)\b"),
        ("Hubs & Surge Protectors", "surge protector", r"\b(?:hub|surge|spike|strip|multiport)\b"),
    ],
    "cases-protectors": [
        ("Protective & Rugged Cases", "phone case", r"\b(?:case|back\s+cover|flip\s+cover|armor|rugged|hybrid)\b"),
        ("Tempered Glass & Guards", "tempered glass", r"\b(?:tempered|glass|screen\s+protector|screen\s+guard)\b"),
        ("Watch Straps & Bands", "watch strap", r"\b(?:strap|band|replacement)\b"),
    ],
    "other": [
        ("Computing & Laptops", "laptop", r"\b(?:laptop|macbook|thinkcentre|pc|desktop)\b"),
        ("Musical Instruments", "musical keyboard", r"\b(?:yamaha|casio|piano|synthesizer|keyboard\s+with\s+adaptor)\b"),
        ("Storage & Batteries", "memory card", r"\b(?:sd\s+card|microsd|memory\s+card|battery|batteries|drive)\b"),
    ],
}


def get_category_clusters(cat_slug: str) -> List[dict]:
    """
    Returns granular sub-category clusters with real product counts and filter URLs
    for the specified category slug.
    """
    clusters_meta = CATEGORY_CLUSTERS_MAP.get(cat_slug, [])
    results = []
    for label, q_term, pattern in clusters_meta:
        cnt = Product.objects.filter(
            category__slug=cat_slug,
            is_available=True,
            selling_price__gt=Decimal("0.00"),
            raw_name__iregex=pattern,
        ).count()
        results.append({
            "name": label,
            "query": q_term,
            "count": cnt,
            "url": f"/c/{cat_slug}/?q={q_term}",
        })
    return results


GRANULAR_24_TAXONOMY = [
    {
        "id": "flagship-5g",
        "name": "5G & Flagship Smartphones",
        "parent_slug": "smartphones",
        "regex": r"\b(?:5g|ultra|pro\s+max|fold|flip|flagship)\b",
    },
    {
        "id": "budget-midrange-phones",
        "name": "Budget & Mid-Range Smartphones",
        "parent_slug": "smartphones",
        "regex": r"\b(?:redmi|realme|oppo|vivo|samsung|oneplus|poco|iqoo|motorola|narzo|phone)\b",
        "exclude_regex": r"\b(?:tablet|tablets|ipad|tab|pad|kindle|ereader)\b",
    },
    {
        "id": "tablets-ipads",
        "name": "Tablets, iPads & eReaders",
        "parent_slug": "smartphones",
        "regex": r"\b(?:tablet|tablets|ipad|tab|pad|kindle|ereader)\b",
    },
    {
        "id": "tws-earbuds",
        "name": "TWS True Wireless Earbuds",
        "parent_slug": "earphones-headphones",
        "regex": r"\b(?:earbud|earbuds|tws|airpods|true\s+wireless|buds)\b",
    },
    {
        "id": "over-ear-headphones",
        "name": "Over-Ear & ANC Headphones",
        "parent_slug": "earphones-headphones",
        "regex": r"\b(?:over-ear|on-ear|headphone|headphones|headset|anc)\b",
    },
    {
        "id": "neckbands",
        "name": "Wireless Neckband Earphones",
        "parent_slug": "earphones-headphones",
        "regex": r"\b(?:neckband|neckbands|bullets|rockerz)\b",
    },
    {
        "id": "wired-earphones",
        "name": "Wired Earphones & IEMs",
        "parent_slug": "earphones-headphones",
        "regex": r"\b(?:wired|in-ear|bassheads|iem|3\.5mm)\b",
    },
    {
        "id": "portable-speakers",
        "name": "Bluetooth & Portable Speakers",
        "parent_slug": "speakers",
        "regex": r"\b(?:portable|bluetooth\s+speaker|go\s*3|wireless\s+speaker|clip|flip|charge)\b",
    },
    {
        "id": "soundbars-home-theatre",
        "name": "Soundbars & Home Theatre Audio",
        "parent_slug": "speakers",
        "regex": r"\b(?:soundbar|sound\s*bar|subwoofer|home\s+theatre|theatre|dolby|channel|sound\s+system)\b",
    },
    {
        "id": "smartwatches-bands",
        "name": "Smartwatches & Fitness Bands",
        "parent_slug": "smartwatches-bands",
        "regex": r"\b(?:watch|smartwatch|band|fitness|tracker|pulse|versa)\b",
    },
    {
        "id": "dslr-mirrorless",
        "name": "DSLR & Mirrorless Cameras",
        "parent_slug": "cameras",
        "regex": r"\b(?:dslr|mirrorless|slr|eos|alpha|digital\s+camera|200d|z50|lumix)\b",
    },
    {
        "id": "security-action-cameras",
        "name": "Smart Security & Action Cameras",
        "parent_slug": "cameras",
        "regex": r"\b(?:cctv|security|pan/tilt|webcam|dashcam|tapo|action\s+camera|gopro)\b",
    },
    {
        "id": "tripods-lighting",
        "name": "Tripods, Gimbals & Studio Lighting",
        "parent_slug": "cameras",
        "regex": r"\b(?:tripod|gimbal|ring\s*light|studio|mount|rig|softbox|light|holder|lens)\b",
    },
    {
        "id": "4k-smart-tvs",
        "name": "4K Ultra HD & Smart Televisions",
        "parent_slug": "tvs",
        "regex": r"\b(?:4k|ultra\s+hd|smart\s+tv|google\s+tv|android\s+tv|qled|oled|led\s+tv|television|bravia)\b",
    },
    {
        "id": "pc-monitors",
        "name": "PC Monitors & Gaming Displays",
        "parent_slug": "tvs",
        "regex": r"\b(?:monitor|curved\s+monitor|gaming\s+monitor|ips\s+display|fhd\s+monitor|hz)\b",
    },
    {
        "id": "keyboards",
        "name": "Mechanical & Wireless Keyboards",
        "parent_slug": "keyboards-mice",
        "regex": r"\b(?:keyboard|keyboards|mechanical|keycaps|switch|backlit)\b",
    },
    {
        "id": "mice",
        "name": "Gaming & Ergonomic Mice",
        "parent_slug": "keyboards-mice",
        "regex": r"\b(?:mouse|mice|gaming\s+mouse|optical|wireless\s+mouse|mx\s+master|trackpad)\b",
    },
    {
        "id": "wall-chargers",
        "name": "Fast Wall Chargers & GaN Adapters",
        "parent_slug": "cables-chargers-powerbanks",
        "regex": r"\b(?:charger|fast\s+charger|gan|adapter|wall\s+charger|power\s+adapter|quick\s+charge)\b",
    },
    {
        "id": "powerbanks",
        "name": "Powerbanks & Portable Energy",
        "parent_slug": "cables-chargers-powerbanks",
        "regex": r"\b(?:power\s*bank|powerbank|battery\s+pack|portable\s+battery)\b",
    },
    {
        "id": "cables",
        "name": "USB-C, Lightning & HDMI Cables",
        "parent_slug": "cables-chargers-powerbanks",
        "regex": r"\b(?:cable|cord|usb-c|type-c|lightning|hdmi|aux|thunderbolt)\b",
    },
    {
        "id": "cases-covers",
        "name": "Phone Cases, Covers & Screen Guards",
        "parent_slug": "cases-protectors",
        "regex": r"\b(?:case|back\s+cover|flip\s+cover|armor|rugged|tempered|glass|screen\s+protector|screen\s+guard|pouch)\b",
    },
    {
        "id": "storage-memory",
        "name": "SSD, Flash Drives & Memory Cards",
        "parent_slug": "other",
        "regex": r"\b(?:sd\s+card|microsd|memory\s+card|ssd|flash\s+drive|pen\s+drive|hard\s+drive|storage)\b",
    },
    {
        "id": "laptops-desktops",
        "name": "Laptops, Desktops & Combos",
        "parent_slug": "other",
        "regex": r"\b(?:laptop|macbook|thinkcentre|pc|desktop|all-in-one|chromebook|notebook)\b",
    },
    {
        "id": "networking-wifi",
        "name": "Wi-Fi Routers & Networking",
        "parent_slug": "other",
        "regex": r"\b(?:router|wifi|wi-fi|range\s+extender|access\s+point|mesh|ethernet|modem|networking)\b",
    },
]

CACHE_KEY_GRANULAR_24 = "granular_24_categories_v2"


def get_24_granular_categories() -> List[dict]:
    """
    Returns the 24 high-density granular product categories with real active item counts,
    minimum starting prices, and representative product cutout thumbnail URLs.
    Cached for 15 minutes.
    """
    cached = cache.get(CACHE_KEY_GRANULAR_24)
    if cached is not None:
        return cached

    items = []
    for entry in GRANULAR_24_TAXONOMY:
        qs = Product.objects.filter(
            category__slug=entry["parent_slug"],
            is_available=True,
            selling_price__gt=Decimal("0.00"),
            raw_name__iregex=entry["regex"],
        )
        if "exclude_regex" in entry:
            qs = qs.exclude(raw_name__iregex=entry["exclude_regex"])

        aggs = qs.aggregate(
            cnt=Count("id"),
            min_p=Min("selling_price"),
            max_p=Max("selling_price"),
        )
        cnt = aggs["cnt"] or 0
        min_p = aggs["min_p"] or Decimal("99.00")

        # Pick representative product with valid image
        top_p = (
            qs.filter(media__media_type="image")
            .prefetch_related("media")
            .order_by("-selling_price", "-source_rating_count", "id")
            .first()
        )
        if not top_p:
            top_p = (
                qs.prefetch_related("media")
                .order_by("-selling_price", "id")
                .first()
            )

        items.append({
            "id": entry["id"],
            "name": entry["name"],
            "parent_slug": entry["parent_slug"],
            "product_count": cnt,
            "min_price": min_p,
            "url": f"/c/{entry['parent_slug']}/?sub={entry['id']}",
            "thumbnail_url": top_p.primary_image_url if top_p else "",
            "lead_title": top_p.display_name if top_p else entry["name"],
        })

    cache.set(CACHE_KEY_GRANULAR_24, items, timeout=CACHE_TTL)
    return items


def get_sub_category_filter(sub_slug: str):
    """
    Retrieves the filter metadata (regex, exclude_regex, display name) for a sub-slug.
    """
    if not sub_slug:
        return None
    for entry in GRANULAR_24_TAXONOMY:
        if entry["id"] == sub_slug:
            return entry
    return None
