"""Inventory service for stock management and availability checks."""

from typing import List, Dict, Any
from uuid import UUID
from dataclasses import dataclass
from sqlalchemy.orm import Session

from app.repositories.product_repository import ProductRepository
from app.repositories.set_item_repository import SetItemRepository


@dataclass
class StockCheckResult:
    """Result of stock availability check.

    Attributes:
        is_available: Whether all requested items are available
        insufficient_items: List of product IDs with insufficient stock
    """

    is_available: bool
    insufficient_items: List[UUID]


@dataclass
class ProductInventory:
    """Product inventory status.

    Attributes:
        id: Product UUID
        name: Product name
        product_type: Product type ('single' or 'set')
        current_stock: Current stock quantity
        initial_stock: Initial stock quantity
        stock_rate: Stock remaining rate (current/initial)
        is_out_of_stock: Whether product is out of stock
    """

    id: UUID
    name: str
    product_type: str
    current_stock: int
    initial_stock: int
    stock_rate: float
    is_out_of_stock: bool


class InventoryService:
    """Service for inventory management and stock calculations.

    This service handles:
    - Stock availability checking before checkout
    - Set product stock calculation from component items
    - Real-time inventory status retrieval
    """

    def __init__(
        self,
        product_repo: ProductRepository = None,
        set_item_repo: SetItemRepository = None,
    ):
        """Initialize InventoryService with repository dependencies.

        Args:
            product_repo: ProductRepository instance
            set_item_repo: SetItemRepository instance
        """
        self.product_repo = product_repo or ProductRepository()
        self.set_item_repo = set_item_repo or SetItemRepository()

    def calculate_set_stock(self, set_product_id: UUID, db: Session) -> int:
        """Calculate available stock for a set product.

        Set stock is determined by the minimum available quantity of
        component items, considering the required quantity of each item.

        Algorithm:
        - Get all set_items for the set product
        - For each set_item: available_stock = item.current_stock / set_item.quantity
        - Return min(available_stocks)

        Args:
            set_product_id: Set product UUID
            db: Database session

        Returns:
            Minimum available stock quantity based on component items

        Preconditions:
        - set_product_id must be a set product

        Postconditions:
        - Returns integer stock quantity (rounded down)
        """
        # Get set composition
        set_items = self.set_item_repo.get_by_set_product_id(set_product_id, db)

        if not set_items:
            return 0

        # Calculate available stock for each component
        available_stocks = []
        for set_item in set_items:
            item_product = self.product_repo.get_by_id(set_item.item_product_id, db)
            if item_product:
                # How many sets can be made from this item?
                available = item_product.current_stock // set_item.quantity
                available_stocks.append(available)
            else:
                # If item not found, set stock is 0
                return 0

        # Return minimum (bottleneck determines set availability)
        return min(available_stocks) if available_stocks else 0

    def check_stock_availability(
        self, checkout_items: List[Dict[str, Any]], db: Session
    ) -> StockCheckResult:
        """Check if requested items are available in stock.

        This method expands set products into their component items and
        calculates the total required quantity for each single product,
        then checks if sufficient stock is available.

        Args:
            checkout_items: List of dicts with product_id and quantity
            db: Database session

        Returns:
            StockCheckResult with availability status and insufficient items

        Preconditions:
        - checkout_items is not empty
        - Each item has product_id and quantity keys

        Postconditions:
        - Does not modify any data (read-only operation)

        Invariants:
        - Database state remains unchanged
        """
        # Step 1: Calculate total required quantity for each product
        # by expanding set products into component items
        required_quantities = {}  # {product_id: total_quantity}

        for item in checkout_items:
            product_id = item["product_id"]
            requested_quantity = item["quantity"]

            product = self.product_repo.get_by_id(product_id, db)

            if not product:
                # Product not found
                return StockCheckResult(
                    is_available=False,
                    insufficient_items=[product_id],
                )

            if product.product_type == "single":
                # Single product: add to required quantities
                current_required = required_quantities.get(product_id, 0)
                required_quantities[product_id] = current_required + requested_quantity

            elif product.product_type == "set":
                # Set product: expand into component items
                set_items = self.set_item_repo.get_by_set_product_id(product_id, db)
                for set_item in set_items:
                    component_id = set_item.item_product_id
                    component_quantity = set_item.quantity * requested_quantity
                    current_required = required_quantities.get(component_id, 0)
                    required_quantities[component_id] = current_required + component_quantity

        # Step 2: Check if sufficient stock is available for all products
        insufficient_items = []

        for product_id, required_qty in required_quantities.items():
            product = self.product_repo.get_by_id(product_id, db)
            if not product:
                insufficient_items.append(product_id)
                continue

            if product.current_stock < required_qty:
                insufficient_items.append(product_id)

        is_available = len(insufficient_items) == 0

        return StockCheckResult(
            is_available=is_available,
            insufficient_items=insufficient_items,
        )

    def get_inventory_status(self, db: Session) -> List[ProductInventory]:
        """Get current inventory status for all products.

        Args:
            db: Database session

        Returns:
            List of ProductInventory objects with current status

        Preconditions:
        - db session is active

        Postconditions:
        - Returns inventory status for all products
        - Set products have calculated stock from components
        """
        products = self.product_repo.get_all(db=db)
        inventory_status = []

        for product in products:
            if product.product_type == "single":
                current_stock = product.current_stock
            elif product.product_type == "set":
                # Calculate stock from component items
                current_stock = self.calculate_set_stock(product.id, db)
            else:
                current_stock = 0

            # Calculate stock rate
            if product.initial_stock > 0:
                stock_rate = current_stock / product.initial_stock
            else:
                stock_rate = 0.0

            is_out_of_stock = current_stock == 0

            inventory_status.append(
                ProductInventory(
                    id=product.id,
                    name=product.name,
                    product_type=product.product_type,
                    current_stock=current_stock,
                    initial_stock=product.initial_stock,
                    stock_rate=stock_rate,
                    is_out_of_stock=is_out_of_stock,
                )
            )

        return inventory_status
