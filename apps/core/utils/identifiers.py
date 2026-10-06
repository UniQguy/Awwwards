"""
Cryptographically secure identifier generators for orders and entities.
"""

from datetime import datetime
import secrets

# Unambiguous 31-character alphanumeric alphabet omitting 0, O, 1, I, L
UNAMBIGUOUS_ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"


def generate_order_number(year: int | None = None) -> str:
    """
    Generate a non-sequential, tamper-proof order number in format:
    EC-<YYYY>-XXXX-XXXX
    Example: EC-2026-F8K9-M4R2
    """
    if year is None:
        year = datetime.now().year

    chunk1 = "".join(secrets.choice(UNAMBIGUOUS_ALPHABET) for _ in range(4))
    chunk2 = "".join(secrets.choice(UNAMBIGUOUS_ALPHABET) for _ in range(4))
    return f"EC-{year}-{chunk1}-{chunk2}"
