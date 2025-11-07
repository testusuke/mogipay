"""KitchenTicket model for kitchen_tickets table."""

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class KitchenTicket(Base):
    """KitchenTicket model representing kitchen order tickets.

    Attributes:
        id: Kitchen ticket UUID (primary key)
        sale_id: Reference to sales_history.id
        completed_at: Timestamp when ticket was completed (NULL = pending)
        completed_by: User who completed the ticket
        created_at: Ticket creation timestamp
    """

    __tablename__ = "kitchen_tickets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sale_id = Column(UUID(as_uuid=True), ForeignKey("sales_history.id", ondelete="CASCADE"), nullable=False)
    completed_at = Column(DateTime, nullable=True)
    completed_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    sale = relationship("SalesHistory", backref="kitchen_ticket")

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint("sale_id", name="unique_sale_ticket"),
        Index(
            "idx_kitchen_tickets_completed",
            "completed_at",
            postgresql_where=Column("completed_at").is_(None)
        ),
    )


class KitchenTicketResponse(BaseModel):
    """Pydantic model for kitchen ticket response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    sale_id: str
    order_time: datetime
    elapsed_minutes: int
    items: list["KitchenTicketItem"]


class KitchenTicketItem(BaseModel):
    """Pydantic model for kitchen ticket item."""

    model_config = ConfigDict(from_attributes=True)

    product_name: str
    product_type: str  # "single" or "set"
    quantity: int
    components: Optional[list["ComponentItem"]] = None


class ComponentItem(BaseModel):
    """Pydantic model for set product component."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    quantity: int


class CompleteTicketRequest(BaseModel):
    """Pydantic model for ticket completion request."""

    completed_by: str


class CompleteTicketResponse(BaseModel):
    """Pydantic model for ticket completion response."""

    model_config = ConfigDict(from_attributes=True)

    ticket_id: str
    completed_at: datetime
    completed_by: str
