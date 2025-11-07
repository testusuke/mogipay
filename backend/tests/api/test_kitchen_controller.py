"""Test Kitchen API Controller.

Tests for kitchen ticket API endpoints:
- GET /api/kitchen/tickets - Retrieve active tickets
- POST /api/kitchen/tickets/:ticket_id/complete - Complete ticket
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.sales_history import SalesHistory
from app.models.sale_item import SaleItem
from app.models.kitchen_ticket import KitchenTicket as KitchenTicketModel
from app.models.product import Product


@pytest.fixture
def client(db, mock_current_user):
    """Create a test client with database and auth overrides.

    Args:
        db: Database session fixture
        mock_current_user: Mock auth user fixture

    Returns:
        TestClient instance with dependency overrides
    """
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = mock_current_user

    yield TestClient(app)

    # Clean up overrides
    app.dependency_overrides.clear()


class TestGetTicketsEndpoint:
    """Test GET /api/kitchen/tickets endpoint."""

    def test_get_tickets_returns_active_tickets(
        self, client, db: Session
    ):
        """Test that GET /api/kitchen/tickets returns active (uncompleted) tickets.

        Requirement: 1.1, 2.1 - Automatic ticket display and chronological sorting
        """
        # Arrange: Create 2 sales with kitchen tickets
        now = datetime.utcnow()

        # Create products
        product1 = Product(
            name="ハンバーガー",
            product_type="single",
            unit_cost=100,
            sale_price=300,
            initial_stock=100,
            current_stock=100,
        )
        product2 = Product(
            name="コーラ",
            product_type="single",
            unit_cost=50,
            sale_price=150,
            initial_stock=100,
            current_stock=100,
        )
        db.add_all([product1, product2])
        db.commit()

        # Create older sale (should appear first)
        sale1 = SalesHistory(
            total_amount=450,
            timestamp=now - timedelta(minutes=10),
        )
        db.add(sale1)
        db.commit()

        sale_item1 = SaleItem(
            sale_id=sale1.id,
            product_id=product1.id,
            product_name=product1.name,
            quantity=1,
            unit_cost=100,
            sale_price=300,
            subtotal=300,
        )
        sale_item2 = SaleItem(
            sale_id=sale1.id,
            product_id=product2.id,
            product_name=product2.name,
            quantity=1,
            unit_cost=50,
            sale_price=150,
            subtotal=150,
        )
        db.add_all([sale_item1, sale_item2])
        db.commit()

        # Create kitchen ticket for sale1 (uncompleted)
        ticket1 = KitchenTicketModel(
            sale_id=sale1.id,
            completed_at=None,
            completed_by=None,
        )
        db.add(ticket1)

        # Create newer sale (should appear second)
        sale2 = SalesHistory(
            total_amount=300,
            timestamp=now - timedelta(minutes=5),
        )
        db.add(sale2)
        db.commit()

        sale_item3 = SaleItem(
            sale_id=sale2.id,
            product_id=product1.id,
            product_name=product1.name,
            quantity=1,
            unit_cost=100,
            sale_price=300,
            subtotal=300,
        )
        db.add(sale_item3)
        db.commit()

        # Create kitchen ticket for sale2 (uncompleted)
        ticket2 = KitchenTicketModel(
            sale_id=sale2.id,
            completed_at=None,
            completed_by=None,
        )
        db.add(ticket2)
        db.commit()

        # Act: Call API endpoint
        response = client.get("/api/kitchen/tickets")

        # Assert: Check response
        assert response.status_code == 200
        data = response.json()

        assert "tickets" in data
        assert len(data["tickets"]) == 2

        # Check that tickets are sorted by oldest first (sale1 before sale2)
        assert data["tickets"][0]["sale_id"] == str(sale1.id)
        assert data["tickets"][1]["sale_id"] == str(sale2.id)

        # Check first ticket structure
        ticket = data["tickets"][0]
        assert "id" in ticket
        assert "sale_id" in ticket
        assert "order_time" in ticket
        assert "elapsed_minutes" in ticket
        assert "items" in ticket

        # Check elapsed time is calculated (approximately 10 minutes for sale1)
        assert ticket["elapsed_minutes"] >= 9
        assert ticket["elapsed_minutes"] <= 11

    def test_get_tickets_excludes_completed_tickets(
        self, db: Session, client
    ):
        """Test that completed tickets are excluded from response.

        Requirement: 3.2 - Ticket deletion on completion
        """
        # Arrange: Create 1 completed and 1 uncompleted ticket
        now = datetime.utcnow()

        product = Product(
            name="ハンバーガー",
            product_type="single",
            unit_cost=100,
            sale_price=300,
            initial_stock=100,
            current_stock=100,
        )
        db.add(product)
        db.commit()

        # Create sale 1 (completed)
        sale1 = SalesHistory(
            total_amount=300,
            timestamp=now - timedelta(minutes=10),
        )
        db.add(sale1)
        db.commit()

        sale_item1 = SaleItem(
            sale_id=sale1.id,
            product_id=product.id,
            product_name=product.name,
            quantity=1,
            unit_cost=100,
            sale_price=300,
            subtotal=300,
        )
        db.add(sale_item1)
        db.commit()

        ticket1 = KitchenTicketModel(
            sale_id=sale1.id,
            completed_at=now - timedelta(minutes=5),
            completed_by="chef1",
        )
        db.add(ticket1)

        # Create sale 2 (uncompleted)
        sale2 = SalesHistory(
            total_amount=300,
            timestamp=now - timedelta(minutes=5),
        )
        db.add(sale2)
        db.commit()

        sale_item2 = SaleItem(
            sale_id=sale2.id,
            product_id=product.id,
            product_name=product.name,
            quantity=1,
            unit_cost=100,
            sale_price=300,
            subtotal=300,
        )
        db.add(sale_item2)
        db.commit()

        ticket2 = KitchenTicketModel(
            sale_id=sale2.id,
            completed_at=None,
            completed_by=None,
        )
        db.add(ticket2)
        db.commit()

        # Act
        response = client.get("/api/kitchen/tickets")

        # Assert: Only uncompleted ticket should be returned
        assert response.status_code == 200
        data = response.json()

        assert len(data["tickets"]) == 1
        assert data["tickets"][0]["sale_id"] == str(sale2.id)

    def test_get_tickets_includes_set_products_with_components(
        self, db: Session, client
    ):
        """Test that set products are expanded with their components.

        Requirement: 1.2, 5.2, 5.3 - Set product display with components
        """
        # Arrange: Create a set product with components
        now = datetime.utcnow()

        # Create component products
        burger = Product(
            name="ハンバーガー",
            product_type="single",
            unit_cost=100,
            sale_price=300,
            initial_stock=100,
            current_stock=100,
        )
        fries = Product(
            name="ポテト",
            product_type="single",
            unit_cost=50,
            sale_price=150,
            initial_stock=100,
            current_stock=100,
        )
        db.add_all([burger, fries])
        db.commit()

        # Create set product
        set_product = Product(
            name="セットA",
            product_type="set",
            unit_cost=150,
            sale_price=400,
            initial_stock=50,
            current_stock=50,
        )
        db.add(set_product)
        db.commit()

        # Create set items
        from app.models.set_item import SetItem
        set_item1 = SetItem(
            set_product_id=set_product.id,
            item_product_id=burger.id,
            quantity=1,
        )
        set_item2 = SetItem(
            set_product_id=set_product.id,
            item_product_id=fries.id,
            quantity=1,
        )
        db.add_all([set_item1, set_item2])
        db.commit()

        # Create sale with set product
        sale = SalesHistory(
            total_amount=400,
            timestamp=now - timedelta(minutes=5),
        )
        db.add(sale)
        db.commit()

        sale_item = SaleItem(
            sale_id=sale.id,
            product_id=set_product.id,
            product_name=set_product.name,
            quantity=1,
            unit_cost=150,
            sale_price=400,
            subtotal=400,
        )
        db.add(sale_item)
        db.commit()

        # Create kitchen ticket
        ticket = KitchenTicketModel(
            sale_id=sale.id,
            completed_at=None,
            completed_by=None,
        )
        db.add(ticket)
        db.commit()

        # Act
        response = client.get("/api/kitchen/tickets")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert len(data["tickets"]) == 1
        ticket_data = data["tickets"][0]

        # Check items structure
        assert len(ticket_data["items"]) == 1
        item = ticket_data["items"][0]

        assert item["product_name"] == "セットA"
        assert item["product_type"] == "set"
        assert item["quantity"] == 1

        # Check components are expanded
        assert "components" in item
        assert item["components"] is not None
        assert len(item["components"]) == 2

        # Check component details
        component_names = [c["name"] for c in item["components"]]
        assert "ハンバーガー" in component_names
        assert "ポテト" in component_names

    def test_get_tickets_returns_empty_when_no_active_tickets(
        self, db: Session, client
    ):
        """Test that empty list is returned when no active tickets exist.

        Requirement: 1.1 - Ticket display
        """
        # Act
        response = client.get("/api/kitchen/tickets")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "tickets" in data
        assert len(data["tickets"]) == 0

    def test_get_tickets_requires_authentication(self, db: Session):
        """Test that endpoint requires authentication.

        Requirement: Security - Authentication required
        """
        # Act: Call without auth override (use fresh TestClient)
        test_client = TestClient(app)
        response = test_client.get("/api/kitchen/tickets")

        # Assert
        assert response.status_code == 401


class TestCompleteTicketEndpoint:
    """Test POST /api/kitchen/tickets/:ticket_id/complete endpoint."""

    def test_complete_ticket_marks_as_completed(
        self, db: Session, client
    ):
        """Test that POST complete endpoint marks ticket as completed.

        Requirement: 3.1, 3.2, 3.4 - Complete button, deletion, completion record
        """
        # Arrange
        now = datetime.utcnow()

        product = Product(
            name="ハンバーガー",
            product_type="single",
            unit_cost=100,
            sale_price=300,
            initial_stock=100,
            current_stock=100,
        )
        db.add(product)
        db.commit()

        sale = SalesHistory(
            total_amount=300,
            timestamp=now - timedelta(minutes=5),
        )
        db.add(sale)
        db.commit()

        sale_item = SaleItem(
            sale_id=sale.id,
            product_id=product.id,
            product_name=product.name,
            quantity=1,
            unit_cost=100,
            sale_price=300,
            subtotal=300,
        )
        db.add(sale_item)
        db.commit()

        ticket = KitchenTicketModel(
            sale_id=sale.id,
            completed_at=None,
            completed_by=None,
        )
        db.add(ticket)
        db.commit()

        # Act
        response = client.post(
            f"/api/kitchen/tickets/{ticket.id}/complete",
            json={"completed_by": "chef1"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["ticket_id"] == str(ticket.id)
        assert data["completed_by"] == "chef1"
        assert "completed_at" in data

        # Verify ticket is marked as completed in database
        db.refresh(ticket)
        assert ticket.completed_at is not None
        assert ticket.completed_by == "chef1"

    def test_complete_ticket_returns_404_if_not_found(
        self, db: Session, client
    ):
        """Test that 404 is returned for non-existent ticket.

        Requirement: Error handling - NOT_FOUND error
        """
        # Arrange
        from uuid import uuid4
        fake_ticket_id = uuid4()

        # Act
        response = client.post(
            f"/api/kitchen/tickets/{fake_ticket_id}/complete",
            json={"completed_by": "chef1"},
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert data["detail"]["error_code"] == "TICKET_NOT_FOUND"

    def test_complete_ticket_returns_409_if_already_completed(
        self, db: Session, client
    ):
        """Test that 409 is returned when completing already completed ticket.

        Requirement: Error handling - ALREADY_COMPLETED error
        """
        # Arrange
        now = datetime.utcnow()

        product = Product(
            name="ハンバーガー",
            product_type="single",
            unit_cost=100,
            sale_price=300,
            initial_stock=100,
            current_stock=100,
        )
        db.add(product)
        db.commit()

        sale = SalesHistory(
            total_amount=300,
            timestamp=now - timedelta(minutes=10),
        )
        db.add(sale)
        db.commit()

        sale_item = SaleItem(
            sale_id=sale.id,
            product_id=product.id,
            product_name=product.name,
            quantity=1,
            unit_cost=100,
            sale_price=300,
            subtotal=300,
        )
        db.add(sale_item)
        db.commit()

        # Create already completed ticket
        ticket = KitchenTicketModel(
            sale_id=sale.id,
            completed_at=now - timedelta(minutes=5),
            completed_by="chef1",
        )
        db.add(ticket)
        db.commit()

        # Act
        response = client.post(
            f"/api/kitchen/tickets/{ticket.id}/complete",
            json={"completed_by": "chef2"},
        )

        # Assert
        assert response.status_code == 409
        data = response.json()
        assert "detail" in data
        assert data["detail"]["error_code"] == "TICKET_ALREADY_COMPLETED"

    def test_complete_ticket_requires_authentication(self, db: Session):
        """Test that endpoint requires authentication.

        Requirement: Security - Authentication required
        """
        # Arrange
        from uuid import uuid4
        ticket_id = uuid4()

        # Act: Call without auth override (use fresh TestClient)
        test_client = TestClient(app)
        response = test_client.post(
            f"/api/kitchen/tickets/{ticket_id}/complete",
            json={"completed_by": "chef1"},
        )

        # Assert
        assert response.status_code == 401

    def test_complete_ticket_validates_request_body(
        self, db: Session, client
    ):
        """Test that request body is validated.

        Requirement: 4.3 - Input validation
        """
        # Arrange
        from uuid import uuid4
        ticket_id = uuid4()

        # Act: Call with missing completed_by
        response = client.post(
            f"/api/kitchen/tickets/{ticket_id}/complete",
            json={},
        )

        # Assert: Should return 422 validation error
        assert response.status_code == 422
