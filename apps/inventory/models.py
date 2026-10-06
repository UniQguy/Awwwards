"""
Inventory and stock reservation models.
All stock holds utilize explicit TTL reservations.
"""

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class Inventory(TimeStampedModel):
    """
    Physical on-hand inventory count per product SKU.
    """

    product = models.OneToOneField(
        "catalog.Product",
        on_delete=models.CASCADE,
        related_name="inventory",
        verbose_name=_("product"),
    )
    quantity = models.PositiveIntegerField(_("on-hand physical quantity"), default=0)
    low_stock_threshold = models.PositiveIntegerField(_("low stock alert threshold"), default=5)
    is_sample_data = models.BooleanField(_("is sample/demo data"), default=True)

    class Meta:
        verbose_name = _("inventory")
        verbose_name_plural = _("inventories")
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gte=0),
                name="check_inventory_quantity_non_negative",
            ),
        ]

    def __str__(self):
        return f"{self.product.sku}: {self.quantity} units"

    @property
    def is_in_stock(self) -> bool:
        return self.quantity > 0

    @property
    def is_low_stock(self) -> bool:
        return 0 < self.quantity <= self.low_stock_threshold


class StockReservation(TimeStampedModel):
    """
    Time-bounded stock reservation.
    Holds inventory during active checkout sessions and payment authorizations.
    Orders are referenced lazily using 'orders.Order'.
    """

    STATUS_RESERVED = "reserved"
    STATUS_CONVERTED = "converted"
    STATUS_RELEASED = "released"

    STATUS_CHOICES = [
        (STATUS_RESERVED, _("Reserved")),
        (STATUS_CONVERTED, _("Converted")),
        (STATUS_RELEASED, _("Released")),
    ]

    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.CASCADE,
        related_name="reservations",
        verbose_name=_("product"),
    )
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reservations",
        verbose_name=_("order"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_reservations",
        verbose_name=_("user"),
    )
    owner_key = models.CharField(_("guest token or owner session key"), max_length=64, blank=True, db_index=True)
    quantity = models.PositiveIntegerField(_("reserved units"))
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_RESERVED,
        db_index=True,
    )
    expires_at = models.DateTimeField(_("expiration timestamp"), db_index=True)
    extended_at = models.DateTimeField(_("extended timestamp"), null=True, blank=True)

    class Meta:
        verbose_name = _("stock reservation")
        verbose_name_plural = _("stock reservations")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "expires_at"], name="idx_resv_status_expires"),
            models.Index(fields=["owner_key", "status"], name="idx_resv_owner_status"),
        ]

    def __str__(self):
        return f"{self.product.sku} x {self.quantity} ({self.status}) - expires {self.expires_at}"

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at
