"""Sales API Controller.

This module provides REST API endpoints for sales management:
- POST /api/sales/checkout - Process checkout
- GET /api/sales/history - Retrieve sales history
- GET /api/sales/summary - Get sales analytics summary
"""

from typing import List, Optional, Annotated
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.services.sales_service import SalesService
from app.services.sales_history_service import SalesHistoryService
from app.services.sales_analytics_service import SalesAnalyticsService
from app.exceptions import InsufficientStockError, ProductNotFoundError


# ========================================
# Request/Response Models
# ========================================

class CheckoutItemRequest(BaseModel):
    """Checkout item in request body."""

    product_id: str = Field(..., description="Product UUID")
    quantity: int = Field(..., gt=0, description="Quantity (must be greater than 0)")


class CheckoutRequest(BaseModel):
    """Request body for checkout endpoint."""

    items: List[CheckoutItemRequest] = Field(..., min_length=1, description="List of items to checkout (at least one)")


class CheckoutResponse(BaseModel):
    """Response for checkout endpoint."""

    model_config = ConfigDict(from_attributes=True)

    sale_id: str = Field(..., description="Sale transaction UUID")
    total_amount: str = Field(..., description="Total amount (Decimal as string)")
    timestamp: datetime = Field(..., description="Transaction timestamp")


class SaleItemResponse(BaseModel):
    """Sale item in response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    sale_id: str
    product_id: str
    product_name: str
    quantity: int
    unit_cost: str
    sale_price: str
    subtotal: str


class SaleTransactionResponse(BaseModel):
    """Sale transaction response."""

    model_config = ConfigDict(from_attributes=True)

    sale_id: str
    total_amount: str
    timestamp: datetime
    items: List[SaleItemResponse]


class SalesSummaryResponse(BaseModel):
    """Sales summary response."""

    model_config = ConfigDict(from_attributes=True)

    total_revenue: str
    daily_revenue: List[str]
    completion_rate: float


class ErrorResponse(BaseModel):
    """Error response model."""

    error_code: str
    message: str
    details: Optional[dict] = None


# ========================================
# Dependency Injection
# ========================================

def get_sales_service() -> SalesService:
    """Get SalesService instance."""
    return SalesService()


def get_sales_history_service() -> SalesHistoryService:
    """Get SalesHistoryService instance."""
    return SalesHistoryService()


def get_sales_analytics_service() -> SalesAnalyticsService:
    """Get SalesAnalyticsService instance."""
    return SalesAnalyticsService()


# ========================================
# Router
# ========================================

router = APIRouter(prefix="/api/sales", tags=["sales"])


# ========================================
# Endpoints
# ========================================

@router.post(
    "/checkout",
    response_model=CheckoutResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Insufficient stock"},
        404: {"model": ErrorResponse, "description": "Product not found"},
        422: {"description": "Validation error"},
    },
)
def checkout(
    request: CheckoutRequest,
    db: Annotated[Session, Depends(get_db)],
    sales_service: Annotated[SalesService, Depends(get_sales_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Process checkout and create sale transaction.

    Args:
        request: Checkout request with items and quantities
        db: Database session
        sales_service: SalesService instance

    Returns:
        CheckoutResponse with sale_id, total_amount, and timestamp

    Raises:
        HTTPException 400: Insufficient stock
        HTTPException 404: Product not found
        HTTPException 422: Validation error
    """
    try:
        # Convert request to CheckoutItem list
        from app.services.sales_service import CheckoutItem
        items = [
            CheckoutItem(product_id=item.product_id, quantity=item.quantity)
            for item in request.items
        ]

        # Process checkout
        transaction = sales_service.process_checkout(items, db)

        # Convert response
        return CheckoutResponse(
            sale_id=str(transaction.sale_id),
            total_amount=str(transaction.total_amount),
            timestamp=transaction.timestamp,
        )

    except InsufficientStockError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INSUFFICIENT_STOCK",
                "message": e.message,
                "details": {
                    "product_id": e.product_id,
                    "requested": e.requested,
                    "available": e.available,
                },
            },
        )

    except ProductNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "RESOURCE_NOT_FOUND",
                "message": e.message,
                "details": {
                    "resource_type": "product",
                    "resource_id": e.product_id,
                },
            },
        )


@router.get(
    "/history",
    response_model=List[SaleTransactionResponse],
    status_code=status.HTTP_200_OK,
)
def get_sales_history(
    db: Annotated[Session, Depends(get_db)],
    sales_history_service: Annotated[SalesHistoryService, Depends(get_sales_history_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
):
    """Get sales history with optional date filtering.

    Args:
        date_from: Start date for filtering (optional)
        date_to: End date for filtering (optional)
        db: Database session
        sales_history_service: SalesHistoryService instance

    Returns:
        List of SaleTransactionResponse
    """
    transactions = sales_history_service.get_sales_history(date_from, date_to, db)

    # Convert to response model
    return [
        SaleTransactionResponse(
            sale_id=str(t.id),
            total_amount=str(t.total_amount),
            timestamp=t.timestamp,
            items=[
                SaleItemResponse(
                    id=str(item.id),
                    sale_id=str(item.sale_id),
                    product_id=str(item.product_id),
                    product_name=item.product_name,
                    quantity=item.quantity,
                    unit_cost=str(item.unit_cost),
                    sale_price=str(item.sale_price),
                    subtotal=str(item.subtotal),
                )
                for item in t.sale_items
            ],
        )
        for t in transactions
    ]


@router.get(
    "/summary",
    response_model=SalesSummaryResponse,
    status_code=status.HTTP_200_OK,
)
def get_sales_summary(
    db: Annotated[Session, Depends(get_db)],
    sales_analytics_service: Annotated[SalesAnalyticsService, Depends(get_sales_analytics_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Get sales analytics summary.

    Args:
        db: Database session
        sales_analytics_service: SalesAnalyticsService instance

    Returns:
        SalesSummaryResponse with total_revenue, daily_revenue, and completion_rate
    """
    summary = sales_analytics_service.get_sales_summary(db)

    return SalesSummaryResponse(
        total_revenue=str(summary.total_revenue),
        daily_revenue=[str(amount) for amount in summary.daily_revenue],
        completion_rate=summary.completion_rate,
    )
