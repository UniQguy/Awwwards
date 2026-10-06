"""
Data parsing utilities for catalog importing and curation.
"""

from decimal import Decimal, InvalidOperation
import re
from typing import Optional
from django.utils.text import slugify


ASIN_URL_REGEX = re.compile(r"/(?:dp|gp/product|d)/([A-Z0-9]{10})", re.IGNORECASE)
ASIN_STANDALONE_REGEX = re.compile(r"\b(B0[A-Z0-9]{8}|[0-9]{9}[0-9X])\b", re.IGNORECASE)


def parse_price(val: Optional[str]) -> Optional[Decimal]:
    """
    Parses currency strings like '₹10,999', 'Rs. 1,499.50', 'Rs. 499', '10999' into Decimal.
    Returns None if missing, negative, or unparseable.
    """
    if not val:
        return None
    s = str(val).strip()
    if "-" in s:
        return None
    # Remove currency prefixes like 'Rs.', 'Rs', 'INR', '₹'
    s = re.sub(r"(?i)\b(?:rs\.?|inr)\b|₹", "", s).strip()
    s = s.replace(",", "")
    match = re.search(r"(\d+(?:\.\d+)?)", s)
    if not match:
        return None
    try:
        dec = Decimal(match.group(1)).quantize(Decimal("0.01"))
        return dec if dec >= Decimal("0.00") else None
    except (InvalidOperation, ValueError):
        return None


def parse_rating(val: Optional[str]) -> Optional[Decimal]:
    """
    Parses ratings like '4.3', '4.0 out of 5 stars', '3,9' into Decimal (0.00 to 5.00).
    """
    if not val:
        return None
    match = re.search(r"(\d+(?:[.,]\d+)?)", str(val).strip())
    if not match:
        return None
    try:
        raw_num = match.group(1).replace(",", ".")
        rating = Decimal(raw_num).quantize(Decimal("0.01"))
        if Decimal("0.00") <= rating <= Decimal("5.00"):
            return rating
        return None
    except (InvalidOperation, ValueError):
        return None


def parse_count(val: Optional[str]) -> Optional[int]:
    """
    Parses count strings like '113,956', '965', '1.5k' into int.
    """
    if not val:
        return None
    s = str(val).strip().lower().replace(",", "")
    if s.endswith("k"):
        try:
            return int(float(s[:-1]) * 1000)
        except ValueError:
            return None
    elif s.endswith("m"):
        try:
            return int(float(s[:-1]) * 1000000)
        except ValueError:
            return None
    cleaned = re.sub(r"[^\d]", "", s)
    if not cleaned:
        return None
    try:
        return int(cleaned)
    except ValueError:
        return None


def extract_asin(url_or_text: Optional[str]) -> Optional[str]:
    """
    Extracts 10-character Amazon ASIN from product URL or text.
    """
    if not url_or_text:
        return None
    text = str(url_or_text).strip()
    match_url = ASIN_URL_REGEX.search(text)
    if match_url:
        return match_url.group(1).upper()
    match_standalone = ASIN_STANDALONE_REGEX.search(text)
    if match_standalone:
        return match_standalone.group(1).upper()
    return None


def clean_display_name(raw_name: str, brand: Optional[str] = None) -> str:
    """
    Cleans lengthy marketplace keyword-stuffed titles into a refined, readable display title.
    Preserves model identifiers while removing marketing noise.
    """
    if not raw_name:
        return "Untitled Product"

    title = raw_name.strip()
    
    # Split on prominent delimiters (e.g., '|', ' - ', ';', '•')
    for delimiter in [" | ", " ; ", " • ", " — "]:
        if delimiter in title:
            title = title.split(delimiter)[0].strip()

    # Clean out common noise tokens
    noise_patterns = [
        r"\(Renewed\)",
        r"\(Refurbished\)",
        r"\(Used\)",
        r"with Warranty.*$",
        r"Upto \d+.*$",
        r"Limited Time Deal.*$",
    ]
    for pat in noise_patterns:
        title = re.sub(pat, "", title, flags=re.IGNORECASE).strip()

    # Ensure brand isn't duplicated if it's already at the start
    if brand and brand.lower() != "unknown" and not title.lower().startswith(brand.lower()):
        # Title doesn't have brand at start; let's leave it as is if it's clear
        pass

    # Cap length elegantly at word boundary if still too long (> 90 chars)
    if len(title) > 90:
        truncated = title[:90]
        last_space = truncated.rfind(" ")
        if last_space > 40:
            title = truncated[:last_space].strip()
        else:
            title = truncated.strip()

    # Clean dangling punctuation
    title = re.sub(r"[\s,.-]+$", "", title).strip()
    return title or raw_name[:90].strip()


def build_unique_slug(base_text: str, asin: str) -> str:
    """
    Builds a reliable, slug for a product using base text and asin.
    """
    clean_slug = slugify(base_text)[:200].rstrip("-")
    if not clean_slug:
        clean_slug = "product"
    if asin:
        return f"{clean_slug}-{asin.lower()}"
    return clean_slug
