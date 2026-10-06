"""
Order shipment tracking service.
"""

from typing import Any, Dict
from apps.orders.models import Order


def get_tracking_info(order: Order) -> Dict[str, Any]:
    """
    Returns tracking status, carrier reference, and delivery progress for an order.
    """
    is_dispatched = order.status in [Order.STATUS_SHIPPED, Order.STATUS_DELIVERED]
    carrier = order.tracking_carrier or "Bluedart / Delhivery Express"
    tracking_num = order.tracking_number or (f"TRK{order.id:08d}" if is_dispatched else "Pending Allocation")

    status_steps = [
        {"status": "confirmed", "label": "Order Confirmed", "completed": order.status != Order.STATUS_PENDING and order.status != Order.STATUS_CANCELLED},
        {"status": "processing", "label": "Processing & Quality Check", "completed": order.status in [Order.STATUS_PROCESSING, Order.STATUS_SHIPPED, Order.STATUS_DELIVERED]},
        {"status": "shipped", "label": "Dispatched with Carrier", "completed": order.status in [Order.STATUS_SHIPPED, Order.STATUS_DELIVERED]},
        {"status": "delivered", "label": "Delivered to Customer", "completed": order.status == Order.STATUS_DELIVERED},
    ]

    return {
        "order_number": order.order_number,
        "status": order.status,
        "carrier": carrier,
        "tracking_number": tracking_num,
        "steps": status_steps,
        "is_delivered": order.status == Order.STATUS_DELIVERED,
        "is_cancelled": order.status == Order.STATUS_CANCELLED,
    }
