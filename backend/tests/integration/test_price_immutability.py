"""Integration tests for price change immutability.

Tests the price history preservation:
1. Sales records maintain original prices after price changes
2. New sales use updated prices
3. Historical data integrity is preserved
4. Financial calculations reflect actual sale prices
"""

import pytest


# 🔴 RED: Test price change immutability
def test_price_change_immutability(client):
    """Test: Past sales history prices remain unchanged after price update.

    Requirements: 2.1-2.4, 9.1
    """
    # Step 1: Register a product
    response = client.post("/api/products", json={
        "name": "test product",
        "unit_cost": 100,
        "sale_price": 200,
        "initial_stock": 10,
        "product_type": "single"
    })
    assert response.status_code == 200
    product_id = response.json()["id"]

    # Step 2: Make a sale at original price (200)
    response = client.post("/api/sales/checkout", json={
        "items": [{"product_id": product_id, "quantity": 1}]
    })
    assert response.status_code == 200
    old_sale_id = response.json()["sale_id"]
    assert float(response.json()["total_amount"]) == 200

    # Step 3: Change price to 300
    response = client.put(f"/api/products/{product_id}/price", json={
        "sale_price": 300
    })
    assert response.status_code == 200

    # Step 4: Verify product price is updated
    response = client.get(f"/api/products/{product_id}")
    assert response.status_code == 200
    assert float(response.json()["sale_price"]) == 300

    # Step 5: Make a new sale at new price (300)
    response = client.post("/api/sales/checkout", json={
        "items": [{"product_id": product_id, "quantity": 1}]
    })
    assert response.status_code == 200
    new_sale_id = response.json()["sale_id"]
    assert float(response.json()["total_amount"]) == 300

    # Step 6: Verify sales history - old sale still shows 200, new sale shows 300
    response = client.get("/api/sales/history")
    assert response.status_code == 200
    history = {h["sale_id"]: h for h in response.json()}

    assert float(history[old_sale_id]["total_amount"]) == 200
    assert float(history[old_sale_id]["items"][0]["sale_price"]) == 200

    assert float(history[new_sale_id]["total_amount"]) == 300
    assert float(history[new_sale_id]["items"][0]["sale_price"]) == 300


# 🔴 RED: Test multiple price changes
def test_multiple_price_changes(client):
    """Test: Multiple price changes preserve all historical prices.

    Requirements: 2.1-2.4, 9.1
    """
    # Register a product
    response = client.post("/api/products", json={
        "name": "商品X",
        "unit_cost": 150,
        "sale_price": 250,
        "initial_stock": 20,
        "product_type": "single"
    })
    product_id = response.json()["id"]

    # Sale 1 at price 250
    response = client.post("/api/sales/checkout", json={
        "items": [{"product_id": product_id, "quantity": 2}]
    })
    sale1_id = response.json()["sale_id"]
    assert float(response.json()["total_amount"]) == 500  # 250 * 2

    # Change price to 300
    client.put(f"/api/products/{product_id}/price", json={"sale_price": 300})

    # Sale 2 at price 300
    response = client.post("/api/sales/checkout", json={
        "items": [{"product_id": product_id, "quantity": 3}]
    })
    sale2_id = response.json()["sale_id"]
    assert float(response.json()["total_amount"]) == 900  # 300 * 3

    # Change price to 350
    client.put(f"/api/products/{product_id}/price", json={"sale_price": 350})

    # Sale 3 at price 350
    response = client.post("/api/sales/checkout", json={
        "items": [{"product_id": product_id, "quantity": 1}]
    })
    sale3_id = response.json()["sale_id"]
    assert float(response.json()["total_amount"]) == 350  # 350 * 1

    # Verify all sales have correct prices
    response = client.get("/api/sales/history")
    history = {h["sale_id"]: h for h in response.json()}

    assert float(history[sale1_id]["items"][0]["sale_price"]) == 250
    assert float(history[sale2_id]["items"][0]["sale_price"]) == 300
    assert float(history[sale3_id]["items"][0]["sale_price"]) == 350

    # Verify financial summary uses actual sale prices
    response = client.get("/api/financial/summary")
    summary = response.json()
    assert float(summary["total_revenue"]) == 1750  # 500 + 900 + 350


# 🔴 RED: Test price change with set products
def test_price_change_immutability_set_product(client):
    """Test: Set product price changes don't affect past sales.

    Requirements: 2.1-2.4, 9.1
    """
    # Create component product
    response = client.post("/api/products", json={
        "name": "単品A",
        "unit_cost": 100,
        "sale_price": 150,
        "initial_stock": 50,
        "product_type": "single"
    })
    item_id = response.json()["id"]

    # Create set product
    response = client.post("/api/products", json={
        "name": "セットA",
        "unit_cost": 200,
        "sale_price": 400,
        "initial_stock": 0,
        "product_type": "set",
        "set_items": [{"product_id": item_id, "quantity": 2}]
    })
    set_id = response.json()["id"]

    # Sale at original price (400)
    response = client.post("/api/sales/checkout", json={
        "items": [{"product_id": set_id, "quantity": 1}]
    })
    old_sale_id = response.json()["sale_id"]
    assert float(response.json()["total_amount"]) == 400

    # Change set product price to 500
    client.put(f"/api/products/{set_id}/price", json={"sale_price": 500})

    # Sale at new price (500)
    response = client.post("/api/sales/checkout", json={
        "items": [{"product_id": set_id, "quantity": 1}]
    })
    new_sale_id = response.json()["sale_id"]
    assert float(response.json()["total_amount"]) == 500

    # Verify sales history
    response = client.get("/api/sales/history")
    history = {h["sale_id"]: h for h in response.json()}

    assert float(history[old_sale_id]["total_amount"]) == 400
    assert float(history[new_sale_id]["total_amount"]) == 500


# 🔴 RED: Test unit cost change immutability
def test_unit_cost_immutability(client):
    """Test: Unit cost changes don't affect past sales records.

    Requirements: 9.1
    """
    # Register a product
    response = client.post("/api/products", json={
        "name": "商品Y",
        "unit_cost": 120,
        "sale_price": 250,
        "initial_stock": 15,
        "product_type": "single"
    })
    product_id = response.json()["id"]

    # Make a sale
    response = client.post("/api/sales/checkout", json={
        "items": [{"product_id": product_id, "quantity": 2}]
    })
    sale_id = response.json()["sale_id"]

    # Update product (including unit cost)
    client.put(f"/api/products/{product_id}", json={
        "name": "商品Y改",
        "unit_cost": 150,  # Changed
        "sale_price": 280,  # Changed
        "initial_stock": 15,
        "product_type": "single"
    })

    # Verify sales history still has original unit_cost
    response = client.get("/api/sales/history")
    history = response.json()
    sale = next(h for h in history if h["sale_id"] == sale_id)
    assert float(sale["items"][0]["unit_cost"]) == 120  # Original cost
    assert float(sale["items"][0]["sale_price"]) == 250  # Original price


# 🔴 RED: Test financial calculation with price changes
def test_financial_calculation_with_price_changes(client):
    """Test: Financial summary correctly calculates with historical prices.

    Requirements: 6.1-6.5, 9.1
    """
    # Register a product
    response = client.post("/api/products", json={
        "name": "商品Z",
        "unit_cost": 100,
        "sale_price": 200,
        "initial_stock": 10,
        "product_type": "single"
    })
    product_id = response.json()["id"]

    # Initial cost = 100 * 10 = 1000
    response = client.get("/api/financial/summary")
    assert float(response.json()["total_cost"]) == 1000

    # Sale 1: 3 items at 200 each
    client.post("/api/sales/checkout", json={
        "items": [{"product_id": product_id, "quantity": 3}]
    })

    # Revenue = 600, Profit = 600 - 1000 = -400
    response = client.get("/api/financial/summary")
    summary = response.json()
    assert float(summary["total_revenue"]) == 600
    assert float(summary["profit"]) == -400
    assert summary["break_even_achieved"] is False

    # Change price to 300
    client.put(f"/api/products/{product_id}/price", json={"sale_price": 300})

    # Sale 2: 5 items at 300 each
    client.post("/api/sales/checkout", json={
        "items": [{"product_id": product_id, "quantity": 5}]
    })

    # Revenue = 600 + 1500 = 2100, Profit = 2100 - 1000 = 1100
    response = client.get("/api/financial/summary")
    summary = response.json()
    assert float(summary["total_revenue"]) == 2100
    assert float(summary["profit"]) == 1100
    assert summary["break_even_achieved"] is True
