import re
from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.functions import Lower
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel, UUIDModel

# ------------------------------------------------------------------------------
# Indian State & Union Territory Choices (GST Compliant)
# ------------------------------------------------------------------------------
class IndianState(models.TextChoices):
    """
    Controlled roster of all 28 Indian States and 8 Union Territories.
    Used for address capture and tax engine determination (CGST+SGST vs IGST).
    """

    # 28 States
    ANDHRA_PRADESH = "Andhra Pradesh", _("Andhra Pradesh")
    ARUNACHAL_PRADESH = "Arunachal Pradesh", _("Arunachal Pradesh")
    ASSAM = "Assam", _("Assam")
    BIHAR = "Bihar", _("Bihar")
    CHHATTISGARH = "Chhattisgarh", _("Chhattisgarh")
    GOA = "Goa", _("Goa")
    GUJARAT = "Gujarat", _("Gujarat")
    HARYANA = "Haryana", _("Haryana")
    HIMACHAL_PRADESH = "Himachal Pradesh", _("Himachal Pradesh")
    JHARKHAND = "Jharkhand", _("Jharkhand")
    KARNATAKA = "Karnataka", _("Karnataka")
    KERALA = "Kerala", _("Kerala")
    MADHYA_PRADESH = "Madhya Pradesh", _("Madhya Pradesh")
    MAHARASHTRA = "Maharashtra", _("Maharashtra")
    MANIPUR = "Manipur", _("Manipur")
    MEGHALAYA = "Meghalaya", _("Meghalaya")
    MIZORAM = "Mizoram", _("Mizoram")
    NAGALAND = "Nagaland", _("Nagaland")
    ODISHA = "Odisha", _("Odisha")
    PUNJAB = "Punjab", _("Punjab")
    RAJASTHAN = "Rajasthan", _("Rajasthan")
    SIKKIM = "Sikkim", _("Sikkim")
    TAMIL_NADU = "Tamil Nadu", _("Tamil Nadu")
    TELANGANA = "Telangana", _("Telangana")
    TRIPURA = "Tripura", _("Tripura")
    UTTAR_PRADESH = "Uttar Pradesh", _("Uttar Pradesh")
    UTTARAKHAND = "Uttarakhand", _("Uttarakhand")
    WEST_BENGAL = "West Bengal", _("West Bengal")

    # 8 Union Territories
    ANDAMAN_AND_NICOBAR = (
        "Andaman and Nicobar Islands",
        _("Andaman and Nicobar Islands"),
    )
    CHANDIGARH = "Chandigarh", _("Chandigarh")
    DADRA_AND_NAGAR_HAVELI_AND_DAMAN_AND_DIU = (
        "Dadra and Nagar Haveli and Daman and Diu",
        _("Dadra and Nagar Haveli and Daman and Diu"),
    )
    DELHI = "Delhi", _("Delhi")
    JAMMU_AND_KASHMIR = "Jammu and Kashmir", _("Jammu and Kashmir")
    LADAKH = "Ladakh", _("Ladakh")
    LAKSHADWEEP = "Lakshadweep", _("Lakshadweep")
    PUDUCHERRY = "Puducherry", _("Puducherry")


# ------------------------------------------------------------------------------
# Field Validators
# ------------------------------------------------------------------------------
PINCODE_VALIDATOR = RegexValidator(
    regex=r"^[1-9][0-9]{5}$",
    message=_("PIN code must be a valid 6-digit Indian postal code."),
)

PHONE_VALIDATOR = RegexValidator(
    regex=r"^(?:\+91|0)?[6-9]\d{9}$",
    message=_(
        "Phone number must be a valid 10-digit Indian mobile number (e.g., 9876543210 or +919876543210)."
    ),
)


# ------------------------------------------------------------------------------
# User Manager
# ------------------------------------------------------------------------------
class UserManager(BaseUserManager):
    """
    Custom user manager where email is the unique identifier for authentication.
    Normalizes and lowercases all email inputs prior to persistence.
    """

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_("An email address must be provided."))

        email = self.normalize_email(email).lower()
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self.create_user(email, password, **extra_fields)


# ------------------------------------------------------------------------------
# Custom User Model
# ------------------------------------------------------------------------------
class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel, UUIDModel):
    """
    Custom email-only user model for ELECTROCART.
    Inherits UUIDModel (public uuid4 identifier) and TimeStampedModel (created_at, updated_at).
    Enforces case-insensitive email uniqueness via PostgreSQL Lower('email') constraint.
    """

    email = models.EmailField(
        _("email address"),
        max_length=255,
        unique=True,
    )
    full_name = models.CharField(
        _("full name"),
        max_length=150,
        blank=True,
    )
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into the Django admin."),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user account should be treated as active."
        ),
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        app_label = "accounts"
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                Lower("email"),
                name="unique_user_email_lower",
            ),
        ]

    def clean(self):
        super().clean()
        if self.email:
            self.email = self.email.lower()

    def get_full_name(self):
        return self.full_name or self.email

    def get_short_name(self):
        return (
            self.full_name.split()[0]
            if self.full_name
            else self.email.split("@")[0]
        )

    def __str__(self):
        return self.email


# ------------------------------------------------------------------------------
# Address Model
# ------------------------------------------------------------------------------
class Address(TimeStampedModel, UUIDModel):
    """
    Customer shipping and billing address model.
    Enforces at most one default address per user via conditional UniqueConstraint.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="addresses",
        verbose_name=_("user"),
    )
    full_name = models.CharField(
        _("full name"),
        max_length=150,
    )
    phone = models.CharField(
        _("phone number"),
        max_length=15,
        validators=[PHONE_VALIDATOR],
    )
    line1 = models.CharField(
        _("address line 1"),
        max_length=255,
        help_text=_("Flat, House no., Building, Company, Apartment"),
    )
    line2 = models.CharField(
        _("address line 2"),
        max_length=255,
        blank=True,
        help_text=_("Area, Street, Sector, Village"),
    )
    landmark = models.CharField(
        _("landmark"),
        max_length=255,
        blank=True,
    )
    city = models.CharField(
        _("town/city"),
        max_length=100,
    )
    state = models.CharField(
        _("state / union territory"),
        max_length=50,
        choices=IndianState.choices,
        help_text=_(
            "Indian State or Union Territory (determines CGST+SGST vs IGST tax split)"
        ),
    )
    pincode = models.CharField(
        _("PIN code"),
        max_length=6,
        validators=[PINCODE_VALIDATOR],
    )
    is_default = models.BooleanField(
        _("default address"),
        default=False,
    )

    class Meta:
        app_label = "accounts"
        verbose_name = _("address")
        verbose_name_plural = _("addresses")
        ordering = ["-is_default", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(is_default=True),
                name="unique_default_address_per_user",
            ),
        ]

    def save(self, *args, **kwargs):
        if self.is_default and self.user_id:
            # Atomically unset other default addresses for this user
            Address.objects.filter(user_id=self.user_id, is_default=True).exclude(
                pk=self.pk
            ).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name}, {self.city}, {self.state} - {self.pincode}"
