"""
Models for shipping rates, zones, singleton configuration, and pincode serviceability.
"""

from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import PINCODE_VALIDATOR
from apps.core.models import TimeStampedModel


class ShippingConfig(TimeStampedModel):
    """
    Singleton configuration model storing live shipping rules.
    Enforces primary key pk=1.
    """

    free_shipping_threshold = models.DecimalField(
        _("free shipping threshold (₹)"),
        max_digits=10,
        decimal_places=2,
        default=getattr(settings, "DEFAULT_FREE_SHIPPING_THRESHOLD", Decimal("499.00")),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    standard_fee = models.DecimalField(
        _("standard shipping fee (₹)"),
        max_digits=10,
        decimal_places=2,
        default=getattr(settings, "DEFAULT_STANDARD_SHIPPING_FEE", Decimal("40.00")),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    cod_fee = models.DecimalField(
        _("cash on delivery fee (₹)"),
        max_digits=10,
        decimal_places=2,
        default=getattr(settings, "DEFAULT_COD_FEE", Decimal("0.00")),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    is_standard_fee_confirmed = models.BooleanField(
        _("standard delivery fee confirmed by owner"),
        default=False,
        help_text=_("Unchecked indicates standard delivery fee is an unconfirmed placeholder."),
    )

    class Meta:
        verbose_name = _("shipping configuration")
        verbose_name_plural = _("shipping configuration")

    def save(self, *args, **kwargs):
        self.pk = 1
        if not self.created_at:
            existing_created = ShippingConfig.objects.filter(pk=1).values_list("created_at", flat=True).first()
            if existing_created:
                self.created_at = existing_created
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls) -> "ShippingConfig":
        """Retrieve the singleton row, initializing from seed defaults if not present."""
        obj, _ = cls.objects.get_or_create(
            pk=1,
            defaults={
                "free_shipping_threshold": getattr(
                    settings, "DEFAULT_FREE_SHIPPING_THRESHOLD", Decimal("499.00")
                ),
                "standard_fee": getattr(
                    settings, "DEFAULT_STANDARD_SHIPPING_FEE", Decimal("40.00")
                ),
                "cod_fee": getattr(
                    settings, "DEFAULT_COD_FEE", Decimal("0.00")
                ),
                "is_standard_fee_confirmed": False,
            },
        )
        return obj

    def __str__(self):
        return f"Shipping Rules (Free over ₹{self.free_shipping_threshold}, Standard ₹{self.standard_fee})"


class ShippingZone(TimeStampedModel):
    """
    Regional shipping delivery zone mapped by 1 to 3 leading PIN code digits.
    """

    SOURCE_CHOICES = [
        ("sample", _("Sample Data")),
        ("imported", _("Imported Carrier Data")),
    ]

    name = models.CharField(_("zone name"), max_length=100)
    pin_prefix = models.CharField(_("PIN code prefix (1-3 digits)"), max_length=3, db_index=True)
    est_days_min = models.PositiveSmallIntegerField(_("min estimated transit days"), default=3)
    est_days_max = models.PositiveSmallIntegerField(_("max estimated transit days"), default=7)
    cod_allowed = models.BooleanField(_("COD allowed"), default=True)
    is_active = models.BooleanField(_("is active"), default=True)
    source = models.CharField(_("data source"), max_length=20, choices=SOURCE_CHOICES, default="sample")

    class Meta:
        verbose_name = _("shipping zone")
        verbose_name_plural = _("shipping zones")
        ordering = ["-pin_prefix"]

    def __str__(self):
        return f"{self.name} (Prefix {self.pin_prefix}: {self.est_days_min}-{self.est_days_max} days)"


class PincodeServiceability(TimeStampedModel):
    """
    Specific 6-digit PIN code serviceability override from logistics partner.
    """

    SOURCE_CHOICES = [
        ("sample", _("Sample Data")),
        ("imported", _("Imported Carrier Data")),
    ]

    pincode = models.CharField(
        _("PIN code"),
        max_length=6,
        unique=True,
        validators=[PINCODE_VALIDATOR],
        db_index=True,
    )
    state = models.CharField(_("state"), max_length=50, blank=True)
    is_serviceable = models.BooleanField(_("is serviceable"), default=True)
    est_days_min = models.PositiveSmallIntegerField(_("min estimated transit days"), default=3)
    est_days_max = models.PositiveSmallIntegerField(_("max estimated transit days"), default=5)
    cod_allowed = models.BooleanField(_("COD allowed"), default=True)
    source = models.CharField(_("data source"), max_length=20, choices=SOURCE_CHOICES, default="sample")

    class Meta:
        verbose_name = _("PIN code serviceability")
        verbose_name_plural = _("PIN code serviceability records")
        ordering = ["pincode"]

    def __str__(self):
        status = "Serviceable" if self.is_serviceable else "Unserviceable"
        return f"PIN {self.pincode} - {status}"
