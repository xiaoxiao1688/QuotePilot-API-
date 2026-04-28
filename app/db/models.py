from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Float, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


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

