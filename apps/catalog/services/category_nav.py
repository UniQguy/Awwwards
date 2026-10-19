"""
Service to provide enriched, cached category navigation metadata for the header mega-menu.
Includes product counts, starting prices, top 5 brands, and representative thumbnail cutouts.
"""

from decimal import Decimal
from typing import List
from django.conf import settings
from django.core.cache import cache
from django.db.models import Count, Min, Q

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
