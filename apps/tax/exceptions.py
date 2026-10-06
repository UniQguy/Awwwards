"""
Exceptions for the Indian GST taxation engine.
"""


class TaxEngineError(Exception):
    """Base exception for all tax engine failures."""


class InvalidStateError(TaxEngineError):
    """Raised when an unrecognized Indian State or Union Territory name is supplied."""


class MissingSellerStateError(TaxEngineError):
    """Raised when SELLER_STATE is empty or not configured."""
