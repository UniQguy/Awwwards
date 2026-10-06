"""
Indian numbering currency to words converter.
Formats Indian Rupee figures into formal words (Crores, Lakhs, Thousands, Hundreds, Paise).
Used for statutory GST Tax Invoices and Bills of Supply under Indian commercial regulations.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Union

ONES = [
    "", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
    "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
    "Seventeen", "Eighteen", "Nineteen",
]

TENS = [
    "", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety",
]


def _two_digits_to_words(n: int) -> str:
    """Convert integer 0-99 to English words."""
    if n == 0:
        return ""
    if n < 20:
        return ONES[n]
    tens_digit = n // 10
    ones_digit = n % 10
    if ones_digit:
        return f"{TENS[tens_digit]} {ONES[ones_digit]}"
    return TENS[tens_digit]


def _three_digits_to_words(n: int) -> str:
    """Convert integer 0-999 to English words."""
    hundreds = n // 100
    rem = n % 100
    words = []
    if hundreds:
        words.append(f"{ONES[hundreds]} Hundred")
    if rem:
        words.append(_two_digits_to_words(rem))
    return " ".join(words)


def number_to_words_inr(amount: Union[Decimal, float, int, str]) -> str:
    """
    Converts a Decimal Rupee amount into formal Indian English words.
    Examples:
        Decimal('0.00') -> 'Rupees Zero Only'
        Decimal('499.00') -> 'Rupees Four Hundred Ninety Nine Only'
        Decimal('1299.50') -> 'Rupees One Thousand Two Hundred Ninety Nine and Fifty Paise Only'
        Decimal('134999.00') -> 'Rupees One Lakh Thirty Four Thousand Nine Hundred Ninety Nine Only'
        Decimal('25000000.00') -> 'Rupees Two Crore Fifty Lakh Only'
    """
    if amount is None or amount == "":
        return ""

    d = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    is_negative = d < 0
    d = abs(d)

    rupees = int(d)
    paise = int((d - rupees) * 100)

    if rupees == 0 and paise == 0:
        return "Rupees Zero Only"

    parts = []

    # Indian grouping: Crores (10^7), Lakhs (10^5), Thousands (10^3), Hundreds
    crores = rupees // 10000000
    rupees %= 10000000

    lakhs = rupees // 100000
    rupees %= 100000

    thousands = rupees // 1000
    rupees %= 1000

    hundreds = rupees

    if crores:
        parts.append(f"{_three_digits_to_words(crores)} Crore")
    if lakhs:
        parts.append(f"{_two_digits_to_words(lakhs)} Lakh")
    if thousands:
        parts.append(f"{_two_digits_to_words(thousands)} Thousand")
    if hundreds:
        parts.append(_three_digits_to_words(hundreds))

    rupees_str = " ".join(parts).strip()
    prefix = "Minus " if is_negative else ""

    if rupees_str and paise:
        paise_str = _two_digits_to_words(paise)
        return f"{prefix}Rupees {rupees_str} and {paise_str} Paise Only"
    elif rupees_str:
        return f"{prefix}Rupees {rupees_str} Only"
    elif paise:
        paise_str = _two_digits_to_words(paise)
        return f"{prefix}{paise_str} Paise Only"

    return "Rupees Zero Only"
