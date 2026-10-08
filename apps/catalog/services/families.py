"""
Product Family Identification Service for ELECTROCART.
Disambiguates product variants (colours, RAM/storage capacities, bundled packs)
into a unified canonical family key to prevent near-duplicate editorial picks.
"""

import re
from typing import List

from apps.catalog.data.colour_map import COLOUR_MAP

EXTRA_COLORS = [
    "sporty orange", "carbon black", "metallic blue", "coral green",
    "mint green", "mint orange", "petal", "copper rose", "smoke", "black", "white",
    "blue", "red", "green", "yellow", "orange", "purple", "grey", "gray", "pink",
    "silver", "gold", "teal", "carbon", "copper", "rose", "coral", "deep sea blue"
]

ALL_COLORS: List[str] = sorted(
    set(list(COLOUR_MAP.keys()) + EXTRA_COLORS),
    key=len,
    reverse=True,
)


def family_key(raw_name: str) -> str:
    """
    Computes a normalized family identifier for a product raw marketplace title.
    Strips parenthetical variant groups, colour words, RAM/storage capacities,
    hardware SKU codes, pack counts, and trailing punctuation.
    Collapses whitespace.
    """
    if not raw_name:
        return ""

    s = raw_name.lower().strip()

    # 1. Remove parenthetical and bracketed groups
    s = re.sub(r"\(.*?\)", " ", s)
    s = re.sub(r"\[.*?\]", " ", s)

    # 2. Split on major pipe delimiter if present
    if "|" in s:
        s = s.split("|")[0].strip()

    # 3. Remove pack counts
    s = re.sub(r"\b(?:pack\s+of\s+\d+|\d+\s*pack|\d+-pack)\b", " ", s)

    # 4. Remove RAM and storage tokens
    s = re.sub(r"\b\d+\s*(?:gb|tb|mb)\s*(?:ram|rom|storage|internal\s*storage)?\b", " ", s)
    s = re.sub(r"\b(?:ram|rom|storage)\b", " ", s)

    # 5. Remove hardware sku / model codes like FB507BKBK, FB507RGPK
    s = re.sub(r"\b[a-z]{1,4}\d{2,}[a-z0-9]*\b", " ", s)

    # 6. Normalize descriptor tokens
    s = re.sub(r"\b(?:in-ear|in\s*ear)\s*(?:wired\s*)?(?:headphones|earphones)\b", "earphones", s)
    s = re.sub(r"\bwired\s*(?:in-ear|in\s*ear)?\s*(?:headphones|earphones)\b", "earphones", s)
    s = re.sub(r"\bwith\s*mic\b", " ", s)
    s = re.sub(r"\bwired\b", " ", s)

    # 7. Remove colour words
    for c in ALL_COLORS:
        s = re.sub(r"\b" + re.escape(c) + r"\b", " ", s)

    # 8. Remove slash/dash separated colors
    s = re.sub(r"[/\\-]", " ", s)

    # 9. Clean punctuation & collapse whitespace
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = " ".join(s.split())
    return s
