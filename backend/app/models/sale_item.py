"""SaleItem model for sale_items table."""

import uuid
from sqlalchemy import Column, String, Integer, Numeric, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class SaleItem(Base):
    """SaleItem model representing sale item details.

    Attributes:
        id: Sale item UUID (primary key)
        sale_id: Sale UUID (foreign key to sales_history)
        product_id: Product UUID (foreign key to products)
        product_name: Product name (snapshot at sale time)
        quantity: Quantity sold
        unit_cost: Unit cost (snapshot at sale time)
        sale_price: Sale price (snapshot at sale time)
        subtotal: Subtotal amount (sale_price * quantity)
    """

    __tablename__ = "sale_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sale_id = Column(UUID(as_uuid=True), ForeignKey("sales_history.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    product_name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_cost = Column(Numeric(10, 2), nullable=False)
    sale_price = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)

    # Relationships
    sale = relationship("SalesHistory", back_populates="sale_items")
    product = relationship("Product", back_populates="sale_items")

    # Constraints
    __table_args__ = (
        CheckConstraint("quantity > 0", name="positive_quantity"),
        CheckConstraint("subtotal >= 0", name="positive_subtotal"),
    )
