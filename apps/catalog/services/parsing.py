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


TRAILING_CONNECTORS = {
    "with", "and", "&", "for", "of", "to", "in", "the", "a", "an", "by", "plus", "added"
}
MARKETING_CLAUSES = re.compile(
    r"\b(?:compatible\s+with|compatible\s+for|designed\s+for|ideal\s+for|suitable\s+for|featuring|packed\s+with)\b.*$",
    re.IGNORECASE,
)


def clean_display_name(raw_name: str, brand: Optional[str] = None) -> str:
    """
    Cleans lengthy marketplace keyword-stuffed titles into a refined, readable display title.
    Preserves model identifiers while removing marketing noise.
    Ensures length <= 90 chars, no trailing connectors, balanced parentheses and quotes.
    """
    if not raw_name:
        return "Untitled Product"

    # Remove replacement/unprintable characters and leading symbols
    title = raw_name.replace("\ufffd", "").strip()
    title = re.sub(r"^[\s®™©•\-\"\'`\(\)\[\]]+", "", title).strip()

    # 1. Split on natural segment boundaries: |, ;, •, em dash, en dash, hyphen with spaces
    for delim in [" | ", " ; ", " • ", " — ", " – ", " - ", "|", ";", "•", "—", "–"]:
        if delim in title:
            parts = title.split(delim)
            first = parts[0].strip()
            # If first part is meaningful (at least 15 chars), take it
            if len(first) >= 15:
                title = first
                break

    # 2. Clean out common noise tokens
    noise_patterns = [
        r"\(Renewed\)",
        r"\(Refurbished\)",
        r"\(Used\)",
        r"with Warranty.*$",
        r"Upto \d+.*$",
        r"Limited Time Deal.*$",
        r"Made in India",
        r"Best Seller",
    ]
    for pat in noise_patterns:
        title = re.sub(pat, "", title, flags=re.IGNORECASE).strip()

    # 3. Strip trailing marketing clauses
    title = MARKETING_CLAUSES.sub("", title).strip()

    # 4. Cap length <= 90 at a word boundary
    if len(title) > 90:
        truncated = title[:90]
        last_space = truncated.rfind(" ")
        if last_space > 25:
            title = truncated[:last_space].strip()
        else:
            title = truncated.strip()

    # 5. Iteratively strip trailing connectors and punctuation
    changed = True
    while changed:
        changed = False
        new_title = re.sub(r"[\s,.:;/\-&•—–]+$", "", title).strip()
        if new_title != title:
            title = new_title
            changed = True
        words = title.split()
        if words and words[-1].lower() in TRAILING_CONNECTORS:
            title = " ".join(words[:-1]).strip()
            changed = True

    # 6. Balance parentheses and quotes
    while title.count("(") > title.count(")"):
        if len(title) < 90:
            title = title + ")"
        else:
            idx = title.rfind("(")
            if idx != -1:
                title = (title[:idx] + title[idx + 1 :]).strip()
            else:
                break

    while title.count(")") > title.count("("):
        idx = title.rfind(")")
        if idx != -1:
            title = (title[:idx] + title[idx + 1 :]).strip()
        else:
            break

    for q in ['"', "'", "`"]:
        while title.count(q) % 2 != 0:
            if title.endswith(q):
                title = title[:-1].strip()
            else:
                idx = title.rfind(q)
                if idx != -1:
                    title = (title[:idx] + title[idx + 1 :]).strip()
                else:
                    break

    # Final cleanup of trailing punctuation and trailing connectors
    changed = True
    while changed:
        changed = False
        new_title = re.sub(r"[\s,.:;/\-&•—–]+$", "", title).strip()
        if new_title != title:
            title = new_title
            changed = True
        words = title.split()
        if words and words[-1].lower() in TRAILING_CONNECTORS:
            title = " ".join(words[:-1]).strip()
            changed = True

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
