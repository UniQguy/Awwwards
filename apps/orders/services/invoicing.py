"""
Sequential gap-free invoicing and credit note issuance service.
Adheres to Indian GST financial year numbering regulations (April 1 - March 31).
"""

from datetime import datetime
from decimal import Decimal
from django.db import transaction
from django.utils import timezone

from apps.orders.models import CreditNote, Invoice, InvoiceCounter, Order


def get_financial_year(dt: datetime | None = None) -> str:
    """
    Returns Indian financial year string (e.g. '2026-27') for a given date.
    Financial year starts April 1st and ends March 31st.
    """
    if dt is None:
        dt = timezone.now()

    year = dt.year
    month = dt.month

    if month >= 4:
        start_year = year
        end_year = (year + 1) % 100
    else:
        start_year = year - 1
        end_year = year % 100

    return f"{start_year}-{end_year:02d}"


def get_next_sequence_number(financial_year: str, series_type: str) -> int:
    """
    Atomically retrieves and increments the sequence number for a financial year and series type.
    Must be called within transaction.atomic().
    """
    counter, _ = InvoiceCounter.objects.select_for_update().get_or_create(
        financial_year=financial_year,
        series_type=series_type,
        defaults={"last_number": 0},
    )
    counter.last_number += 1
    counter.save(update_fields=["last_number"])
    return counter.last_number


def generate_invoice(order: Order) -> Invoice:
    """
    Generates a sequential gap-free invoice for an order.
    Idempotent: returns existing invoice if already issued.
    """
    if hasattr(order, "invoice") and order.invoice:
        return order.invoice

    with transaction.atomic():
        # Check again under lock to prevent race condition
        existing = Invoice.objects.filter(order=order).first()
        if existing:
            return existing

        fy = get_financial_year(order.created_at)
        series_type = (
            InvoiceCounter.SERIES_BILL_OF_SUPPLY
            if order.is_bill_of_supply
            else InvoiceCounter.SERIES_TAX_INVOICE
        )
        seq_num = get_next_sequence_number(fy, series_type)

        prefix = "EC-BOS" if order.is_bill_of_supply else "EC-INV"
        invoice_number = f"{prefix}-{fy}-{seq_num:05d}"

        invoice = Invoice.objects.create(
            invoice_number=invoice_number,
            order=order,
            financial_year=fy,
            sequence_number=seq_num,
            is_bill_of_supply=order.is_bill_of_supply,
            invoice_date=timezone.now(),
        )
        return invoice


def generate_credit_note(order: Order, reason: str = "Order cancellation") -> CreditNote:
    """
    Issues a sequential gap-free GST Credit Note for an order and its tax invoice.
    Idempotent: returns existing credit note if already generated for this invoice.
    """
    if not hasattr(order, "invoice") or not order.invoice:
        raise ValueError(f"Cannot generate credit note for Order {order.order_number}: No invoice exists.")

    with transaction.atomic():
        invoice = order.invoice
        existing = CreditNote.objects.filter(invoice=invoice).first()
        if existing:
            return existing

        now = timezone.now()
        fy = get_financial_year(now)
        series_type = InvoiceCounter.SERIES_CREDIT_NOTE
        seq_num = get_next_sequence_number(fy, series_type)

        credit_note_number = f"EC-CN-{fy}-{seq_num:05d}"

        credit_note = CreditNote.objects.create(
            credit_note_number=credit_note_number,
            invoice=invoice,
            order=order,
            financial_year=fy,
            sequence_number=seq_num,
            amount=order.total_amount,
            tax_amount=order.tax_amount,
            reason=reason,
        )
        return credit_note
