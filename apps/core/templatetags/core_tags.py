"""
Template tags and filters for ELECTROCART presentation layer.
Provides locale-independent Indian Rupee currency formatting and discount helpers.
"""

from decimal import Decimal
from typing import Any
from django import template

register = template.Library()


def _format_inr_digits(int_str: str) -> str:
    """Format an integer string using Indian grouping system (2,2,3)."""
    if len(int_str) <= 3:
        return int_str
    last_three = int_str[-3:]
    remaining = int_str[:-3]
    parts = []
    while remaining:
        parts.append(remaining[-2:])
        remaining = remaining[:-2]
    parts.reverse()
    return f"{','.join(parts)},{last_three}"


@register.filter(name="inr")
def inr(value: Any) -> str:
    """
    Format numeric values into the Indian Rupee presentation format:
    10 -> ₹10
    1299 -> ₹1,299
    100000 -> ₹1,00,000
    134999 -> ₹1,34,999
    None -> ''
    """
    if value is None or value == "":
        return ""

    try:
        # Convert to Decimal for exact precision
        d = Decimal(str(value))
    except Exception:
        return str(value)

    # Determine if value is a whole integer
    is_negative = d < 0
    d = abs(d)

    int_part = int(d)
    dec_part = d - int_part

    int_formatted = _format_inr_digits(str(int_part))
    sign = "-" if is_negative else ""

    if dec_part == Decimal("0"):
        return f"{sign}₹{int_formatted}"
    else:
        dec_formatted = f"{dec_part:.2f}"[2:]
        return f"{sign}₹{int_formatted}.{dec_formatted}"


@register.filter(name="discount_percent")
def discount_percent(mrp: Any, selling_price: Any) -> int:
    """
    Calculate integer discount percentage when MRP is greater than selling price.
    Returns 0 if no savings exist.
    """
    if mrp is None or selling_price is None:
        return 0
    try:
        m = Decimal(str(mrp))
        s = Decimal(str(selling_price))
        if m > s > 0:
            pct = ((m - s) / m) * Decimal("100")
            return int(round(pct))
    except Exception:
        pass
    return 0


@register.filter(name="savings")
def savings(mrp: Any, selling_price: Any) -> str:
    """
    Return formatted savings string (₹...) only when MRP is strictly greater than selling price.
    Returns empty string otherwise.
    """
    if mrp is None or selling_price is None:
        return ""
    try:
        m = Decimal(str(mrp))
        s = Decimal(str(selling_price))
        if m > s:
            return inr(m - s)
    except Exception:
        pass
    return ""


@register.filter(name="subtract")
def subtract(value: Any, arg: Any) -> Any:
    """Subtract arg from value, returning Decimal or 0."""
    try:
        return Decimal(str(value)) - Decimal(str(arg))
    except Exception:
        return 0


@register.filter(name="colour_hex")
def colour_hex(name: Any) -> str:
    """
    Return mapped hex colour for an electronics finish or empty string.
    """
    if not name:
        return ""
    from apps.catalog.data.colour_map import get_colour_hex
    return get_colour_hex(str(name)) or ""

