"""Tests for ProductService using TDD approach."""

import pytest
from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4

from app.services.product_service import (
    ProductService,
    CreateProductData,
    SetItemData,
)
from app.models.product import Product
from app.models.set_item import SetItem


class TestProductService:
    """Test cases for ProductService.

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
    def product_service(self, mock_product_repo, mock_set_item_repo):
        """Create ProductService instance with mocked dependencies."""
        return ProductService(
            product_repo=mock_product_repo,
            set_item_repo=mock_set_item_repo,
        )

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()

    # Test 1: Create single product
    def test_create_single_product(
        self, product_service, mock_product_repo, mock_db
    ):
        """Test creating a single product."""
        product_data = CreateProductData(
            name="からあげ弁当",
            unit_cost=Decimal("300"),
            sale_price=Decimal("500"),
            initial_stock=20,
            product_type="single",
            set_items=None,
        )

        created_product = Product(
            id=uuid4(),
            name="からあげ弁当",
            unit_cost=Decimal("300"),
            sale_price=Decimal("500"),
            initial_stock=20,
            current_stock=20,
            product_type="single",
        )

        mock_product_repo.create.return_value = created_product

        result = product_service.create_product(product_data, mock_db)

        assert result.name == "からあげ弁当"
        assert result.product_type == "single"
        mock_product_repo.create.assert_called_once()

    # Test 2: Create set product with set items
    def test_create_set_product(
        self, product_service, mock_product_repo, mock_set_item_repo, mock_db
    ):
        """Test creating a set product with component items."""
        item1_id = uuid4()
        item2_id = uuid4()

        product_data = CreateProductData(
            name="からあげ弁当セット",
            unit_cost=Decimal("500"),
            sale_price=Decimal("800"),
            initial_stock=0,
            product_type="set",
            set_items=[
                SetItemData(product_id=item1_id, quantity=2),
                SetItemData(product_id=item2_id, quantity=1),
            ],
        )

        created_product = Product(
            id=uuid4(),
            name="からあげ弁当セット",
            unit_cost=Decimal("500"),
            sale_price=Decimal("800"),
            initial_stock=0,
            current_stock=0,
            product_type="set",
        )

        mock_product_repo.create.return_value = created_product
        mock_set_item_repo.create_bulk.return_value = []

        result = product_service.create_product(product_data, mock_db)

        assert result.product_type == "set"
        mock_product_repo.create.assert_called_once()
        mock_set_item_repo.create_bulk.assert_called_once()

    # Test 3: Validate set product must have set_items
    def test_create_set_product_without_set_items_error(
        self, product_service, mock_db
    ):
        """Test that set product without set_items raises error."""
        product_data = CreateProductData(
            name="からあげ弁当セット",
            unit_cost=Decimal("500"),
            sale_price=Decimal("800"),
            initial_stock=0,
            product_type="set",
            set_items=None,  # Missing set items
        )

        with pytest.raises(ValueError) as exc_info:
            product_service.create_product(product_data, mock_db)

        assert "set_items" in str(exc_info.value).lower()

    # Test 4: Update product price
    def test_update_price(
        self, product_service, mock_product_repo, mock_db
    ):
        """Test updating product price.

        Scenario: Change price from 500 to 600
        Expected: Product updated with new price
        """
        product_id = uuid4()
        original_product = Product(
            id=product_id,
            name="からあげ弁当",
            sale_price=Decimal("500"),
            unit_cost=Decimal("300"),
        )

        updated_product = Product(
            id=product_id,
            name="からあげ弁当",
            sale_price=Decimal("600"),
            unit_cost=Decimal("300"),
        )

        mock_product_repo.get_by_id.return_value = original_product
        mock_product_repo.update.return_value = updated_product

        result = product_service.update_price(
            product_id, Decimal("600"), mock_db
        )

        assert result.sale_price == Decimal("600")
        mock_product_repo.update.assert_called_once_with(
            product_id, {"sale_price": Decimal("600")}, mock_db
        )

    # Test 5: Update price for non-existent product
    def test_update_price_product_not_found(
        self, product_service, mock_product_repo, mock_db
    ):
        """Test updating price for non-existent product."""
        product_id = uuid4()
        mock_product_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc_info:
            product_service.update_price(product_id, Decimal("600"), mock_db)

        assert "not found" in str(exc_info.value).lower()

    # Test 6: Get product by ID
    def test_get_product_by_id(
        self, product_service, mock_product_repo, mock_db
    ):
        """Test retrieving product by ID."""
        product_id = uuid4()
        product = Product(
            id=product_id,
            name="からあげ弁当",
            sale_price=Decimal("500"),
            product_type="single",
        )

        mock_product_repo.get_by_id.return_value = product

        result = product_service.get_product_by_id(product_id, mock_db)

        assert result.id == product_id
        assert result.name == "からあげ弁当"

    # Test 7: Get all products
    def test_get_all_products(
        self, product_service, mock_product_repo, mock_db
    ):
        """Test retrieving all products."""
        products = [
            Product(id=uuid4(), name="からあげ弁当", product_type="single"),
            Product(id=uuid4(), name="焼きそば", product_type="single"),
        ]

        mock_product_repo.get_all.return_value = products

        result = product_service.get_all_products(mock_db)

        assert len(result) == 2
        mock_product_repo.get_all.assert_called_once()

    # Test 8: Get products filtered by type
    def test_get_products_by_type(
        self, product_service, mock_product_repo, mock_db
    ):
        """Test retrieving products filtered by type."""
        single_products = [
            Product(id=uuid4(), name="からあげ弁当", product_type="single"),
        ]

        mock_product_repo.get_all.return_value = single_products

        result = product_service.get_all_products(mock_db, product_type="single")

        assert len(result) == 1
        assert result[0].product_type == "single"
        mock_product_repo.get_all.assert_called_with(product_type="single", db=mock_db)

    # Test 9: Update product
    def test_update_product(
        self, product_service, mock_product_repo, mock_db
    ):
        """Test updating product attributes."""
        product_id = uuid4()
        updates = {
            "name": "新からあげ弁当",
            "sale_price": Decimal("550"),
        }

        original_product = Product(
            id=product_id,
            name="からあげ弁当",
            sale_price=Decimal("500"),
        )

        updated_product = Product(
            id=product_id,
            name="新からあげ弁当",
            sale_price=Decimal("550"),
        )

        mock_product_repo.get_by_id.return_value = original_product
        mock_product_repo.update.return_value = updated_product

        result = product_service.update_product(product_id, updates, mock_db)

        assert result.name == "新からあげ弁当"
        assert result.sale_price == Decimal("550")
        mock_product_repo.update.assert_called_once_with(product_id, updates, mock_db)

    # Test 10: Delete product
    def test_delete_product(
        self, product_service, mock_product_repo, mock_db
    ):
        """Test deleting a product."""
        product_id = uuid4()
        mock_product_repo.delete.return_value = True

        result = product_service.delete_product(product_id, mock_db)

        assert result is True
        mock_product_repo.delete.assert_called_once_with(product_id, mock_db)

    # Test 11: Delete non-existent product
    def test_delete_nonexistent_product(
        self, product_service, mock_product_repo, mock_db
    ):
        """Test deleting a non-existent product."""
        product_id = uuid4()
        mock_product_repo.delete.return_value = False

        result = product_service.delete_product(product_id, mock_db)

        assert result is False
