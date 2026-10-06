"""
Django Admin registration for Catalog models.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from apps.catalog.models import (
    Category,
    Collection,
    FeaturedProduct,
    Product,
    ProductMedia,
    ProductSpecification,
)


class ProductSpecificationInline(admin.TabularInline):
    model = ProductSpecification
    extra = 1
    fields = ["key", "value", "source", "is_highlight", "display_order"]


class ProductMediaInline(admin.TabularInline):
    model = ProductMedia
    extra = 1
    fields = ["media_type", "external_image_url", "local_image", "alt_text", "display_order"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "accent_key", "hsn_code", "gst_rate", "is_gst_rate_verified", "is_active", "display_order"]
    list_filter = ["is_active", "is_gst_rate_verified", "accent_key"]
    search_fields = ["name", "slug", "hsn_code"]
    prepopulated_fields = {"slug": ("name",)}
    ordering = ["display_order", "name"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["sku", "display_name", "category", "parsed_brand", "selling_price", "mrp", "is_available", "source_rating"]
    list_filter = ["category", "parsed_brand", "is_available"]
    search_fields = ["sku", "source_asin", "display_name", "raw_name", "parsed_brand"]
    readonly_fields = ["source_asin", "source_url", "effective_hsn", "effective_gst_rate", "effective_gst_verified", "created_at", "updated_at"]
    inlines = [ProductSpecificationInline, ProductMediaInline]
    ordering = ["-source_rating_count", "display_name"]


class FeaturedProductInline(admin.TabularInline):
    model = FeaturedProduct
    extra = 1
    raw_id_fields = ["product"]


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ["title", "slug", "is_active", "is_sample_data", "display_order"]
    list_filter = ["is_active", "is_sample_data"]
    search_fields = ["title", "slug"]
    prepopulated_fields = {"slug": ("title",)}
    inlines = [FeaturedProductInline]
    ordering = ["display_order", "title"]


@admin.register(FeaturedProduct)
class FeaturedProductAdmin(admin.ModelAdmin):
    list_display = ["collection", "product", "is_hero", "callout", "display_order"]
    list_filter = ["collection", "is_hero"]
    search_fields = ["product__display_name", "collection__title"]
    raw_id_fields = ["product"]
