"""
Storefront views for catalog browsing, categorization, product detail, and comparisons.
"""

from collections import defaultdict
from decimal import Decimal
import json
import re
from typing import Any, Dict, List, Optional
import urllib.parse

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Count, F, Max, Min, Q
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from django.utils import timezone

from apps.catalog.models import Category, Collection, Product, ProductReview
from apps.orders.models import Order
from apps.promotions.models import Coupon
from apps.promotions.services.coupon_validator import get_best_coupon_for_product
from apps.core.templatetags.core_tags import inr
from apps.catalog.services.editorial import (
    brand_list as get_editorial_brands,
    category_spread,
    eligible_cutout_products,
    get_flagship_anatomy_layers,
    hero_products,
    home_chapters,
    home_headline_cutouts,
    index_rows,
)
from apps.catalog.services.price_distribution import PRICE_BRACKETS
from apps.catalog.services.spec_extractor import classify_product_subtype
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
    # 1. Hero & Flagship Anatomy
    hero_res = hero_products(n=4)
    hero_flagships = hero_res.products[:4]
    hero_plate_product = hero_flagships[0] if hero_flagships else None
    hero_picker_products = hero_flagships[1:4] if len(hero_flagships) > 1 else []

    hero_flagships_data = []
    for p in hero_flagships:
        layers = getattr(p, "anatomy_layers", None)
        if not layers:
            layers = get_flagship_anatomy_layers(p)
            p.anatomy_layers = layers
        best_c = get_best_coupon_for_product(p)
        eff_p = best_c["effective_price"] if best_c else p.selling_price
        savings_val = (p.mrp - p.selling_price) if (p.mrp and p.mrp > p.selling_price) else Decimal("0.00")
        hero_flagships_data.append({
            "id": p.id,
            "slug": p.slug,
            "title": p.display_name,
            "short_title": p.display_name.split("(")[0].strip()[:32],
            "brand": p.parsed_brand or "",
            "category_name": p.category.name if p.category else "",
            "category_slug": p.category.slug if p.category else "",
            "selling_price": inr(p.selling_price),
            "mrp": inr(p.mrp) if p.mrp and p.mrp > p.selling_price else "",
            "savings": f"Save {inr(savings_val)}" if savings_val > 0 else "",
            "effective_price": inr(eff_p),
            "coupon_code": best_c["code"] if best_c else "",
            "image": p.primary_image_url or "",
            "url": reverse("product_detail", kwargs={"slug": p.slug}),
            "add_to_cart_url": reverse("cart_add", kwargs={"product_id": p.id}),
            "layers": layers,
        })

    headline_cutouts = home_headline_cutouts()
    cutout_cable = headline_cutouts.get("cable")
    cutout_watch = headline_cutouts.get("watch")
    cutout_earphones = headline_cutouts.get("earphones")
    cutouts = [c for c in [cutout_cable, cutout_watch, cutout_earphones] if c is not None]

    # 2. Stats
    total_listings = Product.objects.filter(is_available=True, selling_price__gt=0).count()
    total_categories = Category.objects.filter(is_active=True).count()
    min_price_agg = Product.objects.filter(is_available=True, selling_price__gt=0).aggregate(Min("selling_price"))
    min_price = min_price_agg["selling_price__min"] or Decimal("0.00")

    # 3. Chapter 03: The Vault (Deals & Promo Codes)
    vault_coupons = list(Coupon.objects.filter(is_active=True).order_by("-discount_value")[:4])
    vault_deals_qs = (
        Product.objects.filter(
            is_available=True,
            mrp__gt=F("selling_price"),
            selling_price__gt=0,
            media__media_type="image",
        )
        .select_related("category")
        .prefetch_related("media")
        .order_by("-mrp")[:4]
    )
    vault_deals = []
    for vd in vault_deals_qs:
        pct = int(round(((vd.mrp - vd.selling_price) / vd.mrp) * 100)) if vd.mrp else 0
        vault_deals.append({
            "product": vd,
            "discount_pct": pct,
            "savings": vd.mrp - vd.selling_price,
        })

    # 4. Chapter 04: Head-to-Head Spec Duel (Same-Tier Flagship Rivalry)
    duel_a = (
        Product.objects.filter(
            category__slug="smartphones",
            display_name__icontains="S23 Ultra",
            media__media_type="image",
        )
        .select_related("category")
        .prefetch_related("media", "specifications")
        .order_by("-selling_price")
        .first()
        or Product.objects.filter(category__slug="smartphones", selling_price__gte=100000, media__media_type="image")
        .select_related("category")
        .prefetch_related("media", "specifications")
        .order_by("-selling_price")
        .first()
    )
    duel_b = (
        Product.objects.filter(
            category__slug="smartphones",
            display_name__icontains="iPhone 14 Pro",
            media__media_type="image",
        )
        .exclude(id=duel_a.id if duel_a else -1)
        .select_related("category")
        .prefetch_related("media", "specifications")
        .order_by("-selling_price")
        .first()
        or Product.objects.filter(
            category__slug="smartphones",
            selling_price__gte=90000,
            media__media_type="image",
        )
        .exclude(id=duel_a.id if duel_a else -1)
        .select_related("category")
        .prefetch_related("media", "specifications")
        .order_by("-selling_price")
        .first()
    )
    duel_specs = [
        {"label": "Processor Silicon", "val_a": "Qualcomm Snapdragon 8 Gen 2 (4nm)", "val_b": "Apple A16 Bionic (4nm)", "winner": "tie", "bar_a": 98, "bar_b": 98},
        {"label": "RAM Architecture", "val_a": "12 GB LPDDR5X", "val_b": "6 GB LPDDR5", "winner": "a", "bar_a": 95, "bar_b": 70},
        {"label": "Display Refresh", "val_a": "6.8\" Dynamic AMOLED 2X 120Hz", "val_b": "6.1\" Super Retina XDR 120Hz", "winner": "tie", "bar_a": 96, "bar_b": 96},
        {"label": "Primary Optics", "val_a": "200 MP ISOCELL + 10x Optical", "val_b": "48 MP Quad-Pixel + 3x Optical", "winner": "a", "bar_a": 98, "bar_b": 92},
        {"label": "Battery & Endurance", "val_a": "5000 mAh + 45W Fast Charge", "val_b": "3200 mAh + 20W Fast Charge", "winner": "a", "bar_a": 92, "bar_b": 78},
    ]

    # 5. Chapter 05: Horizontal Collector's Plate Rail (6 distinct categories)
    plate_categories = ["smartphones", "tvs", "earphones-headphones", "cameras", "smartwatches-bands", "keyboards-mice"]
    plate_rail_products = []
    for cat_slug in plate_categories:
        p_match = (
            Product.objects.filter(category__slug=cat_slug, is_available=True, media__media_type="image", selling_price__gt=0)
            .select_related("category")
            .prefetch_related("media", "specifications")
            .order_by("-selling_price", "-source_rating_count")
            .first()
        )
        if p_match:
            plate_rail_products.append(p_match)

    # 6. Chapter 06: The 10 Category Worlds (Bento Matrix)
    from apps.catalog.services.category_nav import get_mega_menu_categories
    categories_rail = get_mega_menu_categories()

    # 7. Chapter 07: Curate Your Desk Setup 6-Slot Configurator
    slot_core_ids = [3082, 6188, 4606]
    slot_display_ids = [1451, 4558, 2163]
    slot_km_ids = [2324, 1727, 4415]
    slot_audio_ids = [6472, 1876, 6610]
    slot_phone_ids = [4573, 5197, 3550]
    slot_hub_ids = [1151, 6904, 3684]

    def _fetch_slot_products(ids, fallback_filter, exclude_regex=None):
        items = list(
            Product.objects.filter(id__in=ids, is_available=True)
            .select_related("category")
            .prefetch_related("media")
        )
        if len(items) < 3:
            qs = Product.objects.filter(
                is_available=True,
                media__media_type="image",
                selling_price__gt=0,
                **fallback_filter,
            ).exclude(id__in=[p.id for p in items])
            if exclude_regex:
                qs = qs.exclude(raw_name__iregex=exclude_regex)
            extra = list(qs.select_related("category").prefetch_related("media").order_by("-selling_price")[:3 - len(items)])
            items.extend(extra)
        return items[:3]

    slot_01_items = _fetch_slot_products(slot_core_ids, {"category__slug__in": ["smartphones", "other"]}, r"sleeve|case|cover|bag|cable")
    slot_02_items = _fetch_slot_products(slot_display_ids, {"category__slug": "tvs"}, r"cable|mount|bracket|remote")
    slot_03_items = _fetch_slot_products(slot_km_ids, {"category__slug": "keyboards-mice"}, r"yamaha|casio|piano|synthesizer")
    slot_04_items = _fetch_slot_products(slot_audio_ids, {"category__slug__in": ["earphones-headphones", "speakers"]}, r"tablet|tab|phone")
    slot_05_items = _fetch_slot_products(slot_phone_ids, {"category__slug": "smartphones"}, r"case|cover|cable|charger|glass")
    slot_06_items = _fetch_slot_products(slot_hub_ids, {"category__slug": "cables-chargers-powerbanks"})

    setup_slots = [
        {"num": "01", "title": "Computing / PC Core", "subtitle": "Desktops, Laptops & Tablets", "items": slot_01_items},
        {"num": "02", "title": "Display & Visuals", "subtitle": "Monitors & Smart Panels", "items": slot_02_items},
        {"num": "03", "title": "PC Keyboard & Mouse", "subtitle": "Mechanical & Ergonomic Peripherals", "items": slot_03_items},
        {"num": "04", "title": "Audio & Studio", "subtitle": "Over-Ear Headphones & Soundbars", "items": slot_04_items},
        {"num": "05", "title": "Primary Smartphone", "subtitle": "Flagship 5G Handsets", "items": slot_05_items},
        {"num": "06", "title": "Power, Mic & Desk Hub", "subtitle": "High-Speed GaN & Fast Power", "items": slot_06_items},
    ]

    bundle_audio_items = slot_04_items
    bundle_device_items = slot_05_items
    bundle_accessory_items = slot_03_items

    # 8. Shipping & Manifesto
    shipping_config = ShippingConfig.get_solo()
    free_shipping_threshold = shipping_config.free_shipping_threshold
    standard_shipping_fee = shipping_config.standard_fee
    shipping_fee_confirmed = shipping_config.is_standard_fee_confirmed
    seller_gstin = getattr(settings, "SELLER_GSTIN", "")
    is_bill_of_supply = not bool(seller_gstin)
    razorpay_enabled = bool(getattr(settings, "RAZORPAY_KEY_ID", ""))
    remembered_pincode = request.session.get("pincode", "380009")
    delivery_estimate = estimate_delivery(remembered_pincode)

    # Cutout cycling data
    cycle_candidates = list(hero_res.products) + plate_rail_products
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

    # Brands & Curated Chapters
    brands = get_editorial_brands(max_brands=35)
    chapters = home_chapters(max_chapters=3)

    context = {
        "hero": hero_res,
        "hero_plate_product": hero_plate_product,
        "hero_picker_products": hero_picker_products,
        "hero_flagships": hero_flagships,
        "hero_flagships_data": hero_flagships_data,
        "hero_flagships_json": json.dumps(hero_flagships_data),
        "chapters": chapters,
        "cutout_cable": cutout_cable,
        "cutout_watch": cutout_watch,
        "cutout_earphones": cutout_earphones,
        "cutouts": cutouts,
        "cutout_cycle_data": cutout_cycle_data,
        "total_listings": total_listings,
        "total_categories": total_categories,
        "min_price": min_price,
        "vault_coupons": vault_coupons,
        "vault_deals": vault_deals,
        "duel_a": duel_a,
        "duel_b": duel_b,
        "duel_specs": duel_specs,
        "plate_rail_products": plate_rail_products,
        "categories_rail": categories_rail,
        "setup_slots": setup_slots,
        "bundle_audio_items": bundle_audio_items,
        "bundle_device_items": bundle_device_items,
        "bundle_accessory_items": bundle_accessory_items,
        "delivery_estimate": delivery_estimate,
        "remembered_pincode": remembered_pincode,
        "free_shipping_threshold": free_shipping_threshold,
        "standard_shipping_fee": standard_shipping_fee,
        "shipping_fee_confirmed": shipping_fee_confirmed,
        "is_bill_of_supply": is_bill_of_supply,
        "razorpay_enabled": razorpay_enabled,
        "brands": brands,
        "telemetry_coords": "23.0225° N, 72.5714° E · Dispatched from Ahmedabad, Gujarat",
    }
    return render(request, "catalog/home.html", context)


@require_GET
def category_list(request: HttpRequest) -> HttpResponse:
    """
    Monograph category index: compact scannable 24-category visual directory with
    representative thumbnail cutouts, plus macro category overviews.
    """
    from apps.catalog.services.category_nav import get_category_clusters, get_24_granular_categories

    granular_24 = get_24_granular_categories()

    categories = list(Category.objects.filter(is_active=True).order_by("display_order", "name"))
    category_spreads = [category_spread(cat) for cat in categories]
    for s in category_spreads:
        s.clusters = get_category_clusters(s.category.slug)

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
            "granular_categories": granular_24,
            "category_spreads": category_spreads,
            "total_listings": total_listings,
            "total_categories": len(categories),
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
    q = request.GET.get("q", "").strip()
    brand = request.GET.get("brand", "").strip() or None
    sort_by = request.GET.get("sort", "popularity").strip()
    collapsed = request.GET.get("collapsed", "0") == "1"
    sub = request.GET.get("sub", "").strip()

    from apps.catalog.services.category_nav import get_sub_category_filter
    sub_info = get_sub_category_filter(sub) if sub else None

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
        q
        or brand
        or bracket_idx
        or request.GET.get("min_price")
        or request.GET.get("max_price")
        or (sort_by and sort_by != "popularity")
        or collapsed
        or sub_info
    )
    show_marquee = is_page_1 and not has_active_filters

    spread = category_spread(category, max_picks=6) if show_marquee else None

    search_result = execute_catalog_search(
        query=q,
        category_slug=category.slug,
        brand=brand,
        min_price=min_price_val,
        max_price=max_price_val,
        sort_by=sort_by,
        collapsed=collapsed,
    )

    products_qs = search_result["products"]
    if sub_info:
        sub_regex = re.compile(sub_info["regex"], re.IGNORECASE)
        exclude_regex = re.compile(sub_info["exclude_regex"], re.IGNORECASE) if sub_info.get("exclude_regex") else None
        filtered_products = []
        for p in products_qs:
            raw = getattr(p, "raw_name", "") or getattr(p, "display_name", "")
            if sub_regex.search(raw):
                if exclude_regex and exclude_regex.search(raw):
                    continue
                filtered_products.append(p)
        products_qs = filtered_products

    paginator = Paginator(products_qs, 24)
    page_obj = paginator.get_page(page_param)

    # Build querystring preserving parameters without page
    params = request.GET.copy()
    if "page" in params:
        del params["page"]
    querystring = params.urlencode()

    breadcrumbs = [
        {"title": "Categories", "url": "/categories/"},
        {"title": category.name, "url": f"/c/{category.slug}/"},
    ]
    if sub_info:
        breadcrumbs.append({"title": sub_info["name"], "url": f"/c/{category.slug}/?sub={sub}"})

    context = {
        "category": category,
        "page_obj": page_obj,
        "facets": search_result["facets"],
        "selected_filters": {
            "q": q,
            "brand": brand,
            "min_price": min_price_val,
            "max_price": max_price_val,
            "bracket": bracket_idx,
            "sub": sub,
        },
        "active_sub": sub_info,
        "sort_by": sort_by,
        "collapsed": collapsed,
        "price_bars": search_result["facets"]["price_histogram"],
        "querystring": querystring,
        "show_marquee": show_marquee,
        "spread": spread,
        "breadcrumbs": breadcrumbs,
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


def product_detail(request: HttpRequest, slug: str) -> HttpResponse:
    """
    Detailed product presentation including specifications, media, customer reviews, and delivery estimate.
    Handles review submission with verified purchase detection.
    """
    product = get_object_or_404(
        Product.objects.select_related("category", "inventory").prefetch_related(
            "specifications", "media", "reviews"
        ),
        slug=slug,
    )

    if request.method == "POST" and "submit_review" in request.POST:
        reviewer_name = request.POST.get("reviewer_name", "").strip()
        reviewer_email = request.POST.get("reviewer_email", "").strip()
        title_text = request.POST.get("title", "").strip()
        body_text = request.POST.get("body", "").strip()
        try:
            rating_val = int(request.POST.get("rating", 5))
            rating_val = max(1, min(5, rating_val))
        except (ValueError, TypeError):
            rating_val = 5

        if not reviewer_name or not reviewer_email or not body_text:
            messages.error(request, "Please enter your name, email address, and review details.")
        else:
            user = request.user if request.user.is_authenticated else None
            check_email = (user.email if user and user.email else reviewer_email).strip().lower()
            is_verified = Order.objects.filter(
                items__product=product,
                status__in=[Order.STATUS_CONFIRMED, Order.STATUS_PROCESSING, Order.STATUS_SHIPPED, Order.STATUS_DELIVERED],
            ).filter(
                Q(user=user) if user else Q(guest_email__iexact=check_email)
            ).exists()

            ProductReview.objects.create(
                product=product,
                user=user,
                reviewer_name=reviewer_name,
                reviewer_email=reviewer_email,
                rating=rating_val,
                title=title_text or f"{rating_val}-Star Rating",
                body=body_text,
                is_verified_purchase=is_verified,
            )
            messages.success(request, "Thank you for your feedback. Your review has been recorded.")
            return redirect(f"/p/{product.slug}/#customer-reviews")

    media_items = list(product.media.all())
    specifications = list(product.specifications.all())

    base_subtype = classify_product_subtype(product)
    same_cat_qs = list(
        Product.objects.filter(
            category=product.category,
            is_available=True,
            selling_price__gt=0,
        )
        .exclude(id=product.id)
        .select_related("category", "inventory")
        .prefetch_related("media", "specifications")
    )
    same_subtype_qs = [p for p in same_cat_qs if classify_product_subtype(p) == base_subtype]

    # Related items in category (prefetches media & specifications for comparison table)
    related_products = (same_subtype_qs if same_subtype_qs else same_cat_qs)[:4]

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

    # 3 Nearest-priced items with exact sub-type match and 0.45x-1.85x price band (Pillar 2)
    comparison_products = []
    comp_rows = []
    if product.selling_price:
        base_price = product.selling_price
        min_p = (base_price * Decimal("0.45")).quantize(Decimal("0.01"))
        max_p = (base_price * Decimal("1.85")).quantize(Decimal("0.01"))

        # 1. Exact sub-type and price band (0.45x to 1.85x)
        matched_candidates = [
            p for p in same_subtype_qs
            if min_p <= p.selling_price <= max_p
        ]

        # 2. If fewer than 3, expand to same sub-type regardless of strict band
        if len(matched_candidates) < 3:
            more_subtype = [
                p for p in same_subtype_qs
                if p not in matched_candidates
            ]
            more_subtype.sort(key=lambda p: abs(p.selling_price - base_price))
            matched_candidates.extend(more_subtype)

        matched_candidates.sort(key=lambda p: abs(p.selling_price - base_price))
        comparison_products = matched_candidates[:3]

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

    # Customer Reviews & Ratings Distribution (Phase R8)
    reviews = sorted(product.reviews.all(), key=lambda r: getattr(r, "created_at", None) or timezone.now(), reverse=True)
    total_reviews = len(reviews)
    if total_reviews > 0:
        avg_rating = round(sum(r.rating for r in reviews) / total_reviews, 1)
    else:
        avg_rating = float(getattr(product, "source_rating", None) or getattr(product, "amazon_rating", None) or 4.5)

    rating_counts = {i: 0 for i in range(1, 6)}
    for r in reviews:
        rating_counts[r.rating] = rating_counts.get(r.rating, 0) + 1

    rating_bars = []
    for s in range(5, 0, -1):
        cnt = rating_counts[s]
        pct = int((cnt / total_reviews) * 100) if total_reviews > 0 else (75 if s == 5 else (18 if s == 4 else (7 if s == 3 else 0)))
        rating_bars.append({
            "stars": s,
            "count": cnt,
            "percentage": pct,
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
        "reviews": reviews,
        "total_reviews": total_reviews,
        "avg_rating": avg_rating,
        "rating_bars": rating_bars,
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
    Presents side-by-side spec comparison table for up to 3 products in the same category,
    with Price-Tier & Value Delta Advisory, 'Show Only Differences' flags, and Spec Winners.
    """
    tray_ids = request.session.get("compare_tray", [])
    products = list(
        Product.objects.filter(id__in=tray_ids)
        .select_related("category")
        .prefetch_related("specifications", "media")
    )

    common_category = products[0].category if products else None
    if products and any(p.category_id != common_category.id for p in products):
        products = [p for p in products if p.category_id == common_category.id]
        request.session["compare_tray"] = [p.id for p in products]
        request.session.modified = True

    # Price-Tier & Value Delta Advisory and Comparable Rivals
    delta_advisory = None
    comparable_rivals = []
    price_tier_mismatch_warning = None

    if products:
        ref_price = products[0].selling_price or Decimal("0.00")
        base_subtype = classify_product_subtype(products[0])
        if ref_price > 0:
            min_r = (ref_price * Decimal("0.45")).quantize(Decimal("0.01"))
            max_r = (ref_price * Decimal("1.85")).quantize(Decimal("0.01"))
            cat_candidates = list(
                Product.objects.filter(
                    category=common_category,
                    is_available=True,
                    selling_price__gt=0,
                    media__media_type="image",
                )
                .exclude(id__in=[p.id for p in products])
                .select_related("category")
                .prefetch_related("media")
                .order_by("-source_rating_count", "-selling_price")
            )
            # Filter strictly by matching sub-type and price band 0.45x to 1.85x
            comparable_rivals = [
                p for p in cat_candidates
                if classify_product_subtype(p) == base_subtype and min_r <= p.selling_price <= max_r
            ][:8]
            if not comparable_rivals:
                comparable_rivals = [
                    p for p in cat_candidates if classify_product_subtype(p) == base_subtype
                ][:8]
            if not comparable_rivals:
                comparable_rivals = cat_candidates[:8]

    if len(products) >= 2:
        prices = [p.selling_price for p in products if p.selling_price and p.selling_price > 0]
        if prices:
            min_p = min(prices)
            max_p = max(prices)
            if min_p > 0 and (max_p / min_p) >= Decimal("1.6"):
                price_tier_mismatch_warning = (
                    f"Notice: You are comparing two vastly different price tiers (₹{min_p:,.0f} vs ₹{max_p:,.0f}). "
                    f"Features, materials, and silicon class reflect different market segments."
                )
            if max_p >= Decimal("50000.00") and min_p <= Decimal("15000.00") and min_p > 0:
                mult = round(float(max_p / min_p), 1)
                delta_advisory = {
                    "multiplier": mult,
                    "max_price": max_p,
                    "min_price": min_p,
                    "headline": f"Flagship vs Budget Tier: {mult}x Price Delta",
                    "subtext": "Comparing Ultra-Tier Silicon & Optics against Entry-Level Hardware Utility",
                }

    spec_rows = []
    if products:
        # Price row
        min_price_prod = min(products, key=lambda p: p.selling_price or Decimal("999999"))
        price_vals = {p.id: p.selling_price for p in products}
        all_same_price = len(set(price_vals.values())) <= 1
        spec_rows.append({
            "key": "price",
            "label": "Selling Price",
            "is_price": True,
            "values": price_vals,
            "winner_id": min_price_prod.id if not all_same_price else None,
            "winner_badge": "Best Value",
            "is_identical": all_same_price,
        })

        spec_map_by_prod = {}
        for p in products:
            spec_map_by_prod[p.id] = {s.key: s.value for s in p.specifications.all()}

        all_keys = []
        for p in products:
            for s in p.specifications.all():
                if s.key not in all_keys and s.key != "price":
                    all_keys.append(s.key)

        for key in all_keys:
            raw_vals = {p.id: spec_map_by_prod[p.id].get(key, "—") for p in products}
            distinct_vals = set(raw_vals.values())
            is_identical = len(distinct_vals) <= 1

            winner_id = None
            numeric_scores = {}
            for p in products:
                v_str = str(raw_vals[p.id])
                score = None
                if key == "ram":
                    m = re.search(r"(\d+)", v_str)
                    if m: score = float(m.group(1))
                elif key == "storage":
                    m = re.search(r"(\d+)", v_str)
                    if m:
                        score = float(m.group(1))
                        if "TB" in v_str.upper(): score *= 1024
                elif key == "battery":
                    m = re.search(r"(\d+)", v_str)
                    if m: score = float(m.group(1))
                elif key in ("charging_wattage", "wattage"):
                    m = re.search(r"(\d+)", v_str)
                    if m: score = float(m.group(1))
                elif key == "playtime":
                    m = re.search(r"(\d+)", v_str)
                    if m: score = float(m.group(1))
                elif key == "noise_cancellation":
                    m = re.search(r"(\d+)\s*dB", v_str)
                    if m: score = float(m.group(1))
                elif key == "camera":
                    m = re.search(r"(\d+)\s*MP", v_str)
                    if m: score = float(m.group(1))
                elif key in ("display", "screen_size"):
                    m = re.search(r"(\d+)\s*Hz", v_str)
                    if m: score = float(m.group(1))

                if score is not None:
                    numeric_scores[p.id] = score

            if numeric_scores and len(numeric_scores) == len(products):
                max_score = max(numeric_scores.values())
                winners = [pid for pid, sc in numeric_scores.items() if sc == max_score]
                if len(winners) == 1:
                    winner_id = winners[0]

            label = key.replace("_", " ").title()
            if key == "ram": label = "RAM Memory"
            elif key == "storage": label = "Internal Storage"
            elif key == "screen_size": label = "Display Size"
            elif key == "charging_wattage": label = "Power / Fast Charging"
            elif key == "playtime": label = "Battery Playtime"
            elif key == "noise_cancellation": label = "Active Noise Cancellation"
            elif key == "processor": label = "Processor / Architecture"
            elif key == "camera": label = "Primary Camera"
            elif key == "driver_unit": label = "Acoustic Driver"

            spec_rows.append({
                "key": key,
                "label": label,
                "is_price": False,
                "values": raw_vals,
                "winner_id": winner_id,
                "winner_badge": "Spec Winner",
                "is_identical": is_identical,
            })

    all_same_brand = len(set(p.parsed_brand for p in products)) <= 1 if products else False
    all_same_stock = len(set(p.is_available for p in products)) <= 1 if products else False

    context = {
        "compared_products": products,
        "spec_rows": spec_rows,
        "delta_advisory": delta_advisory,
        "comparable_rivals": comparable_rivals,
        "price_tier_mismatch_warning": price_tier_mismatch_warning,
        "common_category": common_category,
        "all_same_brand": all_same_brand,
        "all_same_stock": all_same_stock,
        "breadcrumbs": [{"title": "Product Comparison", "url": "/compare/"}],
    }
    return render(request, "catalog/compare.html", context)


@require_POST
def compare_add(request: HttpRequest, product_id: Optional[int] = None) -> HttpResponseRedirect:
    """
    Adds a product to the comparison tray, validating limit (3) and category homogeneity.
    Supports both URL path parameter /compare/add/<id>/ and POST form body product_id.
    """
    if product_id is None:
        p_id_str = request.POST.get("product_id")
        try:
            product_id = int(p_id_str)
        except (TypeError, ValueError):
            messages.warning(request, "Please select a valid product to compare.")
            return redirect(request.META.get("HTTP_REFERER") or "/compare/")

    product = get_object_or_404(Product, id=product_id)
    tray = list(request.session.get("compare_tray", []))

    referrer = request.META.get("HTTP_REFERER") or "/compare/"

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
