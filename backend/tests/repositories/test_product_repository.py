"""Tests for ProductRepository."""

import pytest
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
import threading
import time

from app.models import Product
from app.repositories.product_repository import ProductRepository, InsufficientStockError


class TestProductRepository:
    """Test cases for ProductRepository."""

    def test_create_product(self, db_session):
        """Test creating a new product."""
        repo = ProductRepository()
        product = repo.create(
            name="からあげ弁当",
            unit_cost=Decimal("300.00"),
            sale_price=Decimal("500.00"),
            initial_stock=10,
            current_stock=10,
            product_type="single",
            db=db_session
        )

        assert product.id is not None
        assert product.name == "からあげ弁当"
        assert product.unit_cost == Decimal("300.00")
        assert product.sale_price == Decimal("500.00")
        assert product.initial_stock == 10
        assert product.current_stock == 10
        assert product.product_type == "single"

    def test_get_by_id(self, db_session):
        """Test retrieving a product by ID."""
        repo = ProductRepository()
        created = repo.create(
            name="test product",
            unit_cost=Decimal("100.00"),
            sale_price=Decimal("200.00"),
            initial_stock=5,
            current_stock=5,
            product_type="single",
            db=db_session
        )

        retrieved = repo.get_by_id(created.id, db=db_session)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == "test product"

    def test_get_by_id_not_found(self, db_session):
        """Test retrieving a non-existent product returns None."""
        repo = ProductRepository()
        import uuid
        result = repo.get_by_id(uuid.uuid4(), db=db_session)
        assert result is None

    def test_get_all(self, db_session):
        """Test retrieving all products."""
        repo = ProductRepository()
        repo.create(
            name="product1",
            unit_cost=Decimal("100.00"),
            sale_price=Decimal("200.00"),
            initial_stock=5,
            current_stock=5,
            product_type="single",
            db=db_session
        )
        repo.create(
            name="product2",
            unit_cost=Decimal("150.00"),
            sale_price=Decimal("250.00"),
            initial_stock=3,
            current_stock=3,
            product_type="set",
            db=db_session
        )

        products = repo.get_all(db=db_session)
        assert len(products) == 2

    def test_get_all_filter_by_type(self, db_session):
        """Test filtering products by type."""
        repo = ProductRepository()
        repo.create(
            name="single product",
            unit_cost=Decimal("100.00"),
            sale_price=Decimal("200.00"),
            initial_stock=5,
            current_stock=5,
            product_type="single",
            db=db_session
        )
        repo.create(
            name="set product",
            unit_cost=Decimal("150.00"),
            sale_price=Decimal("250.00"),
            initial_stock=3,
            current_stock=3,
            product_type="set",
            db=db_session
        )

        single_products = repo.get_all(product_type="single", db=db_session)
        assert len(single_products) == 1
        assert single_products[0].name == "single product"

    def test_update_product(self, db_session):
        """Test updating a product."""
        repo = ProductRepository()
        product = repo.create(
            name="original name",
            unit_cost=Decimal("100.00"),
            sale_price=Decimal("200.00"),
            initial_stock=5,
            current_stock=5,
            product_type="single",
            db=db_session
        )

        updated = repo.update(
            product.id,
            {"name": "updated name", "sale_price": Decimal("250.00")},
            db=db_session
        )

        assert updated.name == "updated name"
        assert updated.sale_price == Decimal("250.00")

    def test_delete_product(self, db_session):
        """Test deleting a product."""
        repo = ProductRepository()
        product = repo.create(
            name="to be deleted",
            unit_cost=Decimal("100.00"),
            sale_price=Decimal("200.00"),
            initial_stock=5,
            current_stock=5,
            product_type="single",
            db=db_session
        )

        repo.delete(product.id, db=db_session)
        assert repo.get_by_id(product.id, db=db_session) is None

    def test_decrement_stock_constraint(self, db_session):
        """Test that stock cannot go negative (CHECK constraint)."""
        repo = ProductRepository()
        product = repo.create(
            name="からあげ弁当",
            unit_cost=Decimal("300.00"),
            sale_price=Decimal("500.00"),
            initial_stock=5,
            current_stock=5,
            product_type="single",
            db=db_session
        )

        # Attempting to decrement more than available should raise error
        with pytest.raises(InsufficientStockError):
            repo.decrement_stock(product.id, 10, db=db_session)

    def test_concurrent_stock_decrement(self, db_session, postgres_container):
        """Test concurrent stock decrements with row locking."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        repo = ProductRepository()
        product = repo.create(
            name="test",
            unit_cost=Decimal("100.00"),
            sale_price=Decimal("200.00"),
            initial_stock=10,
            current_stock=10,
            product_type="single",
            db=db_session
        )
        db_session.commit()
        product_id = product.id

        # Create engine and session factory for threads
        engine = create_engine(postgres_container.get_connection_url())
        SessionLocal = sessionmaker(bind=engine)

        errors = []
        success_count = []

        def decrement():
            """Decrement stock in a separate thread with its own session."""
            thread_session = SessionLocal()
            try:
                repo.decrement_stock(product_id, 1, db=thread_session)
                thread_session.commit()
                success_count.append(1)
            except Exception as e:
                thread_session.rollback()
                errors.append(e)
            finally:
                thread_session.close()

        # Create 10 threads to decrement stock
        threads = [threading.Thread(target=decrement) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Check that stock is exactly 0 (no race condition)
        db_session.expire_all()  # Refresh session cache
        updated = repo.get_by_id(product_id, db=db_session)
        assert updated.current_stock == 0
        assert len(success_count) == 10
        assert len(errors) == 0
