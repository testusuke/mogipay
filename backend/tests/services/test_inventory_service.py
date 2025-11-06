"""Tests for InventoryService using TDD approach."""

import pytest
from decimal import Decimal
from unittest.mock import Mock, MagicMock
from uuid import uuid4

from app.services.inventory_service import (
    InventoryService,
    StockCheckResult,
    ProductInventory,
)
from app.models.product import Product
from app.models.set_item import SetItem


class TestInventoryService:
    """Test cases for InventoryService.

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
    def mock_set_item_repo(self):
        """Mock SetItemRepository."""
        return Mock()

    @pytest.fixture
    def inventory_service(self, mock_product_repo, mock_set_item_repo):
        """Create InventoryService instance with mocked dependencies."""
        return InventoryService(
            product_repo=mock_product_repo,
            set_item_repo=mock_set_item_repo,
        )

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()

    # Test 1: Calculate set stock - セット在庫を構成単品から計算
    def test_calculate_set_stock_basic(
        self, inventory_service, mock_product_repo, mock_set_item_repo, mock_db
    ):
        """Test basic set stock calculation from component items.

        Scenario: Set = {item1: 2, item2: 1}, item1 stock=10, item2 stock=5
        Expected: min(10/2, 5/1) = min(5, 5) = 5
        """
        set_product_id = uuid4()

        # Mock set items
        item1 = Product(
            id=uuid4(),
            name="からあげ",
            current_stock=10,
            product_type="single",
        )
        item2 = Product(
            id=uuid4(),
            name="ご飯",
            current_stock=5,
            product_type="single",
        )

        set_items = [
            SetItem(set_product_id=set_product_id, item_product_id=item1.id, quantity=2),
            SetItem(set_product_id=set_product_id, item_product_id=item2.id, quantity=1),
        ]

        mock_set_item_repo.get_by_set_product_id.return_value = set_items
        mock_product_repo.get_by_id.side_effect = [item1, item2]

        # Execute
        result = inventory_service.calculate_set_stock(set_product_id, mock_db)

        # Verify
        assert result == 5
        mock_set_item_repo.get_by_set_product_id.assert_called_once_with(
            set_product_id, mock_db
        )

    def test_calculate_set_stock_bottleneck(
        self, inventory_service, mock_product_repo, mock_set_item_repo, mock_db
    ):
        """Test set stock calculation with bottleneck item.

        Scenario: Set = {item1: 2, item2: 1}, item1 stock=3, item2 stock=10
        Expected: min(3/2, 10/1) = min(1, 10) = 1 (item1 is bottleneck)
        """
        set_product_id = uuid4()

        item1 = Product(id=uuid4(), current_stock=3, product_type="single")
        item2 = Product(id=uuid4(), current_stock=10, product_type="single")

        set_items = [
            SetItem(set_product_id=set_product_id, item_product_id=item1.id, quantity=2),
            SetItem(set_product_id=set_product_id, item_product_id=item2.id, quantity=1),
        ]

        mock_set_item_repo.get_by_set_product_id.return_value = set_items
        mock_product_repo.get_by_id.side_effect = [item1, item2]

        result = inventory_service.calculate_set_stock(set_product_id, mock_db)

        assert result == 1

    def test_calculate_set_stock_zero_stock(
        self, inventory_service, mock_product_repo, mock_set_item_repo, mock_db
    ):
        """Test set stock calculation when component item is out of stock.

        Scenario: Set = {item1: 2, item2: 1}, item1 stock=0, item2 stock=10
        Expected: min(0/2, 10/1) = 0
        """
        set_product_id = uuid4()

        item1 = Product(id=uuid4(), current_stock=0, product_type="single")
        item2 = Product(id=uuid4(), current_stock=10, product_type="single")

        set_items = [
            SetItem(set_product_id=set_product_id, item_product_id=item1.id, quantity=2),
            SetItem(set_product_id=set_product_id, item_product_id=item2.id, quantity=1),
        ]

        mock_set_item_repo.get_by_set_product_id.return_value = set_items
        mock_product_repo.get_by_id.side_effect = [item1, item2]

        result = inventory_service.calculate_set_stock(set_product_id, mock_db)

        assert result == 0

    # Test 2: Check stock availability - 在庫チェック
    def test_check_stock_availability_single_product_sufficient(
        self, inventory_service, mock_product_repo, mock_db
    ):
        """Test stock check for single product with sufficient stock."""
        product_id = uuid4()
        product = Product(
            id=product_id,
            name="からあげ弁当",
            current_stock=10,
            product_type="single",
        )

        mock_product_repo.get_by_id.return_value = product

        # Check if 5 units are available
        checkout_items = [{"product_id": product_id, "quantity": 5}]

        result = inventory_service.check_stock_availability(checkout_items, mock_db)

        assert result.is_available is True
        assert len(result.insufficient_items) == 0

    def test_check_stock_availability_single_product_insufficient(
        self, inventory_service, mock_product_repo, mock_db
    ):
        """Test stock check for single product with insufficient stock."""
        product_id = uuid4()
        product = Product(
            id=product_id,
            name="からあげ弁当",
            current_stock=3,
            product_type="single",
        )

        mock_product_repo.get_by_id.return_value = product

        # Check if 5 units are available (insufficient)
        checkout_items = [{"product_id": product_id, "quantity": 5}]

        result = inventory_service.check_stock_availability(checkout_items, mock_db)

        assert result.is_available is False
        assert product_id in result.insufficient_items

    def test_check_stock_availability_set_product(
        self, inventory_service, mock_product_repo, mock_set_item_repo, mock_db
    ):
        """Test stock check for set product."""
        set_product_id = uuid4()
        set_product = Product(
            id=set_product_id,
            name="からあげ弁当セット",
            product_type="set",
        )

        # Mock calculate_set_stock to return 5
        inventory_service.calculate_set_stock = Mock(return_value=5)
        mock_product_repo.get_by_id.return_value = set_product

        checkout_items = [{"product_id": set_product_id, "quantity": 3}]

        result = inventory_service.check_stock_availability(checkout_items, mock_db)

        assert result.is_available is True
        assert len(result.insufficient_items) == 0

    def test_check_stock_availability_multiple_items(
        self, inventory_service, mock_product_repo, mock_db
    ):
        """Test stock check for multiple items in cart."""
        product1_id = uuid4()
        product2_id = uuid4()

        product1 = Product(id=product1_id, current_stock=10, product_type="single")
        product2 = Product(id=product2_id, current_stock=3, product_type="single")

        mock_product_repo.get_by_id.side_effect = [product1, product2]

        checkout_items = [
            {"product_id": product1_id, "quantity": 5},
            {"product_id": product2_id, "quantity": 5},  # Insufficient
        ]

        result = inventory_service.check_stock_availability(checkout_items, mock_db)

        assert result.is_available is False
        assert product2_id in result.insufficient_items
        assert product1_id not in result.insufficient_items

    # Test 3: Get inventory status - 在庫状況取得
    def test_get_inventory_status_single_products(
        self, inventory_service, mock_product_repo, mock_db
    ):
        """Test inventory status retrieval for single products."""
        products = [
            Product(
                id=uuid4(),
                name="からあげ弁当",
                product_type="single",
                current_stock=10,
                initial_stock=20,
                unit_cost=Decimal("300"),
                sale_price=Decimal("500"),
            ),
            Product(
                id=uuid4(),
                name="焼きそば",
                product_type="single",
                current_stock=0,
                initial_stock=15,
                unit_cost=Decimal("200"),
                sale_price=Decimal("400"),
            ),
        ]

        mock_product_repo.get_all.return_value = products

        result = inventory_service.get_inventory_status(mock_db)

        assert len(result) == 2

        # First product
        assert result[0].name == "からあげ弁当"
        assert result[0].current_stock == 10
        assert result[0].initial_stock == 20
        assert result[0].stock_rate == 0.5  # 10/20
        assert result[0].is_out_of_stock is False

        # Second product (out of stock)
        assert result[1].name == "焼きそば"
        assert result[1].current_stock == 0
        assert result[1].is_out_of_stock is True

    def test_get_inventory_status_with_set_products(
        self, inventory_service, mock_product_repo, mock_set_item_repo, mock_db
    ):
        """Test inventory status retrieval including set products."""
        set_product = Product(
            id=uuid4(),
            name="からあげ弁当セット",
            product_type="set",
            current_stock=0,  # Set products don't track stock directly
            initial_stock=0,
            unit_cost=Decimal("500"),
            sale_price=Decimal("800"),
        )

        single_product = Product(
            id=uuid4(),
            name="からあげ",
            product_type="single",
            current_stock=20,
            initial_stock=30,
            unit_cost=Decimal("100"),
            sale_price=Decimal("150"),
        )

        mock_product_repo.get_all.return_value = [set_product, single_product]

        # Mock calculate_set_stock for set product
        inventory_service.calculate_set_stock = Mock(return_value=10)

        result = inventory_service.get_inventory_status(mock_db)

        assert len(result) == 2

        # Set product uses calculated stock
        set_result = next(r for r in result if r.product_type == "set")
        assert set_result.current_stock == 10
        assert set_result.name == "からあげ弁当セット"

        # Single product uses direct stock
        single_result = next(r for r in result if r.product_type == "single")
        assert single_result.current_stock == 20
        assert single_result.stock_rate == 20 / 30
