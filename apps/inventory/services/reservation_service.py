"""
Stock reservation service: implements high-concurrency reservation lifecycle,
atomic stock decrements, expiration cleanup, and checkout idempotency.
"""

from datetime import timedelta
from typing import Optional

from django.db import transaction
from django.db.models import F, Sum
from django.utils import timezone

from apps.catalog.models import Product
from apps.inventory.exceptions import (
    InsufficientStockError,
    InvalidReservationStateError,
    ReservationExpiredError,
)
from apps.inventory.models import Inventory, StockReservation


def get_available_stock(product: Product) -> int:
    """
    Computes available unreserved stock for a product:
    on-hand physical inventory minus all active unexpired reservations.
    """
    inv = Inventory.objects.filter(product=product).first()
    if not inv:
        return 0
    physical_qty = inv.quantity

    now = timezone.now()
    reserved_qty = (
        StockReservation.objects.filter(
            product=product,
            status=StockReservation.STATUS_RESERVED,
            expires_at__gt=now,
        ).aggregate(total=Sum("quantity"))["total"]
        or 0
    )

    return max(0, physical_qty - reserved_qty)


def reserve_stock(
    product: Product,
    quantity: int,
    owner_key: str = "",
    user=None,
    order=None,
    ttl_minutes: int = 15,
) -> StockReservation:
    """
    Reserves stock for a customer checkout session.
    Idempotent: if an unexpired reservation exists for the same owner/product, extends and updates it.
    """
    if quantity <= 0:
        raise ValueError("Reserved quantity must be strictly positive.")

    now = timezone.now()
    expires_at = now + timedelta(minutes=ttl_minutes)

    with transaction.atomic():
        # Check for existing active reservation for idempotency
        lookup = {
            "product": product,
            "status": StockReservation.STATUS_RESERVED,
            "expires_at__gt": now,
        }
        if order is not None:
            lookup["order"] = order
        elif user is not None and user.is_authenticated:
            lookup["user"] = user
        elif owner_key:
            lookup["owner_key"] = owner_key

        existing = StockReservation.objects.filter(**lookup).first()
        if existing:
            # Check delta availability if quantity increased
            delta = quantity - existing.quantity
            if delta > 0:
                available = get_available_stock(product)
                if available < delta:
                    raise InsufficientStockError(product.sku, quantity, available + existing.quantity)
            existing.quantity = quantity
            existing.expires_at = expires_at
            existing.save(update_fields=["quantity", "expires_at", "updated_at"])
            return existing

        # Fresh reservation: check available capacity
        available = get_available_stock(product)
        if available < quantity:
            raise InsufficientStockError(product.sku, quantity, available)

        reservation = StockReservation.objects.create(
            product=product,
            user=user if (user and user.is_authenticated) else None,
            order=order,
            owner_key=owner_key,
            quantity=quantity,
            status=StockReservation.STATUS_RESERVED,
            expires_at=expires_at,
        )
        return reservation


def extend_reservation(reservation: StockReservation, minutes: int = 30) -> StockReservation:
    """
    Extends an active reservation (e.g. while entering payment gateway).
    """
    with transaction.atomic():
        fresh = StockReservation.objects.select_for_update().get(id=reservation.id)
        if fresh.status != StockReservation.STATUS_RESERVED:
            raise InvalidReservationStateError(
                f"Cannot extend reservation in status '{fresh.status}'."
            )
        now = timezone.now()
        fresh.expires_at = now + timedelta(minutes=minutes)
        fresh.extended_at = now
        fresh.save(update_fields=["expires_at", "extended_at", "updated_at"])
        return fresh


def convert_reservation(reservation: StockReservation, order=None) -> None:
    """
    Converts a reservation into a permanent sale:
    atomically decrements physical inventory and marks status converted.
    """
    with transaction.atomic():
        res = StockReservation.objects.select_for_update().get(id=reservation.id)
        if res.status == StockReservation.STATUS_CONVERTED:
            return  # Idempotent no-op

        if res.status != StockReservation.STATUS_RESERVED:
            raise InvalidReservationStateError(
                f"Cannot convert reservation with status '{res.status}'."
            )

        if res.is_expired:
            raise ReservationExpiredError("Reservation has expired and cannot be converted.")

        # Atomic decrement on Inventory
        rows_updated = Inventory.objects.filter(
            product=res.product,
            quantity__gte=res.quantity,
        ).update(quantity=F("quantity") - res.quantity)

        if rows_updated == 0:
            raise InsufficientStockError(
                res.product.sku,
                res.quantity,
                0,
            )

        res.status = StockReservation.STATUS_CONVERTED
        if order is not None:
            res.order = order
        res.save(update_fields=["status", "order", "updated_at"])


def release_reservation(reservation: StockReservation) -> None:
    """
    Releases an active reservation back to available inventory.
    """
    with transaction.atomic():
        res = StockReservation.objects.select_for_update().get(id=reservation.id)
        if res.status == StockReservation.STATUS_RESERVED:
            res.status = StockReservation.STATUS_RELEASED
            res.save(update_fields=["status", "updated_at"])


def cleanup_expired_reservations() -> int:
    """
    Marks all expired 'reserved' records as 'released'.
    Returns number of released records.
    """
    now = timezone.now()
    count = StockReservation.objects.filter(
        status=StockReservation.STATUS_RESERVED,
        expires_at__lte=now,
    ).update(status=StockReservation.STATUS_RELEASED)
    return count


def cancel_and_restock(product: Product, quantity: int) -> None:
    """
    Restocks physical inventory upon order cancellation.
    """
    with transaction.atomic():
        Inventory.objects.filter(product=product).update(
            quantity=F("quantity") + quantity
        )
