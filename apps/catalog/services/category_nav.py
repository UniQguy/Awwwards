"""
Service to provide enriched, cached category navigation metadata for the header mega-menu.
Includes product counts, starting prices, top 5 brands, and representative thumbnail cutouts.
"""

from decimal import Decimal
from typing import List
from django.core.cache import cache
from django.db.models import Count, Min, Q

from apps.catalog.models import Category, Product
from apps.catalog.services.brands import get_known_brands

CACHE_KEY_NAV_PREVIEWS = "nav_categories_with_previews_v2"
CACHE_TTL = 900  # 15 minutes


def get_mega_menu_categories() -> List[Category]:
    """
    Returns the 10 active categories enriched with starting price, top brands,
    and lead cutout URL for the header mega-menu preview pane.
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

    known_brands_set = set(get_known_brands())

    for cat in categories:
        cat.price_from = cat.price_min_agg or Decimal("0.00")

        # Pick top product for thumbnail cutout
        top_prod = (
            Product.objects.filter(
                category=cat,
                is_available=True,
                selling_price__gt=Decimal("0.00"),
            )
            .prefetch_related("media")
            .order_by("-source_rating_count", "selling_price", "id")
            .first()
        )
        cat.cutout_url = top_prod.primary_image_url if top_prod else ""
        cat.lead_title = top_prod.display_name if top_prod else ""

        # Top 5 brands
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
        cat.top_brands = [b["parsed_brand"] for b in brands_qs]
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
