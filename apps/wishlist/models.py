"""
Customer Wishlist models supporting authenticated users and guest sessions.
"""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class Wishlist(TimeStampedModel):
    """
    Wishlist container attached to a user account or cryptographic guest token.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="wishlists",
        verbose_name=_("customer"),
    )
    guest_token = models.CharField(_("guest session token"), max_length=64, blank=True, db_index=True)

    class Meta:
        verbose_name = _("wishlist")
        verbose_name_plural = _("wishlists")
        ordering = ["-updated_at"]

    def __str__(self):
        owner = self.user.email if self.user else f"Guest ({self.guest_token[:8]}...)"
        return f"Wishlist #{self.id} - {owner}"


class WishlistItem(models.Model):
    """
    Product bookmark in wishlist.
    """

    wishlist = models.ForeignKey(
        Wishlist,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("wishlist"),
    )
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.CASCADE,
        related_name="wishlist_items",
        verbose_name=_("product"),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("wishlist item")
        verbose_name_plural = _("wishlist items")
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["wishlist", "product"], name="unique_wishlist_product"),
        ]

    def __str__(self):
        return f"{self.product.display_name} in Wishlist #{self.wishlist_id}"
