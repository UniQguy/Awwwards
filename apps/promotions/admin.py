"""
Django Admin registration for Coupon and CouponRedemption models.
"""

from django.contrib import admin
from apps.promotions.models import Coupon, CouponRedemption


class CouponRedemptionInline(admin.TabularInline):
    model = CouponRedemption
    extra = 0
    readonly_fields = ["user", "order", "discount_applied", "redeemed_at"]


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ["code", "discount_type", "discount_value", "min_order_amount", "max_discount_amount", "is_active", "valid_until"]
    list_filter = ["discount_type", "is_active", "is_sample_data"]
    search_fields = ["code", "description"]
    filter_horizontal = ["applicable_categories"]
    inlines = [CouponRedemptionInline]


@admin.register(CouponRedemption)
class CouponRedemptionAdmin(admin.ModelAdmin):
    list_display = ["coupon", "user", "order", "discount_applied", "redeemed_at"]
    search_fields = ["coupon__code", "user__email"]
    readonly_fields = ["coupon", "user", "order", "discount_applied", "redeemed_at"]
