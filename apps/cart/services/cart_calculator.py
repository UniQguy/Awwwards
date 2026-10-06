"""
Cart financial calculator: computes subtotal, MRP savings, shipping thresholds,
COD fees, GST tax breakdown, coupon deductions, and grand total.
Strictly utilizes Decimal with ROUND_HALF_UP.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional

from apps.cart.models import Cart
from apps.shipping.models import ShippingConfig
from apps.shipping.services.fees import calculate_cod_fee, calculate_shipping_fee
from apps.tax.services.gst_calculator import resolve_supply
from apps.tax.services.line_allocator import allocate_order_lines


def calculate_cart_summary(
    cart: Cart,
    buyer_state: str = "",
    coupon_discount: Decimal = Decimal("0.00"),
    payment_method: str = "razorpay",
) -> Dict[str, Any]:
    """
    Computes complete financial breakdown of a shopping cart.
    """
    items = list(cart.items.select_related("product", "product__category").all())

    subtotal = Decimal("0.00")
    mrp_total = Decimal("0.00")
    line_details: List[Dict[str, Any]] = []

    for idx, it in enumerate(items):
        prod = it.product
        unit_sp = prod.selling_price or Decimal("0.00")
        unit_mrp = prod.mrp or unit_sp
        line_sp = (unit_sp * it.quantity).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        line_mrp = (unit_mrp * it.quantity).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        savings = max(Decimal("0.00"), line_mrp - line_sp)

        subtotal += line_sp
        mrp_total += line_mrp

        line_details.append({
            "line_index": idx,
            "item_id": it.id,
            "product": prod,
            "quantity": it.quantity,
            "unit_price": unit_sp,
            "unit_price_incl": unit_sp,
            "mrp": unit_mrp,
            "line_subtotal": line_sp,
            "line_mrp_total": line_mrp,
            "line_savings": savings,
            "rate": prod.effective_gst_rate,
            "hsn_code": prod.effective_hsn,
        })

    mrp_savings = max(Decimal("0.00"), mrp_total - subtotal)

    # Shipping fees and progress
    cfg = ShippingConfig.get_solo()
    free_threshold = cfg.free_shipping_threshold
    shipping_fee = calculate_shipping_fee(subtotal) if items else Decimal("0.00")

    if subtotal >= free_threshold or not items:
        free_shipping_progress = 100.0
        free_shipping_remaining = Decimal("0.00")
    else:
        free_shipping_progress = round(float((subtotal / free_threshold) * 100), 1)
        free_shipping_remaining = (free_threshold - subtotal).quantize(Decimal("0.01"))

    # COD fee
    cod_fee = calculate_cod_fee() if (payment_method == "cod" and items) else Decimal("0.00")

    # Clamped discount
    applied_discount = min(subtotal, coupon_discount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # GST allocation
    tax_allocation = None
    tax_amount = Decimal("0.00")
    if items:
        intra_state = True
        if buyer_state:
            try:
                intra_state, _, _ = resolve_supply(buyer_state)
            except Exception:
                intra_state = True

        tax_allocation = allocate_order_lines(
            lines=line_details,
            discount_total=applied_discount,
            shipping_fee=shipping_fee,
            cod_fee=cod_fee,
            intra_state=intra_state,
        )
        tax_amount = tax_allocation.total_tax_amount

    # Grand total
    net_merchandise = max(Decimal("0.00"), subtotal - applied_discount)
    grand_total = (net_merchandise + shipping_fee + cod_fee).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return {
        "items": line_details,
        "line_details": line_details,
        "item_count": sum(ld["quantity"] for ld in line_details),
        "subtotal": subtotal,
        "mrp_total": mrp_total,
        "mrp_savings": mrp_savings,
        "shipping_fee": shipping_fee,
        "free_shipping_threshold": free_threshold,
        "free_shipping_progress": free_shipping_progress,
        "free_shipping_progress_pct": free_shipping_progress,
        "free_shipping_remaining": free_shipping_remaining,
        "is_free_shipping": shipping_fee == Decimal("0.00") and bool(items),
        "cod_fee": cod_fee,
        "coupon_discount": applied_discount,
        "applied_discount": applied_discount,
        "tax_amount": tax_amount,
        "tax_allocation": tax_allocation,
        "grand_total": grand_total,
    }
