"""Tests for FinancialController API endpoints.

This module tests the HTTP layer for financial management:
- Financial summary retrieval
- Total cost and revenue calculations
- Profit/loss calculations
- Break-even status detection
- HTTP response validation
"""

import pytest

from unittest.mock import Mock
from fastapi.testclient import TestClient

from app.services.financial_service import FinancialService, FinancialSummary


@pytest.fixture
def mock_financial_service():
    """Create a mock FinancialService for testing."""
    return Mock(spec=FinancialService)


@pytest.fixture
def client(mock_financial_service, mock_current_user, monkeypatch):
    """Create FastAPI test client with mocked service.

    Note: This will be updated once we create the actual FastAPI app.
    For now, we're writing the test first (TDD Red phase).
    """
    try:
        from app.main import app
        from app.api import financial_controller
        from app.dependencies.auth import get_current_user

        # Mock the service dependency
        def override_get_financial_service():
            return mock_financial_service

        app.dependency_overrides[financial_controller.get_financial_service] = override_get_financial_service
        app.dependency_overrides[get_current_user] = mock_current_user

        return TestClient(app)
    except ImportError:
        # Return None during Red phase - tests will fail expectedly
        return None


# ========================================
# GET /api/financial/summary Tests
# ========================================

def test_get_financial_summary_profit(client, mock_financial_service):
    """🔴 RED: GET /api/financial/summary - profitable scenario"""
    if client is None:
        pytest.skip("App not created yet (TDD Red phase)")

    # Setup mock - break-even achieved (profit)
    mock_financial_service.get_financial_summary.return_value = FinancialSummary(
        total_cost=10000,
        total_revenue=15000,
        profit=5000,
        profit_rate=0.5,
        break_even_achieved=True,
    )

    # Execute
    response = client.get("/api/financial/summary")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["total_cost"] == "10000"
    assert data["total_revenue"] == "15000"
    assert data["profit"] == "5000"
    assert data["profit_rate"] == 0.5
    assert data["break_even_achieved"] is True


def test_get_financial_summary_loss(client, mock_financial_service):
    """🔴 RED: GET /api/financial/summary - loss scenario"""
    if client is None:
        pytest.skip("App not created yet (TDD Red phase)")

    # Setup mock - not break-even yet (loss)
    mock_financial_service.get_financial_summary.return_value = FinancialSummary(
        total_cost=10000,
        total_revenue=7000,
        profit=-3000,
        profit_rate=-0.3,
        break_even_achieved=False,
    )

    # Execute
    response = client.get("/api/financial/summary")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["total_cost"] == "10000"
    assert data["total_revenue"] == "7000"
    assert data["profit"] == "-3000"
    assert data["profit_rate"] == -0.3
    assert data["break_even_achieved"] is False


def test_get_financial_summary_break_even(client, mock_financial_service):
    """🔴 RED: GET /api/financial/summary - exact break-even scenario"""
    if client is None:
        pytest.skip("App not created yet (TDD Red phase)")

    # Setup mock - exact break-even
    mock_financial_service.get_financial_summary.return_value = FinancialSummary(
        total_cost=10000,
        total_revenue=10000,
        profit=0,
        profit_rate=0.0,
        break_even_achieved=True,
    )

    # Execute
    response = client.get("/api/financial/summary")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["total_cost"] == "10000"
    assert data["total_revenue"] == "10000"
    assert data["profit"] == "0"
    assert data["profit_rate"] == 0.0
    assert data["break_even_achieved"] is True


def test_get_financial_summary_no_sales(client, mock_financial_service):
    """🔴 RED: GET /api/financial/summary - no sales yet"""
    if client is None:
        pytest.skip("App not created yet (TDD Red phase)")

    # Setup mock - no sales yet
    mock_financial_service.get_financial_summary.return_value = FinancialSummary(
        total_cost=10000,
        total_revenue=0,
        profit=-10000,
        profit_rate=-1.0,
        break_even_achieved=False,
    )

    # Execute
    response = client.get("/api/financial/summary")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["total_cost"] == "10000"
    assert data["total_revenue"] == "0"
    assert data["profit"] == "-10000"
    assert data["profit_rate"] == -1.0
    assert data["break_even_achieved"] is False


def test_get_financial_summary_zero_cost(client, mock_financial_service):
    """🔴 RED: GET /api/financial/summary - zero cost (edge case)"""
    if client is None:
        pytest.skip("App not created yet (TDD Red phase)")

    # Setup mock - zero cost (all products are free)
    mock_financial_service.get_financial_summary.return_value = FinancialSummary(
        total_cost=0,
        total_revenue=5000,
        profit=5000,
        profit_rate=0.0,  # profit_rate is 0 when cost is 0
        break_even_achieved=True,
    )

    # Execute
    response = client.get("/api/financial/summary")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["total_cost"] == "0"
    assert data["total_revenue"] == "5000"
    assert data["profit"] == "5000"
    assert data["break_even_achieved"] is True
