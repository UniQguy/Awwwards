"""
Order placement service: converts shopping carts into finalized orders,
allocates stock reservations, applies promotions, records tax snapshots,
and issues invoices for COD orders.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from django.db import transaction

from apps.cart.models import Cart
from apps.cart.services.cart_calculator import calculate_cart_summary
from apps.cart.services.cart_service import clear_cart
from apps.core.utils.identifiers import generate_order_number
from apps.inventory.services.reservation_service import (
    convert_reservation,
    extend_reservation,
    reserve_stock,
)
from apps.orders.models import Order, OrderItem, OrderStatusHistory
from apps.orders.services.invoicing import generate_invoice
from apps.promotions.models import CouponRedemption
from apps.promotions.services.coupon_validator import validate_coupon


def place_order(
    cart: Cart,
    user=None,
    guest_email: str = "",
    guest_phone: str = "",
    shipping_address: Optional[Dict[str, Any]] = None,
    billing_address: Optional[Dict[str, Any]] = None,
    payment_method: str = "cod",
    coupon_code: str = "",
    customer_notes: str = "",
    is_bill_of_supply: bool = False,
) -> Order:
    """
    Creates an Order from a Cart.
    Atomically creates stock reservations, items, and tax snapshots.
    """
    cart_items = list(cart.items.select_related("product", "product__category").all())
    if not cart_items:
        raise ValueError("Cannot place an order with an empty cart.")

    if not shipping_address:
        shipping_address = {}
    if not billing_address:
        billing_address = shipping_address

    buyer_state = shipping_address.get("state", "")

    # Validate coupon if provided
    applied_discount = Decimal("0.00")
    validated_coupon = None
    if coupon_code:
        c_res = validate_coupon(coupon_code, cart, user=user)
        if c_res.is_valid:
            applied_discount = c_res.discount_amount
            validated_coupon = c_res.coupon

    # Compute financial summary & tax breakdown
    summary = calculate_cart_summary(
        cart=cart,
        buyer_state=buyer_state,
        coupon_discount=applied_discount,
        payment_method=payment_method,
    )

    with transaction.atomic():
        # Reserve stock for all items
        reservations = []
        for it in cart_items:
            res = reserve_stock(
                product=it.product,
                quantity=it.quantity,
                owner_key=cart.guest_token,
                user=user if user and user.is_authenticated else None,
            )
            reservations.append(res)

        order_num = generate_order_number()
        initial_status = Order.STATUS_CONFIRMED if payment_method == "cod" else Order.STATUS_PENDING

        order = Order.objects.create(
            order_number=order_num,
            user=user if user and user.is_authenticated else None,
            guest_email=guest_email,
            guest_phone=guest_phone,
            shipping_address_snapshot=shipping_address,
            billing_address_snapshot=billing_address,
            status=initial_status,
            payment_method=payment_method,
            payment_status=Order.PAYMENT_STATUS_PENDING,
            subtotal=summary["subtotal"],
            shipping_fee=summary["shipping_fee"],
            discount_amount=summary["coupon_discount"],
            tax_amount=summary["tax_amount"],
            total_amount=summary["grand_total"],
            customer_notes=customer_notes,
            is_bill_of_supply=is_bill_of_supply,
            is_sample_data=any(getattr(it.product, "is_sample_data", False) for it in cart_items),
        )

        # Link reservations to order
        for res in reservations:
            res.order = order
            res.save(update_fields=["order", "updated_at"])

        # Create OrderItems with allocated tax snapshots
        tax_alloc = summary.get("tax_allocation")
        alloc_lines = tax_alloc.lines if tax_alloc else []

        for idx, it in enumerate(cart_items):
            prod = it.product
            unit_sp = prod.selling_price or Decimal("0.00")
            unit_mrp = prod.mrp or unit_sp

            if idx < len(alloc_lines):
                al = alloc_lines[idx]
                discount_alloc = al.discount_share
                taxable_val = al.taxable_value
                cgst = al.cgst
                sgst = al.sgst
                igst = al.igst
                line_tot = al.net_amount
            else:
                line_tot = (unit_sp * it.quantity).quantize(Decimal("0.01"))
                discount_alloc = Decimal("0.00")
                taxable_val = line_tot
                cgst = Decimal("0.00")
                sgst = Decimal("0.00")
                igst = Decimal("0.00")

            OrderItem.objects.create(
                order=order,
                product=prod,
                product_title=prod.display_name,
                product_sku=prod.sku,
                unit_price=unit_sp,
                mrp=unit_mrp,
                quantity=it.quantity,
                hsn_code=prod.effective_hsn,
                gst_rate=prod.effective_gst_rate,
                discount_allocated=discount_alloc,
                taxable_value=taxable_val,
                cgst_amount=cgst,
                sgst_amount=sgst,
                igst_amount=igst,
                line_total=line_tot,
            )

        # Record coupon redemption
        if validated_coupon and applied_discount > Decimal("0.00"):
            CouponRedemption.objects.create(
                coupon=validated_coupon,
                user=user if user and user.is_authenticated else None,
                order=order,
                discount_applied=applied_discount,
            )

        # Record initial status history
        OrderStatusHistory.objects.create(
            order=order,
            from_status="",
            to_status=order.status,
            notes=f"Order created with payment method {payment_method.upper()}.",
            changed_by=user if user and user.is_authenticated else None,
        )

        # Payment method execution
        if payment_method == "cod":
            # For COD: instantly convert reservations to sales and generate invoice
            for res in reservations:
                convert_reservation(res, order=order)
            generate_invoice(order)
        elif payment_method == "razorpay":
            # For Razorpay: extend reservation for 30 minutes to permit gateway checkout
            for res in reservations:
                extend_reservation(res, minutes=30)

        # Clear cart
        clear_cart(cart)

        return order
