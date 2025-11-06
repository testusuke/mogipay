"""Product repository for data access operations."""

from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from app.models.product import Product


class InsufficientStockError(Exception):
    """Exception raised when attempting to decrement stock below zero."""

    pass


class ProductRepository:
    """Repository for Product entity operations.

    This repository handles all database operations for products,
    including CRUD operations and stock management.
    """

    def create(
        self,
        name: str,
        unit_cost: Decimal,
        sale_price: Decimal,
        initial_stock: int,
        current_stock: int,
        product_type: str,
        db: Session,
    ) -> Product:
        """Create a new product.

        NOTE: This method does NOT commit the transaction.
        The caller (Service layer) is responsible for transaction management.

        Args:
            name: Product name
            unit_cost: Unit cost (purchase price)
            sale_price: Sale price (selling price)
            initial_stock: Initial stock quantity
            current_stock: Current stock quantity
            product_type: Product type ('single' or 'set')
            db: Database session

        Returns:
            Created Product instance

        Raises:
            IntegrityError: If database constraints are violated
        """
        product = Product(
            name=name,
            unit_cost=unit_cost,
            sale_price=sale_price,
            initial_stock=initial_stock,
            current_stock=current_stock,
            product_type=product_type,
        )
        db.add(product)
        db.flush()  # Get the ID without committing
        return product

    def get_by_id(self, product_id: UUID, db: Session) -> Optional[Product]:
        """Retrieve a product by ID.

        Args:
            product_id: Product UUID
            db: Database session

        Returns:
            Product instance if found, None otherwise
        """
        stmt = select(Product).where(Product.id == product_id)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_all(
        self, product_type: Optional[str] = None, db: Session = None
    ) -> List[Product]:
        """Retrieve all products, optionally filtered by type.

        Args:
            product_type: Optional product type filter ('single' or 'set')
            db: Database session

        Returns:
            List of Product instances
        """
        stmt = select(Product)
        if product_type:
            stmt = stmt.where(Product.product_type == product_type)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def update(
        self, product_id: UUID, updates: Dict[str, Any], db: Session
    ) -> Optional[Product]:
        """Update a product.

        NOTE: This method does NOT commit the transaction.
        The caller (Service layer) is responsible for transaction management.

        Args:
            product_id: Product UUID
            updates: Dictionary of fields to update
            db: Database session

        Returns:
            Updated Product instance if found, None otherwise

        Raises:
            IntegrityError: If database constraints are violated
        """
        product = self.get_by_id(product_id, db)
        if not product:
            return None

        for key, value in updates.items():
            if hasattr(product, key):
                setattr(product, key, value)

        db.flush()  # Ensure changes are ready
        return product

    def delete(self, product_id: UUID, db: Session) -> bool:
        """Delete a product.

        NOTE: This method does NOT commit the transaction.
        The caller (Service layer) is responsible for transaction management.

        Args:
            product_id: Product UUID
            db: Database session

        Returns:
            True if product was deleted, False if not found
        """
        product = self.get_by_id(product_id, db)
        if not product:
            return False

        db.delete(product)
        db.flush()  # Ensure deletion is ready
        return True

    def decrement_stock(
        self, product_id: UUID, quantity: int, db: Session
    ) -> Product:
        """Decrement product stock with row locking.

        This method uses SELECT FOR UPDATE to prevent race conditions
        during concurrent stock decrements.

        NOTE: This method does NOT commit the transaction.
        The caller (Service layer) is responsible for transaction management.

        Args:
            product_id: Product UUID
            quantity: Quantity to decrement
            db: Database session

        Returns:
            Updated Product instance

        Raises:
            InsufficientStockError: If stock would become negative
            ValueError: If product not found
        """
        # Use SELECT FOR UPDATE to lock the row
        stmt = select(Product).where(Product.id == product_id).with_for_update()
        result = db.execute(stmt)
        product = result.scalar_one_or_none()

        if not product:
            raise ValueError(f"Product {product_id} not found")

        # Check if we have sufficient stock
        if product.current_stock < quantity:
            raise InsufficientStockError(
                f"Insufficient stock: requested {quantity}, available {product.current_stock}"
            )

        # Decrement stock
        product.current_stock -= quantity
        # NOTE: No commit here! Service layer manages the transaction.
        db.flush()  # Ensure changes are ready
        return product
