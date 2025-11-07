"""KitchenTicket repository for data access operations."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.kitchen_ticket import KitchenTicket


class KitchenTicketRepository:
    """Repository for KitchenTicket entity operations.

    This repository handles all database operations for kitchen tickets,
    including creating tickets, marking them as completed, and retrieving
    incomplete tickets.
    """

    def create_ticket(self, sale_id: UUID, db: Session) -> KitchenTicket:
        """Create a new kitchen ticket for a sale.

        NOTE: This method does NOT commit the transaction.
        The caller (Service layer) is responsible for transaction management.

        Args:
            sale_id: UUID of the sales_history record
            db: Database session

        Returns:
            Created KitchenTicket instance

        Raises:
            IntegrityError: If sale_id doesn't exist or ticket already exists for this sale
        """
        ticket = KitchenTicket(sale_id=sale_id)
        db.add(ticket)
        db.flush()  # Get the ticket ID without committing
        return ticket

    def get_incomplete_sale_ids(self, db: Session) -> List[UUID]:
        """Get list of sale IDs for incomplete (pending) tickets.

        Args:
            db: Database session

        Returns:
            List of UUIDs of sales with incomplete tickets
        """
        stmt = select(KitchenTicket.sale_id).where(KitchenTicket.completed_at.is_(None))
        result = db.execute(stmt)
        return [row[0] for row in result.fetchall()]

    def mark_as_completed(
        self,
        ticket_id: UUID,
        completed_by: str,
        completed_at: datetime,
        db: Session
    ) -> None:
        """Mark a kitchen ticket as completed.

        NOTE: This method does NOT commit the transaction.
        The caller (Service layer) is responsible for transaction management.

        Args:
            ticket_id: UUID of the ticket to complete
            completed_by: User identifier who completed the ticket
            completed_at: Timestamp when ticket was completed
            db: Database session

        Raises:
            ValueError: If ticket not found
        """
        stmt = select(KitchenTicket).where(KitchenTicket.id == ticket_id)
        ticket = db.execute(stmt).scalar_one_or_none()

        if not ticket:
            raise ValueError(f"Ticket not found: {ticket_id}")

        ticket.completed_at = completed_at
        ticket.completed_by = completed_by
        db.flush()

    def get_ticket_by_sale_id(self, sale_id: UUID, db: Session) -> Optional[KitchenTicket]:
        """Get a kitchen ticket by sale ID.

        Args:
            sale_id: UUID of the sales_history record
            db: Database session

        Returns:
            KitchenTicket instance if found, None otherwise
        """
        stmt = select(KitchenTicket).where(KitchenTicket.sale_id == sale_id)
        return db.execute(stmt).scalar_one_or_none()

    def get_ticket_by_id(self, ticket_id: UUID, db: Session) -> Optional[KitchenTicket]:
        """Get a kitchen ticket by ticket ID.

        Args:
            ticket_id: UUID of the ticket
            db: Database session

        Returns:
            KitchenTicket instance if found, None otherwise
        """
        stmt = select(KitchenTicket).where(KitchenTicket.id == ticket_id)
        return db.execute(stmt).scalar_one_or_none()
