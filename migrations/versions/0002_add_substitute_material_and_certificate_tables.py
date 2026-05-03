"""add substitute_material_applications, substitute_material_approval_records, supplier_certificates, certificate_alerts tables

Revision ID: 0002_add_substitute_material_and_certificate_tables
Revises: 0001_initial
Create Date: 2026-05-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '0002_add_substitute_material_and_certificate_tables'
down_revision = '0001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'substitute_material_applications',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('application_no', sa.String(length=50), nullable=False),
        sa.Column('original_product_code', sa.String(length=100), nullable=False),
        sa.Column('original_product_name', sa.String(length=200), nullable=False),
        sa.Column('original_specs', sa.JSON(), nullable=True),
        sa.Column('substitute_product_code', sa.String(length=100), nullable=False),
        sa.Column('substitute_product_name', sa.String(length=200), nullable=False),
        sa.Column('substitute_specs', sa.JSON(), nullable=True),
        sa.Column('original_supplier_id', sa.String(length=36), nullable=False),
        sa.Column('substitute_supplier_id', sa.String(length=36), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('advantage', sa.Text(), nullable=True),
        sa.Column('risk_assessment', sa.Text(), nullable=True),
        sa.Column('test_report', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_by', sa.String(length=36), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejected_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_sub_mat_app_created_by', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['original_supplier_id'], ['suppliers.id'], name='fk_sub_mat_app_original_supplier', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['substitute_supplier_id'], ['suppliers.id'], name='fk_sub_mat_app_substitute_supplier', ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('application_no', name='uq_sub_mat_app_no')
    )
    op.create_index(op.f('ix_substitute_material_applications_application_no'), 'substitute_material_applications', ['application_no'], unique=True)
    op.create_index(op.f('ix_substitute_material_applications_created_by'), 'substitute_material_applications', ['created_by'], unique=False)
    op.create_index(op.f('ix_substitute_material_applications_original_product_code'), 'substitute_material_applications', ['original_product_code'], unique=False)
    op.create_index(op.f('ix_substitute_material_applications_original_supplier_id'), 'substitute_material_applications', ['original_supplier_id'], unique=False)
    op.create_index(op.f('ix_substitute_material_applications_status'), 'substitute_material_applications', ['status'], unique=False)
    op.create_index(op.f('ix_substitute_material_applications_substitute_supplier_id'), 'substitute_material_applications', ['substitute_supplier_id'], unique=False)

    op.create_table(
        'supplier_certificates',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('supplier_id', sa.String(length=36), nullable=False),
        sa.Column('certificate_type', sa.String(length=50), nullable=False),
        sa.Column('certificate_no', sa.String(length=100), nullable=False),
        sa.Column('issuing_authority', sa.String(length=200), nullable=True),
        sa.Column('issue_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=False),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=False),
        sa.Column('scope', sa.Text(), nullable=True),
        sa.Column('certificate_file', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('is_renewed', sa.Boolean(), nullable=False),
        sa.Column('renewed_from_id', sa.String(length=36), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('extra', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_supplier_certificates_created_by', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['renewed_from_id'], ['supplier_certificates.id'], name='fk_supplier_certificates_renewed_from', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], name='fk_supplier_certificates_supplier_id', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('supplier_id', 'certificate_type', 'certificate_no', name='uq_supplier_cert_unique')
    )
    op.create_index(op.f('ix_supplier_certificates_certificate_no'), 'supplier_certificates', ['certificate_no'], unique=False)
    op.create_index(op.f('ix_supplier_certificates_certificate_type'), 'supplier_certificates', ['certificate_type'], unique=False)
    op.create_index(op.f('ix_supplier_certificates_created_by'), 'supplier_certificates', ['created_by'], unique=False)
    op.create_index(op.f('ix_supplier_certificates_renewed_from_id'), 'supplier_certificates', ['renewed_from_id'], unique=False)
    op.create_index(op.f('ix_supplier_certificates_status'), 'supplier_certificates', ['status'], unique=False)
    op.create_index(op.f('ix_supplier_certificates_supplier_id'), 'supplier_certificates', ['supplier_id'], unique=False)

    op.create_table(
        'substitute_material_approval_records',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('application_id', sa.String(length=36), nullable=False),
        sa.Column('approver_id', sa.String(length=36), nullable=False),
        sa.Column('approval_action', sa.String(length=20), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('before_status', sa.String(length=20), nullable=False),
        sa.Column('after_status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['application_id'], ['substitute_material_applications.id'], name='fk_sub_mat_approval_app_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['approver_id'], ['users.id'], name='fk_sub_mat_approval_approver', ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_substitute_material_approval_records_application_id'), 'substitute_material_approval_records', ['application_id'], unique=False)
    op.create_index(op.f('ix_substitute_material_approval_records_approver_id'), 'substitute_material_approval_records', ['approver_id'], unique=False)

    op.create_table(
        'certificate_alerts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('certificate_id', sa.String(length=36), nullable=False),
        sa.Column('alert_type', sa.String(length=20), nullable=False),
        sa.Column('alert_days', sa.Integer(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False),
        sa.Column('read_by', sa.String(length=36), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['certificate_id'], ['supplier_certificates.id'], name='fk_certificate_alerts_cert_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['read_by'], ['users.id'], name='fk_certificate_alerts_read_by', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_certificate_alerts_certificate_id'), 'certificate_alerts', ['certificate_id'], unique=False)
    op.create_index(op.f('ix_certificate_alerts_is_read'), 'certificate_alerts', ['is_read'], unique=False)
    op.create_index(op.f('ix_certificate_alerts_read_by'), 'certificate_alerts', ['read_by'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_certificate_alerts_read_by'), table_name='certificate_alerts')
    op.drop_index(op.f('ix_certificate_alerts_is_read'), table_name='certificate_alerts')
    op.drop_index(op.f('ix_certificate_alerts_certificate_id'), table_name='certificate_alerts')
    op.drop_table('certificate_alerts')

    op.drop_index(op.f('ix_substitute_material_approval_records_approver_id'), table_name='substitute_material_approval_records')
    op.drop_index(op.f('ix_substitute_material_approval_records_application_id'), table_name='substitute_material_approval_records')
    op.drop_table('substitute_material_approval_records')

    op.drop_index(op.f('ix_supplier_certificates_supplier_id'), table_name='supplier_certificates')
    op.drop_index(op.f('ix_supplier_certificates_status'), table_name='supplier_certificates')
    op.drop_index(op.f('ix_supplier_certificates_renewed_from_id'), table_name='supplier_certificates')
    op.drop_index(op.f('ix_supplier_certificates_created_by'), table_name='supplier_certificates')
    op.drop_index(op.f('ix_supplier_certificates_certificate_type'), table_name='supplier_certificates')
    op.drop_index(op.f('ix_supplier_certificates_certificate_no'), table_name='supplier_certificates')
    op.drop_table('supplier_certificates')

    op.drop_index(op.f('ix_substitute_material_applications_substitute_supplier_id'), table_name='substitute_material_applications')
    op.drop_index(op.f('ix_substitute_material_applications_status'), table_name='substitute_material_applications')
    op.drop_index(op.f('ix_substitute_material_applications_original_supplier_id'), table_name='substitute_material_applications')
    op.drop_index(op.f('ix_substitute_material_applications_original_product_code'), table_name='substitute_material_applications')
    op.drop_index(op.f('ix_substitute_material_applications_created_by'), table_name='substitute_material_applications')
    op.drop_index(op.f('ix_substitute_material_applications_application_no'), table_name='substitute_material_applications')
    op.drop_table('substitute_material_applications')
