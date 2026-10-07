"""
Transactional Email Notifier Service for ELECTROCART (Phase 7, WP1).
Sends multipart (HTML & plain-text) emails on order lifecycle events.

Strict Invariants:
1. Dispatched strictly inside transaction.on_commit to ensure rollbacks never email.
2. Idempotent per (order, event) via EmailLog model: webhook retries do not resend.
3. Sending failures are caught and logged (with masked emails/tokens); never breaks commerce flow.
4. Links are fully qualified using settings.SITE_URL.
5. Guest order links carry signed token exactly once.
6. Plain language voice from docs/COPY.md; zero remote images.
"""

from decimal import Decimal
import logging
from typing import Any, Dict, Optional

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.template.loader import render_to_string

from apps.orders.models import CreditNote, EmailLog, Order

logger = logging.getLogger("apps.orders.emails")


def mask_email(email: str) -> str:
    """Masks an email address for safe log output (e.g. j***@example.com)."""
    if not email or "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    if len(local) <= 1:
        masked_local = local + "***"
    else:
        masked_local = local[0] + "***" + local[-1]
    return f"{masked_local}@{domain}"


def mask_token(token: str) -> str:
    """Masks a security token for safe logging (e.g. abc***)."""
    if not token:
        return ""
    if len(token) <= 4:
        return "***"
    return token[:3] + "***"


def build_order_url(order: Order, guest_token: Optional[str] = None) -> str:
    """Builds the fully qualified order URL, attaching guest token if applicable."""
    base_url = f"{settings.SITE_URL.rstrip('/')}/orders/{order.order_number}/"
    if guest_token and "token=" not in base_url:
        return f"{base_url}?token={guest_token}"
    return base_url


def _send_transactional_email(
    order: Order,
    event: str,
    subject: str,
    template_prefix: str,
    context: Dict[str, Any],
) -> bool:
    """
    Core sender executing the email delivery with idempotency and error trapping.
    """
    recipient = order.recipient_email
    if not recipient:
        logger.warning(
            "Skipping email for order %s event %s: no recipient email found",
            order.order_number,
            event,
        )
        return False

    # 1. Idempotency check: Skip if this event was already sent for this order
    if EmailLog.objects.filter(order=order, event=event, sent_successfully=True).exists():
        logger.info(
            "Idempotent skip: Email for order %s event %s already sent",
            order.order_number,
            event,
        )
        return False

    context["site_url"] = settings.SITE_URL.rstrip("/")
    html_template = f"{template_prefix}.html"
    txt_template = f"{template_prefix}.txt"

    try:
        html_content = render_to_string(html_template, context)
        text_content = render_to_string(txt_template, context)

        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "orders@electrocart.in")

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=[recipient],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)

        EmailLog.objects.update_or_create(
            order=order,
            event=event,
            defaults={
                "recipient_email": mask_email(recipient),
                "subject": subject,
                "sent_successfully": True,
                "error_message": "",
            },
        )
        logger.info(
            "Successfully sent email for order %s (event: %s) to %s",
            order.order_number,
            event,
            mask_email(recipient),
        )
        return True

    except Exception as err:
        logger.error(
            "Failed to send email for order %s (event: %s) to %s: %s",
            order.order_number,
            event,
            mask_email(recipient),
            str(err),
            exc_info=False,
        )
        EmailLog.objects.update_or_create(
            order=order,
            event=event,
            defaults={
                "recipient_email": mask_email(recipient),
                "subject": subject,
                "sent_successfully": False,
                "error_message": str(err)[:500],
            },
        )
        # Non-blocking: never re-raise to avoid aborting database transactions
        return False


def send_order_confirmation(order: Order, guest_token: Optional[str] = None) -> None:
    """Dispatches order confirmation email upon successful placement."""
    event = "order_confirmation"
    subject = f"Order Confirmed: #{order.order_number}"
    context = {
        "order": order,
        "order_url": build_order_url(order, guest_token),
    }

    def _dispatch():
        _send_transactional_email(order, event, subject, "emails/order_confirmation", context)

    transaction.on_commit(_dispatch)


def send_payment_confirmation(order: Order, payment_id: str, guest_token: Optional[str] = None) -> None:
    """Dispatches payment confirmation email when Razorpay payment is captured."""
    event = "payment_confirmation"
    subject = f"Payment Received: #{order.order_number}"
    context = {
        "order": order,
        "payment_id": payment_id,
        "order_url": build_order_url(order, guest_token),
    }

    def _dispatch():
        _send_transactional_email(order, event, subject, "emails/payment_confirmation", context)

    transaction.on_commit(_dispatch)


def send_status_update(
    order: Order,
    status: str,
    tracking_number: Optional[str] = None,
    carrier: Optional[str] = None,
    estimated_delivery: Optional[str] = None,
    guest_token: Optional[str] = None,
) -> None:
    """Dispatches status update email on fulfillment progression."""
    event = f"status_{status}"
    status_display = dict(Order.STATUS_CHOICES).get(status, status.title())
    subject = f"Order Update: #{order.order_number} is {status_display}"
    context = {
        "order": order,
        "status_display": status_display,
        "carrier": carrier or order.tracking_carrier,
        "tracking_number": tracking_number or order.tracking_number,
        "estimated_delivery": estimated_delivery,
        "order_url": build_order_url(order, guest_token),
    }

    def _dispatch():
        _send_transactional_email(order, event, subject, "emails/status_update", context)

    transaction.on_commit(_dispatch)


def send_cancellation_refund(
    order: Order,
    credit_note: Optional[CreditNote] = None,
    refund_amount: Optional[Decimal] = None,
    reason: str = "",
    guest_token: Optional[str] = None,
) -> None:
    """Dispatches cancellation & refund notice upon order cancellation."""
    event = "cancellation_refund"
    subject = f"Order Cancelled: #{order.order_number}"
    context = {
        "order": order,
        "credit_note": credit_note,
        "refund_amount": refund_amount,
        "reason": reason,
        "order_url": build_order_url(order, guest_token),
    }

    def _dispatch():
        _send_transactional_email(order, event, subject, "emails/cancellation_refund", context)

    transaction.on_commit(_dispatch)


def send_cod_placed(order: Order, guest_token: Optional[str] = None) -> None:
    """Dispatches COD order scheduled note with doorstep cash due."""
    event = "cod_placed"
    subject = f"Cash on Delivery Scheduled: #{order.order_number}"
    context = {
        "order": order,
        "order_url": build_order_url(order, guest_token),
    }

    def _dispatch():
        _send_transactional_email(order, event, subject, "emails/cod_placed", context)

    transaction.on_commit(_dispatch)
