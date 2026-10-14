"""
Cart service: manages cart creation, stock-clamped additions, updates, removals, and guest merges.
"""

from typing import Optional
from django.db import transaction

from apps.catalog.models import Product
from apps.inventory.exceptions import InsufficientStockError
from apps.inventory.services.reservation_service import get_available_stock
from apps.cart.models import Cart, CartItem


def get_or_create_cart(user=None, guest_token: str = "") -> Cart:
    """
    Retrieves or creates active cart for user or guest token.
    """
    if user and user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=user, is_active=True)
        return cart

    if guest_token:
        cart, _ = Cart.objects.get_or_create(guest_token=guest_token, is_active=True)
        return cart

    return Cart.objects.create(is_active=True)


def add_to_cart(cart: Cart, product: Product, quantity: int = 1) -> CartItem:
    """
    Adds a product to cart. Quantity is validated against available inventory.
    """
    if quantity <= 0:
        raise ValueError("Quantity must be positive.")

    available = get_available_stock(product)
    if available < 1:
        raise InsufficientStockError(product.sku, quantity, available)

    with transaction.atomic():
        item = CartItem.objects.filter(cart=cart, product=product).first()
        target_qty = quantity if not item else (item.quantity + quantity)

        if target_qty > available:
            # Clamp to available stock
            target_qty = available

        if item:
            item.quantity = target_qty
            item.is_saved_for_later = False
            item.save(update_fields=["quantity", "is_saved_for_later", "updated_at"])
        else:
            item = CartItem.objects.create(cart=cart, product=product, quantity=target_qty)

        return item


def update_cart_quantity(cart: Cart, product_id: int, quantity: int) -> Optional[CartItem]:
    """
    Updates item quantity. Deletes if quantity <= 0. Clamps to available stock.
    """
    with transaction.atomic():
        item = CartItem.objects.filter(cart=cart, product_id=product_id).first()
        if not item:
            return None

        if quantity <= 0:
            item.delete()
            return None

        available = get_available_stock(item.product)
        target_qty = min(quantity, available) if available > 0 else 0

        if target_qty <= 0:
            item.delete()
            return None

        item.quantity = target_qty
        item.save(update_fields=["quantity", "updated_at"])
        return item


def remove_from_cart(cart: Cart, product_id: int) -> bool:
    """
    Removes item from cart.
    """
    deleted_count, _ = CartItem.objects.filter(cart=cart, product_id=product_id).delete()
    return deleted_count > 0


def clear_cart(cart: Cart) -> None:
    """
    Removes all items from cart.
    """
    cart.items.all().delete()


def merge_carts(guest_cart: Cart, user_cart: Cart) -> Cart:
    """
    Merges items from guest cart into user cart upon login.
    """
    if guest_cart.id == user_cart.id:
        return user_cart

    with transaction.atomic():
        for guest_item in guest_cart.items.all():
            available = get_available_stock(guest_item.product)
            if available <= 0:
                continue

            user_item = CartItem.objects.filter(cart=user_cart, product=guest_item.product).first()
            if user_item:
                target_qty = min(user_item.quantity + guest_item.quantity, available)
                user_item.quantity = target_qty
                user_item.save(update_fields=["quantity", "updated_at"])
            else:
                target_qty = min(guest_item.quantity, available)
                CartItem.objects.create(cart=user_cart, product=guest_item.product, quantity=target_qty)

        guest_cart.is_active = False
        guest_cart.save(update_fields=["is_active", "updated_at"])

    return user_cart
