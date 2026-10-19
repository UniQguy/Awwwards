"""
Storefront views for catalog browsing, categorization, product detail, and comparisons.
"""

from collections import defaultdict
from decimal import Decimal
import urllib.parse

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Count, Max, Min, Q
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from django.utils import timezone

from apps.catalog.models import Category, Collection, Product
from apps.promotions.models import Coupon
from apps.catalog.services.editorial import (
    brand_list as get_editorial_brands,
    category_spread,
    eligible_cutout_products,
    hero_products,
    home_chapters,
    home_headline_cutouts,
    index_rows,
)
from apps.catalog.services.price_distribution import PRICE_BRACKETS
from apps.search.services.search_service import execute_catalog_search
from apps.shipping.models import ShippingConfig
from apps.shipping.services.estimator import estimate_delivery


@require_GET
def home(request: HttpRequest) -> HttpResponse:
    """
    Storefront editorial homepage displaying the Kinetic Monograph:
    - Hero with headline cutouts and single collectible plate
    - Typographic category index
    - Chapters per active category with real stats and plates
    - How buying works here (live config: GST, shipping threshold, payments)
    - Allow-listed brand flowing paragraph
    - Closing line
    """
    # 1. Hero
    hero_res = hero_products(n=4)
    hero_plate_product = hero_res.products[0] if hero_res.products else None
    hero_picker_products = hero_res.products[1:4] if len(hero_res.products) > 1 else []
    headline_cutouts = home_headline_cutouts()
    cutout_cable = headline_cutouts.get("cable")
    cutout_watch = headline_cutouts.get("watch")
    cutout_earphones = headline_cutouts.get("earphones")
    cutouts = [c for c in [cutout_cable, cutout_watch, cutout_earphones] if c is not None]

    # 2. Stats for live hero sentence
    total_listings = Product.objects.filter(is_available=True, selling_price__gt=0).count()
    total_categories = Category.objects.filter(is_active=True).count()
    min_price_agg = Product.objects.filter(is_available=True, selling_price__gt=0).aggregate(Min("selling_price"))
    min_price = min_price_agg["selling_price__min"] or Decimal("0.00")

    # 3. Categories Snap-Rail (10 tiles, WP3)
    from apps.catalog.services.category_nav import get_mega_menu_categories
    categories_rail = get_mega_menu_categories()

    # 4. Typographic Index Rows (legacy fallback)
    index_list = index_rows()

    # 5. Chapters: Top 3 categories only, 4 picks each (WP3)
    chapters = home_chapters(max_chapters=3, picks_per_chapter=4)

    # 6. How Buying Works data
    shipping_config = ShippingConfig.get_solo()
    free_shipping_threshold = shipping_config.free_shipping_threshold
    standard_shipping_fee = shipping_config.standard_fee
    shipping_fee_confirmed = shipping_config.is_standard_fee_confirmed
    seller_gstin = getattr(settings, "SELLER_GSTIN", "")
    is_bill_of_supply = not bool(seller_gstin)
    razorpay_enabled = bool(getattr(settings, "RAZORPAY_KEY_ID", ""))

    # 7. Brands
    brands = get_editorial_brands(max_brands=35)

    # 8. Cutout cycling data for Technique A progressive enhancement (in-memory, 0 extra queries)
    cycle_candidates = list(hero_res.products)
    for ch in chapters:
        cycle_candidates.extend(ch.picks)
    seen_ids = set()
    cutout_cycle_data = []
    for p in cycle_candidates:
        if p.id not in seen_ids and p.primary_image_url:
            seen_ids.add(p.id)
            cutout_cycle_data.append({
                "id": p.id,
                "name": p.display_name,
                "image_url": p.primary_image_url,
            })
            if len(cutout_cycle_data) >= 10:
                break

    # 9. Curated Stories (2 collections with 3 items each, WP3)
    from apps.catalog.models import FeaturedProduct
    from django.db.models import Prefetch
    curated_stories = list(
        Collection.objects.filter(is_active=True)
        .exclude(placement=Collection.PLACEMENT_HOME_HERO)
        .prefetch_related(
            Prefetch(
                "featured_items",
                queryset=FeaturedProduct.objects.select_related("product__category")
                .prefetch_related("product__media")
                .order_by("display_order", "id"),
            )
        )[:2]
    )

    # 10. Budget Ladder (4 price brackets with count and sample thumbnails, WP3)
    p_qs = Product.objects.filter(is_available=True, selling_price__gt=0)
    b_aggs = p_qs.aggregate(
        c_500=Count("id", filter=Q(selling_price__lte=500)),
        c_1500=Count("id", filter=Q(selling_price__gt=500, selling_price__lte=1500)),
        c_5000=Count("id", filter=Q(selling_price__gt=1500, selling_price__lte=5000)),
        c_prem=Count("id", filter=Q(selling_price__gt=5000)),
    )
    budget_ladder = [
        {
            "title": "Under ₹500",
            "count": b_aggs["c_500"] or 0,
            "url": "/search/?max_price=500",
            "samples": [p for p in cycle_candidates if p.selling_price and p.selling_price <= 500 and p.primary_image_url][:3],
        },
        {
            "title": "Under ₹1,500",
            "count": b_aggs["c_1500"] or 0,
            "url": "/search/?min_price=501&max_price=1500",
            "samples": [p for p in cycle_candidates if p.selling_price and 500 < p.selling_price <= 1500 and p.primary_image_url][:3],
        },
        {
            "title": "Under ₹5,000",
            "count": b_aggs["c_5000"] or 0,
            "url": "/search/?min_price=1501&max_price=5000",
            "samples": [p for p in cycle_candidates if p.selling_price and 1500 < p.selling_price <= 5000 and p.primary_image_url][:3],
        },
        {
            "title": "Premium Grade",
            "count": b_aggs["c_prem"] or 0,
            "url": "/search/?min_price=5001",
            "samples": [p for p in cycle_candidates if p.selling_price and p.selling_price > 5000 and p.primary_image_url][:3],
        },
    ]

    context = {
        "hero": hero_res,
        "hero_plate_product": hero_plate_product,
        "hero_picker_products": hero_picker_products,
        "cutout_cable": cutout_cable,
        "cutout_watch": cutout_watch,
        "cutout_earphones": cutout_earphones,
        "cutouts": cutouts,
        "cutout_cycle_data": cutout_cycle_data,
        "total_listings": total_listings,
        "total_categories": total_categories,
        "min_price": min_price,
        "categories_rail": categories_rail,
        "index_rows": index_list,
        "chapters": chapters,
        "curated_stories": curated_stories,
        "budget_ladder": budget_ladder,
        "free_shipping_threshold": free_shipping_threshold,
        "standard_shipping_fee": standard_shipping_fee,
        "shipping_fee_confirmed": shipping_fee_confirmed,
        "is_bill_of_supply": is_bill_of_supply,
        "razorpay_enabled": razorpay_enabled,
        "brands": brands,
    }
    return render(request, "catalog/home.html", context)


@require_GET
def category_list(request: HttpRequest) -> HttpResponse:
    """
    Monograph category index: one tall spread per active category alternating left and right offsets,
    each with category name in display-l, live stats in marginalia, one pick on a plate, and an Enter link.
    """
    categories = list(Category.objects.filter(is_active=True).order_by("display_order", "name"))
    category_spreads = [category_spread(cat) for cat in categories]
    total_listings = Product.objects.filter(is_available=True, selling_price__gt=0).count()
    price_aggs = Product.objects.filter(is_available=True, selling_price__gt=0).aggregate(
        min_price=Min("selling_price"),
        max_price=Max("selling_price"),
    )
    min_price = price_aggs["min_price"] or Decimal("0.00")
    max_price = price_aggs["max_price"] or Decimal("0.00")
    return render(
        request,
        "catalog/category_list.html",
        {
            "category_spreads": category_spreads,
            "total_listings": total_listings,
            "min_price": min_price,
            "max_price": max_price,
        },
    )


@require_GET
def category_detail(request: HttpRequest, slug: str) -> HttpResponse:
    """
    Faceted category catalog page with price brackets, brand filtering, and pagination.
    Top editorial marquee displays only on page 1 with no active filters.
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

    # Check whether editorial marquee should show (page 1, zero search/filter/sort parameters)
    page_param = request.GET.get("page", "1")
    is_page_1 = str(page_param) in ("1", "", "None")
    has_active_filters = bool(
        brand
        or bracket_idx
        or request.GET.get("min_price")
        or request.GET.get("max_price")
        or (sort_by and sort_by != "popularity")
        or collapsed
    )
    show_marquee = is_page_1 and not has_active_filters

    spread = category_spread(category, max_picks=6) if show_marquee else None

    search_result = execute_catalog_search(
        query="",
        category_slug=category.slug,
        brand=brand,
        min_price=min_price_val,
        max_price=max_price_val,
        sort_by=sort_by,
        collapsed=collapsed,
    )

    products_qs = search_result["products"]

    paginator = Paginator(products_qs, 24)
    page_obj = paginator.get_page(page_param)

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
        "show_marquee": show_marquee,
        "spread": spread,
        "breadcrumbs": [
            {"title": "Categories", "url": "/categories/"},
            {"title": category.name, "url": f"/c/{category.slug}/"},
        ],
    }
    return render(request, "catalog/category_detail.html", context)


@require_GET
def category_price_count(request: HttpRequest, slug: str) -> HttpResponse:
    """
    Lightweight, rate-limited JSON endpoint returning product count for given filter parameters.
    Used by dual-thumb slider for progressive enhancement count hints.
    """
    category = get_object_or_404(Category, slug=slug, is_active=True)

    # Rate limiting: max 120 calls per minute per client IP
    client_ip = (
        request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", "127.0.0.1"))
        .split(",")[0]
        .strip()
    )
    cache_key = f"rl_price_count_{client_ip}"
    req_count = cache.get(cache_key, 0)
    if req_count >= 120:
        return JsonResponse({"error": "Rate limit exceeded"}, status=429)
    cache.set(cache_key, req_count + 1, timeout=60)

    brand = request.GET.get("brand", "").strip() or None
    collapsed = request.GET.get("collapsed", "0") in ("1", "true", "True")

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
        collapsed=collapsed,
    )

    return JsonResponse({
        "count": search_result["total_count"],
        "category": category.slug,
        "brand": brand,
        "min_price": str(min_price_val) if min_price_val is not None else None,
        "max_price": str(max_price_val) if max_price_val is not None else None,
        "collapsed": collapsed,
    })


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

    # Related items in category (prefetches media & specifications for comparison table)
    related_products = list(
        Product.objects.filter(category=product.category, is_available=True, selling_price__gt=0)
        .exclude(id=product.id)
        .select_related("category", "inventory")
        .prefetch_related("media", "specifications")[:4]
    )

    # Variant options: check for same raw_name first, then same brand in category
    same_raw_name = list(
        Product.objects.filter(raw_name=product.raw_name, is_available=True, selling_price__gt=0)
        .exclude(id=product.id)
        .select_related("category", "inventory")
        .prefetch_related("media")[:6]
    )
    if same_raw_name:
        other_variants = same_raw_name
    else:
        other_variants = list(
            Product.objects.filter(
                category=product.category,
                parsed_brand=product.parsed_brand,
                is_available=True,
                selling_price__gt=0,
            )
            .exclude(id=product.id)
            .select_related("category", "inventory")
            .prefetch_related("media")[:5]
        )

    # Delivery estimate lookup from session
    remembered_pincode = request.session.get("pincode", "")
    delivery_estimate = None
    if remembered_pincode:
        delivery_estimate = estimate_delivery(remembered_pincode)

    # Active available coupons applicable to this product category
    now = timezone.now()
    available_coupons = list(
        Coupon.objects.filter(is_active=True)
        .filter(Q(valid_from__isnull=True) | Q(valid_from__lte=now))
        .filter(Q(valid_until__isnull=True) | Q(valid_until__gte=now))
        .filter(Q(applicable_categories=product.category) | Q(applicable_categories__isnull=True))
        .distinct()[:3]
    )

    # 3 Nearest-priced items in the same category for comparison table (WP6)
    comparison_products = []
    comp_rows = []
    if product.selling_price and related_products:
        candidates = list(related_products)
        candidates.sort(key=lambda p: abs(p.selling_price - product.selling_price))
        comparison_products = candidates[:3]

        prod_spec_dict = {s.key: s.value for s in specifications}
        comp_spec_dicts = [{s.key: s.value for s in cp.specifications.all()} for cp in comparison_products]

        all_keys = list(prod_spec_dict.keys())
        for cd in comp_spec_dicts:
            for k in cd.keys():
                if k not in all_keys:
                    all_keys.append(k)

        for k in all_keys[:6]:
            comp_rows.append({
                "key": k,
                "product_val": prod_spec_dict.get(k, "\u2014"),
                "comp_vals": [cd.get(k, "\u2014") for cd in comp_spec_dicts],
            })

    context = {
        "product": product,
        "specifications": specifications,
        "media_items": media_items,
        "option_count": len(other_variants),
        "other_variants": other_variants,
        "related_products": related_products,
        "comparison_products": comparison_products,
        "comp_rows": comp_rows,
        "delivery_estimate": delivery_estimate,
        "remembered_pincode": remembered_pincode,
        "available_coupons": available_coupons,
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
