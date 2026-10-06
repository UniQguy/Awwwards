"""
GST extraction, split, and supply resolution engine.
All financial arithmetic strictly utilizes Python Decimal with ROUND_HALF_UP.
"""

from decimal import Decimal, ROUND_HALF_UP
from django.conf import settings

from ..exceptions import MissingSellerStateError
from ..states import normalize_state_name

TWO_PLACES = Decimal("0.01")
ZERO_RUPEES = Decimal("0.00")
HUNDRED = Decimal("100")


def extract_tax(
    price_incl: Decimal, rate: Decimal, registered: bool = True
) -> Decimal:
    """
    Extract the GST component from a tax-inclusive price:
        tax = price_incl * rate / (100 + rate)
    If registered=False (Bill of Supply mode), tax is strictly 0.00.
    """
    if not registered or rate <= ZERO_RUPEES or price_incl <= ZERO_RUPEES:
        return ZERO_RUPEES

    tax = (price_incl * rate) / (HUNDRED + rate)
    return tax.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def split_tax(
    tax: Decimal, intra_state: bool
) -> tuple[Decimal, Decimal, Decimal]:
    """
    Split the extracted tax into (CGST, SGST, IGST).
    Intra-state supply:
        CGST = (tax / 2) rounded HALF_UP
        SGST = tax - CGST (guarantees CGST + SGST == tax exactly, even for odd paise)
        IGST = 0.00
    Inter-state supply:
        CGST = 0.00
        SGST = 0.00
        IGST = tax
    """
    if tax <= ZERO_RUPEES:
        return ZERO_RUPEES, ZERO_RUPEES, ZERO_RUPEES

    if intra_state:
        cgst = (tax / Decimal("2")).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        sgst = tax - cgst
        return cgst, sgst, ZERO_RUPEES
    else:
        return ZERO_RUPEES, ZERO_RUPEES, tax


def resolve_supply(
    delivery_state: str, seller_state: str | None = None
) -> tuple[bool, str, str]:
    """
    Determine if a transaction is intra-state (CGST+SGST) or inter-state (IGST).
    Raises MissingSellerStateError if seller_state is empty.
    Returns:
        tuple of (is_intra_state, normalized_delivery_state, normalized_seller_state)
    """
    if seller_state is None:
        seller_state = getattr(settings, "SELLER_STATE", "")

    if not seller_state or not str(seller_state).strip():
        raise MissingSellerStateError(
            "SELLER_STATE configuration is missing or empty. Cannot resolve tax supply."
        )

    norm_delivery = normalize_state_name(delivery_state)
    norm_seller = normalize_state_name(seller_state)

    is_intra = norm_delivery == norm_seller
    return is_intra, norm_delivery, norm_seller
