"""SetItem repository for data access operations."""

from typing import List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, delete

from app.models.set_item import SetItem


class SetItemRepository:
    """Repository for SetItem entity operations.

    This repository handles all database operations for set items,
    which represent the composition of set products.
    """

    def create(
        self,
        set_product_id: UUID,
        item_product_id: UUID,
        quantity: int,
        db: Session,
    ) -> SetItem:
        """Create a new set item.

        Args:
            set_product_id: Set product UUID
            item_product_id: Item product UUID
            quantity: Quantity of item in set
            db: Database session

        Returns:
            Created SetItem instance

        Raises:
            IntegrityError: If unique constraint or foreign key is violated
        """
        set_item = SetItem(
            set_product_id=set_product_id,
            item_product_id=item_product_id,
            quantity=quantity,
        )
        db.add(set_item)
        db.commit()
        db.refresh(set_item)
        return set_item

    def get_by_set_product_id(
        self, set_product_id: UUID, db: Session
    ) -> List[SetItem]:
        """Retrieve all set items for a set product.

        Args:
            set_product_id: Set product UUID
            db: Database session

        Returns:
            List of SetItem instances
        """
        stmt = select(SetItem).where(SetItem.set_product_id == set_product_id)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def create_bulk(
        self,
        set_product_id: UUID,
        items_data: List[Dict[str, Any]],
        db: Session,
    ) -> List[SetItem]:
        """Create multiple set items in bulk.

        Args:
            set_product_id: Set product UUID
            items_data: List of dicts with item_product_id and quantity
            db: Database session

        Returns:
            List of created SetItem instances

        Raises:
            IntegrityError: If unique constraint or foreign key is violated
        """
        set_items = []
        for item_data in items_data:
            set_item = SetItem(
                set_product_id=set_product_id,
                item_product_id=item_data["item_product_id"],
                quantity=item_data["quantity"],
            )
            db.add(set_item)
            set_items.append(set_item)

        db.commit()

        # Refresh all created items
        for set_item in set_items:
            db.refresh(set_item)

        return set_items

    def delete_by_set_product_id(self, set_product_id: UUID, db: Session) -> int:
        """Delete all set items for a set product.

        Args:
            set_product_id: Set product UUID
            db: Database session

        Returns:
            Number of deleted set items
        """
        stmt = delete(SetItem).where(SetItem.set_product_id == set_product_id)
        result = db.execute(stmt)
        db.commit()
        return result.rowcount
