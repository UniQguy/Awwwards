"""
Storefront wishlist views: viewing items, toggle bookmark, transfer to cart, and removal.
"""

import uuid
from django.contrib import messages
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from apps.cart.services.cart_service import get_or_create_cart
from apps.catalog.models import Product
from apps.core.views import is_json_request
from apps.inventory.exceptions import InsufficientStockError
from apps.wishlist.models import Wishlist, WishlistItem
from apps.wishlist.services.wishlist_service import (
    get_or_create_wishlist,
    move_to_cart,
    toggle_wishlist,
)


def _get_wishlist_for_request(request: HttpRequest) -> Wishlist:
    """Helper retrieving or provisioning wishlist for user or guest."""
    if request.user.is_authenticated:
        return get_or_create_wishlist(user=request.user)

    token = (
        request.COOKIES.get("electrocart_guest_token")
        or request.COOKIES.get("guest_token")
        or request.session.get("guest_token")
    )
    if not token:
        token = str(uuid.uuid4())
        request.session["guest_token"] = token
    return get_or_create_wishlist(guest_token=token)


@require_GET
def wishlist_detail(request: HttpRequest) -> HttpResponse:
    """
    Renders user's saved wishlist items with stock status and actions.
    """
    wishlist = _get_wishlist_for_request(request)
    items = (
        wishlist.items.select_related("product", "product__category", "product__inventory")
        .prefetch_related("product__media")
        .order_by("-created_at")
    )

    context = {
        "wishlist": wishlist,
        "items": items,
        "breadcrumbs": [{"title": "Wishlist", "url": "/wishlist/"}],
    }
    return render(request, "wishlist/wishlist_detail.html", context)


@require_POST
def wishlist_toggle(request: HttpRequest, product_id: int) -> HttpResponse:
    """
    Toggles a product bookmark in the wishlist.
    """
    product = get_object_or_404(Product, id=product_id)
    wishlist = _get_wishlist_for_request(request)

    added = toggle_wishlist(wishlist, product)
    if added:
        msg = f"Added {product.display_name} to your wishlist."
        messages.success(request, msg)
    else:
        msg = f"Removed {product.display_name} from your wishlist."
        messages.info(request, msg)

    if is_json_request(request):
        return JsonResponse({"success": True, "added": added, "message": msg, "count": wishlist.items.count()})

    referrer = request.POST.get("next") or request.META.get("HTTP_REFERER") or "/wishlist/"
    return redirect(referrer)


@require_POST
def wishlist_move_to_cart(request: HttpRequest, product_id: int) -> HttpResponse:
    """
    Transfers an item from the wishlist directly into the active shopping cart.
    """
    product = get_object_or_404(Product, id=product_id)
    wishlist = _get_wishlist_for_request(request)

    if request.user.is_authenticated:
        cart = get_or_create_cart(user=request.user)
    else:
        token = request.session.get("guest_token", "")
        cart = get_or_create_cart(guest_token=token)

    try:
        move_to_cart(wishlist, cart, product, quantity=1)
        messages.success(request, f"Moved {product.display_name} to your shopping cart.")
    except InsufficientStockError:
        messages.error(request, f"Sorry, {product.display_name} is currently out of stock.")

    return redirect("wishlist_detail")


@require_POST
def wishlist_remove(request: HttpRequest, product_id: int) -> HttpResponse:
    """
    Removes an item from wishlist.
    """
    wishlist = _get_wishlist_for_request(request)
    deleted, _ = WishlistItem.objects.filter(wishlist=wishlist, product_id=product_id).delete()
    if deleted:
        messages.info(request, "Item removed from wishlist.")

    return redirect("wishlist_detail")
