"""
Django Admin registration for Wishlist and WishlistItem models.
"""

from django.contrib import admin
from apps.wishlist.models import Wishlist, WishlistItem


class WishlistItemInline(admin.TabularInline):
    model = WishlistItem
    extra = 0
    raw_id_fields = ["product"]


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ["id", "owner_display", "item_count", "updated_at"]
    search_fields = ["user__email", "guest_token"]
    inlines = [WishlistItemInline]

    def owner_display(self, obj):
        return obj.user.email if obj.user else f"Guest ({obj.guest_token[:8]})"

    def item_count(self, obj):
        return obj.items.count()
