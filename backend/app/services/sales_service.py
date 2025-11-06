"""Sales service for checkout processing and transaction management."""

from typing import List, Dict, Any
from uuid import UUID
from decimal import Decimal
from dataclasses import dataclass
from datetime import datetime
from sqlalchemy.orm import Session

from app.repositories.product_repository import ProductRepository
from app.exceptions import InsufficientStockError
from app.repositories.sales_history_repository import SalesHistoryRepository
from app.repositories.set_item_repository import SetItemRepository
from app.services.inventory_service import InventoryService


@dataclass
class CheckoutItem:
    """Item in checkout cart.

    Attributes:
        product_id: Product UUID
        quantity: Quantity to purchase
    """

    product_id: UUID
    quantity: int


@dataclass
class CheckoutResult:
    """Result of checkout process.

    Attributes:
        sale_id: Sale transaction UUID
        total_amount: Total amount charged
        timestamp: Transaction timestamp
    """

    sale_id: UUID
    total_amount: Decimal
    timestamp: datetime


class SalesService:
    """Service for sales transaction processing.

    This service handles:
    - Checkout processing with inventory validation
    - Stock decrement for both single and set products
    - Transaction management with atomicity guarantee
    - Price snapshot capture for sales history
    """

    def __init__(
        self,
        product_repo: ProductRepository = None,
        sales_history_repo: SalesHistoryRepository = None,
        inventory_service: InventoryService = None,
        set_item_repo: SetItemRepository = None,
    ):
        """Initialize SalesService with repository dependencies.

        Args:
            product_repo: ProductRepository instance
            sales_history_repo: SalesHistoryRepository instance
            inventory_service: InventoryService instance
            set_item_repo: SetItemRepository instance
        """
        self.product_repo = product_repo or ProductRepository()
        self.sales_history_repo = sales_history_repo or SalesHistoryRepository()
        self.inventory_service = inventory_service or InventoryService()
        self.set_item_repo = set_item_repo or SetItemRepository()

    def process_checkout(
        self, items: List[CheckoutItem], db: Session
    ) -> CheckoutResult:
        """Process checkout and create sales transaction.

        This method:
        1. Validates product existence
        2. Checks stock availability
        3. Expands set products into component items
        4. Creates sales history with price snapshot
        5. Decrements stock for all items
        6. Commits transaction or rolls back on error

        Args:
            items: List of CheckoutItem objects
            db: Database session

        Returns:
            CheckoutResult with transaction details

        Raises:
            InsufficientStockError: If any product is out of stock
            ValueError: If product not found

        Preconditions:
        - items is not empty
        - db session is active

        Postconditions:
        - Sales history is recorded
        - Inventory is decremented
        - Transaction is committed or rolled back atomically

        Invariants:
        - Stock never becomes negative
        - Sales history always has price snapshot
        """
        # Step 1: Validate products and build item details
        item_details = []
        total_amount = Decimal("0")

        for item in items:
            product = self.product_repo.get_by_id(item.product_id, db)
            if not product:
                raise ValueError(f"Product {item.product_id} not found")

            item_details.append({
                "product": product,
                "quantity": item.quantity,
            })

        # Step 2: Check stock availability
        checkout_items_dict = [
            {"product_id": item.product_id, "quantity": item.quantity}
            for item in items
        ]
        stock_check = self.inventory_service.check_stock_availability(
            checkout_items_dict, db
        )

        if not stock_check.is_available:
            # Get first insufficient product details
            first_insufficient_id = stock_check.insufficient_items[0]
            # Find the requested quantity for this product
            requested_item = next(i for i in items if str(i.product_id) == str(first_insufficient_id))
            # Get product to check available stock
            product = self.product_repo.get_by_id(first_insufficient_id, db)

            raise InsufficientStockError(
                product_id=str(first_insufficient_id),
                requested=requested_item.quantity,
                available=product.current_stock if product else 0
            )

        # Step 3: Begin transaction
        try:
            # Step 4: Prepare sales history items with price snapshot
            sales_items = []
            for item_detail in item_details:
                product = item_detail["product"]
                quantity = item_detail["quantity"]

                # Calculate subtotal
                subtotal = product.sale_price * quantity
                total_amount += subtotal

                # Create sales item with price snapshot
                sales_items.append({
                    "product_id": product.id,
                    "product_name": product.name,
                    "quantity": quantity,
                    "unit_cost": product.unit_cost,
                    "sale_price": product.sale_price,
                    "subtotal": subtotal,
                })

            # Step 5: Create sales history
            sale_transaction = self.sales_history_repo.create_sale(
                total_amount=total_amount,
                sale_items_data=sales_items,
                db=db,
            )

            # Step 6: Decrement stock
            for item_detail in item_details:
                product = item_detail["product"]
                quantity = item_detail["quantity"]

                if product.product_type == "single":
                    # Decrement single product stock
                    self.product_repo.decrement_stock(product.id, quantity, db)
                elif product.product_type == "set":
                    # Decrement component items' stock
                    set_items = self.set_item_repo.get_by_set_product_id(product.id, db)
                    for set_item in set_items:
                        component_quantity = set_item.quantity * quantity
                        self.product_repo.decrement_stock(
                            set_item.item_product_id,
                            component_quantity,
                            db,
                        )

            # Step 7: Commit transaction
            db.commit()

            return CheckoutResult(
                sale_id=sale_transaction.id,
                total_amount=sale_transaction.total_amount,
                timestamp=sale_transaction.timestamp,
            )

        except Exception as e:
            # Rollback on any error
            db.rollback()
            raise e
