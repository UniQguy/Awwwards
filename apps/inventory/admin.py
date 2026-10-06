"""
Django Admin registration for Inventory and StockReservation models.
"""

from django.contrib import admin
from apps.inventory.models import Inventory, StockReservation


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ["product_sku", "product_name", "quantity", "low_stock_threshold", "is_in_stock", "is_low_stock"]
    list_filter = ["is_sample_data"]
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
