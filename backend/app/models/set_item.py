"""SetItem model for set_items table."""

import uuid
from sqlalchemy import Column, Integer, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class SetItem(Base):
    """SetItem model representing set product composition.

    Attributes:
        id: Set item UUID (primary key)
        set_product_id: Set product UUID (foreign key to products)
        item_product_id: Item product UUID (foreign key to products)
        quantity: Quantity of item product in the set
    """

    __tablename__ = "set_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    set_product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    item_product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    quantity = Column(Integer, nullable=False)

    # Relationships
    set_product = relationship("Product", back_populates="set_items", foreign_keys=[set_product_id])
    item_product = relationship("Product", back_populates="item_in_sets", foreign_keys=[item_product_id])

    # Constraints
    __table_args__ = (
        CheckConstraint("quantity > 0", name="positive_quantity"),
        UniqueConstraint("set_product_id", "item_product_id", name="unique_set_item_combination"),
    )
