"""add sensitive_materials, supplier_packaging_capabilities, transport_environment_risks, adaptation_evaluations tables

Revision ID: 0003_add_transport_evaluation_tables
Revises: 0002_add_substitute_material_and_certificate_tables
Create Date: 2026-05-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '0003_add_transport_evaluation_tables'
down_revision = '0002_add_substitute_material_and_certificate_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'sensitive_materials',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('material_code', sa.String(length=50), nullable=False),
        sa.Column('material_name', sa.String(length=200), nullable=False),
        sa.Column('min_temp', sa.Float(), nullable=True),
        sa.Column('max_temp', sa.Float(), nullable=True),
        sa.Column('min_humidity', sa.Float(), nullable=True),
        sa.Column('max_humidity', sa.Float(), nullable=True),
        sa.Column('shock_proof_level', sa.String(length=20), nullable=True),
        sa.Column('shelf_life_days', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('extra', sa.JSON(), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_sensitive_materials_created_by', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('material_code', name='uq_sensitive_materials_material_code')
    )
    op.create_index(op.f('ix_sensitive_materials_created_by'), 'sensitive_materials', ['created_by'], unique=False)
    op.create_index(op.f('ix_sensitive_materials_material_code'), 'sensitive_materials', ['material_code'], unique=True)
    op.create_index(op.f('ix_sensitive_materials_material_name'), 'sensitive_materials', ['material_name'], unique=False)

    op.create_table(
        'supplier_packaging_capabilities',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('supplier_id', sa.String(length=36), nullable=False),
        sa.Column('packaging_method', sa.String(length=50), nullable=True),
        sa.Column('has_desiccant', sa.Boolean(), nullable=False),
        sa.Column('has_vacuum_pack', sa.Boolean(), nullable=False),
        sa.Column('has_cold_chain', sa.Boolean(), nullable=False),
        sa.Column('cold_chain_min_temp', sa.Float(), nullable=True),
        sa.Column('cold_chain_max_temp', sa.Float(), nullable=True),
        sa.Column('packaging_material', sa.String(length=200), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('extra', sa.JSON(), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_packaging_cap_created_by', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], name='fk_packaging_cap_supplier_id', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_supplier_packaging_capabilities_created_by'), 'supplier_packaging_capabilities', ['created_by'], unique=False)
    op.create_index(op.f('ix_supplier_packaging_capabilities_supplier_id'), 'supplier_packaging_capabilities', ['supplier_id'], unique=False)

    op.create_table(
        'transport_environment_risks',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('route_name', sa.String(length=200), nullable=False),
        sa.Column('origin', sa.String(length=200), nullable=True),
        sa.Column('destination', sa.String(length=200), nullable=True),
        sa.Column('transport_mode', sa.String(length=20), nullable=True),
        sa.Column('estimated_duration_hours', sa.Integer(), nullable=True),
        sa.Column('avg_temp', sa.Float(), nullable=True),
        sa.Column('temp_variation', sa.Float(), nullable=True),
        sa.Column('avg_humidity', sa.Float(), nullable=True),
        sa.Column('weather_risk_level', sa.String(length=20), nullable=True),
        sa.Column('road_condition_risk', sa.String(length=20), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('extra', sa.JSON(), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_transport_risk_created_by', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transport_environment_risks_created_by'), 'transport_environment_risks', ['created_by'], unique=False)
    op.create_index(op.f('ix_transport_environment_risks_route_name'), 'transport_environment_risks', ['route_name'], unique=False)

    op.create_table(
        'adaptation_evaluations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('evaluation_no', sa.String(length=50), nullable=False),
        sa.Column('material_id', sa.String(length=36), nullable=False),
        sa.Column('supplier_packaging_id', sa.String(length=36), nullable=False),
        sa.Column('transport_risk_id', sa.String(length=36), nullable=True),
        sa.Column('risk_level', sa.String(length=20), nullable=False),
        sa.Column('risk_score', sa.Float(), nullable=False),
        sa.Column('issues', sa.JSON(), nullable=True),
        sa.Column('suggestions', sa.JSON(), nullable=True),
        sa.Column('evaluator_id', sa.String(length=36), nullable=True),
        sa.Column('evaluated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['evaluator_id'], ['users.id'], name='fk_evaluation_evaluator_id', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['material_id'], ['sensitive_materials.id'], name='fk_evaluation_material_id', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['supplier_packaging_id'], ['supplier_packaging_capabilities.id'], name='fk_evaluation_packaging_id', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['transport_risk_id'], ['transport_environment_risks.id'], name='fk_evaluation_transport_risk_id', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('evaluation_no', name='uq_adaptation_evaluations_evaluation_no')
    )
    op.create_index(op.f('ix_adaptation_evaluations_evaluator_id'), 'adaptation_evaluations', ['evaluator_id'], unique=False)
    op.create_index(op.f('ix_adaptation_evaluations_evaluation_no'), 'adaptation_evaluations', ['evaluation_no'], unique=True)
    op.create_index(op.f('ix_adaptation_evaluations_material_id'), 'adaptation_evaluations', ['material_id'], unique=False)
    op.create_index(op.f('ix_adaptation_evaluations_risk_level'), 'adaptation_evaluations', ['risk_level'], unique=False)
    op.create_index(op.f('ix_adaptation_evaluations_supplier_packaging_id'), 'adaptation_evaluations', ['supplier_packaging_id'], unique=False)
    op.create_index(op.f('ix_adaptation_evaluations_transport_risk_id'), 'adaptation_evaluations', ['transport_risk_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_adaptation_evaluations_transport_risk_id'), table_name='adaptation_evaluations')
    op.drop_index(op.f('ix_adaptation_evaluations_supplier_packaging_id'), table_name='adaptation_evaluations')
    op.drop_index(op.f('ix_adaptation_evaluations_risk_level'), table_name='adaptation_evaluations')
    op.drop_index(op.f('ix_adaptation_evaluations_material_id'), table_name='adaptation_evaluations')
    op.drop_index(op.f('ix_adaptation_evaluations_evaluation_no'), table_name='adaptation_evaluations')
    op.drop_index(op.f('ix_adaptation_evaluations_evaluator_id'), table_name='adaptation_evaluations')
    op.drop_table('adaptation_evaluations')

    op.drop_index(op.f('ix_transport_environment_risks_route_name'), table_name='transport_environment_risks')
    op.drop_index(op.f('ix_transport_environment_risks_created_by'), table_name='transport_environment_risks')
    op.drop_table('transport_environment_risks')

    op.drop_index(op.f('ix_supplier_packaging_capabilities_supplier_id'), table_name='supplier_packaging_capabilities')
    op.drop_index(op.f('ix_supplier_packaging_capabilities_created_by'), table_name='supplier_packaging_capabilities')
    op.drop_table('supplier_packaging_capabilities')

    op.drop_index(op.f('ix_sensitive_materials_material_name'), table_name='sensitive_materials')
    op.drop_index(op.f('ix_sensitive_materials_material_code'), table_name='sensitive_materials')
    op.drop_index(op.f('ix_sensitive_materials_created_by'), table_name='sensitive_materials')
    op.drop_table('sensitive_materials')
