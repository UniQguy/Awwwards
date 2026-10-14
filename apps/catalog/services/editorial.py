"""
Editorial curation and catalog intelligence service for ELECTROCART.
Powers the Kinetic Monograph: home hero, home chapters, category spreads,
typographic index rows, and allow-listed brand indexes.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional, Sequence
from django.db.models import Count, Max, Min, Prefetch, Q

from apps.catalog.models import (
    Category,
    Collection,
    FeaturedProduct,
    Product,
)
from apps.catalog.services.brands import get_known_brands
from apps.catalog.services.families import family_key


@dataclass(frozen=True)
class HeroResult:
    """Hero section products and curation attribution flag."""
    products: List[Product]
    is_auto: bool


@dataclass(frozen=True)
class HomeChapter:
    """One editorial monograph chapter for the homepage."""
    category: Category
    picks: List[Product]
    product_count: int
    price_min: Decimal
    price_max: Decimal
    is_auto: bool
    editorial_line: str


@dataclass(frozen=True)
class CategoryStats:
    """Accurate database statistics for a category monograph spread."""
    listing_count: int
    distinct_raw_name_count: int
    brand_count: int
    price_min: Decimal
    price_max: Decimal
    in_stock_count: int


@dataclass(frozen=True)
class CategorySpreadResult:
    """Editorial spread package for a category marquee."""
    category: Category
    stats: CategoryStats
    picks: List[Product]
    is_auto: bool
    editorial_line: str


@dataclass(frozen=True)
class IndexRow:
    """A row in the typographic monograph category index."""
    category: Category
    count: int
    price_from: Decimal
    pick: Optional[Product]


@dataclass(frozen=True)
class BrandItem:
    """An allow-listed brand with real purchasable listing count."""
    name: str
    product_count: int


def home_headline_cutouts() -> dict[str, Optional[Product]]:
    """
    Returns the three products for the home hero headline:
    - cable: from 'cables-chargers-powerbanks' (after 'plug in')
    - watch: from 'smartwatches-bands' (after 'put on')
    - earphones: from 'earphones-headphones' (after 'listen with')
    Each chosen deterministically by highest rating count, price, id.
    """
    target_slugs = {
        "cable": "cables-chargers-powerbanks",
        "watch": "smartwatches-bands",
        "earphones": "earphones-headphones",
    }
    result = {}
    for key, slug in target_slugs.items():
        prod = (
            Product.objects.filter(
                category__slug=slug,
                is_available=True,
                selling_price__gt=Decimal("0.00"),
                media__media_type="image",
            )
            .select_related("category")
            .prefetch_related("media")
            .order_by("-source_rating_count", "-selling_price", "id")
            .first()
        )
        result[key] = prod if (prod and prod.primary_image_url) else None
    return result


def eligible_cutout_products(products: Sequence[Product], max_cutouts: int = 3) -> List[Product]:
    """
    Returns up to max_cutouts products eligible for inline headline cutouts.
    A product is eligible only if it has an image URL and is purchasable.
    """
    eligible: List[Product] = []
    for p in products:
        if p.is_purchasable and p.primary_image_url:
            eligible.append(p)
            if len(eligible) >= max_cutouts:
                break
    return eligible


HERO_ELIGIBLE_CATEGORIES = [
    "smartphones",
    "tvs",
    "speakers",
    "smartwatches-bands",
    "earphones-headphones",
    "keyboards-mice",
    "cameras",
]


def hero_products(n: int = 3) -> HeroResult:
    """
    Returns hero products for the homepage.
    Checks for active Collection with placement='home_hero'.
    Fallback auto-select excludes accessory categories (cables, cases, other)
    and rotates through primary categories (phones, TVs, audio, cameras) by day-of-year.
    """
    from datetime import date

    # 1. Check curated collection
    curated_col = (
        Collection.objects.filter(placement=Collection.PLACEMENT_HOME_HERO, is_active=True)
        .prefetch_related(
            Prefetch(
                "featured_items",
                queryset=FeaturedProduct.objects.select_related("product__category")
                .prefetch_related("product__media", "product__specifications")
                .order_by("display_order", "id"),
            )
        )
        .first()
    )

    if curated_col:
        curated_prods = [
            fp.product
            for fp in curated_col.featured_items.all()
            if fp.product.is_purchasable and fp.product.primary_image_url
        ]
        if curated_prods:
            return HeroResult(products=curated_prods[:n], is_auto=False)

    # 2. Fallback auto-select: single query across eligible non-accessory categories
    day_of_year = date.today().timetuple().tm_yday
    num_cats = len(HERO_ELIGIBLE_CATEGORIES)
    start_idx = day_of_year % num_cats
    preferred_order = {
        HERO_ELIGIBLE_CATEGORIES[(start_idx + offset) % num_cats]: offset
        for offset in range(num_cats)
    }

    prods = (
        Product.objects.filter(
            selling_price__gt=Decimal("0.00"),
            is_available=True,
            media__media_type="image",
        )
        .exclude(category__slug__in=["cables-chargers-powerbanks", "cases-protectors", "other"])
        .select_related("category")
        .prefetch_related("media", "specifications")
        .order_by("-source_rating_count", "-selling_price", "id")
    )

    best_per_cat = {}
    for p in prods:
        if p.category_id not in best_per_cat and p.primary_image_url:
            best_per_cat[p.category_id] = p

    sorted_candidates = sorted(
        best_per_cat.values(),
        key=lambda prod: preferred_order.get(prod.category.slug, 999),
    )

    return HeroResult(products=sorted_candidates[:n], is_auto=True)


WARM_WORLDS = {"earphones-headphones", "speakers", "cameras", "keyboards-mice", "cases-protectors"}
COOL_WORLDS = {"smartphones", "smartwatches-bands", "tvs", "cables-chargers-powerbanks", "other"}


def home_chapters(max_chapters: int = 6, picks_per_chapter: int = 3) -> List[HomeChapter]:
    """
    Active categories with at least 3 purchasable products.
    Alternates warm and cool monograph worlds so adjacent chapters contrast.
    Each chapter has picks grouped by family_key (defaults to 3 for backwards compatibility, supports 4 for WP3).
    """
    cats = (
        Category.objects.filter(is_active=True)
        .annotate(
            purchasable_count=Count(
                "products",
                filter=Q(products__selling_price__gt=Decimal("0.00"), products__is_available=True),
            ),
            price_min_agg=Min(
                "products__selling_price",
                filter=Q(products__selling_price__gt=Decimal("0.00"), products__is_available=True),
            ),
            price_max_agg=Max(
                "products__selling_price",
                filter=Q(products__selling_price__gt=Decimal("0.00"), products__is_available=True),
            ),
        )
        .filter(purchasable_count__gte=1)
        .order_by("display_order", "id")
    )

    if not cats:
        return []

    # Partition into warm and cool worlds, preserving display_order within each
    warm_cats = [c for c in cats if c.accent_key in WARM_WORLDS]
    cool_cats = [c for c in cats if c.accent_key in COOL_WORLDS]

    # Interleave warm and cool
    interleaved: List[Category] = []
    w_idx, c_idx = 0, 0
    while len(interleaved) < max_chapters and (w_idx < len(warm_cats) or c_idx < len(cool_cats)):
        if w_idx < len(warm_cats):
            interleaved.append(warm_cats[w_idx])
            w_idx += 1
            if len(interleaved) >= max_chapters:
                break
        if c_idx < len(cool_cats):
            interleaved.append(cool_cats[c_idx])
            c_idx += 1

    cat_list = interleaved
    cat_ids = [c.id for c in cat_list]

    # Pre-fetch curated chapter collections
    curated_map = {}
    collections = (
        Collection.objects.filter(
            placement=Collection.PLACEMENT_HOME_CHAPTER,
            is_active=True,
        )
        .prefetch_related(
            Prefetch(
                "featured_items",
                queryset=FeaturedProduct.objects.select_related("product__category")
                .prefetch_related("product__media", "product__specifications")
                .order_by("display_order", "id"),
            )
        )
    )
    for col in collections:
        cat_id = col.category_id
        if not cat_id:
            first_item = col.featured_items.first()
            if first_item and first_item.product_id and first_item.product.category_id:
                cat_id = first_item.product.category_id
        if cat_id and cat_id in cat_ids and cat_id not in curated_map:
            curated_map[cat_id] = col

    chapters: List[HomeChapter] = []

    for cat in cat_list:
        p_count = cat.purchasable_count
        p_min = cat.price_min_agg or Decimal("0.00")
        p_max = cat.price_max_agg or Decimal("0.00")

        # Select picks up to picks_per_chapter
        col = curated_map.get(cat.id)
        if col:
            picks = [
                fp.product
                for fp in col.featured_items.all()
                if fp.product.is_purchasable
            ][:picks_per_chapter]
            is_auto = False
        else:
            picks = []
            is_auto = True

        if len(picks) < picks_per_chapter:
            candidates = (
                Product.objects.filter(
                    category=cat,
                    selling_price__gt=Decimal("0.00"),
                    is_available=True,
                )
                .select_related("category")
                .prefetch_related("media", "specifications")
                .order_by("-source_rating_count", "-selling_price", "id")
            )
            deduped_picks = list(picks)
            seen_families = {family_key(p.raw_name) for p in deduped_picks}
            for prod in candidates:
                fam = family_key(prod.raw_name)
                if fam not in seen_families:
                    seen_families.add(fam)
                    deduped_picks.append(prod)
                    if len(deduped_picks) >= picks_per_chapter:
                        break
            picks = deduped_picks[:picks_per_chapter]
            is_auto = True

        if getattr(cat, "chapter_intro", None) and cat.chapter_intro.strip():
            editorial_line = cat.chapter_intro.strip()
        elif cat.description and cat.description.strip():
            editorial_line = cat.description.strip()
        else:
            editorial_line = f"{p_count} listings from \u20b9{p_min:.2f} to \u20b9{p_max:.2f}."

        chapters.append(
            HomeChapter(
                category=cat,
                picks=picks,
                product_count=p_count,
                price_min=p_min,
                price_max=p_max,
                is_auto=is_auto,
                editorial_line=editorial_line,
            )
        )

    return chapters


def category_spread(category: Category, max_picks: int = 4) -> CategorySpreadResult:
    """
    Generates real stats and up to max_picks for a category marquee spread.
    Curated collection takes precedence; otherwise auto-selects.
    """
    base_qs = Product.objects.filter(
        category=category,
        selling_price__gt=Decimal("0.00"),
        is_available=True,
    )

    listing_count = base_qs.count()
    distinct_raw_count = base_qs.values("raw_name").distinct().count()

    price_aggs = base_qs.aggregate(
        min_p=Min("selling_price"),
        max_p=Max("selling_price"),
    )
    price_min = price_aggs["min_p"] or Decimal("0.00")
    price_max = price_aggs["max_p"] or Decimal("0.00")

    in_stock_count = Product.objects.filter(
        category=category,
        selling_price__gt=Decimal("0.00"),
        is_available=True,
        inventory__quantity__gt=0,
    ).count()

    known_brands = get_known_brands()
    brand_count = (
        base_qs.filter(parsed_brand__in=known_brands)
        .values("parsed_brand")
        .distinct()
        .count()
    )

    stats = CategoryStats(
        listing_count=listing_count,
        distinct_raw_name_count=distinct_raw_count,
        brand_count=brand_count,
        price_min=price_min,
        price_max=price_max,
        in_stock_count=in_stock_count,
    )

    # Curated spread collection
    curated_col = (
        Collection.objects.filter(
            placement=Collection.PLACEMENT_CATEGORY_SPREAD,
            category=category,
            is_active=True,
        )
        .prefetch_related(
            Prefetch(
                "featured_items",
                queryset=FeaturedProduct.objects.select_related("product__category")
                .prefetch_related("product__media", "product__specifications")
                .order_by("display_order", "id"),
            )
        )
        .first()
    )

    if curated_col:
        picks = [
            fp.product
            for fp in curated_col.featured_items.all()
            if fp.product.is_purchasable
        ][:max_picks]
        is_auto = False
    else:
        picks = []
        is_auto = True

    if not picks:
        candidates = (
            base_qs.select_related("category")
            .prefetch_related("media", "specifications")
            .order_by("-source_rating_count", "-selling_price", "id")
        )
        deduped_picks = []
        seen_families = set()
        for prod in candidates:
            fam = family_key(prod.raw_name)
            if fam not in seen_families:
                seen_families.add(fam)
                deduped_picks.append(prod)
                if len(deduped_picks) >= max_picks:
                    break
        picks = deduped_picks
        is_auto = True

    if getattr(category, "chapter_intro", None) and category.chapter_intro.strip():
        editorial_line = category.chapter_intro.strip()
    elif category.description and category.description.strip():
        editorial_line = category.description.strip()
    else:
        editorial_line = (
            f"{stats.listing_count} listings from \u20b9{stats.price_min:.2f} to \u20b9{stats.price_max:.2f}."
        )

    return CategorySpreadResult(
        category=category,
        stats=stats,
        picks=picks,
        is_auto=is_auto,
        editorial_line=editorial_line,
    )


def index_rows() -> List[IndexRow]:
    """
    Returns typographic monograph index rows for /categories/.
    One row per active category with live count, min price, and 1 top pick.
    """
    categories = (
        Category.objects.filter(is_active=True)
        .annotate(
            purchasable_count=Count(
                "products",
                filter=Q(products__selling_price__gt=Decimal("0.00"), products__is_available=True),
            ),
            price_min_agg=Min(
                "products__selling_price",
                filter=Q(products__selling_price__gt=Decimal("0.00"), products__is_available=True),
            ),
        )
        .order_by("display_order", "id")
    )

    rows: List[IndexRow] = []
    for cat in categories:
        count = cat.purchasable_count
        price_from = cat.price_min_agg or Decimal("0.00")

        pick = (
            Product.objects.filter(
                category=cat,
                selling_price__gt=Decimal("0.00"),
                is_available=True,
            )
            .select_related("category")
            .prefetch_related("media", "specifications")
            .order_by("-source_rating_count", "selling_price", "id")
            .first()
        )

        rows.append(
            IndexRow(
                category=cat,
                count=count,
                price_from=price_from,
                pick=pick,
            )
        )

    return rows


def brand_list(max_brands: int = 40) -> List[BrandItem]:
    """
    Returns allow-listed brands with real purchasable listing counts.
    """
    known_brands = get_known_brands()
    brand_aggs = (
        Product.objects.filter(
            parsed_brand__in=known_brands,
            selling_price__gt=Decimal("0.00"),
            is_available=True,
        )
        .values("parsed_brand")
        .annotate(prod_count=Count("id"))
        .order_by("-prod_count", "parsed_brand")[:max_brands]
    )

    return [
        BrandItem(name=item["parsed_brand"], product_count=item["prod_count"])
        for item in brand_aggs
    ]
