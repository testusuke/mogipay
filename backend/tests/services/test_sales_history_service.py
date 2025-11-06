"""Tests for SalesHistoryService using TDD approach."""

import pytest
from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4
from datetime import datetime, timedelta

from app.services.sales_history_service import SalesHistoryService
from app.models.sales_history import SalesHistory
from app.models.sale_item import SaleItem


class TestSalesHistoryService:
    """Test cases for SalesHistoryService.

    Following TDD approach:
    1. RED: Write failing tests first
    2. GREEN: Implement minimal code to pass
    3. REFACTOR: Improve code quality
    """

    @pytest.fixture
    def mock_sales_history_repo(self):
        """Mock SalesHistoryRepository."""
        return Mock()

    @pytest.fixture
    def sales_history_service(self, mock_sales_history_repo):
        """Create SalesHistoryService instance with mocked dependencies."""
        return SalesHistoryService(
            sales_history_repo=mock_sales_history_repo,
        )

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()

    # Test 1: Get sales history without date filter
    def test_get_sales_history_all(
        self, sales_history_service, mock_sales_history_repo, mock_db
    ):
        """Test retrieving all sales history."""
        sales = [
            SalesHistory(
                id=uuid4(),
                total_amount=Decimal("1000"),
                timestamp=datetime(2025, 11, 6, 10, 0),
            ),
            SalesHistory(
                id=uuid4(),
                total_amount=Decimal("500"),
                timestamp=datetime(2025, 11, 6, 11, 0),
            ),
        ]

        mock_sales_history_repo.get_by_date_range.return_value = sales

        result = sales_history_service.get_sales_history(
            date_from=None,
            date_to=None,
            db=mock_db,
        )

        assert len(result) == 2
        assert result[0].total_amount == Decimal("1000")

    # Test 2: Get sales history with date filter
    def test_get_sales_history_with_date_filter(
        self, sales_history_service, mock_sales_history_repo, mock_db
    ):
        """Test retrieving sales history with date range filter."""
        date_from = datetime(2025, 11, 6, 0, 0)
        date_to = datetime(2025, 11, 6, 23, 59)

        sales = [
            SalesHistory(
                id=uuid4(),
                total_amount=Decimal("1000"),
                timestamp=datetime(2025, 11, 6, 10, 0),
            ),
        ]

        mock_sales_history_repo.get_by_date_range.return_value = sales

        result = sales_history_service.get_sales_history(
            date_from=date_from,
            date_to=date_to,
            db=mock_db,
        )

        assert len(result) == 1
        mock_sales_history_repo.get_by_date_range.assert_called_once_with(
            start_date=date_from, end_date=date_to, db=mock_db
        )

    # Test 3: Get sales history ordered by timestamp desc
    def test_get_sales_history_ordered(
        self, sales_history_service, mock_sales_history_repo, mock_db
    ):
        """Test that sales history is ordered by timestamp descending."""
        sales = [
            SalesHistory(
                id=uuid4(),
                total_amount=Decimal("500"),
                timestamp=datetime(2025, 11, 6, 11, 0),
            ),
            SalesHistory(
                id=uuid4(),
                total_amount=Decimal("1000"),
                timestamp=datetime(2025, 11, 6, 10, 0),
            ),
        ]

        mock_sales_history_repo.get_by_date_range.return_value = sales

        result = sales_history_service.get_sales_history(
            date_from=None,
            date_to=None,
            db=mock_db,
        )

        # First should be newer timestamp
        assert result[0].timestamp > result[1].timestamp

    # Test 4: Get sales by ID
    def test_get_sales_by_id(
        self, sales_history_service, mock_sales_history_repo, mock_db
    ):
        """Test retrieving specific sales transaction by ID."""
        sale_id = uuid4()
        sale = SalesHistory(
            id=sale_id,
            total_amount=Decimal("1000"),
            timestamp=datetime.now(),
        )

        mock_sales_history_repo.get_by_id.return_value = sale

        result = sales_history_service.get_sales_by_id(sale_id, mock_db)

        assert result.id == sale_id
        assert result.total_amount == Decimal("1000")

    # Test 5: Get sales by ID - not found
    def test_get_sales_by_id_not_found(
        self, sales_history_service, mock_sales_history_repo, mock_db
    ):
        """Test retrieving non-existent sales transaction."""
        sale_id = uuid4()
        mock_sales_history_repo.get_by_id.return_value = None

        result = sales_history_service.get_sales_by_id(sale_id, mock_db)

        assert result is None

    # Test 6: Date range validation
    def test_get_sales_history_invalid_date_range(
        self, sales_history_service, mock_db
    ):
        """Test that invalid date range raises error."""
        date_from = datetime(2025, 11, 7, 0, 0)
        date_to = datetime(2025, 11, 6, 0, 0)  # Earlier than date_from

        with pytest.raises(ValueError) as exc_info:
            sales_history_service.get_sales_history(
                date_from=date_from,
                date_to=date_to,
                db=mock_db,
            )

        assert "date_from" in str(exc_info.value).lower()

    # Test 7: Empty result handling
    def test_get_sales_history_empty_result(
        self, sales_history_service, mock_sales_history_repo, mock_db
    ):
        """Test handling empty sales history result."""
        mock_sales_history_repo.get_by_date_range.return_value = []

        result = sales_history_service.get_sales_history(
            date_from=None,
            date_to=None,
            db=mock_db,
        )

        assert len(result) == 0
        assert result == []
