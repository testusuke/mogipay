#!/usr/bin/env python3
"""
Seed data script for MogiPay - Yakitori (焼き串) Restaurant
"""

import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.append(str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import Product, SetItem, SalesHistory, SaleItem


def clear_existing_data(db):
    """Clear all existing data from database"""
    print("🗑️  Clearing existing data...")
    try:
        # Delete in correct order due to foreign key constraints
        db.query(SaleItem).delete()  # First delete sale items
        db.query(SalesHistory).delete()  # Then delete sales history
        db.query(SetItem).delete()  # Then delete set items
        db.query(Product).delete()  # Finally delete products
        db.commit()
        print("✅ Existing data cleared")
    except Exception as e:
        db.rollback()
        print(f"❌ Error clearing data: {e}")
        raise


def create_single_products(db):
    """Create single products (串単品)"""
    print("\n🍢 Creating single products (串単品)...")

    products = [
        # 焼き串単品
        {
            "name": "牛カルビ串",
            "unit_cost": 162,
            "sale_price": 400,
            "initial_stock": 200,
            "current_stock": 200,
            "product_type": "single",
        },
        {
            "name": "豚バラ串",
            "unit_cost": 71,
            "sale_price": 200,
            "initial_stock": 400,
            "current_stock": 400,
            "product_type": "single",
        },
        {
            "name": "野菜串",
            "unit_cost": 130,
            "sale_price": 200,
            "initial_stock": 50,
            "current_stock": 50,
            "product_type": "single",
        },
    ]

    created_products = {}

    for product_data in products:
        product = Product(**product_data)
        db.add(product)
        db.flush()  # Get the ID without committing
        created_products[product_data["name"]] = product
        print(f"  ✓ {product_data['name']} (¥{product_data['sale_price']}, 在庫: {product_data['initial_stock']})")

    db.commit()
    print(f"✅ Created {len(products)} single products")

    return created_products


def create_set_products(db, single_products):
    """Create set products (セット商品)"""
    print("\n🍱 Creating set products (セット商品)...")

    # 牛カルビ串3本セット
    set_product_1 = Product(
        name="牛カルビ串3本セット",
        unit_cost=486,  # 162 * 3
        sale_price=1000,
        initial_stock=0,  # セット商品は仮想在庫
        current_stock=0,
        product_type="set",
    )
    db.add(set_product_1)
    db.flush()

    set_items_1 = [
        SetItem(
            set_product_id=set_product_1.id,
            item_product_id=single_products["牛カルビ串"].id,
            quantity=3,
        ),
    ]
    for item in set_items_1:
        db.add(item)

    print(f"  ✓ {set_product_1.name} (¥{set_product_1.sale_price})")
    print(f"    - 牛カルビ串 x3")

    # 豚バラ串3本セット
    set_product_2 = Product(
        name="豚バラ串3本セット",
        unit_cost=213,  # 71 * 3
        sale_price=500,
        initial_stock=0,
        current_stock=0,
        product_type="set",
    )
    db.add(set_product_2)
    db.flush()

    set_items_2 = [
        SetItem(
            set_product_id=set_product_2.id,
            item_product_id=single_products["豚バラ串"].id,
            quantity=3,
        ),
    ]
    for item in set_items_2:
        db.add(item)

    print(f"  ✓ {set_product_2.name} (¥{set_product_2.sale_price})")
    print(f"    - 豚バラ串 x3")

    db.commit()
    print("✅ Created 2 set products")


def main():
    """Main seed data execution"""
    print("=" * 60)
    print("🍢 MogiPay Seed Data - 焼き串屋さん Edition")
    print("=" * 60)

    db = SessionLocal()

    try:
        # Clear existing data
        clear_existing_data(db)

        # Create single products
        single_products = create_single_products(db)

        # Create set products
        create_set_products(db, single_products)

        # Summary
        print("\n" + "=" * 60)
        print("✅ Seed data created successfully!")
        print("=" * 60)
        print("\n📊 Summary:")

        total_products = db.query(Product).count()
        single_count = db.query(Product).filter(Product.product_type == "single").count()
        set_count = db.query(Product).filter(Product.product_type == "set").count()

        print(f"  Total products: {total_products}")
        print(f"  - Single products: {single_count}")
        print(f"  - Set products: {set_count}")

        # Calculate initial investment
        total_cost = db.query(Product).filter(Product.product_type == "single").all()
        total_investment = sum(p.initial_stock * p.unit_cost for p in total_cost)

        print(f"\n💰 Initial Investment: ¥{total_investment:,}")

        print("\n🚀 Ready to start! Run:")
        print("  Terminal 1: make db-up (if not running)")
        print("  Terminal 2: make backend-dev")
        print("  Terminal 3: make frontend-dev")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
