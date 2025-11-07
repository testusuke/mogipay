"""create kitchen tickets table

Revision ID: 8651b808853a
Revises: 0772d324e452
Create Date: 2025-11-07 14:59:27.029818

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8651b808853a'
down_revision: Union[str, Sequence[str], None] = '0772d324e452'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create kitchen_tickets table
    op.create_table(
        'kitchen_tickets',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('sale_id', sa.UUID(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('completed_by', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['sale_id'], ['sales_history.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sale_id', name='unique_sale_ticket')
    )

    # Create partial index for incomplete tickets (WHERE completed_at IS NULL)
    op.create_index(
        'idx_kitchen_tickets_completed',
        'kitchen_tickets',
        ['completed_at'],
        unique=False,
        postgresql_where=sa.text('completed_at IS NULL')
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop index first
    op.drop_index('idx_kitchen_tickets_completed', table_name='kitchen_tickets')
    # Drop table
    op.drop_table('kitchen_tickets')
