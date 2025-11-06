"""Sales history service for retrieving and filtering sales transactions."""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session

from app.repositories.sales_history_repository import SalesHistoryRepository
from app.models.sales_history import SalesHistory


class SalesHistoryService:
    """Service for sales history retrieval and filtering.

    This service handles:
    - Sales history retrieval with date filtering
    - Sales transaction details retrieval
    - Time-series ordered sales data
    """

    def __init__(
        self,
        sales_history_repo: SalesHistoryRepository = None,
    ):
        """Initialize SalesHistoryService with repository dependencies.

        Args:
            sales_history_repo: SalesHistoryRepository instance
        """
        self.sales_history_repo = sales_history_repo or SalesHistoryRepository()

    def get_sales_history(
        self,
        date_from: Optional[datetime],
        date_to: Optional[datetime],
        db: Session,
    ) -> List[SalesHistory]:
        """Get sales history with optional date range filtering.

        Args:
            date_from: Optional start date for filtering
            date_to: Optional end date for filtering
            db: Database session

        Returns:
            List of SalesHistory instances ordered by timestamp desc

        Raises:
            ValueError: If date_from is after date_to

        Preconditions:
        - If date_from and date_to are provided, date_from <= date_to

        Postconditions:
        - Returns sales history within the date range
        - Ordered by timestamp desc (newest first)
        """
        # Validate date range
        if date_from and date_to:
            if date_from > date_to:
                raise ValueError("date_from must be before or equal to date_to")

        # Set default date range if not provided
        if date_from is None:
            date_from = datetime.min
        if date_to is None:
            date_to = datetime.max

        return self.sales_history_repo.get_by_date_range(
            start_date=date_from,
            end_date=date_to,
            db=db,
        )

    def get_sales_by_id(
        self, sales_id: UUID, db: Session
    ) -> Optional[SalesHistory]:
        """Get specific sales transaction by ID.

        Args:
            sales_id: Sales transaction UUID
            db: Database session

        Returns:
            SalesHistory instance if found, None otherwise
        """
        return self.sales_history_repo.get_by_id(sales_id, db)
