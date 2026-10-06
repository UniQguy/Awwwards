"""
Authentication signals: handles cart and wishlist merge when guest logs in.
"""

from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from apps.cart.models import Cart
from apps.cart.services.cart_service import get_or_create_cart, merge_carts
from apps.wishlist.models import Wishlist
from apps.wishlist.services.wishlist_service import get_or_create_wishlist, merge_wishlists


@receiver(user_logged_in)
def merge_guest_data_on_login(sender, request, user, **kwargs):
    """
    Transfers items from anonymous session cart/wishlist to authenticated user account.
    """
    if not request or not user.is_authenticated:
        return

    # Check cookies and session for guest token
    guest_token = (
        request.COOKIES.get("guest_token")
        or request.COOKIES.get("electrocart_guest_token")
        or request.session.get("guest_token")
    )

    if not guest_token:
        return

    # Merge Cart
    guest_cart = Cart.objects.filter(guest_token=guest_token, is_active=True).first()
    if guest_cart:
        user_cart = get_or_create_cart(user=user)
        merge_carts(guest_cart, user_cart)

    # Merge Wishlist
    guest_wishlist = Wishlist.objects.filter(guest_token=guest_token).first()
    if guest_wishlist:
        user_wishlist = get_or_create_wishlist(user=user)
        merge_wishlists(guest_wishlist, user_wishlist)
