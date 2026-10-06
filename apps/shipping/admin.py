"""
Django admin configuration for shipping rules, zones, and pincode serviceability.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import PincodeServiceability, ShippingConfig, ShippingZone


@admin.register(ShippingConfig)
class ShippingConfigAdmin(admin.ModelAdmin):
    list_display = [
        "__str__",
        "free_shipping_threshold",
        "standard_fee",
        "cod_fee",
        "is_standard_fee_confirmed",
        "updated_at",
    ]
    fields = [
        "free_shipping_threshold",
        "standard_fee",
        "cod_fee",
        "is_standard_fee_confirmed",
    ]

    def has_add_permission(self, request):
        return not ShippingConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        config = ShippingConfig.get_solo()
        if not config.is_standard_fee_confirmed:
            extra_context["warning_banner"] = (
                "Standard delivery fee (₹40.00) is an unconfirmed placeholder. Confirm with the business owner."
            )
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(ShippingZone)
class ShippingZoneAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "pin_prefix",
        "transit_window",
        "cod_allowed",
        "is_active",
        "source_badge",
    ]
    list_filter = ["is_active", "source", "cod_allowed"]
    search_fields = ["name", "pin_prefix"]

    def transit_window(self, obj):
        return f"{obj.est_days_min} - {obj.est_days_max} days"
    transit_window.short_description = _("Transit Window")

    def source_badge(self, obj):
        if obj.source == "sample":
            return format_html('<span style="color:#b45309;font-weight:bold;">SAMPLE</span>')
        return format_html('<span style="color:#15803d;">CARRIER</span>')
    source_badge.short_description = _("Source")


@admin.register(PincodeServiceability)
class PincodeServiceabilityAdmin(admin.ModelAdmin):
    list_display = [
        "pincode",
        "state",
        "is_serviceable",
        "est_days_min",
        "est_days_max",
        "cod_allowed",
        "source",
    ]
    list_filter = ["is_serviceable", "source", "state"]
    search_fields = ["pincode", "state"]
