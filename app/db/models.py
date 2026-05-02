from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ParseTask(Base):
    __tablename__ = "parse_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    file_name: Mapped[str] = mapped_column(String(255), index=True)
    file_path: Mapped[str] = mapped_column(String(512))
    file_type: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default=TaskStatus.PENDING.value, index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    supplier_name: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    parse_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ParseRecord(Base):
    __tablename__ = "parse_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    supplier_name: Mapped[str] = mapped_column(String(100), index=True)
    currency: Mapped[str] = mapped_column(String(8))
    parse_confidence: Mapped[float] = mapped_column(Float)
    item_count: Mapped[int] = mapped_column(Integer)
    source_preview: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ComparisonRecord(Base):
    __tablename__ = "comparison_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    demand_title: Mapped[str] = mapped_column(String(120), index=True)
    recommended_supplier: Mapped[str] = mapped_column(String(100), index=True)
    quote_count: Mapped[int] = mapped_column(Integer)
    summary: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class UserRole(str, Enum):
    ADMIN = "admin"
    BUYER = "buyer"
    SUPPLIER = "supplier"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nickname: Mapped[str | None] = mapped_column(String(50), nullable=True)
    role: Mapped[str] = mapped_column(String(20), default=UserRole.BUYER.value, index=True)
    company_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("username", name="uq_users_username"),
        UniqueConstraint("email", name="uq_users_email"),
    )


class SupplierStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    short_name: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    contact_person: Mapped[str | None] = mapped_column(String(50), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    email: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    tax_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    bank_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    bank_account: Mapped[str | None] = mapped_column(String(50), nullable=True)
    rating: Mapped[float] = mapped_column(Float, default=3.0)
    status: Mapped[str] = mapped_column(String(20), default=SupplierStatus.ACTIVE.value, index=True)
    is_verified: Mapped[bool] = mapped_column(default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_by: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", name="fk_suppliers_created_by", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("name", name="uq_suppliers_name"),
    )


class QuoteStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class Quote(Base):
    __tablename__ = "quotes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    quote_number: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True, index=True)
    supplier_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("suppliers.id", name="fk_quotes_supplier_id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", name="fk_quotes_user_id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    demand_title: Mapped[str] = mapped_column(String(200), index=True)
    currency: Mapped[str] = mapped_column(String(8), default="CNY")
    item_count: Mapped[int] = mapped_column(Integer, default=0)
    sub_total: Mapped[float] = mapped_column(Float, default=0)
    shipping_fee: Mapped[float] = mapped_column(Float, default=0)
    tax_rate: Mapped[float] = mapped_column(Float, default=0)
    tax_amount: Mapped[float] = mapped_column(Float, default=0)
    discount_amount: Mapped[float] = mapped_column(Float, default=0)
    grand_total: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(20), default=QuoteStatus.DRAFT.value, index=True)
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    terms: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("quote_number", name="uq_quotes_quote_number"),
    )


class QuoteItem(Base):
    __tablename__ = "quote_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    quote_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("quotes.id", name="fk_quote_items_quote_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    line_number: Mapped[int] = mapped_column(Integer, default=1)
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    product_code: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    product_category: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit: Mapped[str] = mapped_column(String(20), default="pc")
    unit_price: Mapped[float] = mapped_column(Float, default=0)
    currency: Mapped[str] = mapped_column(String(8), default="CNY")
    line_total: Mapped[float] = mapped_column(Float, default=0)
    lead_time_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    specs: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("quote_id", "line_number", name="uq_quote_items_quote_line"),
    )


class SubstituteMaterialStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class SubstituteMaterialApplication(Base):
    __tablename__ = "substitute_material_applications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    application_no: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    original_product_code: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    original_product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    original_specs: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    substitute_product_code: Mapped[str] = mapped_column(String(100), nullable=False)
    substitute_product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    substitute_specs: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    original_supplier_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("suppliers.id", name="fk_sub_mat_app_original_supplier", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    substitute_supplier_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("suppliers.id", name="fk_sub_mat_app_substitute_supplier", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    advantage: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_assessment: Mapped[str | None] = mapped_column(Text, nullable=True)
    test_report: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default=SubstituteMaterialStatus.DRAFT.value, index=True
    )
    created_by: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", name="fk_sub_mat_app_created_by", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("application_no", name="uq_sub_mat_app_no"),
    )


class SubstituteMaterialApprovalRecord(Base):
    __tablename__ = "substitute_material_approval_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    application_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("substitute_material_applications.id", name="fk_sub_mat_approval_app_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    approver_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", name="fk_sub_mat_approval_approver", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    approval_action: Mapped[str] = mapped_column(String(20), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    before_status: Mapped[str] = mapped_column(String(20), nullable=False)
    after_status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class CertificateStatus(str, Enum):
    VALID = "valid"
    EXPIRING = "expiring"
    EXPIRED = "expired"


class CertificateType(str, Enum):
    ISO_9001 = "iso_9001"
    ISO_14001 = "iso_14001"
    ISO_45001 = "iso_45001"
    IATF_16949 = "iatf_16949"
    CE = "ce"
    ROHS = "rohs"
    REACH = "reach"
    FDA = "fda"
    UL = "ul"
    CCC = "ccc"
    OTHER = "other"


class SupplierCertificate(Base):
    __tablename__ = "supplier_certificates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    supplier_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("suppliers.id", name="fk_supplier_certificates_supplier_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    certificate_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    certificate_no: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    issuing_authority: Mapped[str | None] = mapped_column(String(200), nullable=True)
    issue_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scope: Mapped[str | None] = mapped_column(Text, nullable=True)
    certificate_file: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default=CertificateStatus.VALID.value, index=True
    )
    is_renewed: Mapped[bool] = mapped_column(default=False)
    renewed_from_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("supplier_certificates.id", name="fk_supplier_certificates_renewed_from", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    created_by: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", name="fk_supplier_certificates_created_by", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("supplier_id", "certificate_type", "certificate_no", name="uq_supplier_cert_unique"),
    )


class CertificateAlert(Base):
    __tablename__ = "certificate_alerts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    certificate_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("supplier_certificates.id", name="fk_certificate_alerts_cert_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    alert_type: Mapped[str] = mapped_column(String(20), nullable=False)
    alert_days: Mapped[int] = mapped_column(nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(default=False, index=True)
    read_by: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", name="fk_certificate_alerts_read_by", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

