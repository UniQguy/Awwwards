from django.contrib import admin
from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("subject", "name", "email", "created_at", "resolved")
    list_filter = ("resolved", "created_at")
    search_fields = ("name", "email", "subject", "message")
    readonly_fields = ("created_at", "updated_at")
    actions = ["mark_resolved", "mark_unresolved"]

    @admin.action(description="Mark selected inquiries as resolved")
    def mark_resolved(self, request, queryset):
        queryset.update(resolved=True)

    @admin.action(description="Mark selected inquiries as unresolved")
    def mark_unresolved(self, request, queryset):
        queryset.update(resolved=False)
