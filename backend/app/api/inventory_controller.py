"""Inventory API Controller.

This module provides REST API endpoints for inventory management:
- GET /api/inventory/status - Retrieve inventory status for all products
"""

from typing import List, Annotated
from pydantic import BaseModel, Field, ConfigDict
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.services.inventory_service import InventoryService


# ========================================
# Response Models
# ========================================

class ProductInventoryResponse(BaseModel):
    """Product inventory information in response."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Product UUID")
    name: str = Field(..., description="Product name")
    product_type: str = Field(..., description="Product type ('single' or 'set')")
    current_stock: int = Field(..., description="Current stock quantity")
    initial_stock: int = Field(..., description="Initial stock quantity")
    stock_rate: float = Field(..., description="Stock remaining rate (0.0 to 1.0)")
    is_out_of_stock: bool = Field(..., description="Whether the product is out of stock")


class InventoryStatusResponse(BaseModel):
    """Inventory status response containing all products."""

    model_config = ConfigDict(from_attributes=True)

    products: List[ProductInventoryResponse] = Field(..., description="List of product inventory information")


# ========================================
# Dependency Injection
# ========================================

def get_inventory_service() -> InventoryService:
    """Get InventoryService instance."""
    return InventoryService()


# ========================================
# Router
# ========================================

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


# ========================================
# Endpoints
# ========================================

@router.get(
    "/status",
    response_model=InventoryStatusResponse,
    status_code=status.HTTP_200_OK,
)
async def get_inventory_status(
    db: Annotated[Session, Depends(get_db)],
    inventory_service: Annotated[InventoryService, Depends(get_inventory_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Get inventory status for all products.

    This endpoint returns the current stock status for all products,
    including both single and set products. Set product stock is
    calculated dynamically based on the availability of component items.

    Args:
        db: Database session
        inventory_service: InventoryService instance

    Returns:
        InventoryStatusResponse with list of product inventory information
    """
    inventory_list = inventory_service.get_inventory_status(db)

    # Convert to response model
    return InventoryStatusResponse(
        products=[
            ProductInventoryResponse(
                id=str(item.id),
                name=item.name,
                product_type=item.product_type,
                current_stock=item.current_stock,
                initial_stock=item.initial_stock,
                stock_rate=item.stock_rate,
                is_out_of_stock=item.is_out_of_stock,
            )
            for item in inventory_list
        ]
    )
