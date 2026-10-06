"""
Django Admin registration for Orders, OrderItems, Invoices, and CreditNotes.
"""

from django.contrib import admin
from apps.orders.models import (
    CreditNote,
    Invoice,
    InvoiceCounter,
    Order,
    OrderItem,
    OrderStatusHistory,
)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    raw_id_fields = ["product"]
    readonly_fields = [
        "product_title", "product_sku", "unit_price", "mrp", "quantity",
        "hsn_code", "gst_rate", "discount_allocated", "taxable_value",
        "cgst_amount", "sgst_amount", "igst_amount", "line_total",
    ]


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ["from_status", "to_status", "notes", "changed_by", "created_at"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["order_number", "customer_display", "status", "payment_method", "payment_status", "total_amount", "created_at"]
    list_filter = ["status", "payment_method", "payment_status", "is_bill_of_supply"]
    search_fields = ["order_number", "user__email", "guest_email", "tracking_number"]
    inlines = [OrderItemInline, OrderStatusHistoryInline]

    def customer_display(self, obj):
        return obj.user.email if obj.user else f"Guest ({obj.guest_email})"


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ["invoice_number", "order", "financial_year", "sequence_number", "is_bill_of_supply", "invoice_date"]
    list_filter = ["financial_year", "is_bill_of_supply"]
    search_fields = ["invoice_number", "order__order_number"]
    readonly_fields = ["invoice_number", "order", "financial_year", "sequence_number", "invoice_date"]


@admin.register(CreditNote)
class CreditNoteAdmin(admin.ModelAdmin):
    list_display = ["credit_note_number", "invoice", "order", "amount", "tax_amount", "created_at"]
    search_fields = ["credit_note_number", "order__order_number", "invoice__invoice_number"]
    readonly_fields = ["credit_note_number", "invoice", "order", "financial_year", "sequence_number", "amount", "tax_amount", "created_at"]


@admin.register(InvoiceCounter)
class InvoiceCounterAdmin(admin.ModelAdmin):
    list_display = ["financial_year", "series_type", "last_number"]
    list_filter = ["financial_year", "series_type"]
