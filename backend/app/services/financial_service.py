"""Financial service for profit and loss calculations."""

from decimal import Decimal
from dataclasses import dataclass
from sqlalchemy.orm import Session

from app.repositories.product_repository import ProductRepository
from app.repositories.sales_history_repository import SalesHistoryRepository


@dataclass
class FinancialSummary:
    """Financial summary data.

    Attributes:
        total_cost: Total initial cost (initial_stock × unit_cost)
        total_revenue: Total sales revenue
        profit: Profit or loss (revenue - cost)
        profit_rate: Profit rate (profit / revenue)
        break_even_achieved: Whether profit >= 0
    """

    total_cost: Decimal
    total_revenue: Decimal
    profit: Decimal
    profit_rate: float
    break_even_achieved: bool


class FinancialService:
    """Service for financial calculations and profit/loss analysis.

    This service handles:
    - Total cost calculation from product inventory
    - Total revenue calculation from sales history
    - Profit calculation (revenue - cost)
    - Profit rate calculation
    - Break-even achievement detection
    """

    def __init__(
        self,
        product_repo: ProductRepository = None,
        sales_history_repo: SalesHistoryRepository = None,
    ):
        """Initialize FinancialService with repository dependencies.

        Args:
            product_repo: ProductRepository instance
            sales_history_repo: SalesHistoryRepository instance
        """
        self.product_repo = product_repo or ProductRepository()
        self.sales_history_repo = sales_history_repo or SalesHistoryRepository()

    def get_financial_summary(self, db: Session) -> FinancialSummary:
        """Get comprehensive financial summary.

        Args:
            db: Database session

        Returns:
            FinancialSummary with cost, revenue, profit metrics

        Algorithm:
        - total_cost = SUM(products.initial_stock * products.unit_cost)
        - total_revenue = SUM(sales_history.total_amount)
        - profit = total_revenue - total_cost
        - profit_rate = profit / total_revenue
        - break_even_achieved = profit >= 0

        Preconditions:
        - db session is active

        Postconditions:
        - Returns total_cost, total_revenue, profit, break_even status
        """
        # Calculate total cost
        products = self.product_repo.get_all(db=db)
        total_cost = Decimal("0")

        for product in products:
            product_cost = product.initial_stock * product.unit_cost
            total_cost += product_cost

        # Get total revenue
        total_revenue = self.sales_history_repo.get_total_sales(db)

        # Calculate profit
        profit = total_revenue - total_cost

        # Calculate profit rate (avoid division by zero)
        if total_revenue > 0:
            profit_rate = float(profit / total_revenue)
        else:
            profit_rate = 0.0

        # Check break-even achievement
        break_even_achieved = profit >= 0

        return FinancialSummary(
            total_cost=total_cost,
            total_revenue=total_revenue,
            profit=profit,
            profit_rate=profit_rate,
            break_even_achieved=break_even_achieved,
        )
