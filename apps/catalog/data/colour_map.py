"""
Curated color-name to hex map for hardware and accessories finishes.
Used by specimen cards and product pages to render authentic swatches.
If a color is not mapped, templates fall back to the plain text name.
"""

from typing import Optional

COLOUR_MAP = {
    # Monochromes & Neutrals
    "black": "#1A1A1A",
    "carbon black": "#222222",
    "midnight black": "#151515",
    "matte black": "#242424",
    "space black": "#1C1C1E",
    "white": "#F8F8F8",
    "polar white": "#F5F5F5",
    "ceramic white": "#FAFAFA",
    "silver": "#D1D5DB",
    "grey": "#6B7280",
    "gray": "#6B7280",
    "space grey": "#4B4E54",
    "space gray": "#4B4E54",
    "graphite": "#383A3F",
    "titanium": "#878681",

    # Metallics
    "gold": "#D4AF37",
    "champagne gold": "#E5D298",
    "rose gold": "#B76E79",
    "bronze": "#8C6239",
    "copper": "#B87333",

    # Blues & Teals
    "blue": "#2563EB",
    "navy": "#1E3A8A",
    "midnight blue": "#1E293B",
    "pacific blue": "#2E5B88",
    "teal": "#0D9488",
    "cyan": "#06B6D4",
    "coral green": "#2DD4BF",

    # Reds & Oranges
    "red": "#DC2626",
    "furious red": "#B91C1C",
    "crimson": "#991B1B",
    "coral": "#F97316",
    "orange": "#EA580C",
    "amber": "#D97706",

    # Greens & Earth
    "green": "#16A34A",
    "mint green": "#86EFAC",
    "forest green": "#1E4D2B",
    "olive": "#556B2F",
    "sage": "#9CA986",

    # Purples & Pinks
    "purple": "#7E22CE",
    "lavender": "#C084FC",
    "violet": "#6D28D9",
    "pink": "#EC4899",
    "yellow": "#EAB308",
}


def get_colour_hex(name: str) -> Optional[str]:
    """Retrieve hex code for a sanitized color name or return None."""
    if not name:
        return None
    key = name.strip().lower()
    return COLOUR_MAP.get(key)
