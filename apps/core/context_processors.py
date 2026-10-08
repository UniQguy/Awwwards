"""
Global context processors for storefront templates.
Provides fast, non-N+1 cart, wishlist, category navigation, and seller compliance metadata.
"""

from decimal import Decimal
from django.conf import settings
from django.db.models import Sum

from apps.cart.models import Cart, CartItem
from apps.catalog.models import Category
from apps.inventory.models import Inventory
from apps.wishlist.models import Wishlist, WishlistItem


def storefront_context(request):
    """
    Supplies global storefront state across all page templates.
    """
    user = getattr(request, "user", None)
    session = getattr(request, "session", None)
    guest_token = (
        request.COOKIES.get("electrocart_guest_token")
        or request.COOKIES.get("guest_token")
        or (session.get("guest_token", "") if session else "")
    )

    # 1. Cart Count & Total (Single query optimization)
    cart_count = 0
    cart_subtotal = Decimal("0.00")

    cart_lookup = None
    if user and user.is_authenticated:
        cart_lookup = {"user": user, "is_active": True}
    elif guest_token:
        cart_lookup = {"guest_token": guest_token, "is_active": True}

    if cart_lookup:
        cart = (
            Cart.objects.filter(**cart_lookup)
            .prefetch_related("items__product")
            .first()
        )
        if cart:
            for item in cart.items.all():
                cart_count += item.quantity
                if item.product.selling_price:
                    cart_subtotal += item.product.selling_price * item.quantity

    # 2. Wishlist Count
    wishlist_count = 0
    wishlist_lookup = None
    if user and user.is_authenticated:
        wishlist_lookup = {"user": user}
    elif guest_token:
        wishlist_lookup = {"guest_token": guest_token}

    if wishlist_lookup:
        wishlist = Wishlist.objects.filter(**wishlist_lookup).first()
        if wishlist:
            wishlist_count = wishlist.items.count()

    # 3. Active Nav Categories with live product counts
    from django.db.models import Count, Q
    nav_categories = list(
        Category.objects.filter(is_active=True)
        .annotate(product_count=Count("products", filter=Q(products__is_available=True)))
        .only("id", "name", "slug", "accent_key", "display_order")
        .order_by("display_order", "name")
    )

    # 4. Compare Tray count from session
    compare_tray = session.get("compare_tray", []) if session else []
    compare_count = len(compare_tray)

    # 5. Seller & GST Compliance Mode
    seller_gstin = getattr(settings, "SELLER_GSTIN", "").strip()
    is_bill_of_supply = not bool(seller_gstin)
    mode_str = "gst" if bool(seller_gstin) else "bill_of_supply"
    seller_state = getattr(settings, "SELLER_STATE", "Karnataka")
    seller_legal_name = getattr(settings, "SELLER_LEGAL_NAME", "ELECTROCART RETAIL PRIVATE LIMITED")
    seller_address = getattr(settings, "SELLER_ADDRESS", "")

    class SellerMode(str):
        def __new__(cls, val, **kwargs):
            obj = str.__new__(cls, val)
            for k, v in kwargs.items():
                setattr(obj, k, v)
            return obj

        def __getitem__(self, item):
            return getattr(self, item, "")

    seller_mode_obj = SellerMode(
        mode_str,
        is_bill_of_supply=is_bill_of_supply,
        seller_gstin=seller_gstin,
        seller_state=seller_state,
        seller_legal_name=seller_legal_name,
        seller_address=seller_address,
    )

    # 6. Sample stock status
    has_sample_stock = Inventory.objects.filter(is_sample_data=True).exists()

    return {
        "cart_count": cart_count,
        "cart_subtotal": cart_subtotal,
        "wishlist_count": wishlist_count,
        "compare_count": compare_count,
        "compare_tray": compare_tray,
        "nav_categories": nav_categories,
        "seller_mode": seller_mode_obj,
        "is_bill_of_supply": is_bill_of_supply,
        "seller_gstin": seller_gstin,
        "seller_state": seller_state,
        "seller_legal_name": seller_legal_name,
        "seller_address": seller_address,
        "has_sample_stock": has_sample_stock,
        "site_url": getattr(settings, "SITE_URL", "http://localhost:8000"),
        "motion_debug": getattr(settings, "MOTION_DEBUG", False),
    }
