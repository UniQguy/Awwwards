"""
Exceptions for inventory management and stock reservation.
"""


class InventoryError(Exception):
    """Base exception for inventory operations."""
    pass


class InsufficientStockError(InventoryError):
    """Raised when available inventory is lower than requested quantity."""
    def __init__(self, product_sku: str, requested: int, available: int):
        self.product_sku = product_sku
        self.requested = requested
        self.available = available
        super().__init__(
            f"Insufficient stock for {product_sku}: requested {requested}, but only {available} available."
        )


class ReservationExpiredError(InventoryError):
    """Raised when an operation targets an already expired stock reservation."""
    pass


class InvalidReservationStateError(InventoryError):
    """Raised when reservation state transition is invalid."""
    pass
