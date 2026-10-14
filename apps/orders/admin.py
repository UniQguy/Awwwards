"""
Django Admin registration for Orders, OrderItems, Invoices, and CreditNotes.
"""

import csv
from django import forms
from django.contrib import admin, messages
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _

from apps.orders.models import (
    CreditNote,
    Invoice,
    InvoiceCounter,
    Order,
    OrderItem,
    OrderStatusHistory,
)
from apps.orders.services.order_status import (
    can_transition,
    transition_order_status,
    InvalidOrderTransitionError,
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


class OrderAdminForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = "__all__"

    def clean_status(self):
        new_status = self.cleaned_data.get("status")
        if self.instance and self.instance.pk and self.instance.status != new_status:
            if not can_transition(self.instance.status, new_status):
                raise forms.ValidationError(
                    f"Status transition from '{self.instance.status}' to '{new_status}' is not permitted."
                )
        return new_status


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    form = OrderAdminForm
    list_display = ["order_number", "customer_display", "status", "payment_method", "payment_status", "total_amount", "created_at"]
    list_filter = ["status", "payment_method", "payment_status", "is_bill_of_supply"]
    search_fields = ["order_number", "user__email", "guest_email", "tracking_number"]
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    actions = [
        "export_orders_to_csv",
        "mark_confirmed",
        "mark_processing",
        "mark_shipped",
        "mark_delivered",
        "mark_cancelled",
    ]

    def customer_display(self, obj):
        return obj.user.email if obj.user else f"Guest ({obj.guest_email})"

    def get_readonly_fields(self, request, obj=None):
        fields = list(super().get_readonly_fields(request, obj))
        if obj:
            for f in ["subtotal", "shipping_fee", "discount_amount", "tax_amount", "total_amount"]:
                if f not in fields:
                    fields.append(f)
        return fields

    def save_model(self, request, obj, form, change):
        if change and "status" in form.changed_data:
            from_status = form.initial.get("status")
            to_status = obj.status
            obj.status = from_status
            transition_order_status(
                obj,
                to_status,
                notes=f"Staff admin update by {getattr(request.user, 'email', str(request.user))}",
                changed_by=request.user,
            )
        super().save_model(request, obj, form, change)

    @admin.action(description=_("Export selected orders to CSV"))
    def export_orders_to_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="orders_export.csv"'
        writer = csv.writer(response)
        writer.writerow([
            "Order Number",
            "Created Date",
            "Customer Email",
            "Status",
            "Payment Method",
            "Payment Status",
            "Subtotal",
            "Shipping Fee",
            "Discount Amount",
            "Tax Amount",
            "Total Amount",
            "Items Count",
            "Carrier",
            "Tracking Number",
        ])
        for order in queryset.select_related("user").prefetch_related("items"):
            created_str = order.created_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(order, "created_at") and order.created_at else ""
            writer.writerow([
                order.order_number,
                created_str,
                order.recipient_email,
                order.status,
                order.payment_method,
                order.payment_status,
                order.subtotal,
                order.shipping_fee,
                order.discount_amount,
                order.tax_amount,
                order.total_amount,
                order.items.count(),
                order.tracking_carrier,
                order.tracking_number,
            ])
        return response

    @admin.action(description=_("Mark selected orders as Confirmed"))
    def mark_confirmed(self, request, queryset):
        self._batch_transition(request, queryset, Order.STATUS_CONFIRMED, "Confirmed")

    @admin.action(description=_("Mark selected orders as Processing"))
    def mark_processing(self, request, queryset):
        self._batch_transition(request, queryset, Order.STATUS_PROCESSING, "Processing")

    @admin.action(description=_("Mark selected orders as Shipped"))
    def mark_shipped(self, request, queryset):
        self._batch_transition(request, queryset, Order.STATUS_SHIPPED, "Shipped")

    @admin.action(description=_("Mark selected orders as Delivered"))
    def mark_delivered(self, request, queryset):
        self._batch_transition(request, queryset, Order.STATUS_DELIVERED, "Delivered")

    @admin.action(description=_("Cancel and restock selected orders"))
    def mark_cancelled(self, request, queryset):
        self._batch_transition(request, queryset, Order.STATUS_CANCELLED, "Cancelled (restocked)")

    def _batch_transition(self, request, queryset, target_status, label):
        success_count = 0
        error_count = 0
        for order in queryset:
            try:
                transition_order_status(
                    order,
                    target_status,
                    notes=f"Batch updated to {label} by {getattr(request.user, 'email', str(request.user))}",
                    changed_by=request.user,
                )
                success_count += 1
            except Exception as e:
                error_count += 1
                self.message_user(
                    request,
                    f"Could not change order {order.order_number} to {label}: {e}",
                    level=messages.ERROR,
                )
        if success_count:
            self.message_user(
                request,
                f"Successfully updated {success_count} order(s) to {label}.",
                level=messages.SUCCESS,
            )



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
