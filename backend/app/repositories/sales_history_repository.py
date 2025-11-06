"""SalesHistory repository for data access operations."""

from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.sales_history import SalesHistory
from app.models.sale_item import SaleItem


class SalesHistoryRepository:
    """Repository for SalesHistory and SaleItem entity operations.

    This repository handles all database operations for sales transactions,
    including creating sales with their items and retrieving sales data.
    """

    def create_sale(
        self,
        total_amount: Decimal,
        sale_items_data: List[Dict[str, Any]],
        db: Session,
    ) -> SalesHistory:
        """Create a new sales transaction with sale items.

        Args:
            total_amount: Total amount of the sale
            sale_items_data: List of dicts with sale item data
            db: Database session

        Returns:
            Created SalesHistory instance with sale_items loaded

        Raises:
            IntegrityError: If database constraints are violated
        """
        # Create sales history
        sales = SalesHistory(total_amount=total_amount)
        db.add(sales)
        db.flush()  # Get the sales ID

        # Create sale items
        for item_data in sale_items_data:
            sale_item = SaleItem(
                sale_id=sales.id,
                product_id=item_data["product_id"],
                product_name=item_data["product_name"],
                quantity=item_data["quantity"],
                unit_cost=item_data["unit_cost"],
                sale_price=item_data["sale_price"],
                subtotal=item_data["subtotal"],
            )
            db.add(sale_item)

        db.commit()
        db.refresh(sales)
        return sales

    def get_by_id(self, sales_id: UUID, db: Session) -> Optional[SalesHistory]:
        """Retrieve a sales transaction by ID.

        Args:
            sales_id: Sales history UUID
            db: Database session

        Returns:
            SalesHistory instance if found, None otherwise
        """
        stmt = select(SalesHistory).where(SalesHistory.id == sales_id)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        db: Session,
    ) -> List[SalesHistory]:
        """Retrieve sales transactions within a date range.

        Args:
            start_date: Start of date range
            end_date: End of date range
            db: Database session

        Returns:
            List of SalesHistory instances
        """
        stmt = (
            select(SalesHistory)
            .where(SalesHistory.timestamp >= start_date)
            .where(SalesHistory.timestamp <= end_date)
            .order_by(SalesHistory.timestamp.desc())
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def get_total_sales(self, db: Session) -> Decimal:
        """Calculate total sales amount across all transactions.

        Args:
            db: Database session

        Returns:
            Total sales amount
        """
        stmt = select(func.sum(SalesHistory.total_amount))
        result = db.execute(stmt)
        total = result.scalar_one_or_none()
        return total if total is not None else Decimal("0.00")

    def get_daily_sales(self, db: Session) -> List[Tuple[datetime.date, Decimal]]:
        """Get daily sales summary.

        Args:
            db: Database session

        Returns:
            List of tuples (date, total_amount) ordered by date descending
        """
        stmt = (
            select(
                func.date(SalesHistory.timestamp).label("sale_date"),
                func.sum(SalesHistory.total_amount).label("daily_total"),
            )
            .group_by(func.date(SalesHistory.timestamp))
            .order_by(func.date(SalesHistory.timestamp).desc())
        )
        result = db.execute(stmt)
        return [(row.sale_date, row.daily_total) for row in result]
