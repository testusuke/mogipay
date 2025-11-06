"""Sales analytics service for sales summary and completion rate calculations."""

from typing import List
from decimal import Decimal
from dataclasses import dataclass
from sqlalchemy.orm import Session

from app.repositories.sales_history_repository import SalesHistoryRepository
from app.repositories.product_repository import ProductRepository


@dataclass
class SalesSummary:
    """Sales summary data.

    Attributes:
        total_revenue: Total sales revenue
        daily_revenue: List of daily revenue amounts
        completion_rate: Overall completion rate (0.0 to 1.0)
    """

    total_revenue: Decimal
    daily_revenue: List[Decimal]
    completion_rate: float


class SalesAnalyticsService:
    """Service for sales analytics and summary calculations.

    This service handles:
    - Total revenue calculation
    - Daily revenue breakdown
    - Completion rate calculation based on stock sold
    """

    def __init__(
        self,
        sales_history_repo: SalesHistoryRepository = None,
        product_repo: ProductRepository = None,
    ):
        """Initialize SalesAnalyticsService with repository dependencies.

        Args:
            sales_history_repo: SalesHistoryRepository instance
            product_repo: ProductRepository instance
        """
        self.sales_history_repo = sales_history_repo or SalesHistoryRepository()
        self.product_repo = product_repo or ProductRepository()

    def get_sales_summary(self, db: Session) -> SalesSummary:
        """Get comprehensive sales summary.

        Args:
            db: Database session

        Returns:
            SalesSummary with revenue and completion metrics

        Algorithm:
        - total_revenue = SUM(sales_history.total_amount)
        - daily_revenue = GROUP BY date(timestamp), SUM(total_amount)
        - completion_rate = (initial_stock - current_stock) / initial_stock * 100

        Preconditions:
        - db session is active

        Postconditions:
        - Returns total revenue, daily revenue, completion rate
        """
        # Get total revenue
        total_revenue = self.sales_history_repo.get_total_sales(db)

        # Get daily revenue (already ordered by date desc)
        daily_sales = self.sales_history_repo.get_daily_sales(db)
        daily_revenue = [amount for date, amount in daily_sales]

        # Calculate completion rate
        products = self.product_repo.get_all(db=db)

        total_initial = 0
        total_sold = 0

        for product in products:
            total_initial += product.initial_stock
            total_sold += (product.initial_stock - product.current_stock)

        # Calculate completion rate (avoid division by zero)
        if total_initial > 0:
            completion_rate = total_sold / total_initial
        else:
            completion_rate = 0.0

        return SalesSummary(
            total_revenue=total_revenue,
            daily_revenue=daily_revenue,
            completion_rate=completion_rate,
        )
