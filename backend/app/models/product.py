"""Product model for products table."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Product(Base):
    """Product model representing both single and set products.

    Attributes:
        id: Product UUID (primary key)
        name: Product name
        unit_cost: Unit cost (purchase price)
        sale_price: Sale price (selling price)
        initial_stock: Initial stock quantity
        current_stock: Current stock quantity
        product_type: Product type ('single' or 'set')
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    unit_cost = Column(Integer, nullable=False)
    sale_price = Column(Integer, nullable=False)
    initial_stock = Column(Integer, nullable=False)
    current_stock = Column(Integer, nullable=False)
    product_type = Column(String(20), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    set_items = relationship("SetItem", back_populates="set_product", foreign_keys="SetItem.set_product_id", cascade="all, delete-orphan")
    item_in_sets = relationship("SetItem", back_populates="item_product", foreign_keys="SetItem.item_product_id")
    sale_items = relationship("SaleItem", back_populates="product")

    # Constraints
    __table_args__ = (
        CheckConstraint("unit_cost >= 0", name="positive_unit_cost"),
        CheckConstraint("sale_price >= 0", name="positive_sale_price"),
        CheckConstraint("current_stock >= 0", name="non_negative_stock"),
        CheckConstraint("product_type IN ('single', 'set')", name="valid_product_type"),
    )
