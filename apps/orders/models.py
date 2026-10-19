"""
Orders, Invoicing, and Credit Notes models.
Compliant with Indian GST sequential gap-free numbering and financial year series.
"""

from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class Order(TimeStampedModel):
    """
    Customer merchandise order with point-in-time financial snapshots.
    """

    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_PROCESSING = "processing"
    STATUS_SHIPPED = "shipped"
    STATUS_DELIVERED = "delivered"
    STATUS_CANCELLED = "cancelled"
    STATUS_REFUND_REQUIRED = "refund_required"
    STATUS_REFUNDED = "refunded"

    STATUS_CHOICES = [
        (STATUS_PENDING, _("Pending")),
        (STATUS_CONFIRMED, _("Confirmed")),
        (STATUS_PROCESSING, _("Processing")),
        (STATUS_SHIPPED, _("Shipped")),
        (STATUS_DELIVERED, _("Delivered")),
        (STATUS_CANCELLED, _("Cancelled")),
        (STATUS_REFUND_REQUIRED, _("Refund Required")),
        (STATUS_REFUNDED, _("Refunded")),
    ]

    PAYMENT_METHOD_RAZORPAY = "razorpay"
    PAYMENT_METHOD_COD = "cod"

    PAYMENT_METHOD_CHOICES = [
        (PAYMENT_METHOD_RAZORPAY, _("Razorpay Online")),
        (PAYMENT_METHOD_COD, _("Cash on Delivery (COD)")),
    ]

    PAYMENT_STATUS_PENDING = "pending"
    PAYMENT_STATUS_AUTHORIZED = "authorized"
    PAYMENT_STATUS_CAPTURED = "captured"
    PAYMENT_STATUS_FAILED = "failed"
    PAYMENT_STATUS_REFUNDED = "refunded"

    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_STATUS_PENDING, _("Pending")),
        (PAYMENT_STATUS_AUTHORIZED, _("Authorized")),
        (PAYMENT_STATUS_CAPTURED, _("Captured")),
        (PAYMENT_STATUS_FAILED, _("Failed")),
        (PAYMENT_STATUS_REFUNDED, _("Refunded")),
    ]

    order_number = models.CharField(_("order number"), max_length=50, unique=True, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name=_("customer"),
    )
    guest_email = models.EmailField(_("guest email"), blank=True)
    guest_phone = models.CharField(_("guest phone"), max_length=20, blank=True)

    shipping_address_snapshot = models.JSONField(_("shipping address snapshot"), default=dict)
    billing_address_snapshot = models.JSONField(_("billing address snapshot"), default=dict)

    status = models.CharField(_("order status"), max_length=30, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)
    payment_method = models.CharField(_("payment method"), max_length=20, choices=PAYMENT_METHOD_CHOICES, default=PAYMENT_METHOD_COD)
    payment_status = models.CharField(_("payment status"), max_length=20, choices=PAYMENT_STATUS_CHOICES, default=PAYMENT_STATUS_PENDING)

    subtotal = models.DecimalField(_("subtotal (₹)"), max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    shipping_fee = models.DecimalField(_("shipping fee (₹)"), max_digits=10, decimal_places=2, default=Decimal("0.00"), validators=[MinValueValidator(Decimal("0.00"))])
    discount_amount = models.DecimalField(_("coupon discount (₹)"), max_digits=10, decimal_places=2, default=Decimal("0.00"), validators=[MinValueValidator(Decimal("0.00"))])
    tax_amount = models.DecimalField(_("total GST tax (₹)"), max_digits=10, decimal_places=2, default=Decimal("0.00"), validators=[MinValueValidator(Decimal("0.00"))])
    total_amount = models.DecimalField(_("grand total (₹)"), max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])

    tracking_carrier = models.CharField(_("shipping carrier"), max_length=50, blank=True)
    tracking_number = models.CharField(_("tracking reference"), max_length=100, blank=True)
    customer_notes = models.TextField(_("customer delivery notes"), blank=True)
    is_bill_of_supply = models.BooleanField(_("is bill of supply"), default=False)
    is_sample_data = models.BooleanField(_("is sample/demo order"), default=False)

    class Meta:
        verbose_name = _("order")
        verbose_name_plural = _("orders")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"], name="idx_order_status_created"),
            models.Index(fields=["user", "status"], name="idx_order_user_status"),
        ]

    def __str__(self):
        return f"Order {self.order_number} (₹{self.total_amount})"

    @property
    def recipient_email(self) -> str:
        if self.user and self.user.email:
            return self.user.email
        return self.guest_email

    @property
    def is_paid(self) -> bool:
        return self.payment_status == self.PAYMENT_STATUS_CAPTURED

    @property
    def cgst_amount(self) -> Decimal:
        return sum((item.cgst_amount for item in self.items.all()), Decimal("0.00"))

    @property
    def sgst_amount(self) -> Decimal:
        return sum((item.sgst_amount for item in self.items.all()), Decimal("0.00"))

    @property
    def igst_amount(self) -> Decimal:
        return sum((item.igst_amount for item in self.items.all()), Decimal("0.00"))


class OrderItem(models.Model):
    """
    Permanent snapshot of an individual line item purchased in an order.
    """

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items", verbose_name=_("order"))
    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT, related_name="order_items", verbose_name=_("product"))

    product_title = models.CharField(_("product title snapshot"), max_length=255)
    product_sku = models.CharField(_("SKU snapshot"), max_length=50)
    unit_price = models.DecimalField(_("unit selling price snapshot (₹)"), max_digits=12, decimal_places=2)
    mrp = models.DecimalField(_("MRP snapshot (₹)"), max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField(_("quantity"), default=1)

    hsn_code = models.CharField(_("HSN code"), max_length=10, blank=True)
    gst_rate = models.DecimalField(_("GST rate (%)"), max_digits=5, decimal_places=2, default=Decimal("18.00"))

    discount_allocated = models.DecimalField(_("allocated line discount (₹)"), max_digits=10, decimal_places=2, default=Decimal("0.00"))
    taxable_value = models.DecimalField(_("net taxable value (₹)"), max_digits=12, decimal_places=2)
    cgst_amount = models.DecimalField(_("CGST amount (₹)"), max_digits=10, decimal_places=2, default=Decimal("0.00"))
    sgst_amount = models.DecimalField(_("SGST amount (₹)"), max_digits=10, decimal_places=2, default=Decimal("0.00"))
    igst_amount = models.DecimalField(_("IGST amount (₹)"), max_digits=10, decimal_places=2, default=Decimal("0.00"))
    line_total = models.DecimalField(_("line total tax-inclusive (₹)"), max_digits=12, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("order item")
        verbose_name_plural = _("order items")

    def __str__(self):
        return f"{self.product_title} x {self.quantity}"

    @property
    def total_tax(self) -> Decimal:
        return (self.cgst_amount or Decimal("0.00")) + (self.sgst_amount or Decimal("0.00")) + (self.igst_amount or Decimal("0.00"))


class OrderStatusHistory(models.Model):
    """
    Audit log of order state transitions.
    """

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="status_history", verbose_name=_("order"))
    from_status = models.CharField(_("from status"), max_length=30)
    to_status = models.CharField(_("to status"), max_length=30)
    notes = models.TextField(_("notes / rationale"), blank=True)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("changed by"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("order status history")
        verbose_name_plural = _("order status histories")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.order.order_number}: {self.from_status} -> {self.to_status}"


class InvoiceCounter(models.Model):
    """
    Atomic counter ensuring sequential gap-free numbers per financial year.
    Series types: 'tax_invoice', 'bill_of_supply', 'credit_note'.
    """

    SERIES_TAX_INVOICE = "tax_invoice"
    SERIES_BILL_OF_SUPPLY = "bill_of_supply"
    SERIES_CREDIT_NOTE = "credit_note"

    SERIES_CHOICES = [
        (SERIES_TAX_INVOICE, _("Tax Invoice")),
        (SERIES_BILL_OF_SUPPLY, _("Bill of Supply")),
        (SERIES_CREDIT_NOTE, _("Credit Note")),
    ]

    financial_year = models.CharField(_("financial year (e.g. 2026-27)"), max_length=10)
    series_type = models.CharField(_("series type"), max_length=20, choices=SERIES_CHOICES)
    last_number = models.PositiveIntegerField(_("last allocated sequence"), default=0)

    class Meta:
        verbose_name = _("invoice counter")
        verbose_name_plural = _("invoice counters")
        constraints = [
            models.UniqueConstraint(fields=["financial_year", "series_type"], name="unique_fy_series_counter"),
        ]

    def __str__(self):
        return f"{self.financial_year} / {self.series_type}: #{self.last_number}"


class Invoice(TimeStampedModel):
    """
    Tax invoice or bill of supply issued for a confirmed/captured order.
    Numbering format: EC-INV-YYYY-YY-XXXXX or EC-BOS-YYYY-YY-XXXXX.
    """

    invoice_number = models.CharField(_("invoice number"), max_length=50, unique=True, db_index=True)
    order = models.OneToOneField(Order, on_delete=models.PROTECT, related_name="invoice", verbose_name=_("order"))
    financial_year = models.CharField(_("financial year"), max_length=10)
    sequence_number = models.PositiveIntegerField(_("sequence number"))
    is_bill_of_supply = models.BooleanField(_("is bill of supply"), default=False)
    invoice_date = models.DateTimeField(_("invoice issue date"), default=timezone.now)
    pdf_file = models.FileField(_("invoice PDF document"), upload_to="invoices/%Y/", blank=True)

    class Meta:
        verbose_name = _("invoice")
        verbose_name_plural = _("invoices")
        ordering = ["-invoice_date"]

    def __str__(self):
        return f"{self.invoice_number} (Order {self.order.order_number})"


class CreditNote(models.Model):
    """
    GST credit note issued upon order cancellation or return.
    Numbering format: EC-CN-YYYY-YY-XXXXX.
    """

    credit_note_number = models.CharField(_("credit note number"), max_length=50, unique=True, db_index=True)
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="credit_notes", verbose_name=_("original invoice"))
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="credit_notes", verbose_name=_("order"))
    financial_year = models.CharField(_("financial year"), max_length=10)
    sequence_number = models.PositiveIntegerField(_("sequence number"))
    amount = models.DecimalField(_("credit amount (₹)"), max_digits=12, decimal_places=2)
    tax_amount = models.DecimalField(_("credited GST (₹)"), max_digits=10, decimal_places=2)
    reason = models.CharField(_("reason for credit note"), max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("credit note")
        verbose_name_plural = _("credit notes")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.credit_note_number} (Invoice {self.invoice.invoice_number}): ₹{self.amount}"


class EmailLog(TimeStampedModel):
    """
    Audit log and idempotency guard for transactional emails dispatched per order event.
    """

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="email_logs", verbose_name=_("order"))
    event = models.CharField(_("event type"), max_length=60)
    recipient_email = models.CharField(_("masked recipient email"), max_length=255)
    subject = models.CharField(_("subject"), max_length=255)
    sent_successfully = models.BooleanField(_("sent successfully"), default=True)
    error_message = models.TextField(_("error message"), blank=True)

    class Meta:
        verbose_name = _("email log")
        verbose_name_plural = _("email logs")
        constraints = [
            models.UniqueConstraint(fields=["order", "event"], name="unique_order_event_email"),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.order.order_number} - {self.event} ({'Sent' if self.sent_successfully else 'Failed'})"

