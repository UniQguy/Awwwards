"""
Order status transition engine with state validation and automatic restock / credit note actions.
"""

from typing import List
from django.db import transaction

from apps.inventory.services.reservation_service import (
    cancel_and_restock,
    release_reservation,
)
from apps.orders.models import Order, OrderStatusHistory
from apps.orders.services.invoicing import generate_credit_note


ALLOWED_TRANSITIONS = {
    Order.STATUS_PENDING: [
        Order.STATUS_CONFIRMED,
        Order.STATUS_CANCELLED,
    ],
    Order.STATUS_CONFIRMED: [
        Order.STATUS_PROCESSING,
        Order.STATUS_CANCELLED,
        Order.STATUS_REFUND_REQUIRED,
    ],
    Order.STATUS_PROCESSING: [
        Order.STATUS_SHIPPED,
        Order.STATUS_CANCELLED,
        Order.STATUS_REFUND_REQUIRED,
    ],
    Order.STATUS_SHIPPED: [
        Order.STATUS_DELIVERED,
        Order.STATUS_CANCELLED,
    ],
    Order.STATUS_DELIVERED: [
        Order.STATUS_REFUNDED,
    ],
    Order.STATUS_REFUND_REQUIRED: [
        Order.STATUS_REFUNDED,
        Order.STATUS_CANCELLED,
    ],
    Order.STATUS_CANCELLED: [],
    Order.STATUS_REFUNDED: [],
}


class InvalidOrderTransitionError(Exception):
    pass


def can_transition(current_status: str, target_status: str) -> bool:
    return target_status in ALLOWED_TRANSITIONS.get(current_status, [])


def transition_order_status(
    order: Order,
    new_status: str,
    notes: str = "",
    changed_by=None,
) -> Order:
    """
    Transitions an order to a new lifecycle status.
    Executes required inventory restocks and credit note issuance atomically.
    """
    current_status = order.status
    if current_status == new_status:
        return order

    if not can_transition(current_status, new_status):
        raise InvalidOrderTransitionError(
            f"Cannot transition order {order.order_number} from '{current_status}' to '{new_status}'."
        )

    with transaction.atomic():
        # Action on Cancellation
        if new_status == Order.STATUS_CANCELLED:
            if current_status in [Order.STATUS_CONFIRMED, Order.STATUS_PROCESSING, Order.STATUS_SHIPPED]:
                # Order inventory was already decremented from physical stock; restock items
                for item in order.items.all():
                    cancel_and_restock(item.product, item.quantity)

                # Issue credit note if invoice exists
                if hasattr(order, "invoice") and order.invoice:
                    generate_credit_note(
                        order,
                        reason=f"Order cancellation ({notes or 'Customer cancelled'})",
                    )

            elif current_status == Order.STATUS_PENDING:
                # Release pending reservations
                for res in order.reservations.filter(status="reserved"):
                    release_reservation(res)

        # Record audit history
        OrderStatusHistory.objects.create(
            order=order,
            from_status=current_status,
            to_status=new_status,
            notes=notes,
            changed_by=changed_by,
        )

        order.status = new_status
        order.save(update_fields=["status", "updated_at"])
        return order
