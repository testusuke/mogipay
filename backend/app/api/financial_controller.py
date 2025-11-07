"""Financial API Controller.

This module provides REST API endpoints for financial management:
- GET /api/financial/summary - Retrieve financial summary (cost, revenue, profit, break-even status)
"""

from typing import Annotated
from pydantic import BaseModel, Field, ConfigDict
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.services.financial_service import FinancialService


# ========================================
# Response Models
# ========================================

class FinancialSummaryResponse(BaseModel):
    """Financial summary response."""

    model_config = ConfigDict(from_attributes=True)

    total_cost: str = Field(..., description="Total initial cost (Integer as string)")
    total_revenue: str = Field(..., description="Total sales revenue (Integer as string)")
    profit: str = Field(..., description="Profit/Loss amount (Integer as string)")
    profit_rate: float = Field(..., description="Profit rate (profit / cost)")
    break_even_achieved: bool = Field(..., description="Whether break-even point is achieved")


# ========================================
# Dependency Injection
# ========================================

def get_financial_service() -> FinancialService:
    """Get FinancialService instance."""
    return FinancialService()


# ========================================
# Router
# ========================================

router = APIRouter(prefix="/api/financial", tags=["financial"])


# ========================================
# Endpoints
# ========================================

@router.get(
    "/summary",
    response_model=FinancialSummaryResponse,
    status_code=status.HTTP_200_OK,
)
def get_financial_summary(
    db: Annotated[Session, Depends(get_db)],
    financial_service: Annotated[FinancialService, Depends(get_financial_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Get financial summary including cost, revenue, profit, and break-even status.

    This endpoint calculates and returns:
    - Total initial cost (sum of initial_stock * unit_cost for all products)
    - Total sales revenue (sum of all sales transactions)
    - Profit/Loss (revenue - cost)
    - Profit rate (profit / cost, 0 if cost is 0)
    - Break-even achievement status (profit >= 0)

    Args:
        db: Database session
        financial_service: FinancialService instance

    Returns:
        FinancialSummaryResponse with financial summary data
    """
    summary = financial_service.get_financial_summary(db)

    return FinancialSummaryResponse(
        total_cost=str(summary.total_cost),
        total_revenue=str(summary.total_revenue),
        profit=str(summary.profit),
        profit_rate=summary.profit_rate,
        break_even_achieved=summary.break_even_achieved,
    )
