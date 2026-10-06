"""
Django Admin registration for Cart and CartItem models.
"""

from django.contrib import admin
from apps.cart.models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    raw_id_fields = ["product"]


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ["id", "owner_display", "is_active", "total_quantity", "updated_at"]
    list_filter = ["is_active"]
    search_fields = ["user__email", "guest_token"]
    inlines = [CartItemInline]

    def owner_display(self, obj):
        return obj.user.email if obj.user else f"Guest ({obj.guest_token[:8]})"
