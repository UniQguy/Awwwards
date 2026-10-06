"""
Webhook processing and payment confirmation service.
Implements signature verification, deduplication, atomic stock conversion, and refund_required fallback.
"""

from decimal import Decimal
import json
from typing import Any, Dict, Optional

from django.db import transaction
from django.utils import timezone

from apps.inventory.exceptions import (
    InsufficientStockError,
    ReservationExpiredError,
)
from apps.inventory.services.reservation_service import convert_reservation
from apps.orders.models import Order
from apps.orders.services.invoicing import generate_invoice
from apps.payments.models import PaymentTransaction, WebhookEvent
from apps.payments.providers import RazorpayProvider


def verify_and_capture_checkout_payment(
    order: Order,
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
    provider: Optional[RazorpayProvider] = None,
) -> bool:
    """
    Verifies payment signature from frontend checkout callback and confirms the order.
    """
    if provider is None:
        provider = RazorpayProvider()

    valid = provider.verify_payment_signature(
        razorpay_order_id=razorpay_order_id,
        razorpay_payment_id=razorpay_payment_id,
        razorpay_signature=razorpay_signature,
    )
    if not valid:
        return False

    with transaction.atomic():
        # Check if already captured
        if order.payment_status == Order.PAYMENT_STATUS_CAPTURED:
            return True

        # Attempt to convert active stock reservations
        try:
            for res in order.reservations.filter(status="reserved"):
                convert_reservation(res, order=order)

            order.status = Order.STATUS_CONFIRMED
            order.payment_status = Order.PAYMENT_STATUS_CAPTURED
            order.save(update_fields=["status", "payment_status", "updated_at"])

            PaymentTransaction.objects.create(
                order=order,
                payment_method="razorpay",
                amount=order.total_amount,
                currency="INR",
                status=PaymentTransaction.STATUS_CAPTURED,
                gateway_order_id=razorpay_order_id,
                gateway_payment_id=razorpay_payment_id,
                gateway_signature=razorpay_signature,
            )

            # Generate sequential invoice
            generate_invoice(order)
            return True

        except (ReservationExpiredError, InsufficientStockError):
            # Reservation expired and stock was reclaimed
            order.status = Order.STATUS_REFUND_REQUIRED
            order.payment_status = Order.PAYMENT_STATUS_CAPTURED
            order.save(update_fields=["status", "payment_status", "updated_at"])

            PaymentTransaction.objects.create(
                order=order,
                payment_method="razorpay",
                amount=order.total_amount,
                currency="INR",
                status=PaymentTransaction.STATUS_CAPTURED,
                gateway_order_id=razorpay_order_id,
                gateway_payment_id=razorpay_payment_id,
                gateway_signature=razorpay_signature,
                error_description="Reservation expired and inventory unavailable; marked refund_required.",
            )
            return False


def process_webhook_payload(
    raw_body: bytes,
    signature_header: str,
    provider: Optional[RazorpayProvider] = None,
) -> Dict[str, Any]:
    """
    Processes inbound Razorpay webhook payload with deduplication and replay protection.
    """
    if provider is None:
        provider = RazorpayProvider()

    if not provider.verify_webhook_signature(raw_body, signature_header):
        raise PermissionError("Invalid webhook signature.")

    payload = json.loads(raw_body.decode("utf-8"))
    event_id = payload.get("event_id") or payload.get("id") or str(hash(raw_body))
    event_type = payload.get("event", "unknown")

    # Idempotent deduplication check
    with transaction.atomic():
        webhook_event, created = WebhookEvent.objects.select_for_update().get_or_create(
            event_id=event_id,
            defaults={
                "event_type": event_type,
                "payload": payload,
            },
        )
        if not created and webhook_event.is_processed:
            return {"status": "already_processed", "event_id": event_id}

        # Process capture events
        if event_type in ["payment.captured", "order.paid"]:
            payment_entity = (
                payload.get("payload", {})
                .get("payment", {})
                .get("entity", {})
            )
            gateway_order_id = payment_entity.get("order_id", "")
            gateway_payment_id = payment_entity.get("id", "")
            notes = payment_entity.get("notes", {})
            order_number = notes.get("order_number")

            # Resolve Order
            order = None
            if order_number:
                order = Order.objects.filter(order_number=order_number).first()
            if not order and gateway_order_id:
                txn = PaymentTransaction.objects.filter(gateway_order_id=gateway_order_id).first()
                if txn:
                    order = txn.order

            if order:
                # Revalidate & convert stock
                try:
                    for res in order.reservations.filter(status="reserved"):
                        convert_reservation(res, order=order)

                    order.status = Order.STATUS_CONFIRMED
                    order.payment_status = Order.PAYMENT_STATUS_CAPTURED
                    order.save(update_fields=["status", "payment_status", "updated_at"])

                    PaymentTransaction.objects.create(
                        order=order,
                        payment_method="razorpay",
                        amount=order.total_amount,
                        currency="INR",
                        status=PaymentTransaction.STATUS_CAPTURED,
                        gateway_order_id=gateway_order_id,
                        gateway_payment_id=gateway_payment_id,
                        raw_response=payload,
                    )
                    generate_invoice(order)

                except (ReservationExpiredError, InsufficientStockError):
                    order.status = Order.STATUS_REFUND_REQUIRED
                    order.payment_status = Order.PAYMENT_STATUS_CAPTURED
                    order.save(update_fields=["status", "payment_status", "updated_at"])

                    PaymentTransaction.objects.create(
                        order=order,
                        payment_method="razorpay",
                        amount=order.total_amount,
                        currency="INR",
                        status=PaymentTransaction.STATUS_CAPTURED,
                        gateway_order_id=gateway_order_id,
                        gateway_payment_id=gateway_payment_id,
                        error_description="Reservation expired before webhook capture; marked refund_required.",
                        raw_response=payload,
                    )

        webhook_event.is_processed = True
        webhook_event.processed_at = timezone.now()
        webhook_event.save(update_fields=["is_processed", "processed_at"])

    return {"status": "success", "event_id": event_id}
