"""Tests for SalesService using TDD approach."""

import pytest
from decimal import Decimal
from unittest.mock import Mock, MagicMock, call
from uuid import uuid4
from datetime import datetime

from app.services.sales_service import (
    SalesService,
    CheckoutResult,
    CheckoutItem,
)
from app.services.inventory_service import StockCheckResult
from app.models.product import Product
from app.models.set_item import SetItem
from app.exceptions import InsufficientStockError


class TestSalesService:
    """Test cases for SalesService.

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
    def mock_inventory_service(self):
        """Mock InventoryService."""
        return Mock()

    @pytest.fixture
    def mock_set_item_repo(self):
        """Mock SetItemRepository."""
        return Mock()

    @pytest.fixture
    def sales_service(
        self,
        mock_product_repo,
        mock_sales_history_repo,
        mock_inventory_service,
        mock_set_item_repo,
    ):
        """Create SalesService instance with mocked dependencies."""
        return SalesService(
            product_repo=mock_product_repo,
            sales_history_repo=mock_sales_history_repo,
            inventory_service=mock_inventory_service,
            set_item_repo=mock_set_item_repo,
        )

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        db = Mock()
        db.begin = Mock()
        db.commit = Mock()
        db.rollback = Mock()
        return db

    # Test 1: Successful checkout for single product
    def test_process_checkout_single_product_success(
        self, sales_service, mock_product_repo, mock_inventory_service, mock_sales_history_repo, mock_db
    ):
        """Test successful checkout for single product.

        Scenario: Customer buys 2 units of からあげ弁当 (500 yen each)
        Expected: Total 1000 yen, stock decremented by 2
        """
        product_id = uuid4()
        product = Product(
            id=product_id,
            name="からあげ弁当",
            unit_cost=Decimal("300"),
            sale_price=Decimal("500"),
            current_stock=10,
            product_type="single",
        )

        checkout_items = [CheckoutItem(product_id=product_id, quantity=2)]

        # Mock dependencies
        mock_product_repo.get_by_id.return_value = product
        mock_inventory_service.check_stock_availability.return_value = StockCheckResult(
            is_available=True,
            insufficient_items=[],
        )
        mock_sales_history_repo.create_sale.return_value = Mock(
            id=uuid4(),
            total_amount=Decimal("1000"),
            timestamp=datetime.now(),
        )

        # Execute
        result = sales_service.process_checkout(checkout_items, mock_db)

        # Verify
        assert result.total_amount == Decimal("1000")
        mock_product_repo.decrement_stock.assert_called_once_with(product_id, 2, mock_db)
        mock_sales_history_repo.create_sale.assert_called_once()

    # Test 2: Insufficient stock error
    def test_process_checkout_insufficient_stock(
        self, sales_service, mock_product_repo, mock_inventory_service, mock_db
    ):
        """Test checkout with insufficient stock.

        Scenario: Customer requests 5 units but only 3 available
        Expected: InsufficientStockError raised
        """
        product_id = uuid4()
        product = Product(
            id=product_id,
            name="test product",
            unit_cost=Decimal("100"),
            sale_price=Decimal("200"),
            current_stock=3,  # Only 3 available
            product_type="single",
        )

        checkout_items = [CheckoutItem(product_id=product_id, quantity=5)]

        # Mock product repository
        mock_product_repo.get_by_id.return_value = product
        mock_inventory_service.check_stock_availability.return_value = StockCheckResult(
            is_available=False,
            insufficient_items=[product_id],
        )

        # Execute and verify exception
        with pytest.raises(InsufficientStockError) as exc_info:
            sales_service.process_checkout(checkout_items, mock_db)

        assert str(product_id) in str(exc_info.value)

    # Test 3: Set product checkout
    def test_process_checkout_set_product(
        self,
        sales_service,
        mock_product_repo,
        mock_set_item_repo,
        mock_inventory_service,
        mock_sales_history_repo,
        mock_db,
    ):
        """Test checkout for set product.

        Scenario: Customer buys 1 set (からあげ×2 + ご飯×1)
        Expected: Component items' stock decremented correctly
        """
        set_product_id = uuid4()
        item1_id = uuid4()
        item2_id = uuid4()

        set_product = Product(
            id=set_product_id,
            name="からあげ弁当セット",
            unit_cost=Decimal("500"),
            sale_price=Decimal("800"),
            product_type="set",
        )

        item1 = Product(
            id=item1_id,
            name="からあげ",
            unit_cost=Decimal("100"),
            sale_price=Decimal("150"),
            current_stock=20,
            product_type="single",
        )

        item2 = Product(
            id=item2_id,
            name="ご飯",
            unit_cost=Decimal("50"),
            sale_price=Decimal("100"),
            current_stock=30,
            product_type="single",
        )

        set_items = [
            SetItem(set_product_id=set_product_id, item_product_id=item1_id, quantity=2),
            SetItem(set_product_id=set_product_id, item_product_id=item2_id, quantity=1),
        ]

        checkout_items = [CheckoutItem(product_id=set_product_id, quantity=1)]

        # Mock dependencies
        mock_product_repo.get_by_id.side_effect = [set_product, item1, item2]
        mock_set_item_repo.get_by_set_product_id.return_value = set_items
        mock_inventory_service.check_stock_availability.return_value = StockCheckResult(
            is_available=True,
            insufficient_items=[],
        )
        mock_sales_history_repo.create_sale.return_value = Mock(
            id=uuid4(),
            total_amount=Decimal("800"),
            timestamp=datetime.now(),
        )

        # Execute
        result = sales_service.process_checkout(checkout_items, mock_db)

        # Verify component items' stock was decremented
        assert mock_product_repo.decrement_stock.call_count == 2
        mock_product_repo.decrement_stock.assert_any_call(item1_id, 2, mock_db)
        mock_product_repo.decrement_stock.assert_any_call(item2_id, 1, mock_db)

    # Test 4: Multiple items checkout
    def test_process_checkout_multiple_items(
        self,
        sales_service,
        mock_product_repo,
        mock_inventory_service,
        mock_sales_history_repo,
        mock_db,
    ):
        """Test checkout with multiple different products."""
        product1_id = uuid4()
        product2_id = uuid4()

        product1 = Product(
            id=product1_id,
            name="からあげ弁当",
            unit_cost=Decimal("300"),
            sale_price=Decimal("500"),
            current_stock=10,
            product_type="single",
        )

        product2 = Product(
            id=product2_id,
            name="焼きそば",
            unit_cost=Decimal("200"),
            sale_price=Decimal("400"),
            current_stock=5,
            product_type="single",
        )

        checkout_items = [
            CheckoutItem(product_id=product1_id, quantity=2),
            CheckoutItem(product_id=product2_id, quantity=1),
        ]

        mock_product_repo.get_by_id.side_effect = [product1, product2]
        mock_inventory_service.check_stock_availability.return_value = StockCheckResult(
            is_available=True,
            insufficient_items=[],
        )
        mock_sales_history_repo.create_sale.return_value = Mock(
            id=uuid4(),
            total_amount=Decimal("1400"),  # 500*2 + 400*1
            timestamp=datetime.now(),
        )

        result = sales_service.process_checkout(checkout_items, mock_db)

        assert result.total_amount == Decimal("1400")
        assert mock_product_repo.decrement_stock.call_count == 2

    # Test 5: Product not found error
    def test_process_checkout_product_not_found(
        self, sales_service, mock_product_repo, mock_db
    ):
        """Test checkout with non-existent product."""
        product_id = uuid4()
        checkout_items = [CheckoutItem(product_id=product_id, quantity=1)]

        mock_product_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc_info:
            sales_service.process_checkout(checkout_items, mock_db)

        assert "not found" in str(exc_info.value).lower()

    # Test 6: Transaction rollback on error
    def test_process_checkout_rollback_on_error(
        self,
        sales_service,
        mock_product_repo,
        mock_inventory_service,
        mock_sales_history_repo,
        mock_db,
    ):
        """Test that transaction is rolled back on error."""
        product_id = uuid4()
        product = Product(
            id=product_id,
            name="test",
            unit_cost=Decimal("100"),
            sale_price=Decimal("200"),
            current_stock=10,
            product_type="single",
        )

        checkout_items = [CheckoutItem(product_id=product_id, quantity=1)]

        mock_product_repo.get_by_id.return_value = product
        mock_inventory_service.check_stock_availability.return_value = StockCheckResult(
            is_available=True,
            insufficient_items=[],
        )

        # Simulate error during transaction creation
        mock_sales_history_repo.create_sale.side_effect = Exception("Database error")

        with pytest.raises(Exception):
            sales_service.process_checkout(checkout_items, mock_db)

        # Verify rollback was called
        mock_db.rollback.assert_called_once()

    # Test 7: Price snapshot in sales history
    def test_process_checkout_price_snapshot(
        self,
        sales_service,
        mock_product_repo,
        mock_inventory_service,
        mock_sales_history_repo,
        mock_db,
    ):
        """Test that current prices are captured in sales history."""
        product_id = uuid4()
        product = Product(
            id=product_id,
            name="からあげ弁当",
            unit_cost=Decimal("300"),
            sale_price=Decimal("500"),
            current_stock=10,
            product_type="single",
        )

        checkout_items = [CheckoutItem(product_id=product_id, quantity=2)]

        mock_product_repo.get_by_id.return_value = product
        mock_inventory_service.check_stock_availability.return_value = StockCheckResult(
            is_available=True,
            insufficient_items=[],
        )
        mock_sales_history_repo.create_sale.return_value = Mock(
            id=uuid4(),
            total_amount=Decimal("1000"),
            timestamp=datetime.now(),
        )

        sales_service.process_checkout(checkout_items, mock_db)

        # Verify create_sale was called with correct price snapshot
        call_args = mock_sales_history_repo.create_sale.call_args
        # Check keyword arguments
        items_arg = call_args.kwargs["sale_items_data"]

        assert len(items_arg) == 1
        assert items_arg[0]["product_name"] == "からあげ弁当"
        assert items_arg[0]["unit_cost"] == Decimal("300")
        assert items_arg[0]["sale_price"] == Decimal("500")
        assert items_arg[0]["quantity"] == 2
        assert items_arg[0]["subtotal"] == Decimal("1000")
