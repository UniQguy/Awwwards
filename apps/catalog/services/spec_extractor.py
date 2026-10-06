"""
Specification extractor service: parses structured technical specifications directly from title text.
"""

import re
from typing import Dict, List, Tuple

SPEC_PATTERNS: List[Tuple[str, str, re.Pattern]] = [
    # (Key, Display Label, Regex Pattern)
    (
        "ram",
        "RAM",
        re.compile(r"\b(\d+\s*(?:GB|MB))\s*(?:RAM|LPDDR\w*)?\b", re.IGNORECASE),
    ),
    (
        "storage",
        "Internal Storage",
        re.compile(r"\b(\d+\s*(?:GB|TB))\s*(?:ROM|Storage|SSD|HDD|NVMe|eMMC)\b", re.IGNORECASE),
    ),
    (
        "screen_size",
        "Display Size",
        re.compile(r"\b(\d+(?:\.\d+)?)\s*(?:inch|\"|\'\'|\-inch|cm)\b", re.IGNORECASE),
    ),
    (
        "battery",
        "Battery Capacity",
        re.compile(r"\b(\d{3,5}\s*mAh)\b", re.IGNORECASE),
    ),
    (
        "playtime",
        "Battery / Playtime",
        re.compile(r"\b(\d+\s*(?:h|hrs|hours))\s*(?:playtime|playback|battery\s*life)?\b", re.IGNORECASE),
    ),
    (
        "charging_wattage",
        "Power / Wattage",
        re.compile(r"\b(\d+\s*W(?:att)?)\b", re.IGNORECASE),
    ),
    (
        "resolution",
        "Resolution",
        re.compile(r"\b(4K\s*UHD|4K|Ultra\s*HD|1080p|FHD|Full\s*HD|2K|HD\s*Ready|QHD)\b", re.IGNORECASE),
    ),
    (
        "connectivity",
        "Connectivity",
        re.compile(r"\b(5G|4G\s*LTE|Bluetooth\s*\d*(?:\.\d+)?|Wi-Fi\s*\d*|Type-C|USB-C|Lightning)\b", re.IGNORECASE),
    ),
    (
        "cable_length",
        "Length",
        re.compile(r"\b(\d+(?:\.\d+)?\s*(?:m|meter|meters|ft|feet))\b", re.IGNORECASE),
    ),
    (
        "color",
        "Color",
        re.compile(
            r"\b(Black|Blue|Green|White|Red|Silver|Gold|Grey|Gray|Midnight|Starlight|Purple|Pink|Orange|Yellow|Titanium)\b",
            re.IGNORECASE,
        ),
    ),
]


def extract_specifications(title: str) -> Dict[str, str]:
    """
    Extracts key-value technical specifications from product title string.
    Returns dictionary of {spec_key: spec_value}.
    """
    if not title:
        return {}

    specs: Dict[str, str] = {}
    for spec_key, label, pattern in SPEC_PATTERNS:
        match = pattern.search(title)
        if match:
            val = match.group(1).strip()
            # If screen_size, add unit
            if spec_key == "screen_size" and not val.endswith('"') and not "inch" in val.lower():
                val = f'{val}"'
            specs[label] = val

    return specs
