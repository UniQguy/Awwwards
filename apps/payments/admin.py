"""
Django Admin registration for PaymentTransaction and WebhookEvent models.
"""

from django.contrib import admin
from apps.payments.models import PaymentTransaction, WebhookEvent


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ["id", "order_display", "payment_method", "amount", "currency", "status", "created_at"]
    list_filter = ["status", "payment_method", "currency"]
    search_fields = ["order__order_number", "gateway_order_id", "gateway_payment_id"]
    readonly_fields = ["created_at", "updated_at"]

    def order_display(self, obj):
        return obj.order.order_number


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ["event_id", "event_type", "is_processed", "processed_at", "created_at"]
    list_filter = ["is_processed", "event_type"]
    search_fields = ["event_id", "event_type"]
    readonly_fields = ["created_at"]
