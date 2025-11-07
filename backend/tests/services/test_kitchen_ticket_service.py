"""Tests for KitchenTicketService using TDD approach."""

import pytest
from unittest.mock import Mock
from uuid import uuid4, UUID
from datetime import datetime, timedelta
from decimal import Decimal

from app.services.kitchen_ticket_service import (
    KitchenTicketService,
    TicketNotFoundError,
    TicketAlreadyCompletedError,
)
from app.models.kitchen_ticket import KitchenTicket
from app.models.sales_history import SalesHistory
from app.models.sale_item import SaleItem
from app.models.product import Product
from app.models.set_item import SetItem


class TestKitchenTicketService:
    """Test cases for KitchenTicketService.

    Following TDD approach:
    1. RED: Write failing tests first
    2. GREEN: Implement minimal code to pass
    3. REFACTOR: Improve code quality
    """

    @pytest.fixture
    def mock_kitchen_ticket_repo(self):
        """Mock KitchenTicketRepository."""
        return Mock()

    @pytest.fixture
    def mock_sales_history_repo(self):
        """Mock SalesHistoryRepository."""
        return Mock()

    @pytest.fixture
    def mock_set_item_repo(self):
        """Mock SetItemRepository."""
        return Mock()

    @pytest.fixture
    def kitchen_ticket_service(
        self,
        mock_kitchen_ticket_repo,
        mock_sales_history_repo,
        mock_set_item_repo,
    ):
        """Create KitchenTicketService instance with mocked dependencies."""
        return KitchenTicketService(
            kitchen_ticket_repo=mock_kitchen_ticket_repo,
            sales_history_repo=mock_sales_history_repo,
            set_item_repo=mock_set_item_repo,
        )

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        db = Mock()
        db.commit = Mock()
        db.rollback = Mock()
        return db

    # Test 1: Get active tickets returns sorted by order time
    def test_get_active_tickets_returns_sorted_by_order_time(
        self,
        kitchen_ticket_service,
        mock_kitchen_ticket_repo,
        mock_sales_history_repo,
        mock_set_item_repo,
        mock_db,
    ):
        """Test that active tickets are returned in order of oldest first.

        Scenario: 3 tickets exist with different order times
        Expected: Tickets are returned sorted by oldest timestamp first
        """
        # Arrange: Create test data
        sale_id_1 = uuid4()
        sale_id_2 = uuid4()
        sale_id_3 = uuid4()

        # Sale 2 is oldest (10 minutes ago)
        sale_2_time = datetime.utcnow() - timedelta(minutes=10)
        # Sale 1 is middle (5 minutes ago)
        sale_1_time = datetime.utcnow() - timedelta(minutes=5)
        # Sale 3 is newest (1 minute ago)
        sale_3_time = datetime.utcnow() - timedelta(minutes=1)

        # Mock incomplete sale IDs (not sorted)
        mock_kitchen_ticket_repo.get_incomplete_sale_ids.return_value = [
            sale_id_1,
            sale_id_2,
            sale_id_3,
        ]

        # Mock sales history data
        sale_1 = SalesHistory(
            id=sale_id_1,
            total_amount=Decimal("1000"),
            timestamp=sale_1_time,
        )
        sale_1.sale_items = [
            SaleItem(
                id=uuid4(),
                sale_id=sale_id_1,
                product_id=uuid4(),
                product_name="コーラ",
                quantity=2,
                unit_cost=50,
                sale_price=150,
                subtotal=300,
            )
        ]

        sale_2 = SalesHistory(
            id=sale_id_2,
            total_amount=Decimal("500"),
            timestamp=sale_2_time,
        )
        sale_2.sale_items = [
            SaleItem(
                id=uuid4(),
                sale_id=sale_id_2,
                product_id=uuid4(),
                product_name="ハンバーガー",
                quantity=1,
                unit_cost=200,
                sale_price=500,
                subtotal=500,
            )
        ]

        sale_3 = SalesHistory(
            id=sale_id_3,
            total_amount=Decimal("800"),
            timestamp=sale_3_time,
        )
        sale_3.sale_items = [
            SaleItem(
                id=uuid4(),
                sale_id=sale_id_3,
                product_id=uuid4(),
                product_name="ポテト",
                quantity=3,
                unit_cost=100,
                sale_price=200,
                subtotal=600,
            )
        ]

        mock_sales_history_repo.get_by_id.side_effect = [sale_1, sale_2, sale_3]

        # Mock kitchen tickets
        mock_kitchen_ticket_repo.get_ticket_by_sale_id.side_effect = [
            KitchenTicket(id=uuid4(), sale_id=sale_id_1),
            KitchenTicket(id=uuid4(), sale_id=sale_id_2),
            KitchenTicket(id=uuid4(), sale_id=sale_id_3),
        ]

        # Mock set_item_repo (these are single products, not sets)
        mock_set_item_repo.get_by_set_product_id.return_value = []

        # Act: Get active tickets
        tickets = kitchen_ticket_service.get_active_tickets(mock_db)

        # Assert: Tickets are sorted by oldest first (sale_2, sale_1, sale_3)
        assert len(tickets) == 3
        assert tickets[0].sale_id == str(sale_id_2)  # oldest
        assert tickets[1].sale_id == str(sale_id_1)  # middle
        assert tickets[2].sale_id == str(sale_id_3)  # newest

    # Test 2: Get active tickets expands set products
    def test_get_active_tickets_expands_set_products(
        self,
        kitchen_ticket_service,
        mock_kitchen_ticket_repo,
        mock_sales_history_repo,
        mock_set_item_repo,
        mock_db,
    ):
        """Test that set products are expanded into their components.

        Scenario: Sale contains 1 set product "セットA" (ハンバーガー×1 + ポテト×1)
        Expected: Ticket shows セットA with components listed
        """
        # Arrange: Create test data
        sale_id = uuid4()
        set_product_id = uuid4()
        hamburger_id = uuid4()
        potato_id = uuid4()

        sale_time = datetime.utcnow() - timedelta(minutes=3)

        # Mock incomplete sale IDs
        mock_kitchen_ticket_repo.get_incomplete_sale_ids.return_value = [sale_id]

        # Mock sale with set product
        sale = SalesHistory(
            id=sale_id,
            total_amount=Decimal("1000"),
            timestamp=sale_time,
        )
        sale.sale_items = [
            SaleItem(
                id=uuid4(),
                sale_id=sale_id,
                product_id=set_product_id,
                product_name="セットA",
                quantity=2,  # 2 sets
                unit_cost=400,
                sale_price=1000,
                subtotal=2000,
            )
        ]

        mock_sales_history_repo.get_by_id.return_value = sale

        # Mock set items (components of the set)
        mock_set_item_repo.get_by_set_product_id.return_value = [
            SetItem(
                set_product_id=set_product_id,
                item_product_id=hamburger_id,
                quantity=1,  # 1 hamburger per set
            ),
            SetItem(
                set_product_id=set_product_id,
                item_product_id=potato_id,
                quantity=1,  # 1 potato per set
            ),
        ]

        # Mock _get_product_name_by_id method
        # We need to mock the database query for product names
        mock_db.execute.return_value.scalar_one_or_none.side_effect = [
            "ハンバーガー",  # First component
            "ポテト",  # Second component
        ]

        # Mock kitchen ticket
        mock_kitchen_ticket_repo.get_ticket_by_sale_id.return_value = KitchenTicket(
            id=uuid4(), sale_id=sale_id
        )

        # Act: Get active tickets
        tickets = kitchen_ticket_service.get_active_tickets(mock_db)

        # Assert: Set product is expanded
        assert len(tickets) == 1
        ticket = tickets[0]
        assert len(ticket.items) == 1
        item = ticket.items[0]
        assert item.product_name == "セットA"
        assert item.product_type == "set"
        assert item.quantity == 2
        assert len(item.components) == 2
        # 2 sets × 1 hamburger each = 2 hamburgers
        assert item.components[0].name == "ハンバーガー"
        assert item.components[0].quantity == 2
        # 2 sets × 1 potato each = 2 potatoes
        assert item.components[1].name == "ポテト"
        assert item.components[1].quantity == 2

    # Test 3: Get active tickets calculates elapsed time
    def test_get_active_tickets_calculates_elapsed_time(
        self,
        kitchen_ticket_service,
        mock_kitchen_ticket_repo,
        mock_sales_history_repo,
        mock_set_item_repo,
        mock_db,
    ):
        """Test that elapsed time is calculated correctly.

        Scenario: Ticket created 5 minutes ago
        Expected: elapsed_minutes is 5
        """
        # Arrange: Create test data
        sale_id = uuid4()
        sale_time = datetime.utcnow() - timedelta(minutes=5, seconds=30)

        mock_kitchen_ticket_repo.get_incomplete_sale_ids.return_value = [sale_id]

        sale = SalesHistory(
            id=sale_id,
            total_amount=Decimal("500"),
            timestamp=sale_time,
        )
        sale.sale_items = [
            SaleItem(
                id=uuid4(),
                sale_id=sale_id,
                product_id=uuid4(),
                product_name="コーラ",
                quantity=1,
                unit_cost=50,
                sale_price=150,
                subtotal=150,
            )
        ]

        mock_sales_history_repo.get_by_id.return_value = sale

        # Mock kitchen ticket
        mock_kitchen_ticket_repo.get_ticket_by_sale_id.return_value = KitchenTicket(
            id=uuid4(), sale_id=sale_id
        )

        # Mock set_item_repo (single product, not a set)
        mock_set_item_repo.get_by_set_product_id.return_value = []

        # Act: Get active tickets
        tickets = kitchen_ticket_service.get_active_tickets(mock_db)

        # Assert: Elapsed time is approximately 5 minutes
        assert len(tickets) == 1
        ticket = tickets[0]
        assert ticket.elapsed_minutes >= 5
        assert ticket.elapsed_minutes <= 6  # Allow 1 minute tolerance

    # Test 4: Complete ticket marks as completed
    def test_complete_ticket_marks_as_completed(
        self,
        kitchen_ticket_service,
        mock_kitchen_ticket_repo,
        mock_db,
    ):
        """Test that completing a ticket updates the database.

        Scenario: Valid ticket ID is provided
        Expected: Ticket is marked as completed with timestamp and user
        """
        # Arrange: Create test data
        ticket_id = uuid4()
        user_id = "chef_001"

        # Mock ticket exists and is not completed
        mock_kitchen_ticket = KitchenTicket(
            id=ticket_id,
            sale_id=uuid4(),
            completed_at=None,
            completed_by=None,
        )
        mock_kitchen_ticket_repo.get_ticket_by_id.return_value = mock_kitchen_ticket

        # Act: Complete the ticket
        result = kitchen_ticket_service.complete_ticket(ticket_id, user_id, mock_db)

        # Assert: Repository was called with correct parameters
        mock_kitchen_ticket_repo.mark_as_completed.assert_called_once()
        call_args = mock_kitchen_ticket_repo.mark_as_completed.call_args[1]
        assert call_args["ticket_id"] == ticket_id
        assert call_args["completed_by"] == user_id
        assert isinstance(call_args["completed_at"], datetime)
        assert call_args["db"] == mock_db

        # Assert: Transaction was committed
        mock_db.commit.assert_called_once()

        # Assert: Result is returned
        assert result.ticket_id == str(ticket_id)
        assert result.completed_by == user_id
        assert isinstance(result.completed_at, datetime)

    # Test 5: Complete ticket raises error if not found
    def test_complete_ticket_raises_error_if_not_found(
        self,
        kitchen_ticket_service,
        mock_kitchen_ticket_repo,
        mock_db,
    ):
        """Test that completing a non-existent ticket raises error.

        Scenario: Ticket ID does not exist
        Expected: TicketNotFoundError is raised
        """
        # Arrange: Non-existent ticket ID
        ticket_id = uuid4()
        user_id = "chef_001"

        # Mock ticket not found
        mock_kitchen_ticket_repo.get_ticket_by_id.return_value = None

        # Act & Assert: Expect error
        with pytest.raises(TicketNotFoundError):
            kitchen_ticket_service.complete_ticket(ticket_id, user_id, mock_db)

        # Assert: Transaction was rolled back
        mock_db.rollback.assert_called_once()

    # Test 6: Complete ticket raises error if already completed
    def test_complete_ticket_raises_error_if_already_completed(
        self,
        kitchen_ticket_service,
        mock_kitchen_ticket_repo,
        mock_db,
    ):
        """Test that completing an already completed ticket raises error.

        Scenario: Ticket is already marked as completed
        Expected: TicketAlreadyCompletedError is raised
        """
        # Arrange: Already completed ticket
        ticket_id = uuid4()
        user_id = "chef_001"

        mock_kitchen_ticket = KitchenTicket(
            id=ticket_id,
            sale_id=uuid4(),
            completed_at=datetime.utcnow() - timedelta(minutes=5),
            completed_by="chef_002",
        )
        mock_kitchen_ticket_repo.get_ticket_by_id.return_value = mock_kitchen_ticket

        # Act & Assert: Expect error
        with pytest.raises(TicketAlreadyCompletedError):
            kitchen_ticket_service.complete_ticket(ticket_id, user_id, mock_db)

        # Assert: Transaction was rolled back
        mock_db.rollback.assert_called_once()
