"""Kitchen API schemas.

This module defines Pydantic models for kitchen ticket API requests and responses:
- Request validation models
- Response serialization models
- Data transfer objects
"""

from typing import Optional, List, Literal
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ComponentItemResponse(BaseModel):
    """Component item in set product response.

    Attributes:
        name: Component product name
        quantity: Quantity of the component
    """

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description="Component product name")
    quantity: int = Field(..., gt=0, description="Component quantity")


class KitchenTicketItemResponse(BaseModel):
    """Kitchen ticket item in response.

    Attributes:
        product_name: Product name
        product_type: Product type ('single' or 'set')
        quantity: Quantity ordered
        components: List of components (for set products only)
    """

    model_config = ConfigDict(from_attributes=True)

    product_name: str = Field(..., description="Product name")
    product_type: Literal["single", "set"] = Field(..., description="Product type")
    quantity: int = Field(..., gt=0, description="Quantity ordered")
    components: Optional[List[ComponentItemResponse]] = Field(
        None,
        description="Components for set products (null for single products)"
    )


class KitchenTicketResponse(BaseModel):
    """Kitchen ticket response model.

    Attributes:
        id: Ticket UUID
        sale_id: Sale transaction UUID
        order_time: Order timestamp
        elapsed_minutes: Minutes elapsed since order
        items: List of ticket items
    """

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Ticket UUID")
    sale_id: str = Field(..., description="Sale transaction UUID")
    order_time: datetime = Field(..., description="Order timestamp")
    elapsed_minutes: int = Field(..., ge=0, description="Minutes elapsed since order")
    items: List[KitchenTicketItemResponse] = Field(..., description="List of ticket items")


class KitchenTicketListResponse(BaseModel):
    """Response model for kitchen ticket list endpoint.

    Attributes:
        tickets: List of active tickets
    """

    tickets: List[KitchenTicketResponse] = Field(..., description="List of active tickets")


class CompleteTicketRequest(BaseModel):
    """Request model for completing a ticket.

    Attributes:
        completed_by: User identifier who completed the ticket
    """

    completed_by: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="User identifier who completed the ticket"
    )


class CompleteTicketResponse(BaseModel):
    """Response model for ticket completion.

    Attributes:
        ticket_id: Completed ticket UUID
        completed_at: Completion timestamp
        completed_by: User who completed the ticket
    """

    model_config = ConfigDict(from_attributes=True)

    ticket_id: str = Field(..., description="Completed ticket UUID")
    completed_at: datetime = Field(..., description="Completion timestamp")
    completed_by: str = Field(..., description="User who completed the ticket")


class ErrorResponse(BaseModel):
    """Standard error response model.

    Attributes:
        error_code: Machine-readable error code
        message: Human-readable error message
        details: Optional additional error details
    """

    error_code: str
    message: str
    details: Optional[dict] = None
