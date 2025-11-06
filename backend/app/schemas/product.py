"""Product API schemas.

This module defines Pydantic models for product API requests and responses:
- Request validation models
- Response serialization models
- Data transfer objects
"""

from typing import Optional, List, Literal
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict


class SetItemRequest(BaseModel):
    """Set item component in product creation request.

    Attributes:
        product_id: UUID of the component product
        quantity: Quantity of the component in the set
    """

    product_id: UUID = Field(..., description="Component product UUID")
    quantity: int = Field(..., gt=0, description="Quantity of component in set")


class CreateProductRequest(BaseModel):
    """Request model for creating a new product.

    Attributes:
        name: Product name (1-255 characters)
        unit_cost: Unit cost (purchase price, >= 0)
        sale_price: Sale price (selling price, >= 0)
        initial_stock: Initial stock quantity (>= 0)
        product_type: Product type ('single' or 'set')
        set_items: List of set components (required for set products)
    """

    name: str = Field(..., min_length=1, max_length=255, description="Product name")
    unit_cost: int = Field(..., ge=0, description="Unit cost (purchase price)")
    sale_price: int = Field(..., ge=0, description="Sale price (selling price)")
    initial_stock: int = Field(..., ge=0, description="Initial stock quantity")
    product_type: Literal["single", "set"] = Field(..., description="Product type")
    set_items: Optional[List[SetItemRequest]] = Field(
        None,
        description="Set components (required for set products)"
    )

    @field_validator("set_items")
    @classmethod
    def validate_set_items(
        cls,
        value: Optional[List[SetItemRequest]],
        info
    ) -> Optional[List[SetItemRequest]]:
        """Validate set_items based on product_type.

        Args:
            value: Set items list
            info: Validation info containing other fields

        Returns:
            Validated set items

        Raises:
            ValueError: If set product doesn't have set_items
        """
        # Note: We check product_type in the controller, not here
        # to allow proper validation flow
        return value


class UpdateProductRequest(BaseModel):
    """Request model for updating a product.

    All fields are optional for partial updates.

    Attributes:
        name: Product name
        unit_cost: Unit cost
        sale_price: Sale price
    """

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    unit_cost: Optional[int] = Field(None, ge=0)
    sale_price: Optional[int] = Field(None, ge=0)


class UpdatePriceRequest(BaseModel):
    """Request model for updating product price only.

    Attributes:
        sale_price: New sale price
    """

    sale_price: int = Field(..., ge=0, description="New sale price")


class SetItemResponse(BaseModel):
    """Set item component in product response.

    Attributes:
        product_id: UUID of the component product
        quantity: Quantity of the component in the set
    """

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    product_id: UUID = Field(..., validation_alias="item_product_id")
    quantity: int


class ProductResponse(BaseModel):
    """Response model for product data.

    Attributes:
        id: Product UUID
        name: Product name
        unit_cost: Unit cost (purchase price)
        sale_price: Sale price (selling price)
        initial_stock: Initial stock quantity
        current_stock: Current stock quantity
        product_type: Product type ('single' or 'set')
        set_items: List of set components (for set products)
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    unit_cost: int
    sale_price: int
    initial_stock: int
    current_stock: int
    product_type: Literal["single", "set"]
    set_items: Optional[List[SetItemResponse]] = None
    created_at: datetime
    updated_at: datetime


class DeleteProductResponse(BaseModel):
    """Response model for product deletion.

    Attributes:
        success: Whether deletion was successful
        message: Success or error message
    """

    success: bool
    message: str


class ErrorResponse(BaseModel):
    """Standard error response model.

    Attributes:
        error_code: Machine-readable error code
        message: Human-readable error message
        details: Optional additional error details
    """

    error_code: str
    message: str
    details: Optional[dict] = None
