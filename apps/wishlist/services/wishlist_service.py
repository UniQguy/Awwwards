"""
Wishlist service: manages bookmarks, toggles, transfers to cart, and guest merges.
"""

from django.db import transaction
from apps.catalog.models import Product
from apps.cart.models import Cart
from apps.cart.services.cart_service import add_to_cart
from apps.wishlist.models import Wishlist, WishlistItem


def get_or_create_wishlist(user=None, guest_token: str = "") -> Wishlist:
    """
    Retrieves or creates wishlist for user or guest token.
    """
    if user and user.is_authenticated:
        wishlist, _ = Wishlist.objects.get_or_create(user=user)
        return wishlist

    if guest_token:
        wishlist, _ = Wishlist.objects.get_or_create(guest_token=guest_token)
        return wishlist

    return Wishlist.objects.create()


def toggle_wishlist(wishlist: Wishlist, product: Product) -> bool:
    """
    Toggles a product's presence in the wishlist.
    Returns True if added, False if removed.
    """
    item = WishlistItem.objects.filter(wishlist=wishlist, product=product).first()
    if item:
        item.delete()
        return False
    else:
        WishlistItem.objects.create(wishlist=wishlist, product=product)
        return True


def move_to_cart(wishlist: Wishlist, cart: Cart, product: Product, quantity: int = 1):
    """
    Moves an item from wishlist to shopping cart.
    """
    with transaction.atomic():
        cart_item = add_to_cart(cart, product, quantity=quantity)
        WishlistItem.objects.filter(wishlist=wishlist, product=product).delete()
        return cart_item


def merge_wishlists(guest_wishlist: Wishlist, user_wishlist: Wishlist) -> Wishlist:
    """
    Merges bookmarks from guest wishlist into user wishlist upon login.
    """
    if guest_wishlist.id == user_wishlist.id:
        return user_wishlist

    with transaction.atomic():
        for guest_item in guest_wishlist.items.all():
            WishlistItem.objects.get_or_create(wishlist=user_wishlist, product=guest_item.product)
        guest_wishlist.items.all().delete()

    return user_wishlist
