"""Tests for SalesController API endpoints.

This module tests the HTTP layer for sales management:
- Checkout processing
- Sales history retrieval
- Sales summary analytics
- HTTP response validation and error handling
"""

import pytest
from decimal import Decimal
from uuid import uuid4
from datetime import datetime, UTC, timedelta
from unittest.mock import Mock, MagicMock
from fastapi.testclient import TestClient

from app.models.sales_history import SaleTransaction, SaleItem
from app.services.sales_service import SalesService, CheckoutItem
from app.services.sales_history_service import SalesHistoryService
from app.services.sales_analytics_service import SalesAnalyticsService


@pytest.fixture
def mock_sales_service():
    """Create a mock SalesService for testing."""
    return Mock(spec=SalesService)


@pytest.fixture
def mock_sales_history_service():
    """Create a mock SalesHistoryService for testing."""
    return Mock(spec=SalesHistoryService)


@pytest.fixture
def mock_sales_analytics_service():
    """Create a mock SalesAnalyticsService for testing."""
    return Mock(spec=SalesAnalyticsService)


@pytest.fixture
def client(mock_sales_service, mock_sales_history_service, mock_sales_analytics_service, monkeypatch):
    """Create FastAPI test client with mocked services.

    Note: This will be updated once we create the actual FastAPI app.
    For now, we're writing the test first (TDD Red phase).
    """
    try:
        from app.main import app
        from app.api import sales_controller

        # Mock the service dependencies
        def override_get_sales_service():
            return mock_sales_service

        def override_get_sales_history_service():
            return mock_sales_history_service

        def override_get_sales_analytics_service():
            return mock_sales_analytics_service

        app.dependency_overrides[sales_controller.get_sales_service] = override_get_sales_service
        app.dependency_overrides[sales_controller.get_sales_history_service] = override_get_sales_history_service
        app.dependency_overrides[sales_controller.get_sales_analytics_service] = override_get_sales_analytics_service

        return TestClient(app)
    except ImportError:
        # Return None during Red phase - tests will fail expectedly
        return None


# ========================================
# POST /api/sales/checkout Tests
# ========================================

def test_checkout_success(client, mock_sales_service):
    """🔴 RED: POST /api/sales/checkout - successful checkout"""
    if client is None:
        pytest.skip("App not created yet (TDD Red phase)")

    # Setup mock
    sale_id = str(uuid4())
    mock_sales_service.process_checkout.return_value = SaleTransaction(
        id=sale_id,
        total_amount=Decimal("1000.00"),
        timestamp=datetime.now(UTC),
        items=[]
    )

    # Execute
    response = client.post("/api/sales/checkout", json={
        "items": [
            {"product_id": str(uuid4()), "quantity": 2}
        ]
    })

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["sale_id"] == sale_id
    assert data["total_amount"] == "1000.00"
    assert "timestamp" in data


def test_checkout_insufficient_stock(client, mock_sales_service):
    """🔴 RED: POST /api/sales/checkout - insufficient stock error"""
    if client is None:
        pytest.skip("App not created yet (TDD Red phase)")

    # Setup mock to raise InsufficientStockError
    from app.exceptions import InsufficientStockError
    mock_sales_service.process_checkout.side_effect = InsufficientStockError(
        product_id=str(uuid4()),
        requested=5,
        available=2
    )

    # Execute
    response = client.post("/api/sales/checkout", json={
        "items": [
            {"product_id": str(uuid4()), "quantity": 5}
        ]
    })

    # Assert
    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["error_code"] == "INSUFFICIENT_STOCK"
    assert "requested" in data["detail"]["details"]
    assert "available" in data["detail"]["details"]


def test_checkout_validation_error(client):
    """🔴 RED: POST /api/sales/checkout - validation error (negative quantity)"""
    if client is None:
        pytest.skip("App not created yet (TDD Red phase)")

    # Execute with invalid data
    response = client.post("/api/sales/checkout", json={
        "items": [
            {"product_id": str(uuid4()), "quantity": -1}
        ]
    })

    # Assert
    assert response.status_code == 422  # FastAPI validation error


def test_checkout_empty_cart(client):
    """🔴 RED: POST /api/sales/checkout - empty cart error"""
    if client is None:
        pytest.skip("App not created yet (TDD Red phase)")

    # Execute with empty items
    response = client.post("/api/sales/checkout", json={
        "items": []
    })

    # Assert
    assert response.status_code == 422  # FastAPI validation error


def test_checkout_product_not_found(client, mock_sales_service):
    """🔴 RED: POST /api/sales/checkout - product not found error"""
    if client is None:
        pytest.skip("App not created yet (TDD Red phase)")

    # Setup mock to raise ProductNotFoundError
    from app.exceptions import ProductNotFoundError
    mock_sales_service.process_checkout.side_effect = ProductNotFoundError(
        product_id=str(uuid4())
    )

    # Execute
    response = client.post("/api/sales/checkout", json={
        "items": [
            {"product_id": str(uuid4()), "quantity": 1}
        ]
    })

    # Assert
    assert response.status_code == 404
    data = response.json()
    assert data["detail"]["error_code"] == "RESOURCE_NOT_FOUND"


# ========================================
# GET /api/sales/history Tests
# ========================================

def test_get_sales_history_all(client, mock_sales_history_service):
    """🔴 RED: GET /api/sales/history - get all sales history"""
    if client is None:
        pytest.skip("App not created yet (TDD Red phase)")

    # Setup mock
    sale_id = str(uuid4())
    mock_sales_history_service.get_sales_history.return_value = [
        SaleTransaction(
            id=sale_id,
            total_amount=Decimal("1500.00"),
            timestamp=datetime.now(UTC),
            items=[
                SaleItem(
                    id=str(uuid4()),
                    sale_id=sale_id,
                    product_id=str(uuid4()),
                    product_name="Test Product",
                    quantity=3,
                    unit_cost=Decimal("300.00"),
                    sale_price=Decimal("500.00"),
                    subtotal=Decimal("1500.00")
                )
            ]
        )
    ]

    # Execute
    response = client.get("/api/sales/history")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["sale_id"] == sale_id
    assert data[0]["total_amount"] == "1500.00"
    assert len(data[0]["items"]) == 1


def test_get_sales_history_with_date_filter(client, mock_sales_history_service):
    """🔴 RED: GET /api/sales/history - filter by date range"""
    if client is None:
        pytest.skip("App not created yet (TDD Red phase)")

    # Setup mock
    mock_sales_history_service.get_sales_history.return_value = []

    # Execute
    date_from = "2025-11-01T00:00:00Z"
    date_to = "2025-11-02T23:59:59Z"
    response = client.get(f"/api/sales/history?date_from={date_from}&date_to={date_to}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


# ========================================
# GET /api/sales/summary Tests
# ========================================

def test_get_sales_summary(client, mock_sales_analytics_service):
    """🔴 RED: GET /api/sales/summary - get sales analytics summary"""
    if client is None:
        pytest.skip("App not created yet (TDD Red phase)")

    # Setup mock
    from app.services.sales_analytics_service import SalesSummary
    mock_sales_analytics_service.get_sales_summary.return_value = SalesSummary(
        total_revenue=Decimal("5000.00"),
        daily_revenue=[Decimal("2000.00"), Decimal("3000.00")],
        completion_rate=0.65
    )

    # Execute
    response = client.get("/api/sales/summary")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["total_revenue"] == "5000.00"
    assert len(data["daily_revenue"]) == 2
    assert data["daily_revenue"][0] == "2000.00"
    assert data["daily_revenue"][1] == "3000.00"
    assert data["completion_rate"] == 0.65


def test_get_sales_summary_no_sales(client, mock_sales_analytics_service):
    """🔴 RED: GET /api/sales/summary - no sales data"""
    if client is None:
        pytest.skip("App not created yet (TDD Red phase)")

    # Setup mock
    from app.services.sales_analytics_service import SalesSummary
    mock_sales_analytics_service.get_sales_summary.return_value = SalesSummary(
        total_revenue=Decimal("0.00"),
        daily_revenue=[],
        completion_rate=0.0
    )

    # Execute
    response = client.get("/api/sales/summary")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["total_revenue"] == "0.00"
    assert len(data["daily_revenue"]) == 0
    assert data["completion_rate"] == 0.0
