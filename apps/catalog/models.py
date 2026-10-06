"""
Catalog models: Category, Product, ProductSpecification, ProductMedia, Collection, FeaturedProduct.
All financial arithmetic strictly utilizes Decimal. Check constraints and indexes protect integrity.
"""

from decimal import Decimal
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class Category(TimeStampedModel):
    """
    Product category mapped to a distinct editorial colour-world and GST taxation defaults.
    """

    name = models.CharField(_("category name"), max_length=100)
    slug = models.SlugField(_("slug"), max_length=100, unique=True)
    hsn_code = models.CharField(_("HSN code"), max_length=10, blank=True)
    gst_rate = models.DecimalField(
        _("default GST rate (%)"),
        max_digits=5,
        decimal_places=2,
        default=Decimal("18.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    is_gst_rate_verified = models.BooleanField(
        _("is GST rate verified with accountant"),
        default=False,
    )
    accent_key = models.CharField(
        _("accent key / colour-world slug"),
        max_length=50,
        help_text=_("Matches one of the 10 frozen category colour world slugs in verify_contrast.py"),
    )
    display_order = models.PositiveIntegerField(_("display order"), default=0)
    description = models.TextField(_("editorial description"), blank=True)
    is_active = models.BooleanField(_("is active"), default=True)

    class Meta:
        verbose_name = _("category")
        verbose_name_plural = _("categories")
        ordering = ["display_order", "name"]

    def __str__(self):
        status = "" if self.is_gst_rate_verified else " [UNVERIFIED GST]"
        return f"{self.name} ({self.gst_rate}%){status}"


class Product(TimeStampedModel):
    """
    Core merchandise item imported from the electronics dataset or managed directly.
    """

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
        verbose_name=_("category"),
    )
    sku = models.CharField(_("SKU"), max_length=30, unique=True, db_index=True)
    slug = models.SlugField(_("slug"), max_length=255, unique=True)
    raw_name = models.CharField(_("original raw marketplace title"), max_length=500)
    display_name = models.CharField(_("curated display title"), max_length=255)
    source_asin = models.CharField(_("source Amazon ASIN"), max_length=20, unique=True, db_index=True)
    source_url = models.URLField(_("source marketplace URL"), max_length=500, blank=True)
    parsed_brand = models.CharField(_("brand"), max_length=100, default="Unknown", db_index=True)
    selling_price = models.DecimalField(
        _("selling price (₹, tax-inclusive)"),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    mrp = models.DecimalField(
        _("maximum retail price (MRP ₹)"),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    is_available = models.BooleanField(_("is available in stock"), default=True)
    source_rating = models.DecimalField(
        _("source rating (1.00 - 5.00)"),
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
    )
    source_rating_count = models.PositiveIntegerField(
        _("source rating count"),
        null=True,
        blank=True,
        db_index=True,
    )
    description = models.TextField(_("product description / monograph notes"), blank=True)
    hsn_code = models.CharField(_("HSN override"), max_length=10, blank=True)
    gst_rate = models.DecimalField(
        _("GST rate override (%)"),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    is_gst_rate_verified = models.BooleanField(
        _("is GST override rate verified"),
        default=False,
    )
    search_text = models.TextField(_("denormalized search vector"), blank=True)

    class Meta:
        verbose_name = _("product")
        verbose_name_plural = _("products")
        ordering = ["-source_rating_count", "display_name"]
        constraints = [
            models.CheckConstraint(
                condition=Q(selling_price__gte=0) | Q(selling_price__isnull=True),
                name="check_product_selling_price_non_negative",
            ),
            models.CheckConstraint(
                condition=Q(mrp__gte=0) | Q(mrp__isnull=True),
                name="check_product_mrp_non_negative",
            ),
            models.CheckConstraint(
                condition=Q(source_rating__gte=0, source_rating__lte=5) | Q(source_rating__isnull=True),
                name="check_product_rating_range_0_5",
            ),
        ]
        indexes = [
            models.Index(fields=["category", "selling_price"], name="idx_prod_cat_price"),
            models.Index(fields=["category", "is_available"], name="idx_prod_cat_avail"),
            models.Index(fields=["parsed_brand"], name="idx_prod_brand"),
            models.Index(fields=["source_rating_count"], name="idx_prod_rating_cnt"),
            models.Index(fields=["raw_name"], name="idx_prod_raw_name"),
        ]

    def __str__(self):
        price_str = f"₹{self.selling_price}" if self.selling_price else "Unpriced"
        return f"{self.display_name} ({self.sku}) - {price_str}"

    @property
    def effective_hsn(self) -> str:
        return self.hsn_code if self.hsn_code else self.category.hsn_code

    @property
    def effective_gst_rate(self) -> Decimal:
        return self.gst_rate if self.gst_rate is not None else self.category.gst_rate

    @property
    def effective_gst_verified(self) -> bool:
        if self.gst_rate is not None:
            return self.is_gst_rate_verified
        return self.category.is_gst_rate_verified

    @property
    def is_purchasable(self) -> bool:
        return self.selling_price is not None and self.selling_price > Decimal("0.00") and self.is_available

    def save(self, *args, **kwargs):
        # Automatically update denormalized search_text
        brand = self.parsed_brand or ""
        cat_name = self.category.name if self.category_id else ""
        self.search_text = f"{self.raw_name} {self.display_name} {brand} {cat_name} {self.sku} {self.source_asin}".lower()
        super().save(*args, **kwargs)


class ProductSpecification(TimeStampedModel):
    """
    Normalized key-value specification parsed from title or curated by editors.
    """

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="specifications",
        verbose_name=_("product"),
    )
    key = models.CharField(_("attribute key"), max_length=100)
    value = models.CharField(_("attribute value"), max_length=255)
    source = models.CharField(_("provenance"), max_length=30, default="parsed_from_title")
    is_highlight = models.BooleanField(_("highlight in editorial cards"), default=False)
    display_order = models.PositiveIntegerField(_("display order"), default=0)

    class Meta:
        verbose_name = _("product specification")
        verbose_name_plural = _("product specifications")
        ordering = ["-is_highlight", "display_order", "key"]
        constraints = [
            models.UniqueConstraint(fields=["product", "key"], name="unique_product_spec_key"),
        ]

    def __str__(self):
        return f"{self.key}: {self.value}"


class ProductMedia(TimeStampedModel):
    """
    Visual assets for a product: marketplace photos, local webp cutouts, video/3D placeholders.
    """

    MEDIA_TYPES = [
        ("image", _("Product Photograph")),
        ("video_placeholder", _("Kinetic Video Placeholder")),
        ("model_placeholder", _("3D Model Plinth Placeholder")),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="media",
        verbose_name=_("product"),
    )
    media_type = models.CharField(_("media type"), max_length=20, choices=MEDIA_TYPES, default="image")
    external_image_url = models.URLField(_("external CDN / marketplace URL"), max_length=500, blank=True)
    local_image = models.ImageField(_("local asset file"), upload_to="products/%Y/%m/", blank=True)
    alt_text = models.CharField(_("alt text description"), max_length=255, blank=True)
    display_order = models.PositiveIntegerField(_("display order"), default=0)
    width = models.PositiveIntegerField(_("width (px)"), null=True, blank=True)
    height = models.PositiveIntegerField(_("height (px)"), null=True, blank=True)

    class Meta:
        verbose_name = _("product media")
        verbose_name_plural = _("product media items")
        ordering = ["display_order", "id"]

    def clean(self):
        if self.media_type == "image" and not self.external_image_url and not self.local_image:
            raise ValidationError(_("An image media item must provide either an external URL or a local file."))

    @property
    def url(self) -> str:
        if self.local_image:
            return self.local_image.url
        return self.external_image_url or ""

    def __str__(self):
        return f"{self.product.sku} - {self.get_media_type_display()} (#{self.display_order})"


class Collection(TimeStampedModel):
    """
    Curated editorial groupings of real products for themed homepage spreads.
    """

    title = models.CharField(_("collection title"), max_length=150)
    slug = models.SlugField(_("slug"), max_length=150, unique=True)
    intro = models.TextField(_("editorial introduction"), blank=True)
    is_active = models.BooleanField(_("is active"), default=True)
    display_order = models.PositiveIntegerField(_("display order"), default=0)
    is_sample_data = models.BooleanField(_("is sample/demo data"), default=False)

    class Meta:
        verbose_name = _("editorial collection")
        verbose_name_plural = _("editorial collections")
        ordering = ["display_order", "title"]

    def __str__(self):
        sample = " [SAMPLE]" if self.is_sample_data else ""
        return f"{self.title}{sample}"


class FeaturedProduct(TimeStampedModel):
    """
    Through-model assigning specific catalog products to an editorial collection slot.
    """

    collection = models.ForeignKey(
        Collection,
        on_delete=models.CASCADE,
        related_name="featured_items",
        verbose_name=_("collection"),
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="collection_features",
        verbose_name=_("product"),
    )
    display_order = models.PositiveIntegerField(_("display order"), default=0)
    callout = models.CharField(_("short editorial note"), max_length=140, blank=True)
    is_hero = models.BooleanField(_("hero slot"), default=False)

    class Meta:
        verbose_name = _("featured product slot")
        verbose_name_plural = _("featured product slots")
        ordering = ["display_order", "id"]
        constraints = [
            models.UniqueConstraint(fields=["collection", "product"], name="unique_collection_featured_product"),
        ]

    def __str__(self):
        hero = " (Hero)" if self.is_hero else ""
        return f"{self.collection.title} -> {self.product.display_name}{hero}"
