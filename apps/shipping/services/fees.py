"""
Shipping fee calculation and free shipping threshold determination.
"""

from dataclasses import dataclass
from decimal import Decimal

from ..models import ShippingConfig

ZERO = Decimal("0.00")


@dataclass(frozen=True)
class ShippingQuote:
    delivery_fee: Decimal
    original_fee: Decimal
    is_free: bool
    cod_fee: Decimal
    amount_to_free: Decimal
    total_shipping_charges: Decimal


def quote(
    items_total_after_discount: Decimal,
    payment_method: str = "razorpay",
    config: ShippingConfig | None = None,
) -> ShippingQuote:
    """
    Calculate final shipping and COD charges based on net items subtotal.
    Threshold invariant:
        Subtotal >= threshold qualifies for free standard shipping.
        E.g., 499.00 -> free; 498.99 -> pays standard fee.
    """
    if config is None:
        config = ShippingConfig.get_solo()

    net_total = Decimal(str(items_total_after_discount))
    threshold = config.free_shipping_threshold
    standard_fee = config.standard_fee

    if net_total >= threshold:
        is_free = True
        delivery_fee = ZERO
        amount_to_free = ZERO
    else:
        is_free = False
        delivery_fee = standard_fee
        amount_to_free = max(ZERO, threshold - net_total)

    is_cod = payment_method.strip().lower() == "cod"
    cod_fee = config.cod_fee if is_cod else ZERO
    total_charges = delivery_fee + cod_fee

    return ShippingQuote(
        delivery_fee=delivery_fee,
        original_fee=standard_fee,
        is_free=is_free,
        cod_fee=cod_fee,
        amount_to_free=amount_to_free,
        total_shipping_charges=total_charges,
    )
