"""Tests for SalesHistoryRepository."""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta, UTC

from app.models import Product, SalesHistory, SaleItem
from app.repositories.sales_history_repository import SalesHistoryRepository
from app.repositories.product_repository import ProductRepository


class TestSalesHistoryRepository:
    """Test cases for SalesHistoryRepository."""

    def test_create_sales_transaction(self, db_session):
        """Test creating a sales transaction with sale items."""
        # Create product
        product_repo = ProductRepository()
        product = product_repo.create(
            name="Karaage Bento",
            unit_cost=Decimal("300.00"),
            sale_price=Decimal("500.00"),
            initial_stock=10,
            current_stock=10,
            product_type="single",
            db=db_session
        )

        # Create sales transaction
        repo = SalesHistoryRepository()
        sale_items_data = [
            {
                "product_id": product.id,
                "product_name": product.name,
                "quantity": 2,
                "unit_cost": product.unit_cost,
                "sale_price": product.sale_price,
                "subtotal": product.sale_price * 2
            }
        ]
        sales = repo.create_sale(
            total_amount=Decimal("1000.00"),
            sale_items_data=sale_items_data,
            db=db_session
        )

        assert sales.id is not None
        assert sales.total_amount == Decimal("1000.00")
        assert sales.timestamp is not None
        assert len(sales.sale_items) == 1
        assert sales.sale_items[0].product_name == "Karaage Bento"
        assert sales.sale_items[0].quantity == 2
        assert sales.sale_items[0].subtotal == Decimal("1000.00")

    def test_get_by_id(self, db_session):
        """Test retrieving a sales transaction by ID."""
        # Create product and sales
        product_repo = ProductRepository()
        product = product_repo.create(
            name="Test Product",
            unit_cost=Decimal("100.00"),
            sale_price=Decimal("200.00"),
            initial_stock=10,
            current_stock=10,
            product_type="single",
            db=db_session
        )

        repo = SalesHistoryRepository()
        sale_items_data = [
            {
                "product_id": product.id,
                "product_name": product.name,
                "quantity": 1,
                "unit_cost": product.unit_cost,
                "sale_price": product.sale_price,
                "subtotal": product.sale_price
            }
        ]
        created = repo.create_sale(
            total_amount=Decimal("200.00"),
            sale_items_data=sale_items_data,
            db=db_session
        )

        # Retrieve sales
        retrieved = repo.get_by_id(created.id, db=db_session)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.total_amount == Decimal("200.00")
        assert len(retrieved.sale_items) == 1

    def test_get_by_date_range(self, db_session):
        """Test retrieving sales transactions by date range."""
        # Create product
        product_repo = ProductRepository()
        product = product_repo.create(
            name="Test Product",
            unit_cost=Decimal("100.00"),
            sale_price=Decimal("200.00"),
            initial_stock=10,
            current_stock=10,
            product_type="single",
            db=db_session
        )

        repo = SalesHistoryRepository()
        sale_items_data = [
            {
                "product_id": product.id,
                "product_name": product.name,
                "quantity": 1,
                "unit_cost": product.unit_cost,
                "sale_price": product.sale_price,
                "subtotal": product.sale_price
            }
        ]

        # Create multiple sales
        repo.create_sale(Decimal("200.00"), sale_items_data, db=db_session)
        repo.create_sale(Decimal("300.00"), sale_items_data, db=db_session)
        repo.create_sale(Decimal("400.00"), sale_items_data, db=db_session)

        # Get sales by date range
        now = datetime.now(UTC)
        start_date = now - timedelta(days=1)
        end_date = now + timedelta(days=1)

        sales = repo.get_by_date_range(start_date, end_date, db=db_session)
        assert len(sales) == 3

    def test_get_total_sales(self, db_session):
        """Test calculating total sales amount."""
        # Create product
        product_repo = ProductRepository()
        product = product_repo.create(
            name="Test Product",
            unit_cost=Decimal("100.00"),
            sale_price=Decimal("200.00"),
            initial_stock=10,
            current_stock=10,
            product_type="single",
            db=db_session
        )

        repo = SalesHistoryRepository()
        sale_items_data = [
            {
                "product_id": product.id,
                "product_name": product.name,
                "quantity": 1,
                "unit_cost": product.unit_cost,
                "sale_price": product.sale_price,
                "subtotal": product.sale_price
            }
        ]

        # Create sales
        repo.create_sale(Decimal("200.00"), sale_items_data, db=db_session)
        repo.create_sale(Decimal("300.00"), sale_items_data, db=db_session)

        # Get total sales
        total = repo.get_total_sales(db=db_session)
        assert total == Decimal("500.00")

    def test_get_daily_sales(self, db_session):
        """Test getting daily sales summary."""
        # Create product
        product_repo = ProductRepository()
        product = product_repo.create(
            name="Test Product",
            unit_cost=Decimal("100.00"),
            sale_price=Decimal("200.00"),
            initial_stock=10,
            current_stock=10,
            product_type="single",
            db=db_session
        )

        repo = SalesHistoryRepository()
        sale_items_data = [
            {
                "product_id": product.id,
                "product_name": product.name,
                "quantity": 1,
                "unit_cost": product.unit_cost,
                "sale_price": product.sale_price,
                "subtotal": product.sale_price
            }
        ]

        # Create sales
        repo.create_sale(Decimal("200.00"), sale_items_data, db=db_session)
        repo.create_sale(Decimal("300.00"), sale_items_data, db=db_session)

        # Get daily sales
        daily_sales = repo.get_daily_sales(db=db_session)
        assert len(daily_sales) >= 1
        today = datetime.now(UTC).date()
        for date, amount in daily_sales:
            if date == today:
                assert amount == Decimal("500.00")

    def test_price_snapshot_immutability(self, db_session):
        """Test that price changes don't affect past sales records."""
        # Create product
        product_repo = ProductRepository()
        product = product_repo.create(
            name="Test Product",
            unit_cost=Decimal("100.00"),
            sale_price=Decimal("200.00"),
            initial_stock=10,
            current_stock=10,
            product_type="single",
            db=db_session
        )

        # Create sales with original price
        repo = SalesHistoryRepository()
        sale_items_data = [
            {
                "product_id": product.id,
                "product_name": product.name,
                "quantity": 1,
                "unit_cost": product.unit_cost,
                "sale_price": product.sale_price,
                "subtotal": product.sale_price
            }
        ]
        original_sale = repo.create_sale(
            Decimal("200.00"),
            sale_items_data,
            db=db_session
        )
        original_sale_id = original_sale.id

        # Change product price
        product_repo.update(
            product.id,
            {"sale_price": Decimal("300.00")},
            db=db_session
        )

        # Verify original sale still has old price
        retrieved_sale = repo.get_by_id(original_sale_id, db=db_session)
        assert retrieved_sale.sale_items[0].sale_price == Decimal("200.00")
        assert retrieved_sale.total_amount == Decimal("200.00")

    def test_cascade_delete_sale_items(self, db_session):
        """Test that sale items are deleted when sales history is deleted."""
        # Create product and sales
        product_repo = ProductRepository()
        product = product_repo.create(
            name="Test Product",
            unit_cost=Decimal("100.00"),
            sale_price=Decimal("200.00"),
            initial_stock=10,
            current_stock=10,
            product_type="single",
            db=db_session
        )

        repo = SalesHistoryRepository()
        sale_items_data = [
            {
                "product_id": product.id,
                "product_name": product.name,
                "quantity": 1,
                "unit_cost": product.unit_cost,
                "sale_price": product.sale_price,
                "subtotal": product.sale_price
            }
        ]
        sales = repo.create_sale(
            Decimal("200.00"),
            sale_items_data,
            db=db_session
        )

        # Verify sale items exist
        assert len(sales.sale_items) == 1
        sale_item_id = sales.sale_items[0].id

        # Delete sales history (would be done indirectly in real code)
        db_session.delete(sales)
        db_session.commit()

        # Verify sale items are cascade deleted
        from sqlalchemy import select
        stmt = select(SaleItem).where(SaleItem.id == sale_item_id)
        result = db_session.execute(stmt)
        assert result.scalar_one_or_none() is None
