"""Product service for product management and CRUD operations."""

from typing import List, Dict, Any, Optional
from uuid import UUID
from decimal import Decimal
from dataclasses import dataclass
from sqlalchemy.orm import Session

from app.repositories.product_repository import ProductRepository
from app.repositories.set_item_repository import SetItemRepository
from app.models.product import Product


@dataclass
class SetItemData:
    """Set item data for product creation.

    Attributes:
        product_id: Component product UUID
        quantity: Quantity of component in the set
    """

    product_id: UUID
    quantity: int


@dataclass
class CreateProductData:
    """Data for creating a product.

    Attributes:
        name: Product name
        unit_cost: Unit cost (purchase price)
        sale_price: Sale price (selling price)
        initial_stock: Initial stock quantity
        product_type: Product type ('single' or 'set')
        set_items: List of set items (required for set products)
    """

    name: str
    unit_cost: Decimal
    sale_price: Decimal
    initial_stock: int
    product_type: str
    set_items: Optional[List[SetItemData]] = None


class ProductService:
    """Service for product management.

    This service handles:
    - Product creation (both single and set products)
    - Product updates and price changes
    - Product deletion
    - Product retrieval and filtering
    - Set product composition management
    """

    def __init__(
        self,
        product_repo: ProductRepository = None,
        set_item_repo: SetItemRepository = None,
    ):
        """Initialize ProductService with repository dependencies.

        Args:
            product_repo: ProductRepository instance
            set_item_repo: SetItemRepository instance
        """
        self.product_repo = product_repo or ProductRepository()
        self.set_item_repo = set_item_repo or SetItemRepository()

    def create_product(
        self, data: CreateProductData, db: Session
    ) -> Product:
        """Create a new product.

        This method manages the transaction for creating both the product
        and its set items (if applicable) as a single atomic operation.

        Args:
            data: Product creation data
            db: Database session

        Returns:
            Created Product instance

        Raises:
            ValueError: If set product doesn't have set_items
            ValueError: If set_items contain invalid product IDs

        Preconditions:
        - data is validated
        - If product_type is 'set', set_items is not empty

        Postconditions:
        - Product is created
        - If set product, set_items are created
        - Both operations succeed or both are rolled back
        """
        try:
            # Validate set product requirements
            if data.product_type == "set":
                if not data.set_items or len(data.set_items) == 0:
                    raise ValueError(
                        "Set products must have at least one set_items component"
                    )

            # Create product
            product = self.product_repo.create(
                name=data.name,
                unit_cost=data.unit_cost,
                sale_price=data.sale_price,
                initial_stock=data.initial_stock,
                current_stock=data.initial_stock,
                product_type=data.product_type,
                db=db,
            )

            # Create set items if this is a set product
            if data.product_type == "set" and data.set_items:
                items_data = [
                    {
                        "item_product_id": item.product_id,
                        "quantity": item.quantity,
                    }
                    for item in data.set_items
                ]
                self.set_item_repo.create_bulk(
                    set_product_id=product.id,
                    items_data=items_data,
                    db=db,
                )

            # Commit transaction
            db.commit()
            db.refresh(product)
            return product

        except Exception:
            db.rollback()
            raise

    def update_price(
        self, product_id: UUID, new_price: Decimal, db: Session
    ) -> Product:
        """Update product sale price.

        This method manages the transaction for price updates.

        Args:
            product_id: Product UUID
            new_price: New sale price
            db: Database session

        Returns:
            Updated Product instance

        Raises:
            ValueError: If product not found

        Preconditions:
        - product_id exists
        - new_price > 0

        Postconditions:
        - Product sale_price is updated
        - updated_at is updated
        - Past sales history is unchanged (by design)
        """
        try:
            product = self.product_repo.get_by_id(product_id, db)
            if not product:
                raise ValueError(f"Product {product_id} not found")

            updated_product = self.product_repo.update(
                product_id,
                {"sale_price": new_price},
                db,
            )

            # Commit transaction
            db.commit()
            db.refresh(updated_product)
            return updated_product

        except Exception:
            db.rollback()
            raise

    def get_product_by_id(
        self, product_id: UUID, db: Session
    ) -> Optional[Product]:
        """Get product by ID.

        Args:
            product_id: Product UUID
            db: Database session

        Returns:
            Product instance if found, None otherwise
        """
        return self.product_repo.get_by_id(product_id, db)

    def get_all_products(
        self, db: Session, product_type: Optional[str] = None
    ) -> List[Product]:
        """Get all products, optionally filtered by type.

        Args:
            db: Database session
            product_type: Optional product type filter ('single' or 'set')

        Returns:
            List of Product instances
        """
        return self.product_repo.get_all(product_type=product_type, db=db)

    def update_product(
        self, product_id: UUID, updates: Dict[str, Any], db: Session
    ) -> Optional[Product]:
        """Update product attributes.

        This method manages the transaction for product updates.

        Args:
            product_id: Product UUID
            updates: Dictionary of fields to update
            db: Database session

        Returns:
            Updated Product instance if found, None otherwise
        """
        try:
            product = self.product_repo.get_by_id(product_id, db)
            if not product:
                return None

            updated_product = self.product_repo.update(product_id, updates, db)

            # Commit transaction
            db.commit()
            db.refresh(updated_product)
            return updated_product

        except Exception:
            db.rollback()
            raise

    def delete_product(self, product_id: UUID, db: Session) -> bool:
        """Delete a product.

        This method manages the transaction for product deletion.

        Args:
            product_id: Product UUID
            db: Database session

        Returns:
            True if product was deleted, False if not found
        """
        try:
            result = self.product_repo.delete(product_id, db)

            if result:
                # Commit transaction
                db.commit()

            return result

        except Exception:
            db.rollback()
            raise
