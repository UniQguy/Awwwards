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
    category_slug = request.GET.get("c", "").strip() or None
    brand = request.GET.get("brand", "").strip() or None
    sort_by = request.GET.get("sort", "popularity").strip()

    min_price_val = None
    max_price_val = None

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
        sort_by=sort_by,
    )

    products_qs = search_result["products"].select_related("inventory").prefetch_related("media")

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
        "selected_filters": {
            "category": category_slug,
            "brand": brand,
            "bracket": bracket_idx,
            "min_price": min_price_val,
            "max_price": max_price_val,
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

    # 1. Matching categories (max 2)
    categories = list(
        Category.objects.filter(is_active=True, name__icontains=query)
        .values("name", "slug")[:2]
    )

    # 2. Matching brands (max 2)
    known_brands = get_known_brands()
    matching_brands = [b for b in known_brands if query in b.lower()][:2]

    # 3. Matching products (max 4)
    products = list(
        Product.objects.filter(is_available=True, selling_price__gt=0, search_text__icontains=query)
        .values("id", "display_name", "slug", "selling_price", "parsed_brand")[:4]
    )

    return JsonResponse({
        "products": products,
        "categories": categories,
        "brands": matching_brands,
    })
