"""
Storefront shopping cart views: detail, add, update, remove, clear, and coupon management.
Supports both standard POST/PRG HTML forms and JSON responses for progressive enhancement.
"""

from decimal import Decimal
import uuid

from django.conf import settings
from django.contrib import messages
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from apps.cart.models import Cart
from apps.cart.services.cart_calculator import calculate_cart_summary
from apps.cart.services.cart_service import (
    add_to_cart,
    clear_cart,
    get_or_create_cart,
    remove_from_cart,
    update_cart_quantity,
)
from apps.catalog.models import Product
from apps.core.views import is_json_request
from apps.inventory.exceptions import InsufficientStockError
from apps.promotions.services.coupon_validator import validate_coupon


def _get_cart_for_request(request: HttpRequest) -> Cart:
    """Helper retrieving or provisioning active cart for user or guest."""
    if request.user.is_authenticated:
        return get_or_create_cart(user=request.user)

    token = (
        request.COOKIES.get("electrocart_guest_token")
        or request.COOKIES.get("guest_token")
        or request.session.get("guest_token")
    )
    if not token:
        token = str(uuid.uuid4())
        request.session["guest_token"] = token
    return get_or_create_cart(guest_token=token)


def _ensure_guest_cookie(response: HttpResponse, request: HttpRequest) -> HttpResponse:
    """Sets guest token cookie if generated in session."""
    if not request.user.is_authenticated:
        token = request.session.get("guest_token")
        if token and "electrocart_guest_token" not in request.COOKIES:
            response.set_cookie(
                "electrocart_guest_token",
                token,
                max_age=30 * 86400,
                httponly=True,
                samesite="Lax",
            )
    return response


def cart_detail(request: HttpRequest) -> HttpResponse:
    """
    Renders shopping cart contents, line item editing, and financial calculation breakdown.
    """
    cart = _get_cart_for_request(request)

    applied_code = request.session.get("applied_coupon_code", "").strip()
    coupon_discount = Decimal("0.00")
    coupon_obj = None

    if applied_code:
        user = request.user if request.user.is_authenticated else None
        res = validate_coupon(applied_code, cart, user=user)
        if res.is_valid:
            coupon_discount = res.discount_amount
            coupon_obj = res.coupon
        else:
            # Code no longer valid (e.g. cart items removed dropping below min order)
            del request.session["applied_coupon_code"]
            request.session.modified = True
            messages.warning(request, f"Coupon '{applied_code}' removed: {res.message}")
            applied_code = ""

    summary = calculate_cart_summary(
        cart=cart,
        coupon_discount=coupon_discount,
        payment_method="razorpay",
    )

    cross_sell_products = []
    cross_sell_category = None
    cart_prods = [d["product"] for d in summary.get("line_details", [])]
    if cart_prods:
        first_prod = cart_prods[0]
        if first_prod and first_prod.category:
            cross_sell_category = first_prod.category
            cart_product_ids = {p.id for p in cart_prods}
            seen_families = {p.family_key for p in cart_prods}
            qs = (
                Product.objects.filter(category=cross_sell_category, is_available=True)
                .exclude(id__in=cart_product_ids)
                .select_related("category")
                .prefetch_related("media", "specifications")
                .order_by("-source_rating_count", "id")
            )
            for p in qs:
                if p.family_key not in seen_families:
                    seen_families.add(p.family_key)
                    cross_sell_products.append(p)
                    if len(cross_sell_products) >= 4:
                        break

    context = {
        "cart": cart,
        "summary": summary,
        "applied_coupon_code": applied_code,
        "coupon": coupon_obj,
        "cross_sell_products": cross_sell_products,
        "cross_sell_category": cross_sell_category,
        "max_qty_per_line": getattr(settings, "CART_MAX_QTY_PER_LINE", 10),
        "breadcrumbs": [{"title": "Bag", "url": "/cart/"}],
    }
    response = render(request, "cart/cart_detail.html", context)
    return _ensure_guest_cookie(response, request)


@require_POST
def cart_add(request: HttpRequest, product_id: int) -> HttpResponse:
    """
    Adds specified quantity of a product to cart.
    """
    product = get_object_or_404(Product, id=product_id)
    cart = _get_cart_for_request(request)

    try:
        raw_qty = int(request.POST.get("quantity", 1))
        max_limit = getattr(settings, "CART_MAX_QTY_PER_LINE", 10)
        quantity = max(1, min(raw_qty, max_limit))
    except (ValueError, TypeError):
        quantity = 1

    try:
        item = add_to_cart(cart, product, quantity=quantity)
        msg = f"Added {item.quantity} x {product.display_name} to cart."
        messages.success(request, msg)
        success = True
    except InsufficientStockError:
        msg = f"Sorry, {product.display_name} is currently out of stock."
        messages.error(request, msg)
        success = False

    if is_json_request(request):
        summary = calculate_cart_summary(cart)
        json_resp = JsonResponse({
            "success": success,
            "message": msg,
            "cart_count": cart.total_items,
            "item": {
                "id": product.id,
                "name": product.display_name,
                "price": str(product.selling_price or Decimal("0.00")),
                "formatted_price": f"₹{product.selling_price:,.0f}" if product.selling_price else "₹0",
                "image_url": product.primary_image_url or "",
                "quantity": quantity,
            },
            "summary": {
                "subtotal": str(summary["subtotal"]),
                "formatted_subtotal": f"₹{summary['subtotal']:,.0f}",
                "grand_total": str(summary["grand_total"]),
                "formatted_grand_total": f"₹{summary['grand_total']:,.0f}",
                "free_shipping_progress": float(summary["free_shipping_progress"]),
                "free_shipping_remaining": str(summary["free_shipping_remaining"]),
                "formatted_free_shipping_remaining": f"₹{summary['free_shipping_remaining']:,.0f}",
                "free_shipping_qualified": summary["free_shipping_progress"] >= 100,
            },
        })
        return _ensure_guest_cookie(json_resp, request)

    referrer = request.POST.get("next") or request.META.get("HTTP_REFERER") or "/cart/"
    response = redirect(referrer)
    return _ensure_guest_cookie(response, request)


@require_POST
def cart_update(request: HttpRequest, product_id: int) -> HttpResponse:
    """
    Updates line item quantity in shopping cart.
    """
    cart = _get_cart_for_request(request)

    try:
        raw_qty = int(request.POST.get("quantity", 1))
        max_limit = getattr(settings, "CART_MAX_QTY_PER_LINE", 10)
        quantity = max(0, min(raw_qty, max_limit))
    except (ValueError, TypeError):
        quantity = 1

    item = update_cart_quantity(cart, product_id, quantity)
    if item:
        messages.success(request, f"Updated quantity to {item.quantity}.")
    else:
        messages.info(request, "Item removed from cart.")

    if is_json_request(request):
        summary = calculate_cart_summary(cart)
        line_item = next(
            (ld for ld in summary.get("line_details", []) if ld.get("product") and ld["product"].id == product_id),
            None,
        )
        return JsonResponse({
            "success": True,
            "cart_count": cart.total_items,
            "item_removed": item is None,
            "line_subtotal": str(line_item["line_subtotal"]) if line_item else "0.00",
            "formatted_line_subtotal": f"₹{line_item['line_subtotal']:,.0f}" if line_item else "₹0",
            "summary": {
                "subtotal": str(summary["subtotal"]),
                "formatted_subtotal": f"₹{summary['subtotal']:,.0f}",
                "grand_total": str(summary["grand_total"]),
                "formatted_grand_total": f"₹{summary['grand_total']:,.0f}",
                "shipping_fee": str(summary["shipping_fee"]),
                "free_shipping_progress": float(summary["free_shipping_progress"]),
                "free_shipping_remaining": str(summary["free_shipping_remaining"]),
                "formatted_free_shipping_remaining": f"₹{summary['free_shipping_remaining']:,.0f}",
                "free_shipping_qualified": summary["free_shipping_progress"] >= 100,
                "mrp_savings": str(summary["mrp_savings"]),
                "formatted_mrp_savings": f"₹{summary['mrp_savings']:,.0f}",
            },
        })

    return redirect("cart_detail")


@require_POST
def cart_remove(request: HttpRequest, product_id: int) -> HttpResponse:
    """
    Removes a product completely from cart.
    """
    cart = _get_cart_for_request(request)
    remove_from_cart(cart, product_id)
    messages.info(request, "Item removed from cart.")

    if is_json_request(request):
        return JsonResponse({"success": True, "cart_count": cart.total_items})

    return redirect("cart_detail")


@require_POST
def cart_clear(request: HttpRequest) -> HttpResponse:
    """
    Clears all items from cart.
    """
    cart = _get_cart_for_request(request)
    clear_cart(cart)
    if "applied_coupon_code" in request.session:
        del request.session["applied_coupon_code"]
        request.session.modified = True

    messages.info(request, "Your shopping cart is now empty.")
    return redirect("cart_detail")


@ratelimit(key="ip", rate="10/m", block=False)
@require_POST
def coupon_apply(request: HttpRequest) -> HttpResponse:
    """
    Validates and attaches a promotional discount code to the cart session.
    Rate-limited to prevent brute-force code enumeration.
    """
    if getattr(request, "limited", False):
        from apps.core.views import error_429
        return error_429(request)

    code = request.POST.get("code", "").strip()
    if not code:
        messages.error(request, "Please enter a promotional code.")
        return redirect("cart_detail")

    cart = _get_cart_for_request(request)
    user = request.user if request.user.is_authenticated else None

    result = validate_coupon(code, cart, user=user)
    if result.is_valid and result.coupon:
        request.session["applied_coupon_code"] = result.coupon.code
        request.session.modified = True
        messages.success(request, f"Coupon '{result.coupon.code}' applied! Saved ₹{result.discount_amount}.")
    else:
        messages.error(request, result.message)

    return redirect("cart_detail")


@require_POST
def coupon_remove(request: HttpRequest) -> HttpResponse:
    """
    Removes currently applied coupon code from session.
    """
    if "applied_coupon_code" in request.session:
        del request.session["applied_coupon_code"]
        request.session.modified = True
        messages.info(request, "Coupon removed.")

    return redirect("cart_detail")
