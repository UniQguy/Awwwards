"""
Django Admin registration for Inventory and StockReservation models.
"""

from django.contrib import admin
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.inventory.models import Inventory, StockReservation


class LowStockFilter(admin.SimpleListFilter):
    title = _("Stock level")
    parameter_name = "stock_level"

    def lookups(self, request, model_admin):
        return [
            ("in_stock", _("In Stock (> 0)")),
            ("low_stock", _("Low Stock (<= threshold)")),
            ("out_of_stock", _("Out of Stock (0)")),
        ]

    def queryset(self, request, queryset):
        if self.value() == "in_stock":
            return queryset.filter(quantity__gt=0)
        if self.value() == "low_stock":
            return queryset.filter(quantity__gt=0, quantity__lte=models.F("low_stock_threshold"))
        if self.value() == "out_of_stock":
            return queryset.filter(quantity=0)
        return queryset


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ["product_sku", "product_name", "quantity", "low_stock_threshold", "is_in_stock", "is_low_stock"]
    list_filter = [LowStockFilter, "is_sample_data"]
    search_fields = ["product__sku", "product__display_name", "product__source_asin"]
    raw_id_fields = ["product"]

    def product_sku(self, obj):
        return obj.product.sku

    def product_name(self, obj):
        return obj.product.display_name


@admin.register(StockReservation)
class StockReservationAdmin(admin.ModelAdmin):
    list_display = ["id", "product_sku", "quantity", "status", "expires_at", "owner_key", "is_expired"]
    list_filter = ["status"]
    search_fields = ["product__sku", "owner_key", "user__email"]
    raw_id_fields = ["product", "user", "order"]

    def product_sku(self, obj):
        return obj.product.sku
