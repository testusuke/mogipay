"""Tests for SetItemRepository."""

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Product, SetItem
from app.repositories.set_item_repository import SetItemRepository
from app.repositories.product_repository import ProductRepository


class TestSetItemRepository:
    """Test cases for SetItemRepository."""

    def test_create_set_item(self, db_session):
        """Test creating a new set item."""
        # Create set product and item product first
        product_repo = ProductRepository()
        set_product = product_repo.create(
            name="Bento Set",
            unit_cost=500,
            sale_price=800,
            initial_stock=5,
            current_stock=5,
            product_type="set",
            db=db_session
        )
        item_product = product_repo.create(
            name="Karaage",
            unit_cost=100,
            sale_price=200,
            initial_stock=20,
            current_stock=20,
            product_type="single",
            db=db_session
        )

        # Create set item
        repo = SetItemRepository()
        set_item = repo.create(
            set_product_id=set_product.id,
            item_product_id=item_product.id,
            quantity=3,
            db=db_session
        )

        assert set_item.id is not None
        assert set_item.set_product_id == set_product.id
        assert set_item.item_product_id == item_product.id
        assert set_item.quantity == 3

    def test_get_by_set_product_id(self, db_session):
        """Test retrieving set items by set product ID."""
        # Create products
        product_repo = ProductRepository()
        set_product = product_repo.create(
            name="Bento Set",
            unit_cost=500,
            sale_price=800,
            initial_stock=5,
            current_stock=5,
            product_type="set",
            db=db_session
        )
        item1 = product_repo.create(
            name="Karaage",
            unit_cost=100,
            sale_price=200,
            initial_stock=20,
            current_stock=20,
            product_type="single",
            db=db_session
        )
        item2 = product_repo.create(
            name="Rice",
            unit_cost=50,
            sale_price=100,
            initial_stock=30,
            current_stock=30,
            product_type="single",
            db=db_session
        )

        # Create set items
        repo = SetItemRepository()
        repo.create(set_product.id, item1.id, 3, db=db_session)
        repo.create(set_product.id, item2.id, 1, db=db_session)

        # Retrieve set items
        set_items = repo.get_by_set_product_id(set_product.id, db=db_session)
        assert len(set_items) == 2

    def test_create_multiple_set_items_bulk(self, db_session):
        """Test creating multiple set items in bulk."""
        # Create products
        product_repo = ProductRepository()
        set_product = product_repo.create(
            name="Bento Set",
            unit_cost=500,
            sale_price=800,
            initial_stock=5,
            current_stock=5,
            product_type="set",
            db=db_session
        )
        item1 = product_repo.create(
            name="Karaage",
            unit_cost=100,
            sale_price=200,
            initial_stock=20,
            current_stock=20,
            product_type="single",
            db=db_session
        )
        item2 = product_repo.create(
            name="Rice",
            unit_cost=50,
            sale_price=100,
            initial_stock=30,
            current_stock=30,
            product_type="single",
            db=db_session
        )

        # Create bulk set items
        repo = SetItemRepository()
        items_data = [
            {"item_product_id": item1.id, "quantity": 3},
            {"item_product_id": item2.id, "quantity": 1},
        ]
        set_items = repo.create_bulk(set_product.id, items_data, db=db_session)

        assert len(set_items) == 2
        assert set_items[0].quantity == 3
        assert set_items[1].quantity == 1

    def test_delete_by_set_product_id(self, db_session):
        """Test deleting all set items for a set product."""
        # Create products
        product_repo = ProductRepository()
        set_product = product_repo.create(
            name="Bento Set",
            unit_cost=500,
            sale_price=800,
            initial_stock=5,
            current_stock=5,
            product_type="set",
            db=db_session
        )
        item1 = product_repo.create(
            name="Karaage",
            unit_cost=100,
            sale_price=200,
            initial_stock=20,
            current_stock=20,
            product_type="single",
            db=db_session
        )
        item2 = product_repo.create(
            name="Rice",
            unit_cost=50,
            sale_price=100,
            initial_stock=30,
            current_stock=30,
            product_type="single",
            db=db_session
        )

        # Create set items
        repo = SetItemRepository()
        repo.create(set_product.id, item1.id, 3, db=db_session)
        repo.create(set_product.id, item2.id, 1, db=db_session)

        # Delete all set items
        deleted_count = repo.delete_by_set_product_id(set_product.id, db=db_session)
        assert deleted_count == 2

        # Verify deletion
        set_items = repo.get_by_set_product_id(set_product.id, db=db_session)
        assert len(set_items) == 0

    def test_cascade_delete_on_set_product_deletion(self, db_session):
        """Test that set items are automatically deleted when set product is deleted."""
        # Create products
        product_repo = ProductRepository()
        set_product = product_repo.create(
            name="Bento Set",
            unit_cost=500,
            sale_price=800,
            initial_stock=5,
            current_stock=5,
            product_type="set",
            db=db_session
        )
        item_product = product_repo.create(
            name="Karaage",
            unit_cost=100,
            sale_price=200,
            initial_stock=20,
            current_stock=20,
            product_type="single",
            db=db_session
        )

        # Create set item
        repo = SetItemRepository()
        set_item = repo.create(
            set_product_id=set_product.id,
            item_product_id=item_product.id,
            quantity=3,
            db=db_session
        )
        set_item_id = set_item.id

        # Delete set product
        product_repo.delete(set_product.id, db=db_session)

        # Verify set item is automatically deleted (CASCADE)
        set_items = repo.get_by_set_product_id(set_product.id, db=db_session)
        assert len(set_items) == 0

    def test_unique_constraint_violation(self, db_session):
        """Test that duplicate set-item combinations are rejected."""
        # Create products
        product_repo = ProductRepository()
        set_product = product_repo.create(
            name="Bento Set",
            unit_cost=500,
            sale_price=800,
            initial_stock=5,
            current_stock=5,
            product_type="set",
            db=db_session
        )
        item_product = product_repo.create(
            name="Karaage",
            unit_cost=100,
            sale_price=200,
            initial_stock=20,
            current_stock=20,
            product_type="single",
            db=db_session
        )

        # Create first set item
        repo = SetItemRepository()
        repo.create(set_product.id, item_product.id, 3, db=db_session)

        # Attempt to create duplicate set-item combination
        with pytest.raises(IntegrityError):
            repo.create(set_product.id, item_product.id, 5, db=db_session)
