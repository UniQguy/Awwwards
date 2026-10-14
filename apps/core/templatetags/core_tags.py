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


@register.filter(name="balance_amp")
def balance_amp(value: Any) -> str:
    """
    Ensures that ampersands in titles never leave an orphaned '&' on a line alone.
    Replaces ' & ' with ' &amp;&nbsp;' so the ampersand stays glued to the following word.
    """
    if not value:
        return ""
    import re
    from django.utils.safestring import mark_safe
    s = str(value)
    s = re.sub(r"\s+&\s+", " &amp;&nbsp;", s)
    s = re.sub(r"\s+&amp;\s+", " &amp;&nbsp;", s)
    return mark_safe(s)


@register.filter(name="strip_brand")
def strip_brand(title: Any, brand: Any) -> str:
    """
    Strips brand name from the beginning of the product title if it repeats the brand
    already shown above the card title.
    Preserves model identifiers when the stripped portion begins with numbers or short model names (e.g., 'Redmi 9', 'Echo Dot', 'JBL Go 3').
    """
    if not title:
        return ""
    import re
    t = str(title).strip()
    if not brand:
        return t
    b = str(brand).strip()
    if not b or b.lower() in ("unknown", "generic"):
        return t
    pattern = rf"^{re.escape(b)}\s*[-:|,]?\s*"
    match = re.match(pattern, t, flags=re.IGNORECASE)
    if not match:
        return t
    remainder = t[match.end():].strip()
    if not remainder:
        return t
    # If remainder starts with a digit or short model keyword, do NOT strip brand
    if re.match(r"^(?:\d|[A-Za-z]?\d|Go\b|Dot\b|Mini\b|Air\b|Pro\b|Plus\b|Max\b|SE\b|Lite\b|Wave\b|Airdopes\b|BassHeads\b|Ninja\b|ColorFit\b|XPS\b)", remainder, re.IGNORECASE):
        return t
    return remainder


@register.simple_tag
def static_file_exists(path: Any) -> bool:
    """Check if static file exists on filesystem."""
    if not path:
        return False
    from pathlib import Path
    from django.conf import settings
    clean_path = str(path).lstrip("/")
    if clean_path.startswith("static/"):
        clean_path = clean_path[7:]
    direct_path = Path(settings.BASE_DIR) / "static" / clean_path
    if direct_path.is_file():
        return True
    from django.contrib.staticfiles import finders
    return bool(finders.find(clean_path))


@register.filter(name="star_glyphs")
def star_glyphs(rating: Any) -> str:
    """
    Render honest star glyphs (1-5) for a numeric rating:
    e.g. 4.2 -> '★★★★☆'
    """
    if rating is None or rating == "":
        return ""
    try:
        r = float(rating)
        full = min(5, max(0, int(round(r))))
        empty = 5 - full
        return ("★" * full) + ("☆" * empty)
    except Exception:
        return ""



