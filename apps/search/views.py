"""
Storefront search views: full-text faceted search and typeahead suggestions.
"""

from decimal import Decimal
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from django_ratelimit.decorators import ratelimit

from apps.catalog.models import Category, Product
from apps.catalog.services.brands import get_known_brands
from apps.catalog.services.price_distribution import PRICE_BRACKETS
from apps.search.services.search_service import execute_catalog_search


@require_GET
def search_view(request: HttpRequest) -> HttpResponse:
    """
    Faceted search results page with token scoring, spelling correction, and filters.
    """
    query = request.GET.get("q", "").strip()
    category_slug = request.GET.get("category", "").strip() or request.GET.get("c", "").strip() or None
    brand = request.GET.get("brand", "").strip() or None
    sort_by = request.GET.get("sort", "popularity").strip()

    min_price_val = None
    max_price_val = None
    min_rating_val = None

    if request.GET.get("rating"):
        try:
            min_rating_val = Decimal(request.GET.get("rating").strip())
        except Exception:
            pass

    bracket_idx = request.GET.get("bracket")
    if bracket_idx is not None and bracket_idx != "":
        try:
            b_idx = int(bracket_idx)
            if 0 <= b_idx < len(PRICE_BRACKETS):
                bracket = PRICE_BRACKETS[b_idx]
                min_price_val = bracket["min"]
                max_price_val = bracket["max"]
        except (ValueError, TypeError):
            pass

    if min_price_val is None and request.GET.get("min_price"):
        try:
            min_price_val = Decimal(request.GET.get("min_price").strip())
        except Exception:
            pass

    if max_price_val is None and request.GET.get("max_price"):
        try:
            max_price_val = Decimal(request.GET.get("max_price").strip())
        except Exception:
            pass

    search_result = execute_catalog_search(
        query=query,
        category_slug=category_slug,
        brand=brand,
        min_price=min_price_val,
        max_price=max_price_val,
        min_rating=min_rating_val,
        sort_by=sort_by,
    )

    products_qs = search_result["products"]

    paginator = Paginator(products_qs, 24)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    params = request.GET.copy()
    if "page" in params:
        del params["page"]
    querystring = params.urlencode()

    context = {
        "query": query,
        "page_obj": page_obj,
        "total_count": search_result["total_count"],
        "facets": search_result["facets"],
        "did_you_mean": search_result["did_you_mean"],
        "is_fallback": search_result.get("is_fallback", False),
        "fallback_label": search_result.get("fallback_label", ""),
        "selected_filters": {
            "category": category_slug,
            "brand": brand,
            "bracket": bracket_idx,
            "min_price": min_price_val,
            "max_price": max_price_val,
            "rating": request.GET.get("rating", "").strip(),
        },
        "sort_by": sort_by,
        "querystring": querystring,
        "breadcrumbs": [{"title": f"Search: {query or 'All'}", "url": f"/search/?q={query}"}],
    }
    return render(request, "search/search_results.html", context)


@ratelimit(key="ip", rate="60/m", block=False)
@require_GET
def search_suggest(request: HttpRequest) -> JsonResponse:
    """
    Fast JSON suggestion endpoint returning matching products, categories, and brands (max 8).
    """
    if getattr(request, "limited", False):
        return JsonResponse({"error": "Rate limit exceeded."}, status=429)

    query = request.GET.get("q", "").strip().lower()
    if len(query) < 2:
        return JsonResponse({"products": [], "categories": [], "brands": []})

    # 1. Matching categories (max 2) with counts
    from django.db.models import Count, Q
    categories = [
        {
            "name": c.name,
            "slug": c.slug,
            "url": f"/c/{c.slug}/",
            "count": c.product_count,
        }
        for c in Category.objects.filter(is_active=True, name__icontains=query)
        .annotate(product_count=Count("products", filter=Q(products__is_available=True)))
        .order_by("name")[:2]
    ]

    # 2. Matching brands (max 3) with live counts
    known_brands = get_known_brands()
    matching_brands_raw = [b for b in known_brands if query in b.lower()][:3]
    brand_items = []
    for b in matching_brands_raw:
        b_count = Product.objects.filter(is_available=True, parsed_brand__iexact=b).count()
        brand_items.append({
            "name": b,
            "url": f"/search/?brand={b}",
            "count": b_count,
        })

    # 3. Matching products using ranked search (up to max 5)
    remaining_slots = min(5, max(1, 8 - len(categories) - len(brand_items)))
    search_res = execute_catalog_search(query=query, collapsed=True)
    product_objs = search_res["products"][:remaining_slots]
    products = [
        {
            "id": p.id,
            "display_name": p.display_name,
            "slug": p.slug,
            "selling_price": str(p.selling_price) if p.selling_price else None,
            "parsed_brand": p.parsed_brand or "",
            "image_url": p.primary_image_url,
            "url": f"/p/{p.slug}/",
            "option_count": getattr(p, "option_count", 1),
        }
        for p in product_objs
    ]

    return JsonResponse({
        "products": products,
        "categories": categories,
        "brands": matching_brands_raw,
        "brand_items": brand_items,
    })
