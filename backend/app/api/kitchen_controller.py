"""Kitchen API Controller.

This module provides REST API endpoints for kitchen ticket management:
- GET /api/kitchen/tickets - Retrieve active tickets
- POST /api/kitchen/tickets/:ticket_id/complete - Complete ticket
"""

from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.services.kitchen_ticket_service import (
    KitchenTicketService,
    TicketNotFoundError,
    TicketAlreadyCompletedError,
)
from app.schemas.kitchen import (
    KitchenTicketListResponse,
    CompleteTicketRequest,
    CompleteTicketResponse,
    ErrorResponse,
)


# ========================================
# Dependency Injection
# ========================================

def get_kitchen_ticket_service() -> KitchenTicketService:
    """Get KitchenTicketService instance."""
    return KitchenTicketService()


# ========================================
# Router
# ========================================

router = APIRouter(prefix="/api/kitchen", tags=["kitchen"])


# ========================================
# Endpoints
# ========================================

@router.get(
    "/tickets",
    response_model=KitchenTicketListResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"description": "Unauthorized - Authentication required"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def get_tickets(
    db: Annotated[Session, Depends(get_db)],
    kitchen_ticket_service: Annotated[KitchenTicketService, Depends(get_kitchen_ticket_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Get all active (uncompleted) kitchen tickets.

    This endpoint:
    - Returns tickets sorted by oldest first (chronological order)
    - Includes elapsed time since order
    - Expands set products into their components
    - Excludes completed tickets

    Args:
        db: Database session
        kitchen_ticket_service: KitchenTicketService instance
        current_user: Authenticated user information

    Returns:
        KitchenTicketListResponse with list of active tickets

    Raises:
        HTTPException 401: Authentication required
        HTTPException 500: Internal server error

    Requirements:
        - 1.1: Automatic ticket display
        - 1.2: Set product display with components
        - 2.1: Chronological sorting
        - 2.3: Elapsed time display
        - 6.1: Real-time updates (via polling)
    """
    try:
        tickets = kitchen_ticket_service.get_active_tickets(db)
        return KitchenTicketListResponse(tickets=tickets)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "チケット一覧の取得中にエラーが発生しました。",
            },
        )


@router.post(
    "/tickets/{ticket_id}/complete",
    response_model=CompleteTicketResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"description": "Unauthorized - Authentication required"},
        404: {"model": ErrorResponse, "description": "Ticket not found"},
        409: {"model": ErrorResponse, "description": "Ticket already completed"},
        422: {"description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def complete_ticket(
    ticket_id: UUID,
    request: CompleteTicketRequest,
    db: Annotated[Session, Depends(get_db)],
    kitchen_ticket_service: Annotated[KitchenTicketService, Depends(get_kitchen_ticket_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Mark a kitchen ticket as completed.

    This endpoint:
    - Validates ticket existence
    - Checks ticket is not already completed
    - Records completion timestamp and user
    - Removes ticket from active list

    Args:
        ticket_id: UUID of the ticket to complete
        request: CompleteTicketRequest with completed_by field
        db: Database session
        kitchen_ticket_service: KitchenTicketService instance
        current_user: Authenticated user information

    Returns:
        CompleteTicketResponse with completion details

    Raises:
        HTTPException 401: Authentication required
        HTTPException 404: Ticket not found
        HTTPException 409: Ticket already completed
        HTTPException 422: Validation error
        HTTPException 500: Internal server error

    Requirements:
        - 3.1: Complete button functionality
        - 3.2: Ticket deletion from list
        - 3.4: Completion record (timestamp and user)
    """
    try:
        result = kitchen_ticket_service.complete_ticket(
            ticket_id=ticket_id,
            completed_by=request.completed_by,
            db=db,
        )
        return result

    except TicketNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "TICKET_NOT_FOUND",
                "message": f"チケットが見つかりません: {ticket_id}",
            },
        )

    except TicketAlreadyCompletedError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error_code": "TICKET_ALREADY_COMPLETED",
                "message": f"このチケットは既に完了済みです: {ticket_id}",
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "チケット完了処理中にエラーが発生しました。",
            },
        )
