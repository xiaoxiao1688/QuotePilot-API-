"""initial migration: create users, suppliers, quotes, quote_items tables

Revision ID: 0001_initial
Revises: 
Create Date: 2026-04-29 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('nickname', sa.String(length=50), nullable=True),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('company_id', sa.String(length=36), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uq_users_email'),
        sa.UniqueConstraint('username', name='uq_users_username')
    )
    op.create_index(op.f('ix_users_company_id'), 'users', ['company_id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    op.create_table(
        'suppliers',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('short_name', sa.String(length=50), nullable=True),
        sa.Column('contact_person', sa.String(length=50), nullable=True),
        sa.Column('phone', sa.String(length=30), nullable=True),
        sa.Column('email', sa.String(length=100), nullable=True),
        sa.Column('address', sa.String(length=500), nullable=True),
        sa.Column('tax_id', sa.String(length=50), nullable=True),
        sa.Column('bank_name', sa.String(length=100), nullable=True),
        sa.Column('bank_account', sa.String(length=50), nullable=True),
        sa.Column('rating', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('extra', sa.JSON(), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_suppliers_created_by', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_suppliers_name')
    )
    op.create_index(op.f('ix_suppliers_created_by'), 'suppliers', ['created_by'], unique=False)
    op.create_index(op.f('ix_suppliers_email'), 'suppliers', ['email'], unique=False)
    op.create_index(op.f('ix_suppliers_name'), 'suppliers', ['name'], unique=True)
    op.create_index(op.f('ix_suppliers_short_name'), 'suppliers', ['short_name'], unique=False)
    op.create_index(op.f('ix_suppliers_status'), 'suppliers', ['status'], unique=False)

    op.create_table(
        'quotes',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('quote_number', sa.String(length=50), nullable=True),
        sa.Column('supplier_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('demand_title', sa.String(length=200), nullable=False),
        sa.Column('currency', sa.String(length=8), nullable=False),
        sa.Column('item_count', sa.Integer(), nullable=False),
        sa.Column('sub_total', sa.Float(), nullable=False),
        sa.Column('shipping_fee', sa.Float(), nullable=False),
        sa.Column('tax_rate', sa.Float(), nullable=False),
        sa.Column('tax_amount', sa.Float(), nullable=False),
        sa.Column('discount_amount', sa.Float(), nullable=False),
        sa.Column('grand_total', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=True),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('terms', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('extra', sa.JSON(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejected_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], name='fk_quotes_supplier_id', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_quotes_user_id', ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('quote_number', name='uq_quotes_quote_number')
    )
    op.create_index(op.f('ix_quotes_demand_title'), 'quotes', ['demand_title'], unique=False)
    op.create_index(op.f('ix_quotes_quote_number'), 'quotes', ['quote_number'], unique=True)
    op.create_index(op.f('ix_quotes_status'), 'quotes', ['status'], unique=False)
    op.create_index(op.f('ix_quotes_supplier_id'), 'quotes', ['supplier_id'], unique=False)
    op.create_index(op.f('ix_quotes_user_id'), 'quotes', ['user_id'], unique=False)

    op.create_table(
        'quote_items',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('quote_id', sa.String(length=36), nullable=False),
        sa.Column('line_number', sa.Integer(), nullable=False),
        sa.Column('product_name', sa.String(length=200), nullable=False),
        sa.Column('product_code', sa.String(length=50), nullable=True),
        sa.Column('product_category', sa.String(length=100), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit', sa.String(length=20), nullable=False),
        sa.Column('unit_price', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=8), nullable=False),
        sa.Column('line_total', sa.Float(), nullable=False),
        sa.Column('lead_time_days', sa.Integer(), nullable=True),
        sa.Column('specs', sa.JSON(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['quote_id'], ['quotes.id'], name='fk_quote_items_quote_id', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('quote_id', 'line_number', name='uq_quote_items_quote_line')
    )
    op.create_index(op.f('ix_quote_items_product_category'), 'quote_items', ['product_category'], unique=False)
    op.create_index(op.f('ix_quote_items_product_code'), 'quote_items', ['product_code'], unique=False)
    op.create_index(op.f('ix_quote_items_quote_id'), 'quote_items', ['quote_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_quote_items_quote_id'), table_name='quote_items')
    op.drop_index(op.f('ix_quote_items_product_code'), table_name='quote_items')
    op.drop_index(op.f('ix_quote_items_product_category'), table_name='quote_items')
    op.drop_table('quote_items')

    op.drop_index(op.f('ix_quotes_user_id'), table_name='quotes')
    op.drop_index(op.f('ix_quotes_supplier_id'), table_name='quotes')
    op.drop_index(op.f('ix_quotes_status'), table_name='quotes')
    op.drop_index(op.f('ix_quotes_quote_number'), table_name='quotes')
    op.drop_index(op.f('ix_quotes_demand_title'), table_name='quotes')
    op.drop_table('quotes')

    op.drop_index(op.f('ix_suppliers_status'), table_name='suppliers')
    op.drop_index(op.f('ix_suppliers_short_name'), table_name='suppliers')
    op.drop_index(op.f('ix_suppliers_name'), table_name='suppliers')
    op.drop_index(op.f('ix_suppliers_email'), table_name='suppliers')
    op.drop_index(op.f('ix_suppliers_created_by'), table_name='suppliers')
    op.drop_table('suppliers')

    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_role'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_company_id'), table_name='users')
    op.drop_table('users')
