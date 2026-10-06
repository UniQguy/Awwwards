"""
Promotions and coupon models.
All monetary reductions computed in Decimal. Case-insensitive code uniqueness enforced.
"""

from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class Coupon(TimeStampedModel):
    """
    Promotional discount coupon code.
    """

    TYPE_PERCENTAGE = "percentage"
    TYPE_FIXED = "fixed"

    TYPE_CHOICES = [
        (TYPE_PERCENTAGE, _("Percentage Discount (%)")),
        (TYPE_FIXED, _("Fixed Amount (₹)")),
    ]

    code = models.CharField(_("coupon code"), max_length=30, unique=True, db_index=True)
    description = models.CharField(_("editorial description"), max_length=255, blank=True)
    discount_type = models.CharField(_("discount type"), max_length=20, choices=TYPE_CHOICES, default=TYPE_PERCENTAGE)
    discount_value = models.DecimalField(
        _("discount value"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    min_order_amount = models.DecimalField(
        _("minimum order amount (₹)"),
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    max_discount_amount = models.DecimalField(
        _("maximum discount cap (₹)"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text=_("Upper limit for percentage discounts"),
    )
    applicable_categories = models.ManyToManyField(
        "catalog.Category",
        blank=True,
        related_name="coupons",
        verbose_name=_("applicable categories"),
        help_text=_("Leave empty to apply sitewide"),
    )
    usage_limit_total = models.PositiveIntegerField(
        _("global usage limit"),
        null=True,
        blank=True,
        help_text=_("Maximum redemptions across all customers"),
    )
    usage_limit_per_user = models.PositiveIntegerField(
        _("per-user usage limit"),
        default=1,
    )
    valid_from = models.DateTimeField(_("valid from"))
    valid_until = models.DateTimeField(_("valid until"))
    is_active = models.BooleanField(_("is active"), default=True)
    is_sample_data = models.BooleanField(_("is sample/demo coupon"), default=False)

    class Meta:
        verbose_name = _("coupon")
        verbose_name_plural = _("coupons")
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(Lower("code"), name="unique_coupon_code_case_insensitive"),
        ]

    def __str__(self):
        desc = f"{self.discount_value}%" if self.discount_type == self.TYPE_PERCENTAGE else f"₹{self.discount_value}"
        return f"{self.code.upper()} ({desc} off)"

    @property
    def is_currently_valid(self) -> bool:
        now = timezone.now()
        return self.is_active and (self.valid_from <= now <= self.valid_until)


class CouponRedemption(models.Model):
    """
    Audit log of coupon redemption on an order.
    """

    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.CASCADE,
        related_name="redemptions",
        verbose_name=_("coupon"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="coupon_redemptions",
        verbose_name=_("user"),
    )
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="coupon_redemptions",
        verbose_name=_("order"),
    )
    discount_applied = models.DecimalField(
        _("discount applied (₹)"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    redeemed_at = models.DateTimeField(_("redemption timestamp"), auto_now_add=True)

    class Meta:
        verbose_name = _("coupon redemption")
        verbose_name_plural = _("coupon redemptions")
        ordering = ["-redeemed_at"]

    def __str__(self):
        return f"{self.coupon.code} redeemed on Order #{self.order_id or 'Pending'}: ₹{self.discount_applied}"
