"""
Coupon validation and discount calculation service.
Provides structured reason codes for invalid attempts and exact Decimal financial arithmetic.
"""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from django.utils import timezone

from apps.cart.models import Cart
from apps.promotions.models import Coupon


@dataclass(frozen=True)
class CouponValidationResult:
    is_valid: bool
    discount_amount: Decimal
    coupon: Optional[Coupon] = None
    reason_code: Optional[str] = None
    message: str = ""


REASON_INVALID_CODE = "INVALID_CODE"
REASON_INACTIVE = "INACTIVE"
REASON_NOT_STARTED = "NOT_STARTED"
REASON_EXPIRED = "EXPIRED"
REASON_GLOBAL_LIMIT = "GLOBAL_LIMIT_EXCEEDED"
REASON_USER_LIMIT = "USER_LIMIT_EXCEEDED"
REASON_MIN_ORDER = "MIN_ORDER_NOT_MET"
REASON_CATEGORY_MISMATCH = "CATEGORY_MISMATCH"
REASON_EMPTY_CART = "EMPTY_CART"


def validate_coupon(
    coupon_code: str,
    cart: Cart,
    user=None,
) -> CouponValidationResult:
    """
    Validates a coupon code against a customer's shopping cart and user profile.
    """
    if not coupon_code or not coupon_code.strip():
        return CouponValidationResult(
            is_valid=False,
            discount_amount=Decimal("0.00"),
            reason_code=REASON_INVALID_CODE,
            message="Please provide a promotional code.",
        )

    code_clean = coupon_code.strip()
    coupon = Coupon.objects.filter(code__iexact=code_clean).first()

    if not coupon:
        return CouponValidationResult(
            is_valid=False,
            discount_amount=Decimal("0.00"),
            reason_code=REASON_INVALID_CODE,
            message=f"Promotional code '{code_clean}' was not recognized.",
        )

    if not coupon.is_active:
        return CouponValidationResult(
            is_valid=False,
            discount_amount=Decimal("0.00"),
            coupon=coupon,
            reason_code=REASON_INACTIVE,
            message="This promotional code is no longer active.",
        )

    now = timezone.now()
    if now < coupon.valid_from:
        return CouponValidationResult(
            is_valid=False,
            discount_amount=Decimal("0.00"),
            coupon=coupon,
            reason_code=REASON_NOT_STARTED,
            message="This promotion has not started yet.",
        )

    if now > coupon.valid_until:
        return CouponValidationResult(
            is_valid=False,
            discount_amount=Decimal("0.00"),
            coupon=coupon,
            reason_code=REASON_EXPIRED,
            message="This promotional code has expired.",
        )

    # Check global redemption limit
    if coupon.usage_limit_total is not None:
        if coupon.redemptions.count() >= coupon.usage_limit_total:
            return CouponValidationResult(
                is_valid=False,
                discount_amount=Decimal("0.00"),
                coupon=coupon,
                reason_code=REASON_GLOBAL_LIMIT,
                message="This promotion has reached its maximum redemptions.",
            )

    # Check per-user limit
    if user and user.is_authenticated and coupon.usage_limit_per_user:
        user_count = coupon.redemptions.filter(user=user).count()
        if user_count >= coupon.usage_limit_per_user:
            return CouponValidationResult(
                is_valid=False,
                discount_amount=Decimal("0.00"),
                coupon=coupon,
                reason_code=REASON_USER_LIMIT,
                message="You have already redeemed this promotional code.",
            )

    items = list(cart.items.select_related("product", "product__category").all())
    if not items:
        return CouponValidationResult(
            is_valid=False,
            discount_amount=Decimal("0.00"),
            coupon=coupon,
            reason_code=REASON_EMPTY_CART,
            message="Your cart is empty.",
        )

    cart_subtotal = sum(
        (it.product.selling_price or Decimal("0.00")) * it.quantity for it in items
    )

    if cart_subtotal < coupon.min_order_amount:
        return CouponValidationResult(
            is_valid=False,
            discount_amount=Decimal("0.00"),
            coupon=coupon,
            reason_code=REASON_MIN_ORDER,
            message=f"Minimum merchandise value of INR {coupon.min_order_amount} required to apply this code.",
        )

    # Check category restrictions
    restricted_cats = list(coupon.applicable_categories.all())
    if restricted_cats:
        restricted_cat_ids = {c.id for c in restricted_cats}
        eligible_items = [it for it in items if it.product.category_id in restricted_cat_ids]
        if not eligible_items:
            return CouponValidationResult(
                is_valid=False,
                discount_amount=Decimal("0.00"),
                coupon=coupon,
                reason_code=REASON_CATEGORY_MISMATCH,
                message="This coupon is only valid for selected merchandise categories.",
            )
        eligible_subtotal = sum(
            (it.product.selling_price or Decimal("0.00")) * it.quantity for it in eligible_items
        )
    else:
        eligible_subtotal = cart_subtotal

    # Calculate discount
    if coupon.discount_type == Coupon.TYPE_PERCENTAGE:
        raw_discount = (eligible_subtotal * coupon.discount_value / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        if coupon.max_discount_amount:
            discount = min(raw_discount, coupon.max_discount_amount)
        else:
            discount = raw_discount
    else:  # FIXED
        discount = min(eligible_subtotal, coupon.discount_value)

    discount = max(Decimal("0.00"), min(discount, cart_subtotal)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    return CouponValidationResult(
        is_valid=True,
        discount_amount=discount,
        coupon=coupon,
        reason_code=None,
        message=f"Applied {coupon.code.upper()}! Savings of INR {discount}.",
    )
