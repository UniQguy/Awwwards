"""
Django admin configuration for custom User and Address models.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import Address, User


class AddressInline(admin.TabularInline):
    model = Address
    extra = 0
    fields = [
        "full_name",
        "phone",
        "line1",
        "city",
        "state",
        "pincode",
        "is_default",
    ]


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ["email"]
    list_display = [
        "email",
        "full_name",
        "is_staff",
        "is_active",
        "created_at",
    ]
    list_filter = ["is_staff", "is_active", "created_at"]
    search_fields = ["email", "full_name"]
    inlines = [AddressInline]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("full_name",)}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login",)}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = [
        "full_name",
        "city",
        "state",
        "pincode",
        "is_default",
        "user",
        "created_at",
    ]
    list_filter = ["state", "is_default"]
    search_fields = ["full_name", "phone", "city", "pincode", "user__email"]
