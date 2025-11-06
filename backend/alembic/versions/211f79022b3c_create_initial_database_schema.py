"""create initial database schema

Revision ID: 211f79022b3c
Revises:
Create Date: 2025-11-06 18:55:32.113960

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '211f79022b3c'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create products table
    op.create_table(
        'products',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('unit_cost', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('sale_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('initial_stock', sa.Integer(), nullable=False),
        sa.Column('current_stock', sa.Integer(), nullable=False),
        sa.Column('product_type', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.CheckConstraint('unit_cost >= 0', name='positive_unit_cost'),
        sa.CheckConstraint('sale_price >= 0', name='positive_sale_price'),
        sa.CheckConstraint('current_stock >= 0', name='non_negative_stock'),
        sa.CheckConstraint("product_type IN ('single', 'set')", name='valid_product_type'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_products_type', 'products', ['product_type'])
    op.create_index('idx_products_created_at', 'products', ['created_at'])

    # Create set_items table
    op.create_table(
        'set_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('set_product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('item_product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.CheckConstraint('quantity > 0', name='positive_quantity'),
        sa.ForeignKeyConstraint(['set_product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['item_product_id'], ['products.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('set_product_id', 'item_product_id', name='unique_set_item_combination')
    )
    op.create_index('idx_set_items_set_product', 'set_items', ['set_product_id'])

    # Create sales_history table
    op.create_table(
        'sales_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('total_amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.CheckConstraint('total_amount >= 0', name='positive_total_amount'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_sales_history_timestamp', 'sales_history', ['timestamp'])

    # Create sale_items table
    op.create_table(
        'sale_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('sale_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_name', sa.String(length=255), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_cost', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('sale_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('subtotal', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.CheckConstraint('quantity > 0', name='positive_quantity'),
        sa.CheckConstraint('subtotal >= 0', name='positive_subtotal'),
        sa.ForeignKeyConstraint(['sale_id'], ['sales_history.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_sale_items_sale_id', 'sale_items', ['sale_id'])
    op.create_index('idx_sale_items_product_id', 'sale_items', ['product_id'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop tables in reverse order (respecting foreign key constraints)
    op.drop_index('idx_sale_items_product_id', table_name='sale_items')
    op.drop_index('idx_sale_items_sale_id', table_name='sale_items')
    op.drop_table('sale_items')

    op.drop_index('idx_sales_history_timestamp', table_name='sales_history')
    op.drop_table('sales_history')

    op.drop_index('idx_set_items_set_product', table_name='set_items')
    op.drop_table('set_items')

    op.drop_index('idx_products_created_at', table_name='products')
    op.drop_index('idx_products_type', table_name='products')
    op.drop_table('products')
