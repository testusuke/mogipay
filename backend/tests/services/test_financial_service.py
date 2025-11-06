"""Tests for FinancialService using TDD approach."""

import pytest

from unittest.mock import Mock
from uuid import uuid4

from app.services.financial_service import (
    FinancialService,
    FinancialSummary,
)
from app.models.product import Product


class TestFinancialService:
    """Test cases for FinancialService.

    Following TDD approach:
    1. RED: Write failing tests first
    2. GREEN: Implement minimal code to pass
    3. REFACTOR: Improve code quality
    """

    @pytest.fixture
    def mock_product_repo(self):
        """Mock ProductRepository."""
        return Mock()

    @pytest.fixture
    def mock_sales_history_repo(self):
        """Mock SalesHistoryRepository."""
        return Mock()

    @pytest.fixture
    def financial_service(self, mock_product_repo, mock_sales_history_repo):
        """Create FinancialService instance with mocked dependencies."""
        return FinancialService(
            product_repo=mock_product_repo,
            sales_history_repo=mock_sales_history_repo,
        )

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()

    # Test 1: Basic financial summary
    def test_get_financial_summary_basic(
        self, financial_service, mock_product_repo, mock_sales_history_repo, mock_db
    ):
        """Test basic financial summary calculation.

        Scenario:
        - Product 1: 20 units @ 300 yen = 6000 yen cost
        - Product 2: 15 units @ 200 yen = 3000 yen cost
        Total cost: 9000 yen
        Total revenue: 12000 yen
        Profit: 3000 yen
        """
        products = [
            Product(
                id=uuid4(),
                name="からあげ弁当",
                unit_cost=300,
                initial_stock=20,
            ),
            Product(
                id=uuid4(),
                name="焼きそば",
                unit_cost=200,
                initial_stock=15,
            ),
        ]

        mock_product_repo.get_all.return_value = products
        mock_sales_history_repo.get_total_sales.return_value = 12000

        result = financial_service.get_financial_summary(mock_db)

        assert result.total_cost == 9000
        assert result.total_revenue == 12000
        assert result.profit == 3000
        assert result.break_even_achieved is True

    # Test 2: Break-even not achieved
    def test_get_financial_summary_not_break_even(
        self, financial_service, mock_product_repo, mock_sales_history_repo, mock_db
    ):
        """Test financial summary when break-even is not achieved."""
        products = [
            Product(
                id=uuid4(),
                name="からあげ弁当",
                unit_cost=300,
                initial_stock=20,
            ),
        ]

        mock_product_repo.get_all.return_value = products
        mock_sales_history_repo.get_total_sales.return_value = 5000

        result = financial_service.get_financial_summary(mock_db)

        assert result.total_cost == 6000
        assert result.total_revenue == 5000
        assert result.profit == -1000
        assert result.break_even_achieved is False

    # Test 3: Exactly break-even
    def test_get_financial_summary_exact_break_even(
        self, financial_service, mock_product_repo, mock_sales_history_repo, mock_db
    ):
        """Test financial summary at exact break-even point."""
        products = [
            Product(
                id=uuid4(),
                name="からあげ弁当",
                unit_cost=300,
                initial_stock=20,
            ),
        ]

        mock_product_repo.get_all.return_value = products
        mock_sales_history_repo.get_total_sales.return_value = 6000

        result = financial_service.get_financial_summary(mock_db)

        assert result.total_cost == 6000
        assert result.total_revenue == 6000
        assert result.profit == 0
        assert result.break_even_achieved is True

    # Test 4: Profit rate calculation
    def test_get_financial_summary_profit_rate(
        self, financial_service, mock_product_repo, mock_sales_history_repo, mock_db
    ):
        """Test profit rate calculation.

        Scenario:
        Cost: 10000, Revenue: 15000
        Profit: 5000
        Profit rate: 5000/15000 = 0.333... (33.3%)
        """
        products = [
            Product(
                id=uuid4(),
                name="test",
                unit_cost=500,
                initial_stock=20,
            ),
        ]

        mock_product_repo.get_all.return_value = products
        mock_sales_history_repo.get_total_sales.return_value = 15000

        result = financial_service.get_financial_summary(mock_db)

        # Profit rate = 5000/15000 = 0.333...
        assert abs(result.profit_rate - 0.333) < 0.01

    # Test 5: Zero revenue (no sales)
    def test_get_financial_summary_zero_revenue(
        self, financial_service, mock_product_repo, mock_sales_history_repo, mock_db
    ):
        """Test financial summary with no sales."""
        products = [
            Product(
                id=uuid4(),
                name="からあげ弁当",
                unit_cost=300,
                initial_stock=20,
            ),
        ]

        mock_product_repo.get_all.return_value = products
        mock_sales_history_repo.get_total_sales.return_value = 0

        result = financial_service.get_financial_summary(mock_db)

        assert result.total_cost == 6000
        assert result.total_revenue == 0
        assert result.profit == -6000
        assert result.profit_rate == 0.0  # Avoid division by zero
        assert result.break_even_achieved is False

    # Test 6: Multiple products with different costs
    def test_get_financial_summary_multiple_products(
        self, financial_service, mock_product_repo, mock_sales_history_repo, mock_db
    ):
        """Test financial summary with multiple products."""
        products = [
            Product(
                id=uuid4(),
                name="からあげ弁当",
                unit_cost=300,
                initial_stock=20,
            ),
            Product(
                id=uuid4(),
                name="焼きそば",
                unit_cost=200,
                initial_stock=15,
            ),
            Product(
                id=uuid4(),
                name="セット",
                unit_cost=500,
                initial_stock=10,
            ),
        ]

        mock_product_repo.get_all.return_value = products
        mock_sales_history_repo.get_total_sales.return_value = 20000

        result = financial_service.get_financial_summary(mock_db)

        # Total cost = 20*300 + 15*200 + 10*500 = 6000 + 3000 + 5000 = 14000
        assert result.total_cost == 14000
        assert result.total_revenue == 20000
        assert result.profit == 6000
        assert result.break_even_achieved is True

    # Test 7: Empty products list
    def test_get_financial_summary_no_products(
        self, financial_service, mock_product_repo, mock_sales_history_repo, mock_db
    ):
        """Test financial summary with no products."""
        mock_product_repo.get_all.return_value = []
        mock_sales_history_repo.get_total_sales.return_value = 0

        result = financial_service.get_financial_summary(mock_db)

        assert result.total_cost == 0
        assert result.total_revenue == 0
        assert result.profit == 0
        assert result.profit_rate == 0.0
        assert result.break_even_achieved is True  # 0 >= 0
