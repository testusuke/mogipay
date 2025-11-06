"""Integration tests for full sales flow.

Tests the complete flow from API to database:
1. Product registration
2. Checkout process
3. Inventory verification
4. Sales history validation
5. Transaction rollback on errors
"""

import pytest


# 🔴 RED: Test full sales flow
def test_full_sales_flow(client):
    """Test: Product registration → Checkout → Inventory verification.

    Requirements: 3.1-3.8, 7.3-7.4, 9.2-9.3
    """
    # Step 1: Register a product
    response = client.post("/api/products", json={
        "name": "からあげ弁当",
        "unit_cost": 300,
        "sale_price": 500,
        "initial_stock": 10,
        "product_type": "single"
    })
    assert response.status_code == 200, f"Product creation failed: {response.json()}"
    product_id = response.json()["id"]

    # Step 2: Checkout 3 items
    response = client.post("/api/sales/checkout", json={
        "items": [{"product_id": product_id, "quantity": 3}]
    })
    assert response.status_code == 200, f"Checkout failed: {response.json()}"
    sale_data = response.json()
    assert sale_data["total_amount"] == "1500"  # 500 * 3

    # Step 3: Verify inventory (10 - 3 = 7)
    response = client.get("/api/inventory/status")
    assert response.status_code == 200
    products = response.json()["products"]
    product = next(p for p in products if p["id"] == product_id)
    assert product["current_stock"] == 7
    assert product["initial_stock"] == 10

    # Step 4: Verify sales history
    response = client.get("/api/sales/history")
    assert response.status_code == 200
    history = response.json()
    assert len(history) == 1
    assert history[0]["total_amount"] == "1500"
    assert len(history[0]["items"]) == 1
    assert history[0]["items"][0]["product_name"] == "からあげ弁当"
    assert history[0]["items"][0]["quantity"] == 3


# 🔴 RED: Test transaction rollback on error
def test_transaction_rollback_on_error(client):
    """Test: Transaction rolls back on insufficient stock error.

    Requirements: 9.2-9.3
    """
    # Register a product with limited stock
    response = client.post("/api/products", json={
        "name": "test product",
        "unit_cost": 100,
        "sale_price": 200,
        "initial_stock": 2,
        "product_type": "single"
    })
    assert response.status_code == 200
    product_id = response.json()["id"]

    # Try to checkout more than available stock (should fail)
    response = client.post("/api/sales/checkout", json={
        "items": [{"product_id": product_id, "quantity": 5}]
    })
    assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.json()}"
    error_data = response.json()
    assert "detail" in error_data, f"No 'detail' in response: {error_data}"
    error_detail = error_data["detail"]
    assert error_detail["error_code"] == "INSUFFICIENT_STOCK", f"Wrong error_code: {error_detail}"

    # Verify inventory has not changed (rollback successful)
    response = client.get("/api/inventory/status")
    products = response.json()["products"]
    product = next(p for p in products if p["id"] == product_id)
    assert product["current_stock"] == 2  # Stock unchanged

    # Verify no sales history was created
    response = client.get("/api/sales/history")
    history = response.json()
    assert len(history) == 0


# 🔴 RED: Test multiple sales flow
def test_multiple_sales_flow(client):
    """Test: Multiple sales transactions update inventory correctly.

    Requirements: 3.1-3.8, 7.3-7.4
    """
    # Register a product
    response = client.post("/api/products", json={
        "name": "弁当",
        "unit_cost": 200,
        "sale_price": 400,
        "initial_stock": 20,
        "product_type": "single"
    })
    product_id = response.json()["id"]

    # First sale: 5 items
    response = client.post("/api/sales/checkout", json={
        "items": [{"product_id": product_id, "quantity": 5}]
    })
    assert response.status_code == 200
    assert response.json()["total_amount"] == "2000"  # 400 * 5

    # Second sale: 3 items
    response = client.post("/api/sales/checkout", json={
        "items": [{"product_id": product_id, "quantity": 3}]
    })
    assert response.status_code == 200
    assert response.json()["total_amount"] == "1200"  # 400 * 3

    # Third sale: 7 items
    response = client.post("/api/sales/checkout", json={
        "items": [{"product_id": product_id, "quantity": 7}]
    })
    assert response.status_code == 200
    assert response.json()["total_amount"] == "2800"  # 400 * 7

    # Verify inventory (20 - 5 - 3 - 7 = 5)
    response = client.get("/api/inventory/status")
    products = response.json()["products"]
    product = next(p for p in products if p["id"] == product_id)
    assert product["current_stock"] == 5

    # Verify sales history has 3 records
    response = client.get("/api/sales/history")
    history = response.json()
    assert len(history) == 3
    total_revenue = sum(int(sale["total_amount"]) for sale in history)
    assert total_revenue == 6000  # 2000 + 1200 + 2800


# 🔴 RED: Test financial summary after sales
def test_financial_summary_after_sales(client):
    """Test: Financial summary reflects sales correctly.

    Requirements: 6.1-6.5
    """
    # Register a product
    response = client.post("/api/products", json={
        "name": "商品A",
        "unit_cost": 150,
        "sale_price": 300,
        "initial_stock": 10,
        "product_type": "single"
    })
    product_id = response.json()["id"]

    # Initial financial summary (no sales yet)
    response = client.get("/api/financial/summary")
    assert response.status_code == 200
    summary = response.json()
    assert summary["total_cost"] == "1500"  # 150 * 10
    assert summary["total_revenue"] == "0"
    assert summary["profit"] == "-1500"
    assert summary["break_even_achieved"] is False

    # Make a sale: 6 items
    response = client.post("/api/sales/checkout", json={
        "items": [{"product_id": product_id, "quantity": 6}]
    })
    assert response.status_code == 200

    # Financial summary after first sale
    response = client.get("/api/financial/summary")
    summary = response.json()
    assert summary["total_cost"] == "1500"
    assert summary["total_revenue"] == "1800"  # 300 * 6
    assert summary["profit"] == "300"  # 1800 - 1500
    assert summary["break_even_achieved"] is True  # Profit >= 0


# 🔴 RED: Test sales analytics after sales
def test_sales_analytics_after_sales(client):
    """Test: Sales analytics calculates completion rate correctly.

    Requirements: 5.1-5.5
    """
    # Register a product
    response = client.post("/api/products", json={
        "name": "商品B",
        "unit_cost": 100,
        "sale_price": 250,
        "initial_stock": 50,
        "product_type": "single"
    })
    product_id = response.json()["id"]

    # Make sales: 30 items total
    client.post("/api/sales/checkout", json={
        "items": [{"product_id": product_id, "quantity": 15}]
    })
    client.post("/api/sales/checkout", json={
        "items": [{"product_id": product_id, "quantity": 10}]
    })
    client.post("/api/sales/checkout", json={
        "items": [{"product_id": product_id, "quantity": 5}]
    })

    # Get sales summary
    response = client.get("/api/sales/summary")
    assert response.status_code == 200
    summary = response.json()
    assert summary["total_revenue"] == "7500"  # 250 * 30
    assert summary["completion_rate"] == pytest.approx(0.6, rel=0.01)  # (50-20)/50 = 0.6 (60%)
