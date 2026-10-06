"""
Storefront views for catalog browsing, categorization, product detail, and comparisons.
"""

from collections import defaultdict
from decimal import Decimal
import urllib.parse

from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from apps.catalog.models import Category, Collection, Product
from apps.catalog.services.price_distribution import PRICE_BRACKETS
from apps.search.services.search_service import execute_catalog_search
from apps.shipping.services.estimator import estimate_delivery


@require_GET
def home(request: HttpRequest) -> HttpResponse:
    """
    Storefront editorial homepage displaying catalog statistics, collections, and categories.
    """
    total_products_count = Product.objects.filter(is_available=True, selling_price__gt=0).count()
    categories_count = Category.objects.filter(is_active=True).count()

    featured_collections = (
        Collection.objects.filter(is_active=True)
        .prefetch_related(
            "featured_items__product__media",
            "featured_items__product__category",
        )
        .order_by("display_order", "title")[:4]
    )

    categories = list(
        Category.objects.filter(is_active=True)
        .order_by("display_order", "name")
    )

    context = {
        "total_products_count": total_products_count,
        "categories_count": categories_count,
        "featured_collections": featured_collections,
        "categories": categories,
    }
    return render(request, "catalog/home.html", context)


@require_GET
def category_list(request: HttpRequest) -> HttpResponse:
    """
    Index of all active merchandise categories with real-time product counts.
    """
    categories = (
        Category.objects.filter(is_active=True)
        .annotate(
            product_count=Count(
                "products",
                filter=Q(products__is_available=True, products__selling_price__gt=0),
            )
        )
        .order_by("display_order", "name")
    )
    return render(request, "catalog/category_list.html", {"categories": categories})


@require_GET
def category_detail(request: HttpRequest, slug: str) -> HttpResponse:
    """
    Faceted category catalog page with price brackets, brand filtering, and pagination.
    """
    category = get_object_or_404(Category, slug=slug, is_active=True)

    # Filter arguments
    brand = request.GET.get("brand", "").strip() or None
    sort_by = request.GET.get("sort", "popularity").strip()
    collapsed = request.GET.get("collapsed", "0") == "1"

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
        query="",
        category_slug=category.slug,
        brand=brand,
        min_price=min_price_val,
        max_price=max_price_val,
        sort_by=sort_by,
        collapsed=collapsed,
    )

    products_qs = search_result["products"].prefetch_related("media")

    paginator = Paginator(products_qs, 24)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    # Build querystring preserving parameters without page
    params = request.GET.copy()
    if "page" in params:
        del params["page"]
    querystring = params.urlencode()

    context = {
        "category": category,
        "page_obj": page_obj,
        "facets": search_result["facets"],
        "selected_filters": {
            "brand": brand,
            "min_price": min_price_val,
            "max_price": max_price_val,
            "bracket": bracket_idx,
        },
        "sort_by": sort_by,
        "collapsed": collapsed,
        "price_bars": search_result["facets"]["price_histogram"],
        "querystring": querystring,
        "breadcrumbs": [
            {"title": "Categories", "url": "/categories/"},
            {"title": category.name, "url": f"/c/{category.slug}/"},
        ],
    }
    return render(request, "catalog/category_detail.html", context)


@require_GET
def product_detail(request: HttpRequest, slug: str) -> HttpResponse:
    """
    Detailed product presentation including specifications, media, ratings, and pincode check.
    """
    product = get_object_or_404(
        Product.objects.select_related("category", "inventory").prefetch_related(
            "specifications", "media"
        ),
        slug=slug,
    )

    media_items = list(product.media.all())
    specifications = list(product.specifications.all())

    # Related items in category
    related_products = (
        Product.objects.filter(category=product.category, is_available=True, selling_price__gt=0)
        .exclude(id=product.id)
        .prefetch_related("media")[:4]
    )

    # Variant options by same brand in category
    other_variants = (
        Product.objects.filter(
            category=product.category,
            parsed_brand=product.parsed_brand,
            is_available=True,
            selling_price__gt=0,
        )
        .exclude(id=product.id)
        .prefetch_related("media")[:5]
    )

    # Delivery estimate lookup from session
    remembered_pincode = request.session.get("pincode", "")
    delivery_estimate = None
    if remembered_pincode:
        delivery_estimate = estimate_delivery(remembered_pincode)

    context = {
        "product": product,
        "specifications": specifications,
        "media_items": media_items,
        "option_count": other_variants.count(),
        "other_variants": other_variants,
        "related_products": related_products,
        "delivery_estimate": delivery_estimate,
        "remembered_pincode": remembered_pincode,
        "max_cart_qty": getattr(settings, "CART_MAX_QTY_PER_LINE", 10),
        "breadcrumbs": [
            {"title": "Categories", "url": "/categories/"},
            {"title": product.category.name, "url": f"/c/{product.category.slug}/"},
            {"title": product.display_name, "url": f"/p/{product.slug}/"},
        ],
    }
    return render(request, "catalog/product_detail.html", context)


@require_GET
def brand_list(request: HttpRequest) -> HttpResponse:
    """
    Alphabetical index of all catalog brands with active product tallies.
    """
    brand_counts = (
        Product.objects.filter(is_available=True, selling_price__gt=0)
        .exclude(parsed_brand="Unknown")
        .values("parsed_brand")
        .annotate(count=Count("id"))
        .order_by("parsed_brand")
    )

    brands_grouped = defaultdict(list)
    for b in brand_counts:
        name = b["parsed_brand"]
        first_char = name[0].upper() if name and name[0].isalpha() else "#"
        brands_grouped[first_char].append({"name": name, "count": b["count"]})

    # Sort groups alphabetically
    sorted_groups = sorted(brands_grouped.items(), key=lambda x: (x[0] == "#", x[0]))

    return render(
        request,
        "catalog/brand_list.html",
        {
            "brands_grouped": sorted_groups,
            "breadcrumbs": [{"title": "Brands", "url": "/brands/"}],
        },
    )


# ==============================================================================
# PRODUCT COMPARISON TRAY
# ==============================================================================


@require_GET
def compare_tray(request: HttpRequest) -> HttpResponse:
    """
    Presents side-by-side spec comparison table for up to 3 products in the same category.
    """
    tray_ids = request.session.get("compare_tray", [])
    products = list(
        Product.objects.filter(id__in=tray_ids)
        .select_related("category")
        .prefetch_related("specifications", "media")
    )

    # Build spec matrix
    spec_matrix = {}
    common_category = products[0].category if products else None

    if products:
        all_keys = set()
        for p in products:
            for s in p.specifications.all():
                all_keys.add(s.key)

        sorted_keys = sorted(all_keys)
        for key in sorted_keys:
            spec_matrix[key] = {}
            for p in products:
                match = next((s.value for s in p.specifications.all() if s.key == key), "—")
                spec_matrix[key][p.id] = match

    context = {
        "compared_products": products,
        "spec_matrix": spec_matrix,
        "common_category": common_category,
        "breadcrumbs": [{"title": "Product Comparison", "url": "/compare/"}],
    }
    return render(request, "catalog/compare.html", context)


@require_POST
def compare_add(request: HttpRequest, product_id: int) -> HttpResponseRedirect:
    """
    Adds a product to the comparison tray, validating limit (3) and category homogeneity.
    """
    product = get_object_or_404(Product, id=product_id)
    tray = list(request.session.get("compare_tray", []))

    referrer = request.META.get("HTTP_REFERER") or "/"

    if product.id in tray:
        messages.info(request, f"{product.display_name} is already in the comparison tray.")
        return redirect(referrer)

    if len(tray) >= 3:
        messages.warning(request, "You can compare up to 3 products at a time. Remove one to add another.")
        return redirect(referrer)

    if tray:
        first_product = Product.objects.filter(id=tray[0]).first()
        if first_product and first_product.category_id != product.category_id:
            messages.error(
                request,
                f"Comparison is restricted to products in the same category ({first_product.category.name}).",
            )
            return redirect(referrer)

    tray.append(product.id)
    request.session["compare_tray"] = tray
    request.session.modified = True
    messages.success(request, f"Added {product.display_name} to comparison.")
    return redirect(referrer)


@require_POST
def compare_remove(request: HttpRequest, product_id: int) -> HttpResponseRedirect:
    """
    Removes a product from the active comparison tray.
    """
    tray = list(request.session.get("compare_tray", []))
    if product_id in tray:
        tray.remove(product_id)
        request.session["compare_tray"] = tray
        request.session.modified = True
        messages.success(request, "Product removed from comparison tray.")

    referrer = request.META.get("HTTP_REFERER") or "/compare/"
    return redirect(referrer)


@require_POST
def compare_clear(request: HttpRequest) -> HttpResponseRedirect:
    """
    Clears all items from the active comparison tray.
    """
    request.session["compare_tray"] = []
    request.session.modified = True
    messages.info(request, "Comparison tray cleared.")
    referrer = request.META.get("HTTP_REFERER") or "/"
    return redirect(referrer)
