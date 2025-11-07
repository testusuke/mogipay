"""KitchenTicket service for business logic operations."""

from typing import List
from uuid import UUID
from datetime import datetime
from dataclasses import dataclass
from sqlalchemy.orm import Session

from app.repositories.kitchen_ticket_repository import KitchenTicketRepository
from app.repositories.sales_history_repository import SalesHistoryRepository
from app.repositories.set_item_repository import SetItemRepository
from app.models.kitchen_ticket import (
    KitchenTicketResponse,
    KitchenTicketItem,
    ComponentItem,
    CompleteTicketResponse,
)


# Custom exceptions
class TicketNotFoundError(Exception):
    """Raised when ticket is not found."""

    pass


class TicketAlreadyCompletedError(Exception):
    """Raised when ticket is already completed."""

    pass


class KitchenTicketService:
    """Service for kitchen ticket management.

    This service handles:
    - Retrieving active tickets from sales history
    - Expanding set products into components
    - Calculating elapsed time since order
    - Completing tickets with timestamp tracking
    """

    def __init__(
        self,
        kitchen_ticket_repo: KitchenTicketRepository = None,
        sales_history_repo: SalesHistoryRepository = None,
        set_item_repo: SetItemRepository = None,
    ):
        """Initialize KitchenTicketService with repository dependencies.

        Args:
            kitchen_ticket_repo: KitchenTicketRepository instance
            sales_history_repo: SalesHistoryRepository instance
            set_item_repo: SetItemRepository instance
        """
        self.kitchen_ticket_repo = kitchen_ticket_repo or KitchenTicketRepository()
        self.sales_history_repo = sales_history_repo or SalesHistoryRepository()
        self.set_item_repo = set_item_repo or SetItemRepository()

    def get_active_tickets(self, db: Session) -> List[KitchenTicketResponse]:
        """Get all active (uncompleted) kitchen tickets.

        This method:
        1. Retrieves incomplete sale IDs from kitchen_tickets table
        2. Fetches sales history and items for those IDs
        3. Expands set products into their components
        4. Calculates elapsed time since order
        5. Sorts tickets by oldest first

        Args:
            db: Database session

        Returns:
            List of KitchenTicketResponse sorted by order time (oldest first)

        Preconditions:
        - db session is active

        Postconditions:
        - Tickets are sorted by timestamp ascending
        - Set products are expanded with components
        - Elapsed time is calculated for each ticket

        Invariants:
        - Completed tickets are never included
        - Elapsed time is always >= 0
        """
        # Step 1: Get incomplete sale IDs
        incomplete_sale_ids = self.kitchen_ticket_repo.get_incomplete_sale_ids(db)

        if not incomplete_sale_ids:
            return []

        # Step 2: Fetch sales history for incomplete tickets
        sales_list = []
        for sale_id in incomplete_sale_ids:
            sale = self.sales_history_repo.get_by_id(sale_id, db)
            if sale:
                sales_list.append(sale)

        # Step 3: Sort by timestamp (oldest first)
        sales_list.sort(key=lambda s: s.timestamp)

        # Step 4: Build ticket responses with item expansion
        tickets = []
        current_time = datetime.utcnow()

        for sale in sales_list:
            # Calculate elapsed time
            elapsed_time = current_time - sale.timestamp
            elapsed_minutes = int(elapsed_time.total_seconds() // 60)

            # Build ticket items
            ticket_items = []
            for sale_item in sale.sale_items:
                # Check if this is a set product by trying to get set items
                set_items = self.set_item_repo.get_by_set_product_id(
                    sale_item.product_id, db
                )

                if set_items:
                    # This is a set product - expand components
                    components = []
                    for set_item in set_items:
                        # Get component product name
                        # For now, we need to implement get_product_name_by_id in SalesHistoryRepository
                        component_name = self._get_product_name_by_id(
                            set_item.item_product_id, db
                        )
                        component_quantity = set_item.quantity * sale_item.quantity
                        components.append(
                            ComponentItem(
                                name=component_name,
                                quantity=component_quantity,
                            )
                        )

                    ticket_items.append(
                        KitchenTicketItem(
                            product_name=sale_item.product_name,
                            product_type="set",
                            quantity=sale_item.quantity,
                            components=components,
                        )
                    )
                else:
                    # This is a single product
                    ticket_items.append(
                        KitchenTicketItem(
                            product_name=sale_item.product_name,
                            product_type="single",
                            quantity=sale_item.quantity,
                            components=None,
                        )
                    )

            # Get or create kitchen ticket for this sale
            kitchen_ticket = self.kitchen_ticket_repo.get_ticket_by_sale_id(
                sale.id, db
            )
            if not kitchen_ticket:
                # Create ticket if it doesn't exist (this handles the case where
                # a sale was created but no ticket was created yet)
                kitchen_ticket = self.kitchen_ticket_repo.create_ticket(sale.id, db)
                db.commit()

            tickets.append(
                KitchenTicketResponse(
                    id=str(kitchen_ticket.id),
                    sale_id=str(sale.id),
                    order_time=sale.timestamp,
                    elapsed_minutes=elapsed_minutes,
                    items=ticket_items,
                )
            )

        return tickets

    def complete_ticket(
        self, ticket_id: UUID, completed_by: str, db: Session
    ) -> CompleteTicketResponse:
        """Mark a kitchen ticket as completed.

        This method:
        1. Validates ticket existence
        2. Checks ticket is not already completed
        3. Marks ticket as completed with timestamp
        4. Commits transaction

        Args:
            ticket_id: UUID of the ticket to complete
            completed_by: User identifier who completed the ticket
            db: Database session

        Returns:
            CompleteTicketResponse with completion details

        Raises:
            TicketNotFoundError: If ticket does not exist
            TicketAlreadyCompletedError: If ticket is already completed

        Preconditions:
        - ticket_id exists in database
        - ticket is not already completed

        Postconditions:
        - Ticket is marked as completed
        - completed_at and completed_by are set
        - Transaction is committed

        Invariants:
        - Completed tickets cannot be completed again
        """
        try:
            # Step 1: Get ticket
            ticket = self.kitchen_ticket_repo.get_ticket_by_id(ticket_id, db)

            if not ticket:
                raise TicketNotFoundError(f"Ticket not found: {ticket_id}")

            # Step 2: Check if already completed
            if ticket.completed_at is not None:
                raise TicketAlreadyCompletedError(
                    f"Ticket {ticket_id} is already completed"
                )

            # Step 3: Mark as completed
            completed_at = datetime.utcnow()
            self.kitchen_ticket_repo.mark_as_completed(
                ticket_id=ticket_id,
                completed_by=completed_by,
                completed_at=completed_at,
                db=db,
            )

            # Step 4: Commit transaction
            db.commit()

            return CompleteTicketResponse(
                ticket_id=str(ticket_id),
                completed_at=completed_at,
                completed_by=completed_by,
            )

        except (TicketNotFoundError, TicketAlreadyCompletedError):
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise e

    def _get_product_name_by_id(self, product_id: UUID, db: Session) -> str:
        """Get product name by ID.

        This is a helper method to retrieve product names for set components.

        Args:
            product_id: Product UUID
            db: Database session

        Returns:
            Product name string
        """
        # We need to get the product name from somewhere
        # The easiest way is to look it up in sale_items
        from app.models.sale_item import SaleItem
        from sqlalchemy import select

        stmt = select(SaleItem.product_name).where(SaleItem.product_id == product_id).limit(1)
        result = db.execute(stmt)
        product_name = result.scalar_one_or_none()

        if product_name:
            return product_name

        # If not found in sale_items, look up in products table
        from app.models.product import Product

        stmt = select(Product.name).where(Product.id == product_id)
        result = db.execute(stmt)
        product_name = result.scalar_one_or_none()

        return product_name if product_name else "Unknown Product"
