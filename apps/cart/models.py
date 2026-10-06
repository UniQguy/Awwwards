"""
Shopping Cart models for guest and authenticated customer sessions.
"""

from decimal import Decimal
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class Cart(TimeStampedModel):
    """
    Shopping cart container attached to a registered user or cryptographic guest token.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="carts",
        verbose_name=_("customer"),
    )
    guest_token = models.CharField(_("guest session token"), max_length=64, blank=True, db_index=True)
    is_active = models.BooleanField(_("is active"), default=True)

    class Meta:
        verbose_name = _("cart")
        verbose_name_plural = _("carts")
        ordering = ["-updated_at"]

    def __str__(self):
        owner = self.user.email if self.user else f"Guest ({self.guest_token[:8]}...)"
        return f"Cart #{self.id} - {owner}"

    @property
    def total_quantity(self) -> int:
        return sum(item.quantity for item in self.items.all())


class CartItem(TimeStampedModel):
    """
    Individual line item in shopping cart.
    """

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("cart"),
    )
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.CASCADE,
        related_name="cart_items",
        verbose_name=_("product"),
    )
    quantity = models.PositiveIntegerField(_("quantity"), default=1)

    class Meta:
        verbose_name = _("cart item")
        verbose_name_plural = _("cart items")
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(fields=["cart", "product"], name="unique_cart_product"),
            models.CheckConstraint(condition=Q(quantity__gt=0), name="check_cart_item_quantity_positive"),
        ]

    def __str__(self):
        return f"{self.product.display_name} x {self.quantity}"

    @property
    def line_subtotal(self) -> Decimal:
        if self.product.selling_price:
            return (self.product.selling_price * self.quantity).quantize(Decimal("0.01"))
        return Decimal("0.00")

    @property
    def line_mrp_total(self) -> Decimal:
        if self.product.mrp:
            return (self.product.mrp * self.quantity).quantize(Decimal("0.01"))
        return self.line_subtotal
