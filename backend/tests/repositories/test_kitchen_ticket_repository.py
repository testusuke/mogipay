"""Tests for KitchenTicketRepository."""

import pytest
from datetime import datetime, UTC

from app.models import KitchenTicket, SalesHistory
from app.repositories.kitchen_ticket_repository import KitchenTicketRepository
from app.repositories.sales_history_repository import SalesHistoryRepository


class TestKitchenTicketRepository:
    """Test cases for KitchenTicketRepository."""

    def test_create_ticket(self, db_session):
        """Test creating a kitchen ticket."""
        # Create sales transaction first
        sales_repo = SalesHistoryRepository()
        sale = sales_repo.create_sale(
            total_amount=1000,
            sale_items_data=[],
            db=db_session
        )

        # Create kitchen ticket
        repo = KitchenTicketRepository()
        ticket = repo.create_ticket(sale_id=sale.id, db=db_session)

        assert ticket.id is not None
        assert ticket.sale_id == sale.id
        assert ticket.completed_at is None
        assert ticket.completed_by is None
        assert ticket.created_at is not None

    def test_get_incomplete_sale_ids(self, db_session):
        """Test retrieving incomplete ticket sale IDs."""
        # Create sales transactions
        sales_repo = SalesHistoryRepository()
        sale1 = sales_repo.create_sale(total_amount=1000, sale_items_data=[], db=db_session)
        sale2 = sales_repo.create_sale(total_amount=2000, sale_items_data=[], db=db_session)
        sale3 = sales_repo.create_sale(total_amount=3000, sale_items_data=[], db=db_session)

        # Create tickets
        repo = KitchenTicketRepository()
        ticket1 = repo.create_ticket(sale_id=sale1.id, db=db_session)
        ticket2 = repo.create_ticket(sale_id=sale2.id, db=db_session)
        ticket3 = repo.create_ticket(sale_id=sale3.id, db=db_session)

        # Complete one ticket
        repo.mark_as_completed(
            ticket_id=ticket2.id,
            completed_by="chef1",
            completed_at=datetime.now(UTC),
            db=db_session
        )

        # Get incomplete sale IDs
        incomplete_ids = repo.get_incomplete_sale_ids(db=db_session)

        assert len(incomplete_ids) == 2
        assert sale1.id in incomplete_ids
        assert sale3.id in incomplete_ids
        assert sale2.id not in incomplete_ids

    def test_mark_as_completed(self, db_session):
        """Test marking a ticket as completed."""
        # Create sales transaction and ticket
        sales_repo = SalesHistoryRepository()
        sale = sales_repo.create_sale(total_amount=1000, sale_items_data=[], db=db_session)

        repo = KitchenTicketRepository()
        ticket = repo.create_ticket(sale_id=sale.id, db=db_session)

        # Mark as completed
        completed_time = datetime.now(UTC)
        repo.mark_as_completed(
            ticket_id=ticket.id,
            completed_by="chef1",
            completed_at=completed_time,
            db=db_session
        )

        # Verify completion
        db_session.refresh(ticket)
        assert ticket.completed_at is not None
        assert ticket.completed_by == "chef1"

    def test_get_ticket_by_sale_id(self, db_session):
        """Test retrieving a ticket by sale ID."""
        # Create sales transaction and ticket
        sales_repo = SalesHistoryRepository()
        sale = sales_repo.create_sale(total_amount=1000, sale_items_data=[], db=db_session)

        repo = KitchenTicketRepository()
        created_ticket = repo.create_ticket(sale_id=sale.id, db=db_session)

        # Retrieve ticket
        ticket = repo.get_ticket_by_sale_id(sale_id=sale.id, db=db_session)

        assert ticket is not None
        assert ticket.id == created_ticket.id
        assert ticket.sale_id == sale.id

    def test_get_ticket_by_sale_id_returns_none_when_not_found(self, db_session):
        """Test that get_ticket_by_sale_id returns None when ticket doesn't exist."""
        import uuid

        repo = KitchenTicketRepository()
        ticket = repo.get_ticket_by_sale_id(sale_id=uuid.uuid4(), db=db_session)

        assert ticket is None

    def test_unique_constraint_on_sale_id(self, db_session):
        """Test that UNIQUE constraint prevents duplicate tickets for same sale."""
        # Create sales transaction and ticket
        sales_repo = SalesHistoryRepository()
        sale = sales_repo.create_sale(total_amount=1000, sale_items_data=[], db=db_session)

        repo = KitchenTicketRepository()
        repo.create_ticket(sale_id=sale.id, db=db_session)

        # Attempt to create duplicate ticket should raise error
        with pytest.raises(Exception):  # SQLAlchemy IntegrityError
            repo.create_ticket(sale_id=sale.id, db=db_session)
            db_session.commit()
