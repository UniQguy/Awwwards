"""
Specification extractor service for ELECTROCART.
Parses structured technical specifications directly from title text with
evidence-based validation and category-specific range sanity guards.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Category-specific sanity ranges (min, max)
SANITY_RANGES = {
    "tvs": {
        "screen_size": (15.0, 120.0),
    },
    "smartphones": {
        "screen_size": (3.0, 8.0),
        "ram": (1.0, 24.0),
        "storage": (8.0, 2048.0),
        "battery": (500.0, 20000.0),
    },
    "smartwatches-bands": {
        "screen_size": (0.9, 2.5),
    },
}

# Standard ordered spec keys for display captions per category
CATEGORY_CAPTION_SPEC_ORDER = {
    "tvs": ["screen_size", "resolution", "connectivity"],
    "smartphones": ["ram", "storage", "battery", "screen_size"],
    "smartwatches-bands": ["screen_size", "playtime", "connectivity"],
    "earphones-headphones": ["playtime", "connectivity", "charging_wattage"],
    "speakers": ["charging_wattage", "connectivity", "playtime"],
    "cables-chargers-powerbanks": ["charging_wattage", "cable_length", "connectivity", "battery"],
    "keyboards-mice": ["connectivity"],
    "cameras": ["resolution", "connectivity"],
}


def parse_screen_size(title: str, category_slug: Optional[str] = None) -> Optional[Tuple[str, str, str]]:
    """
    Parses screen/display size:
    1. Prefers explicit inch value ('NN inches', 'NN inch', 'NN"').
    2. Falls back to 'NN cm' only when no inch value exists, converting to inches (cm / 2.54).
    Never emits a centimetre value directly as inches.
    Returns tuple: (machine_key, display_label, formatted_value) or None if absent/implausible.
    """
    # 1. Inch pattern: matches '50 inches', '43 inch', '43-inch', '43"', '1.69"'
    inch_match = re.search(r"(?:\b(\d+(?:\.\d+)?)\s*(?:inch|inches|\-inch)\b|(\d+(?:\.\d+)?)\s*[\"\'\u201d\u201c])", title, re.IGNORECASE)
    val_inches: Optional[float] = None
    raw_inch_str: Optional[str] = None
    source_note = ""

    if inch_match:
        raw_inch_str = inch_match.group(1) or inch_match.group(2)
        try:
            val_inches = float(raw_inch_str)
        except ValueError:
            val_inches = None

    # 2. Fallback to cm conversion if no inch value found
    if val_inches is None:
        cm_match = re.search(r"\b(\d+(?:\.\d+)?)\s*cm\b", title, re.IGNORECASE)
        if cm_match:
            try:
                cm_val = float(cm_match.group(1))
                val_inches = round(cm_val / 2.54, 1)
                source_note = f"converted from {cm_val} cm"
            except ValueError:
                val_inches = None

    if val_inches is None:
        return None

    # Range sanity check
    if category_slug and category_slug in SANITY_RANGES:
        min_val, max_val = SANITY_RANGES[category_slug].get("screen_size", (0.0, 1000.0))
        if not (min_val <= val_inches <= max_val):
            logger.info(
                "Dropped implausible screen_size %.1f for category %s: out of range [%.1f, %.1f]",
                val_inches,
                category_slug,
                min_val,
                max_val,
            )
            return None

    # Format cleanly (e.g. 50" instead of 50.0", but 1.69" or 42.5")
    if raw_inch_str:
        formatted = f"{raw_inch_str}\""
    else:
        formatted = f"{val_inches:g}\""
    if category_slug:
        label = "Display Size" if category_slug in ("smartwatches-bands", "smartphones") else "Screen Size"
    else:
        label = "Display Size" if (val_inches <= 12.0 or "display" in title.lower()) else "Screen Size"
    return ("screen_size", label, formatted)


def parse_ram_and_storage(title: str, category_slug: Optional[str] = None) -> List[Tuple[str, str, str]]:
    """
    Parses and disambiguates RAM and Internal Storage.
    Handles '2GB RAM, 32GB Storage', '6GB + 128GB', '6GB/128GB', '8GB RAM', '256GB Storage'.
    """
    results: List[Tuple[str, str, str]] = []
    ram_gb: Optional[float] = None
    storage_gb: Optional[float] = None

    # Pattern A: Combined '6GB + 128GB' or '6GB / 128GB' or '6GB, 128GB'
    combo_match = re.search(r"\b(\d+)\s*GB\s*[\+,/]\s*(\d+)\s*(?:GB|TB)\b", title, re.IGNORECASE)
    if combo_match:
        try:
            r_val = float(combo_match.group(1))
            s_val = float(combo_match.group(2))
            if "TB" in combo_match.group(0).upper():
                s_val *= 1024
            if r_val <= 24.0:
                ram_gb = r_val
                storage_gb = s_val
        except ValueError:
            pass

    # Pattern B: Explicit 'X GB RAM'
    if ram_gb is None:
        ram_match = re.search(r"\b(\d+)\s*GB\s*(?:RAM|LPDDR\w*)\b", title, re.IGNORECASE)
        if ram_match:
            try:
                ram_gb = float(ram_match.group(1))
            except ValueError:
                pass

    # Pattern C: Explicit 'X GB Storage' or 'X TB Storage' or 'X GB ROM'
    if storage_gb is None:
        storage_match = re.search(r"\b(\d+)\s*(GB|TB)\s*(?:Storage|ROM|SSD|Internal\s+Storage)\b", title, re.IGNORECASE)
        if storage_match:
            try:
                s_num = float(storage_match.group(1))
                unit = storage_match.group(2).upper()
                storage_gb = s_num * 1024 if unit == "TB" else s_num
            except ValueError:
                pass

    # Sanity checks for RAM
    if ram_gb is not None:
        min_ram, max_ram = SANITY_RANGES.get(category_slug, {}).get("ram", (1.0, 24.0)) if category_slug else (1.0, 64.0)
        if min_ram <= ram_gb <= max_ram:
            results.append(("ram", "RAM", f"{int(ram_gb)} GB" if ram_gb.is_integer() else f"{ram_gb} GB"))
        else:
            logger.info("Dropped implausible RAM %.1f GB: out of range", ram_gb)

    # Sanity checks for Storage
    if storage_gb is not None:
        min_stor, max_stor = SANITY_RANGES.get(category_slug, {}).get("storage", (8.0, 2048.0)) if category_slug else (8.0, 8192.0)
        if min_stor <= storage_gb <= max_stor:
            if storage_gb >= 1024 and (storage_gb % 1024 == 0):
                formatted = f"{int(storage_gb // 1024)} TB"
            else:
                formatted = f"{int(storage_gb)} GB" if storage_gb.is_integer() else f"{storage_gb} GB"
            results.append(("storage", "Internal Storage", formatted))
        else:
            logger.info("Dropped implausible Storage %.1f GB: out of range", storage_gb)

    return results


def parse_battery(title: str, category_slug: Optional[str] = None) -> Optional[Tuple[str, str, str]]:
    bat_match = re.search(r"\b(\d{3,5})\s*mAh\b", title, re.IGNORECASE)
    if bat_match:
        try:
            val = float(bat_match.group(1))
            if category_slug == "smartphones":
                min_b, max_b = SANITY_RANGES["smartphones"]["battery"]
                if not (min_b <= val <= max_b):
                    return None
            return ("battery", "Battery Capacity", f"{int(val)} mAh")
        except ValueError:
            pass
    return None


def parse_resolution(title: str) -> Optional[Tuple[str, str, str]]:
    res_match = re.search(r"\b(4K\s*UHD|4K\s*Ultra\s*HD|4K|Ultra\s*HD|1080p|Full\s*HD|FHD|2K|HD\s*Ready|QHD)\b", title, re.IGNORECASE)
    if res_match:
        raw = res_match.group(1).strip()
        norm = "4K Ultra HD" if "4K" in raw.upper() else raw
        return ("resolution", "Resolution", norm)
    return None


def parse_connectivity(title: str) -> Optional[Tuple[str, str, str]]:
    conn_match = re.search(r"\b(5G|4G\s*LTE|Bluetooth\s*\d*(?:\.\d+)?|Wi-Fi|Type-C|USB-C|Lightning)\b", title, re.IGNORECASE)
    if conn_match:
        return ("connectivity", "Connectivity", conn_match.group(1).strip())
    return None


def parse_charging_wattage(title: str) -> Optional[Tuple[str, str, str]]:
    w_match = re.search(r"\b(\d+)\s*W(?:att)?\b", title, re.IGNORECASE)
    if w_match:
        return ("charging_wattage", "Power / Wattage", f"{w_match.group(1)}W")
    return None


def parse_playtime(title: str) -> Optional[Tuple[str, str, str]]:
    p_match = re.search(r"\b(\d+)\s*(?:h|hrs|hours)\s*(?:playtime|playback|battery\s*life)?\b", title, re.IGNORECASE)
    if p_match:
        return ("playtime", "Playtime", f"{p_match.group(1)} Hours")
    return None


def parse_cable_length(title: str) -> Optional[Tuple[str, str, str]]:
    len_match = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:m|meter|meters|ft|feet)\b", title, re.IGNORECASE)
    if len_match:
        return ("cable_length", "Length", len_match.group(0).strip())
    return None


class SpecValue(str):
    def __new__(cls, value: str, label: str = ""):
        inst = super().__new__(cls, str(value))
        inst.label = label
        return inst

    @property
    def value(self) -> str:
        return str(self)

    def __getitem__(self, key):
        if key == "value":
            return str(self)
        if key == "label":
            return self.label
        return super().__getitem__(key)

    def get(self, key, default=None):
        if key == "value":
            return str(self)
        if key == "label":
            return self.label
        return default


class SpecDict(dict):
    """
    Dictionary supporting both machine-key access (e.g. specs['screen_size']['value'])
    and human-label lookup (e.g. specs.get('Display Size')).
    """
    def __getitem__(self, key):
        if super().__contains__(key):
            return super().__getitem__(key)
        for v in self.values():
            if getattr(v, "label", None) == key:
                return v
        raise KeyError(key)

    def get(self, key, default=None):
        if super().__contains__(key):
            return super().get(key)
        for v in self.values():
            if getattr(v, "label", None) == key:
                return v
        return default

    def __contains__(self, key):
        if super().__contains__(key):
            return True
        return any(getattr(v, "label", None) == key for v in self.values())


def extract_specifications(title: str, category_slug: Optional[str] = None) -> SpecDict:
    """
    Extracts key-value technical specifications from product title string with category sanity validation.
    Returns SpecDict mapping machine keys to SpecValue (which supports both dict-like and string-like lookups).
    """
    if not title:
        return SpecDict()

    specs = SpecDict()

    # Screen / Display size
    size_spec = parse_screen_size(title, category_slug=category_slug)
    if size_spec:
        specs[size_spec[0]] = SpecValue(size_spec[2], label=size_spec[1])

    # RAM and Storage
    for key, label, val in parse_ram_and_storage(title, category_slug=category_slug):
        clean_val = val.replace(" ", "") if ("GB" in val or "TB" in val) else val
        specs[key] = SpecValue(clean_val, label=label)

    # Battery
    bat = parse_battery(title, category_slug=category_slug)
    if bat:
        specs[bat[0]] = SpecValue(bat[2].replace(" ", ""), label=bat[1])

    # Resolution
    res = parse_resolution(title)
    if res:
        specs[res[0]] = SpecValue(res[2], label=res[1])

    # Connectivity
    conn = parse_connectivity(title)
    if conn:
        specs[conn[0]] = SpecValue(conn[2], label=conn[1])

    # Wattage
    w = parse_charging_wattage(title)
    if w:
        specs[w[0]] = SpecValue(w[2].replace(" ", ""), label=w[1])

    # Playtime
    p = parse_playtime(title)
    if p:
        specs[p[0]] = SpecValue(p[2], label=p[1])

    # Cable length
    c_len = parse_cable_length(title)
    if c_len:
        specs[c_len[0]] = SpecValue(c_len[2], label=c_len[1])

    # Color
    color_match = re.search(
        r"\b(Black|Blue|Green|White|Red|Silver|Gold|Grey|Gray|Midnight|Starlight|Purple|Pink|Orange|Yellow|Titanium)\b",
        title,
        re.IGNORECASE,
    )
    if color_match:
        specs["color"] = SpecValue(color_match.group(1).capitalize(), label="Color")

    return specs

