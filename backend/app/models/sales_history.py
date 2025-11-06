"""SalesHistory model for sales_history table."""

import uuid
from datetime import datetime
from sqlalchemy import Column, Numeric, DateTime, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class SalesHistory(Base):
    """SalesHistory model representing sales transactions.

    Attributes:
        id: Sales history UUID (primary key)
        total_amount: Total amount of the sale
        timestamp: Transaction timestamp
    """

    __tablename__ = "sales_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    total_amount = Column(Numeric(10, 2), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    sale_items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint("total_amount >= 0", name="positive_total_amount"),
    )
