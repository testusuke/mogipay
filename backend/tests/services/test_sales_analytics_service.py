"""Tests for SalesAnalyticsService using TDD approach."""

import pytest
from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4
from datetime import datetime, date

from app.services.sales_analytics_service import (
    SalesAnalyticsService,
    SalesSummary,
)
from app.models.product import Product


class TestSalesAnalyticsService:
    """Test cases for SalesAnalyticsService.

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
    def mock_product_repo(self):
        """Mock ProductRepository."""
        return Mock()

    @pytest.fixture
    def sales_analytics_service(
        self, mock_sales_history_repo, mock_product_repo
    ):
        """Create SalesAnalyticsService instance with mocked dependencies."""
        return SalesAnalyticsService(
            sales_history_repo=mock_sales_history_repo,
            product_repo=mock_product_repo,
        )

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()

    # Test 1: Get sales summary with total revenue
    def test_get_sales_summary_basic(
        self, sales_analytics_service, mock_sales_history_repo, mock_product_repo, mock_db
    ):
        """Test getting basic sales summary."""
        # Mock total sales
        mock_sales_history_repo.get_total_sales.return_value = Decimal("10000")

        # Mock daily sales
        mock_sales_history_repo.get_daily_sales.return_value = [
            (date(2025, 11, 6), Decimal("6000")),
            (date(2025, 11, 7), Decimal("4000")),
        ]

        # Mock products
        products = [
            Product(
                id=uuid4(),
                name="からあげ弁当",
                initial_stock=20,
                current_stock=5,
            ),
            Product(
                id=uuid4(),
                name="焼きそば",
                initial_stock=15,
                current_stock=0,
            ),
        ]
        mock_product_repo.get_all.return_value = products

        result = sales_analytics_service.get_sales_summary(mock_db)

        assert result.total_revenue == Decimal("10000")
        assert len(result.daily_revenue) == 2
        assert result.daily_revenue[0] == Decimal("6000")

    # Test 2: Calculate completion rate
    def test_get_sales_summary_completion_rate(
        self, sales_analytics_service, mock_sales_history_repo, mock_product_repo, mock_db
    ):
        """Test completion rate calculation.

        Scenario: 20 initial -> 5 remaining = 75% sold
                  15 initial -> 0 remaining = 100% sold
        Overall: (15 + 15) / (20 + 15) = 30/35 = 85.7%
        """
        mock_sales_history_repo.get_total_sales.return_value = Decimal("10000")
        mock_sales_history_repo.get_daily_sales.return_value = []

        products = [
            Product(
                id=uuid4(),
                name="からあげ弁当",
                initial_stock=20,
                current_stock=5,
            ),
            Product(
                id=uuid4(),
                name="焼きそば",
                initial_stock=15,
                current_stock=0,
            ),
        ]
        mock_product_repo.get_all.return_value = products

        result = sales_analytics_service.get_sales_summary(mock_db)

        # (20-5 + 15-0) / (20 + 15) = 30/35 = ~0.857
        assert abs(result.completion_rate - 0.857) < 0.01

    # Test 3: Completion rate with zero initial stock
    def test_get_sales_summary_zero_initial_stock(
        self, sales_analytics_service, mock_sales_history_repo, mock_product_repo, mock_db
    ):
        """Test completion rate when total initial stock is zero."""
        mock_sales_history_repo.get_total_sales.return_value = Decimal("0")
        mock_sales_history_repo.get_daily_sales.return_value = []

        products = [
            Product(
                id=uuid4(),
                name="セット商品",
                initial_stock=0,
                current_stock=0,
            ),
        ]
        mock_product_repo.get_all.return_value = products

        result = sales_analytics_service.get_sales_summary(mock_db)

        assert result.completion_rate == 0.0

    # Test 4: Daily revenue ordering
    def test_get_sales_summary_daily_revenue_order(
        self, sales_analytics_service, mock_sales_history_repo, mock_product_repo, mock_db
    ):
        """Test that daily revenue is ordered correctly."""
        mock_sales_history_repo.get_total_sales.return_value = Decimal("10000")
        mock_sales_history_repo.get_daily_sales.return_value = [
            (date(2025, 11, 7), Decimal("4000")),  # Day 2
            (date(2025, 11, 6), Decimal("6000")),  # Day 1
        ]
        mock_product_repo.get_all.return_value = []

        result = sales_analytics_service.get_sales_summary(mock_db)

        # Should be ordered by date desc (most recent first)
        assert result.daily_revenue[0] == Decimal("4000")
        assert result.daily_revenue[1] == Decimal("6000")

    # Test 5: Empty sales history
    def test_get_sales_summary_no_sales(
        self, sales_analytics_service, mock_sales_history_repo, mock_product_repo, mock_db
    ):
        """Test sales summary with no sales."""
        mock_sales_history_repo.get_total_sales.return_value = Decimal("0")
        mock_sales_history_repo.get_daily_sales.return_value = []
        mock_product_repo.get_all.return_value = []

        result = sales_analytics_service.get_sales_summary(mock_db)

        assert result.total_revenue == Decimal("0")
        assert len(result.daily_revenue) == 0
        assert result.completion_rate == 0.0

    # Test 6: All products sold out (100% completion)
    def test_get_sales_summary_complete_sellout(
        self, sales_analytics_service, mock_sales_history_repo, mock_product_repo, mock_db
    ):
        """Test completion rate when all products are sold out."""
        mock_sales_history_repo.get_total_sales.return_value = Decimal("10000")
        mock_sales_history_repo.get_daily_sales.return_value = []

        products = [
            Product(
                id=uuid4(),
                name="からあげ弁当",
                initial_stock=20,
                current_stock=0,
            ),
            Product(
                id=uuid4(),
                name="焼きそば",
                initial_stock=15,
                current_stock=0,
            ),
        ]
        mock_product_repo.get_all.return_value = products

        result = sales_analytics_service.get_sales_summary(mock_db)

        assert result.completion_rate == 1.0  # 100%
