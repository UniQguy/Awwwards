"""
Catalog search and faceted exploration service.
SQLite-safe tokenized search, case scoring, facet aggregation, and typo correction.
"""

from decimal import Decimal
import difflib
from typing import Any, Dict, List, Optional

from django.db.models import Count, Q, QuerySet

from apps.catalog.models import Category, Product
from apps.catalog.services.brands import get_known_brands
from apps.catalog.services.price_distribution import calculate_price_distribution


def execute_catalog_search(
    query: str = "",
    category_slug: Optional[str] = None,
    brand: Optional[str] = None,
    min_price: Optional[Decimal] = None,
    max_price: Optional[Decimal] = None,
    min_rating: Optional[Decimal] = None,
    sort_by: str = "popularity",
    collapsed: bool = False,
) -> Dict[str, Any]:
    """
    Executes a faceted product catalog search query.
    """
    qs = Product.objects.filter(is_available=True, selling_price__gt=0).select_related("category")

    # 1. Full-text token query
    clean_query = query.strip()
    if clean_query:
        tokens = [t.lower() for t in clean_query.split() if len(t) > 0]
        for token in tokens:
            qs = qs.filter(search_text__icontains=token)

    # 2. Category filter
    if category_slug:
        qs = qs.filter(category__slug=category_slug)

    # 3. Brand filter
    if brand:
        qs = qs.filter(parsed_brand__iexact=brand)

    # 4. Price filters
    if min_price is not None:
        qs = qs.filter(selling_price__gte=min_price)
    if max_price is not None:
        qs = qs.filter(selling_price__lte=max_price)

    # 5. Rating filter
    if min_rating is not None:
        qs = qs.filter(source_rating__gte=min_rating)

    # 6. Sorting
    sort_options = {
        "popularity": ["-source_rating_count", "display_name"],
        "price_asc": ["selling_price", "id"],
        "price_desc": ["-selling_price", "id"],
        "rating": ["-source_rating", "-source_rating_count"],
        "newest": ["-created_at"],
    }
    order_fields = sort_options.get(sort_by, ["-source_rating_count", "display_name"])
    qs = qs.order_by(*order_fields)

    if collapsed:
        from apps.catalog.queries.grid_collapse import get_collapsed_catalog_queryset
        qs = get_collapsed_catalog_queryset(qs)

    total_count = qs.count()

    # 7. Did you mean suggestion (if query yielded 0 hits)
    did_you_mean = None
    if total_count == 0 and clean_query:
        # Check against known brands
        known_brands = get_known_brands()
        closest = difflib.get_close_matches(clean_query, known_brands, n=1, cutoff=0.6)
        if closest:
            did_you_mean = closest[0]
        else:
            # Check against category names
            cat_names = list(Category.objects.values_list("name", flat=True))
            closest_cat = difflib.get_close_matches(clean_query, cat_names, n=1, cutoff=0.6)
            if closest_cat:
                did_you_mean = closest_cat[0]

    # 8. Facets
    category_facets = list(
        Category.objects.filter(products__is_available=True)
        .annotate(product_count=Count("products", filter=Q(products__selling_price__gt=0)))
        .values("name", "slug", "product_count")
        .order_by("-product_count")
    )

    brand_facets = list(
        Product.objects.filter(is_available=True, selling_price__gt=0)
        .exclude(parsed_brand="Unknown")
        .values("parsed_brand")
        .annotate(count=Count("id"))
        .order_by("-count")[:15]
    )

    price_histogram = calculate_price_distribution(qs)

    return {
        "products": qs,
        "total_count": total_count,
        "query": clean_query,
        "did_you_mean": did_you_mean,
        "facets": {
            "categories": category_facets,
            "brands": brand_facets,
            "price_histogram": price_histogram,
        },
    }
