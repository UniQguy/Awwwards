"""
Brand detection and allowlist resolution service.
"""

from pathlib import Path
import re
from typing import List, Optional

ALLOWLIST_PATH = Path(__file__).resolve().parent.parent / "data" / "brand_allowlist.txt"

_CACHE_BRANDS: Optional[List[str]] = None


def get_known_brands() -> List[str]:
    """
    Returns the ordered list of known brand names.
    Longer brand names are checked first to handle multi-word brands (e.g. 'Fire-Boltt', 'Western Digital').
    """
    global _CACHE_BRANDS
    if _CACHE_BRANDS is not None:
        return _CACHE_BRANDS

    brands: List[str] = []
    if ALLOWLIST_PATH.exists():
        with open(ALLOWLIST_PATH, "r", encoding="utf-8") as f:
            for line in f:
                b = line.strip()
                if b and not b.startswith("#"):
                    brands.append(b)

    # Fallback if file missing or empty
    if not brands:
        brands = [
            "Apple", "Samsung", "OnePlus", "Xiaomi", "Redmi", "Realme", "boAt",
            "Noise", "Fire-Boltt", "JBL", "Sony", "Dell", "HP", "Lenovo",
            "Logitech", "Portronics", "Zebronics", "Ambrane", "Boult", "Philips",
            "SanDisk", "Seagate", "TP-Link", "Acer", "Asus", "Bose", "Sennheiser",
            "Canon", "Nikon", "Panasonic", "LG", "Motorola", "Google", "Nothing",
            "Oppo", "Vivo", "Poco", "Anker", "Belkin", "Spigen", "Keychron"
        ]

    # Sort descending by length so compound names like 'Western Digital' match before 'Western'
    brands.sort(key=lambda x: len(x), reverse=True)
    _CACHE_BRANDS = brands
    return _CACHE_BRANDS


def detect_brand(title: str) -> str:
    """
    Detects brand from product title using allowlist prefix and word-boundary matching.
    Returns canonical brand casing, or first word, or 'Unknown'.
    """
    if not title:
        return "Unknown"

    # Strip leading symbols (registered marks, trademarks, bullets, quotes, dashes)
    cleaned_title = re.sub(r"^[\s®™©•\-\"\'`\(\)\[\]]+", "", str(title)).strip()
    if not cleaned_title:
        return "Unknown"

    brands = get_known_brands()

    # 1. Check if title starts with brand name (case-insensitive)
    for b in brands:
        pattern = rf"^{re.escape(b)}\b"
        if re.search(pattern, cleaned_title, re.IGNORECASE):
            return b

    # 2. Check if brand occurs anywhere in the title with word boundary
    for b in brands:
        pattern = rf"\b{re.escape(b)}\b"
        if re.search(pattern, cleaned_title, re.IGNORECASE):
            return b

    # 3. Fallback: extract first word if valid token
    first_word_match = re.match(r"^([A-Za-z0-9\-]+)", cleaned_title)
    if first_word_match:
        candidate = first_word_match.group(1)
        if len(candidate) > 1 and candidate.lower() not in ["the", "new", "all", "pro", "best"]:
            # If acronym (all caps 2-3 letters like HP, LG), keep uppercase
            if candidate.isupper() and len(candidate) <= 3:
                return candidate
            return candidate.capitalize()

    return "Unknown"
