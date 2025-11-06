"""Integration tests for set product inventory synchronization.

Tests the complete set product flow:
1. Set product creation with components
2. Set product inventory calculation
3. Component inventory deduction on set sales
4. Insufficient component stock handling
5. Transaction consistency
"""

import pytest


# 🔴 RED: Test set product inventory sync
def test_set_product_inventory_sync(client):
    """Test: Set product sale deducts component inventory correctly.

    Requirements: 7.4-7.6, 9.2
    """
    # Step 1: Create component products
    response1 = client.post("/api/products", json={
        "name": "からあげ",
        "unit_cost": 100,
        "sale_price": 150,
        "initial_stock": 20,
        "product_type": "single"
    })
    assert response1.status_code == 200
    item1_id = response1.json()["id"]

    response2 = client.post("/api/products", json={
        "name": "ご飯",
        "unit_cost": 50,
        "sale_price": 100,
        "initial_stock": 30,
        "product_type": "single"
    })
    assert response2.status_code == 200
    item2_id = response2.json()["id"]

    # Step 2: Create set product (からあげ×2 + ご飯×1)
    response = client.post("/api/products", json={
        "name": "からあげ弁当セット",
        "unit_cost": 250,
        "sale_price": 500,
        "initial_stock": 0,
        "product_type": "set",
        "set_items": [
            {"product_id": item1_id, "quantity": 2},
            {"product_id": item2_id, "quantity": 1}
        ]
    })
    assert response.status_code == 200, f"Set product creation failed: {response.status_code} - {response.json()}"
    set_id = response.json()["id"]

    # Step 3: Verify set inventory calculation
    # Set stock = min(20/2, 30/1) = min(10, 30) = 10
    response = client.get("/api/inventory/status")
    products = {p["id"]: p for p in response.json()["products"]}
    assert products[set_id]["current_stock"] == 10

    # Step 4: Sell 1 set
    response = client.post("/api/sales/checkout", json={
        "items": [{"product_id": set_id, "quantity": 1}]
    })
    assert response.status_code == 200
    assert float(response.json()["total_amount"]) == 500

    # Step 5: Verify component inventory deduction
    response = client.get("/api/inventory/status")
    products = {p["id"]: p for p in response.json()["products"]}
    assert products[item1_id]["current_stock"] == 18  # 20 - 2
    assert products[item2_id]["current_stock"] == 29  # 30 - 1
    assert products[set_id]["current_stock"] == 9  # min(18/2, 29/1) = 9


# 🔴 RED: Test set product with insufficient components
def test_set_product_insufficient_component_stock(client):
    """Test: Set product sale fails if any component is insufficient.

    Requirements: 7.4-7.5
    """
    # Create component products
    response1 = client.post("/api/products", json={
        "name": "パン",
        "unit_cost": 80,
        "sale_price": 120,
        "initial_stock": 5,  # Limited stock
        "product_type": "single"
    })
    item1_id = response1.json()["id"]

    response2 = client.post("/api/products", json={
        "name": "ハム",
        "unit_cost": 50,
        "sale_price": 80,
        "initial_stock": 20,
        "product_type": "single"
    })
    item2_id = response2.json()["id"]

    # Create set product (パン×2 + ハム×3)
    response = client.post("/api/products", json={
        "name": "サンドイッチセット",
        "unit_cost": 200,
        "sale_price": 400,
        "initial_stock": 0,
        "product_type": "set",
        "set_items": [
            {"product_id": item1_id, "quantity": 2},
            {"product_id": item2_id, "quantity": 3}
        ]
    })
    set_id = response.json()["id"]

    # Set stock = min(5/2, 20/3) = min(2, 6) = 2
    response = client.get("/api/inventory/status")
    products = {p["id"]: p for p in response.json()["products"]}
    assert products[set_id]["current_stock"] == 2

    # Try to sell 3 sets (should fail)
    response = client.post("/api/sales/checkout", json={
        "items": [{"product_id": set_id, "quantity": 3}]
    })
    assert response.status_code == 400
    error_data = response.json()
    assert error_data["detail"]["error_code"] == "INSUFFICIENT_STOCK"

    # Verify component stock unchanged (transaction rollback)
    response = client.get("/api/inventory/status")
    products = {p["id"]: p for p in response.json()["products"]}
    assert products[item1_id]["current_stock"] == 5
    assert products[item2_id]["current_stock"] == 20


# 🔴 RED: Test multiple set product sales
def test_multiple_set_product_sales(client):
    """Test: Multiple set sales correctly update component inventory.

    Requirements: 7.4, 9.2
    """
    # Create components
    response1 = client.post("/api/products", json={
        "name": "野菜",
        "unit_cost": 60,
        "sale_price": 100,
        "initial_stock": 50,
        "product_type": "single"
    })
    item1_id = response1.json()["id"]

    response2 = client.post("/api/products", json={
        "name": "肉",
        "unit_cost": 150,
        "sale_price": 250,
        "initial_stock": 30,
        "product_type": "single"
    })
    item2_id = response2.json()["id"]

    # Create set (野菜×3 + 肉×2)
    response = client.post("/api/products", json={
        "name": "野菜炒めセット",
        "unit_cost": 300,
        "sale_price": 600,
        "initial_stock": 0,
        "product_type": "set",
        "set_items": [
            {"product_id": item1_id, "quantity": 3},
            {"product_id": item2_id, "quantity": 2}
        ]
    })
    set_id = response.json()["id"]

    # Set stock = min(50/3, 30/2) = min(16, 15) = 15
    response = client.get("/api/inventory/status")
    products = {p["id"]: p for p in response.json()["products"]}
    assert products[set_id]["current_stock"] == 15

    # First sale: 5 sets
    client.post("/api/sales/checkout", json={
        "items": [{"product_id": set_id, "quantity": 5}]
    })

    # Verify after first sale
    response = client.get("/api/inventory/status")
    products = {p["id"]: p for p in response.json()["products"]}
    assert products[item1_id]["current_stock"] == 35  # 50 - 15
    assert products[item2_id]["current_stock"] == 20  # 30 - 10
    assert products[set_id]["current_stock"] == 10  # min(35/3, 20/2) = 10

    # Second sale: 8 sets
    client.post("/api/sales/checkout", json={
        "items": [{"product_id": set_id, "quantity": 8}]
    })

    # Verify after second sale
    response = client.get("/api/inventory/status")
    products = {p["id"]: p for p in response.json()["products"]}
    assert products[item1_id]["current_stock"] == 11  # 35 - 24
    assert products[item2_id]["current_stock"] == 4   # 20 - 16
    assert products[set_id]["current_stock"] == 2    # min(11/3, 4/2) = 2


# 🔴 RED: Test mixed sale (single + set products)
def test_mixed_single_and_set_product_sale(client):
    """Test: Cart with both single and set products works correctly.

    Requirements: 3.1-3.8, 7.4
    """
    # Create single products
    response1 = client.post("/api/products", json={
        "name": "飲み物",
        "unit_cost": 50,
        "sale_price": 100,
        "initial_stock": 100,
        "product_type": "single"
    })
    drink_id = response1.json()["id"]

    response2 = client.post("/api/products", json={
        "name": "おにぎり",
        "unit_cost": 80,
        "sale_price": 150,
        "initial_stock": 60,
        "product_type": "single"
    })
    onigiri_id = response2.json()["id"]

    # Create set product (おにぎり×2)
    response = client.post("/api/products", json={
        "name": "おにぎりセット",
        "unit_cost": 150,
        "sale_price": 250,
        "initial_stock": 0,
        "product_type": "set",
        "set_items": [
            {"product_id": onigiri_id, "quantity": 2}
        ]
    })
    set_id = response.json()["id"]

    # Mixed sale: 1 set + 2 drinks
    response = client.post("/api/sales/checkout", json={
        "items": [
            {"product_id": set_id, "quantity": 1},
            {"product_id": drink_id, "quantity": 2}
        ]
    })
    assert response.status_code == 200
    assert float(response.json()["total_amount"]) == 450  # 250 + (100*2)

    # Verify inventory
    response = client.get("/api/inventory/status")
    products = {p["id"]: p for p in response.json()["products"]}
    assert products[drink_id]["current_stock"] == 98   # 100 - 2
    assert products[onigiri_id]["current_stock"] == 58  # 60 - 2
    assert products[set_id]["current_stock"] == 29     # min(58/2) = 29


# 🔴 RED: Test set product out of stock display
def test_set_product_out_of_stock_display(client):
    """Test: Set product shows out of stock when any component is depleted.

    Requirements: 7.5, 7.7
    """
    # Create components with one having very low stock
    response1 = client.post("/api/products", json={
        "name": "レタス",
        "unit_cost": 30,
        "sale_price": 50,
        "initial_stock": 2,  # Very low stock
        "product_type": "single"
    })
    item1_id = response1.json()["id"]

    response2 = client.post("/api/products", json={
        "name": "トマト",
        "unit_cost": 40,
        "sale_price": 60,
        "initial_stock": 100,
        "product_type": "single"
    })
    item2_id = response2.json()["id"]

    # Create set (レタス×1 + トマト×1)
    response = client.post("/api/products", json={
        "name": "サラダセット",
        "unit_cost": 70,
        "sale_price": 150,
        "initial_stock": 0,
        "product_type": "set",
        "set_items": [
            {"product_id": item1_id, "quantity": 1},
            {"product_id": item2_id, "quantity": 1}
        ]
    })
    set_id = response.json()["id"]

    # Set stock = min(2/1, 100/1) = 2
    response = client.get("/api/inventory/status")
    products = {p["id"]: p for p in response.json()["products"]}
    assert products[set_id]["current_stock"] == 2
    assert products[set_id]["is_out_of_stock"] is False

    # Sell 2 sets (depletes レタス)
    client.post("/api/sales/checkout", json={
        "items": [{"product_id": set_id, "quantity": 2}]
    })

    # Verify set is now out of stock
    response = client.get("/api/inventory/status")
    products = {p["id"]: p for p in response.json()["products"]}
    assert products[item1_id]["current_stock"] == 0
    assert products[item1_id]["is_out_of_stock"] is True
    assert products[set_id]["current_stock"] == 0
    assert products[set_id]["is_out_of_stock"] is True
