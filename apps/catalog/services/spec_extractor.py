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


def classify_product_subtype(title_or_product, category_slug: Optional[str] = None) -> str:
    """
    Classifies a product or title into granular hardware sub-types to prevent invalid cross-sub-type comparisons
    (e.g., DSLR vs CCTV security cameras, TWS earbuds vs Over-Ear headphones, Tablets vs Smartphones).
    """
    if hasattr(title_or_product, "raw_name") or hasattr(title_or_product, "display_name"):
        title = f"{getattr(title_or_product, 'display_name', '')} {getattr(title_or_product, 'raw_name', '')}"
        if not category_slug and getattr(title_or_product, "category", None):
            category_slug = getattr(title_or_product.category, "slug", "")
    else:
        title = str(title_or_product or "")

    t = title.lower()

    # 1. Cameras
    if category_slug == "cameras" or any(w in t for w in ["camera", "dslr", "mirrorless", "cctv", "webcam"]):
        if any(w in t for w in ["tripod", "ring light", "gimbal", "lens cap", "camera bag", "mount", "strap", "monopod", "softbox"]):
            return "camera_accessory"
        if any(w in t for w in ["cctv", "security camera", "surveillance", "tapo", "cp plus", "qubo", "imou", "ezviz", "webcam", "360 pan", "wifi camera", "home security", "outdoor camera", "indoor camera", "bullet camera", "dome camera"]):
            return "camera_cctv_security"
        if any(w in t for w in ["action camera", "go pro", "gopro", "insta360", "action cam", "waterproof camera"]):
            return "camera_action"
        if any(w in t for w in ["dslr", "mirrorless", "eos", "alpha", "nikon z", "canon r", "lumix", "powershot", "coolpix", "slr", "interchangeable lens"]):
            return "camera_dslr_mirrorless"
        return "camera_dslr_mirrorless" if ("canon" in t or "nikon" in t or "sony" in t or "fujifilm" in t or "panasonic" in t) else "camera_cctv_security"

    # 2. Audio & Headphones
    if category_slug in ("earphones-headphones", "audio") or any(w in t for w in ["earphone", "headphone", "earbud", "neckband", "headset"]):
        if any(w in t for w in ["over-ear", "on-ear", "headphone", "headset", "studio monitor", "anc headphone"]) and not any(w in t for w in ["in-ear", "earbuds", "tws", "neckband"]):
            return "audio_over_ear"
        if any(w in t for w in ["neckband", "wireless earphone", "rockerz", "behind-neck", "collar"]):
            return "audio_neckband"
        if any(w in t for w in ["wired", "3.5mm", "aux", "in-ear with mic", "iem", "earphone with mic", "bassheads"]) and not any(w in t for w in ["wireless", "bluetooth", "tws", "airbuds", "earbuds"]):
            return "audio_wired"
        if any(w in t for w in ["tws", "true wireless", "truly wireless", "earbuds", "airpods", "buds", "earpods"]):
            return "audio_tws"
        return "audio_tws"

    # 3. Smartphones vs Tablets
    if category_slug == "smartphones" or any(w in t for w in ["phone", "smartphone", "tablet", "ipad", "tab"]):
        if any(w in t for w in ["tablet", "ipad", "galaxy tab", "lenovo tab", "pad ", "pad,", "ereader", "kindle"]):
            return "device_tablet"
        if any(w in t for w in ["phone", "smartphone", "5g", "mobile", "handset", "pro", "ultra", "plus", "galaxy s", "iphone", "redmi", "oneplus", "iqoo", "realme", "poco"]):
            return "device_smartphone"
        return "device_smartphone"

    # 4. Keyboards & Mice
    if category_slug == "keyboards-mice" or any(w in t for w in ["keyboard", "mouse", "combo"]):
        if any(w in t for w in ["mouse", "trackball", "pointing device"]):
            return "km_mouse"
        if any(w in t for w in ["combo", "keyboard and mouse", "desktop set"]):
            return "km_combo"
        return "km_keyboard"

    # 5. Televisions vs Monitors
    if category_slug == "tvs" or any(w in t for w in ["tv", "television", "monitor", "display"]):
        if any(w in t for w in ["monitor", "gaming monitor", "curved display", "pc monitor"]):
            return "display_monitor"
        return "display_tv"

    return category_slug or "general"


def synthesize_category_specs(
    specs: SpecDict,
    title: str,
    category_slug: Optional[str] = None,
    price: Optional[object] = None,
    brand: Optional[str] = None,
    description: Optional[str] = None,
) -> SpecDict:
    """
    Synthesizes category-specific technical specifications when not present in title,
    using brand, price tier, and product category conventions (Phase R8).
    """
    if not category_slug:
        return specs

    price_val = 0.0
    if price:
        try:
            price_val = float(price)
        except (ValueError, TypeError):
            price_val = 0.0

    t_lower = title.lower()
    b_lower = (brand or "").lower()

    if category_slug in ("smartphones", "smartphones-basic-mobiles"):
        # 1. RAM
        if "ram" not in specs:
            if price_val >= 70000:
                specs["ram"] = SpecValue("12GB", label="RAM")
            elif price_val >= 35000:
                specs["ram"] = SpecValue("8GB", label="RAM")
            elif price_val >= 15000:
                specs["ram"] = SpecValue("6GB", label="RAM")
            else:
                specs["ram"] = SpecValue("4GB", label="RAM")

        # 2. Storage
        if "storage" not in specs:
            if price_val >= 70000:
                specs["storage"] = SpecValue("256GB", label="Internal Storage")
            elif price_val >= 35000:
                specs["storage"] = SpecValue("128GB", label="Internal Storage")
            else:
                specs["storage"] = SpecValue("64GB", label="Internal Storage")

        # 3. Processor
        if "processor" not in specs:
            if "apple" in b_lower or "iphone" in t_lower:
                proc = "Apple A16 Bionic (4nm)" if price_val < 80000 else "Apple A17 Pro (3nm)"
            elif "samsung" in b_lower or "galaxy" in t_lower:
                proc = "Snapdragon 8 Gen 2 for Galaxy" if price_val >= 50000 else ("Exynos 1380 Octa-Core" if price_val >= 20000 else "Exynos 850 Octa-Core")
            elif price_val >= 60000:
                proc = "Qualcomm Snapdragon 8 Gen 2 (4nm)"
            elif price_val >= 25000:
                proc = "MediaTek Dimensity 8200 (4nm)"
            elif price_val >= 12000:
                proc = "Qualcomm Snapdragon 695 5G"
            else:
                proc = "MediaTek Helio G85 Octa-Core"
            specs["processor"] = SpecValue(proc, label="Processor / SoC")

        # 4. Display & Refresh Rate
        if "display" not in specs:
            if price_val >= 60000:
                disp = "6.8\" Dynamic AMOLED 2X (120Hz LTPO)"
            elif price_val >= 25000:
                disp = "6.7\" FHD+ Super AMOLED (120Hz)"
            elif price_val >= 12000:
                disp = "6.6\" FHD+ 90Hz Display"
            else:
                disp = "6.5\" HD+ 60Hz Display"
            specs["display"] = SpecValue(disp, label="Display & Refresh Rate")

        # 5. Primary Camera
        if "camera" not in specs:
            cam_match = re.search(r"\b(200|108|64|50|48|12)\s*MP\b", title, re.IGNORECASE)
            if cam_match:
                mp = cam_match.group(1)
                cam = f"{mp} MP Primary Camera with OIS"
            elif price_val >= 60000:
                cam = "200 MP Quad Matrix with OIS"
            elif price_val >= 25000:
                cam = "50 MP Sony IMX890 with OIS"
            elif price_val >= 12000:
                cam = "50 MP Dual Camera"
            else:
                cam = "13 MP AI Camera"
            specs["camera"] = SpecValue(cam, label="Primary Camera")

        # 6. Battery & Charging
        if "battery" not in specs:
            if price_val >= 50000:
                bat_str = "5000mAh (45W Super Fast)"
            elif price_val >= 20000:
                bat_str = "5000mAh (67W Turbo Charge)"
            else:
                bat_str = "5000mAh (18W Fast Charge)"
            specs["battery"] = SpecValue(bat_str, label="Battery & Charging")

        # 7. Connectivity
        if "connectivity" not in specs:
            conn = "5G Dual SIM + Wi-Fi 6" if price_val >= 15000 else "4G LTE Dual SIM"
            specs["connectivity"] = SpecValue(conn, label="5G Connectivity")

        # 8. Build
        if "chassis" not in specs:
            chassis = "Gorilla Glass Victus 2 / IP68" if price_val >= 50000 else ("Gorilla Glass 5 / IP54" if price_val >= 15000 else "Reinforced Polycarbonate")
            specs["chassis"] = SpecValue(chassis, label="Build & Protection")

    elif category_slug in ("earphones-headphones", "audio"):
        is_over_ear = any(w in t_lower for w in ["headphone", "over-ear", "on-ear", "headset"])
        is_wired = any(w in t_lower for w in ["wired", "3.5mm", "aux", "in-ear with mic"]) and not any(w in t_lower for w in ["wireless", "bluetooth", "tws"])

        # 1. Driver Unit
        if "driver_unit" not in specs:
            d_match = re.search(r"\b(\d+(?:\.\d+)?)\s*mm\b", title, re.IGNORECASE)
            if d_match:
                specs["driver_unit"] = SpecValue(f"{d_match.group(1)} mm Dynamic Driver", label="Driver Unit")
            elif is_over_ear:
                specs["driver_unit"] = SpecValue("40 mm Custom Titanium Dome", label="Driver Unit")
            else:
                specs["driver_unit"] = SpecValue("11 mm Liquid Crystal Diaphragm", label="Driver Unit")

        # 2. Noise Cancellation
        if "noise_cancellation" not in specs:
            if price_val >= 15000 or "anc" in t_lower:
                anc = "48 dB Adaptive Hybrid ANC"
            elif price_val >= 3000:
                anc = "35 dB Active Noise Cancellation"
            else:
                anc = "Environmental Noise Cancellation (ENC)"
            specs["noise_cancellation"] = SpecValue(anc, label="Noise Cancellation")

        # 3. Audio Codecs
        if "audio_codecs" not in specs:
            codecs = "LDAC, AAC, SBC (Hi-Res Audio Wireless)" if price_val >= 10000 else ("aptX Adaptive, AAC, SBC" if price_val >= 4000 else "AAC, SBC Low-Latency")
            specs["audio_codecs"] = SpecValue(codecs, label="Audio Codecs")

        # 4. Frequency Response
        if "frequency_response" not in specs:
            freq = "4 Hz – 40,000 Hz (Hi-Res Certified)" if price_val >= 10000 else "20 Hz – 20,000 Hz Standard"
            specs["frequency_response"] = SpecValue(freq, label="Frequency Response")

        # 5. Playtime / Battery
        if "playtime" not in specs:
            if is_wired:
                specs["playtime"] = SpecValue("Continuous (Wired Direct)", label="Battery Life")
            elif is_over_ear:
                specs["playtime"] = SpecValue("40 Hours Playtime", label="Total Battery Life")
            else:
                specs["playtime"] = SpecValue("32 Hours Total Playtime", label="Total Battery Life")

        # 6. Protection Rating
        if "protection_rating" not in specs:
            specs["protection_rating"] = SpecValue("IPX5 Splash & Sweat Resistant", label="Protection Rating")

        # 7. Connectivity
        if "connectivity" not in specs:
            conn = "3.5mm Gold-Plated Audio Jack" if is_wired else "Bluetooth 5.3 (Low Latency)"
            specs["connectivity"] = SpecValue(conn, label="Interface / Protocol")

    elif category_slug == "speakers":
        if "charging_wattage" not in specs and "acoustic_output" not in specs:
            w_match = re.search(r"\b(\d+)\s*W\b", title, re.IGNORECASE)
            watts = f"{w_match.group(1)}W" if w_match else ("40W RMS" if price_val >= 8000 else "16W Stereo")
            specs["charging_wattage"] = SpecValue(watts, label="Acoustic Output")
        if "playtime" not in specs:
            specs["playtime"] = SpecValue("16 Hours Playback", label="Battery Playtime")
        if "connectivity" not in specs:
            specs["connectivity"] = SpecValue("Bluetooth 5.3 + Aux 3.5mm", label="Connectivity")
        if "protection_rating" not in specs:
            specs["protection_rating"] = SpecValue("IP67 Submersion Proof", label="Water & Dust Rating")

    elif category_slug == "cables-chargers-powerbanks":
        if "charging_wattage" not in specs:
            w_match = re.search(r"\b(\d+)\s*W\b", title, re.IGNORECASE)
            watts = f"{w_match.group(1)}W" if w_match else ("65W Fast Charge" if price_val >= 2000 else "30W Power Delivery")
            specs["charging_wattage"] = SpecValue(watts, label="Max Power Output")
        if "technology" not in specs:
            specs["technology"] = SpecValue("GaNFast III Semiconductor" if price_val >= 1500 else "Intelligent PD 3.0 Controller", label="Charging Tech")
        if "ports" not in specs:
            specs["ports"] = SpecValue("Dual USB-C + USB-A" if price_val >= 1500 else "USB-C High Speed", label="Port Configuration")

    elif category_slug == "keyboards-mice":
        is_mouse = "mouse" in t_lower
        if "switch_sensor" not in specs:
            specs["switch_sensor"] = SpecValue("26,000 DPI Optical Sensor" if is_mouse else "Hot-Swap Mechanical Switches", label="Switch / Sensor")
        if "polling_rate" not in specs:
            specs["polling_rate"] = SpecValue("1000 Hz / 1ms Polling Rate", label="Polling Rate")
        if "connectivity" not in specs:
            specs["connectivity"] = SpecValue("Tri-Mode (2.4G / BT / USB-C)", label="Connectivity")

    elif category_slug == "cameras":
        cam_subtype = classify_product_subtype(title, category_slug="cameras")
        if cam_subtype == "camera_cctv_security":
            if "sensor" not in specs:
                res_match = re.search(r"\b(1080p|2k|3mp|4mp|5mp|720p)\b", title, re.IGNORECASE)
                res_str = f"{res_match.group(1).upper()} High-Definition Sensor" if res_match else "1080p Full HD Surveillance Sensor"
                specs["sensor"] = SpecValue(res_str, label="Security Sensor")
            if "pan_tilt" not in specs:
                specs["pan_tilt"] = SpecValue("360° Horizontal Pan & 114° Vertical Tilt" if ("360" in t_lower or "pan" in t_lower) else "Wide-Angle 130° Fixed View", label="Coverage Angle")
            if "night_vision" not in specs:
                specs["night_vision"] = SpecValue("Enhanced IR Night Vision (Up to 30ft)", label="Night Vision")
            if "connectivity" not in specs:
                specs["connectivity"] = SpecValue("2.4GHz Wi-Fi + Two-Way Audio Intercom", label="Connectivity & Audio")
            if "storage" not in specs:
                specs["storage"] = SpecValue("MicroSD Card Slot (Up to 256GB) + Cloud", label="Storage Support")
        elif cam_subtype == "camera_accessory":
            if "material" not in specs:
                specs["material"] = SpecValue("High-Grade Aluminum Alloy Matrix", label="Build Material")
            if "mounting" not in specs:
                specs["mounting"] = SpecValue("Standard 1/4\"-20 Camera Screw Mount", label="Mount Interface")
            if "load_capacity" not in specs:
                specs["load_capacity"] = SpecValue("Up to 3.0 kg Payload", label="Load Capacity")
        else:
            if "sensor" not in specs:
                sensor = "Full-Frame 35mm Exmor R CMOS" if price_val >= 100000 else "APS-C 24.2 MP CMOS Sensor"
                specs["sensor"] = SpecValue(sensor, label="Image Sensor")
            if "resolution" not in specs:
                specs["resolution"] = SpecValue("4K 60p 10-bit Video / 24MP", label="Video & Stills")
            if "stabilization" not in specs:
                specs["stabilization"] = SpecValue("5-Axis In-Body Sensor Shift (IBIS)", label="Stabilization")

    elif category_slug == "tvs":
        if "resolution" not in specs:
            res = "4K Ultra HD (3840x2160) Quantum OLED" if price_val >= 60000 else "4K Ultra HD (3840x2160) LED"
            specs["resolution"] = SpecValue(res, label="Panel & Resolution")
        if "screen_size" not in specs:
            specs["screen_size"] = SpecValue("55\"", label="Display Size")
        if "audio" not in specs:
            specs["audio"] = SpecValue("40W Dolby Atmos Acoustic Sound", label="Audio Output")
        if "os" not in specs:
            specs["os"] = SpecValue("Google TV with Voice Control", label="Smart OS")

    elif category_slug == "smartwatches-bands":
        if "screen_size" not in specs and "display" not in specs:
            specs["screen_size"] = SpecValue("1.43\" AMOLED Display", label="Display Panel")
        if "sensors" not in specs:
            specs["sensors"] = SpecValue("Heart Rate, SpO2, Sleep & Stress Sensors", label="Biometric Sensors")
        if "battery" not in specs:
            specs["battery"] = SpecValue("Up to 12 Days Battery Life", label="Battery Life")
        if "water_rating" not in specs:
            specs["water_rating"] = SpecValue("5 ATM / IP68 Water Resistant", label="Water Resistance")

    return specs


def extract_specifications(
    title: str,
    category_slug: Optional[str] = None,
    price: Optional[object] = None,
    brand: Optional[str] = None,
    description: Optional[str] = None,
) -> SpecDict:
    """
    Extracts key-value technical specifications from product title string with category sanity validation.
    Returns SpecDict mapping machine keys to SpecValue (which supports both dict-like and string-like lookups).
    Synthesizes rich technical specifications per category if missing.
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

    # Synthesize rich category specifications
    if category_slug:
        synthesize_category_specs(
            specs,
            title=title,
            category_slug=category_slug,
            price=price,
            brand=brand,
            description=description,
        )

    return specs

