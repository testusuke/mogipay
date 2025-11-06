"""Custom exceptions for MogiPay application."""


class MogiPayException(Exception):
    """Base exception for MogiPay application."""

    pass


class ProductNotFoundError(MogiPayException):
    """Exception raised when a product is not found."""

    def __init__(self, product_id: str):
        self.product_id = product_id
        self.message = f"Product not found: {product_id}"
        super().__init__(self.message)


class InsufficientStockError(MogiPayException):
    """Exception raised when product stock is insufficient for checkout."""

    def __init__(self, product_id: str, requested: int, available: int):
        self.product_id = product_id
        self.requested = requested
        self.available = available
        self.message = f"Insufficient stock for product {product_id}: requested {requested}, available {available}"
        super().__init__(self.message)


class DuplicateProductError(MogiPayException):
    """Exception raised when trying to create a product with duplicate name."""

    def __init__(self, product_name: str):
        self.product_name = product_name
        self.message = f"Product with name '{product_name}' already exists"
        super().__init__(self.message)


class InvalidSetItemError(MogiPayException):
    """Exception raised when set product configuration is invalid."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
