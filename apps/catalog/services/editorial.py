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


def hero_products(n: int = 3) -> HeroResult:
    """
    Returns hero products for the homepage.
    Checks for active Collection with placement='home_hero'.
    Fallback auto-select: priced, available, in-stock products with an image,
    ranked by source_rating_count descending, one per category, deterministic.
    """
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

    # 2. Fallback auto-select
    # Order by rating count desc, selling price desc, id
    candidates = (
        Product.objects.filter(
            selling_price__gt=Decimal("0.00"),
            is_available=True,
            media__media_type="image",
        )
        .select_related("category")
        .prefetch_related("media", "specifications")
        .distinct()
        .order_by("-source_rating_count", "-selling_price", "id")
    )

    selected: List[Product] = []
    seen_categories = set()

    for p in candidates:
        if p.category_id not in seen_categories:
            seen_categories.add(p.category_id)
            selected.append(p)
            if len(selected) >= n:
                break

    return HeroResult(products=selected, is_auto=True)


def home_chapters(max_chapters: int = 6) -> List[HomeChapter]:
    """
    Active categories with at least 4 purchasable products, ordered by display_order.
    Each with up to 4 picks (curated collection else auto-selected by rating then price),
    plus real stats from the database (never hardcoded).
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
        .filter(purchasable_count__gt=0)
        .order_by("display_order", "id")
    )

    if not cats:
        return []

    cats_with_4 = [c for c in cats if c.purchasable_count >= 4]
    cat_list = cats_with_4[:max_chapters] if cats_with_4 else list(cats[:max_chapters])
    cat_ids = [c.id for c in cat_list]

    # Pre-fetch curated chapter collections for these categories
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

        # Picks
        col = curated_map.get(cat.id)
        if col:
            picks = [
                fp.product
                for fp in col.featured_items.all()
                if fp.product.is_purchasable
            ][:4]
            is_auto = False
        else:
            picks = []
            is_auto = True

        if not picks:
            picks = list(
                Product.objects.filter(
                    category=cat,
                    selling_price__gt=Decimal("0.00"),
                    is_available=True,
                )
                .select_related("category")
                .prefetch_related("media", "specifications")
                .order_by("-source_rating_count", "selling_price", "id")[:4]
            )
            is_auto = True

        # Factual editorial line
        if col and col.title:
            editorial_line = f"{col.title}: {col.intro}" if col.intro else col.title
        elif cat.description and cat.description.strip():
            editorial_line = cat.description.strip()
        else:
            editorial_line = f"{p_count} listings from ₹{p_min} to ₹{p_max}."

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


def category_spread(category: Category) -> CategorySpreadResult:
    """
    Generates real stats and up to 4 picks for a category marquee spread.
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
        ][:4]
        is_auto = False
    else:
        picks = []
        is_auto = True

    if not picks:
        picks = list(
            base_qs.select_related("category")
            .prefetch_related("media", "specifications")
            .order_by("-source_rating_count", "selling_price", "id")[:4]
        )
        is_auto = True

    if category.description and category.description.strip():
        editorial_line = category.description.strip()
    else:
        editorial_line = f"{listing_count} listings from ₹{price_min} to ₹{price_max}."

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
