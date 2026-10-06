"""
Payment transaction and webhook idempotency models.
"""

from decimal import Decimal
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class PaymentTransaction(TimeStampedModel):
    """
    Log of payment attempts and gateway state transitions per order.
    """

    STATUS_CREATED = "created"
    STATUS_AUTHORIZED = "authorized"
    STATUS_CAPTURED = "captured"
    STATUS_FAILED = "failed"
    STATUS_REFUNDED = "refunded"

    STATUS_CHOICES = [
        (STATUS_CREATED, _("Created")),
        (STATUS_AUTHORIZED, _("Authorized")),
        (STATUS_CAPTURED, _("Captured")),
        (STATUS_FAILED, _("Failed")),
        (STATUS_REFUNDED, _("Refunded")),
    ]

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="transactions",
        verbose_name=_("order"),
    )
    payment_method = models.CharField(_("payment method"), max_length=20, default="razorpay")
    amount = models.DecimalField(_("amount (₹)"), max_digits=12, decimal_places=2)
    currency = models.CharField(_("currency"), max_length=5, default="INR")
    status = models.CharField(_("transaction status"), max_length=20, choices=STATUS_CHOICES, default=STATUS_CREATED, db_index=True)

    gateway_order_id = models.CharField(_("gateway order ID (e.g. order_...)"), max_length=100, blank=True, db_index=True)
    gateway_payment_id = models.CharField(_("gateway payment ID (e.g. pay_...)"), max_length=100, blank=True, db_index=True)
    gateway_signature = models.CharField(_("gateway HMAC signature"), max_length=255, blank=True)

    error_code = models.CharField(_("gateway error code"), max_length=100, blank=True)
    error_description = models.TextField(_("gateway error description"), blank=True)
    raw_response = models.JSONField(_("gateway raw payload"), default=dict, blank=True)

    class Meta:
        verbose_name = _("payment transaction")
        verbose_name_plural = _("payment transactions")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Txn #{self.id} for Order {self.order.order_number}: ₹{self.amount} ({self.status})"


class WebhookEvent(models.Model):
    """
    Audit and deduplication record for inbound payment gateway webhooks.
    Enforces exactly-once processing using event_id uniqueness.
    """

    event_id = models.CharField(_("unique event ID"), max_length=100, unique=True, db_index=True)
    event_type = models.CharField(_("event type (e.g. payment.captured)"), max_length=100, db_index=True)
    payload = models.JSONField(_("raw webhook payload"), default=dict)
    is_processed = models.BooleanField(_("is processed"), default=False)
    processed_at = models.DateTimeField(_("processing timestamp"), null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("webhook event")
        verbose_name_plural = _("webhook events")
        ordering = ["-created_at"]

    def __str__(self):
        status = "PROCESSED" if self.is_processed else "PENDING"
        return f"Webhook {self.event_id} ({self.event_type}) - {status}"
