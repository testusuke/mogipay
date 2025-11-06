"""
Integration test for overlapping stock requirements.

This test verifies that when multiple items share component products,
the stock check correctly calculates the total required quantity.
"""
import pytest

from app.models import Product, SetItem
from app.services.sales_service import SalesService, CheckoutItem
from app.exceptions import InsufficientStockError


def test_overlapping_stock_insufficient(db_session):
    """Test that overlapping stock requirements are correctly detected as insufficient.

    Scenario:
    - ねぎま串 stock: 100
    - 串ドリンクセット requires: ねぎま串 x2
    - Purchase: 串ドリンクセット x49 (requires 98 ねぎま串) + ねぎま串 x4
    - Total required: 98 + 4 = 102 ねぎま串
    - Expected: InsufficientStockError (only 100 available)
    """
    # Create single products
    negima = Product(
        name="ねぎま串",
        unit_cost=80,
        sale_price=150,
        initial_stock=100,
        current_stock=100,
        product_type="single",
    )
    ocha = Product(
        name="お茶",
        unit_cost=30,
        sale_price=100,
        initial_stock=150,
        current_stock=150,
        product_type="single",
    )
    db_session.add(negima)
    db_session.add(ocha)
    db_session.flush()

    # Create set product
    kushi_drink_set = Product(
        name="串ドリンクセット",
        unit_cost=130,
        sale_price=250,
        initial_stock=0,
        current_stock=0,
        product_type="set",
    )
    db_session.add(kushi_drink_set)
    db_session.flush()

    # Define set composition
    set_item_1 = SetItem(
        set_product_id=kushi_drink_set.id,
        item_product_id=negima.id,
        quantity=2,
    )
    set_item_2 = SetItem(
        set_product_id=kushi_drink_set.id,
        item_product_id=ocha.id,
        quantity=1,
    )
    db_session.add(set_item_1)
    db_session.add(set_item_2)
    db_session.commit()

    # Attempt checkout
    sales_service = SalesService()

    # 串ドリンクセット 49個 (ねぎま串 98本) + ねぎま串 4本 = 合計 102本
    # 在庫は 100本なので不足
    items = [
        CheckoutItem(product_id=kushi_drink_set.id, quantity=49),
        CheckoutItem(product_id=negima.id, quantity=4),
    ]

    # Should raise InsufficientStockError
    with pytest.raises(InsufficientStockError) as exc_info:
        sales_service.process_checkout(items, db_session)

    # Verify stock hasn't changed (transaction rolled back)
    db_session.refresh(negima)
    assert negima.current_stock == 100, "Stock should not have changed"
    db_session.refresh(ocha)
    assert ocha.current_stock == 150, "Stock should not have changed"


def test_overlapping_stock_sufficient(db_session):
    """Test that overlapping stock requirements work when sufficient stock is available.

    Scenario:
    - ねぎま串 stock: 100
    - 串ドリンクセット requires: ねぎま串 x2
    - Purchase: 串ドリンクセット x48 (requires 96 ねぎま串) + ねぎま串 x4
    - Total required: 96 + 4 = 100 ねぎま串
    - Expected: Success
    """
    # Create single products
    negima = Product(
        name="ねぎま串",
        unit_cost=80,
        sale_price=150,
        initial_stock=100,
        current_stock=100,
        product_type="single",
    )
    ocha = Product(
        name="お茶",
        unit_cost=30,
        sale_price=100,
        initial_stock=150,
        current_stock=150,
        product_type="single",
    )
    db_session.add(negima)
    db_session.add(ocha)
    db_session.flush()

    # Create set product
    kushi_drink_set = Product(
        name="串ドリンクセット",
        unit_cost=130,
        sale_price=250,
        initial_stock=0,
        current_stock=0,
        product_type="set",
    )
    db_session.add(kushi_drink_set)
    db_session.flush()

    # Define set composition
    set_item_1 = SetItem(
        set_product_id=kushi_drink_set.id,
        item_product_id=negima.id,
        quantity=2,
    )
    set_item_2 = SetItem(
        set_product_id=kushi_drink_set.id,
        item_product_id=ocha.id,
        quantity=1,
    )
    db_session.add(set_item_1)
    db_session.add(set_item_2)
    db_session.commit()

    # Attempt checkout
    sales_service = SalesService()

    # 串ドリンクセット 48個 (ねぎま串 96本) + ねぎま串 4本 = 合計 100本
    # 在庫は 100本なので成功
    items = [
        CheckoutItem(product_id=kushi_drink_set.id, quantity=48),
        CheckoutItem(product_id=negima.id, quantity=4),
    ]

    # Should succeed
    result = sales_service.process_checkout(items, db_session)
    assert result is not None

    # Verify stock changed correctly
    db_session.refresh(negima)
    assert negima.current_stock == 0, "ねぎま串 should be depleted (96 + 4 = 100)"
    db_session.refresh(ocha)
    assert ocha.current_stock == 102, "お茶 should have 48 consumed (150 - 48 = 102)"
