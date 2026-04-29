from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class QuoteItemBase(BaseModel):
    line_number: int = Field(default=1, ge=1)
    product_name: str = Field(min_length=1, max_length=200)
    product_code: Optional[str] = Field(default=None, max_length=50)
    product_category: Optional[str] = Field(default=None, max_length=100)
    quantity: int = Field(default=1, ge=1)
    unit: str = Field(default="pc", max_length=20)
    unit_price: float = Field(default=0, ge=0)
    currency: str = Field(default="CNY", max_length=8)
    lead_time_days: Optional[int] = Field(default=None, ge=0)
    specs: Optional[dict] = None
    description: Optional[str] = None


class QuoteItemCreate(QuoteItemBase):
    pass


class QuoteItemUpdate(BaseModel):
    line_number: Optional[int] = Field(default=None, ge=1)
    product_name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    product_code: Optional[str] = Field(default=None, max_length=50)
    product_category: Optional[str] = Field(default=None, max_length=100)
    quantity: Optional[int] = Field(default=None, ge=1)
    unit: Optional[str] = Field(default=None, max_length=20)
    unit_price: Optional[float] = Field(default=None, ge=0)
    currency: Optional[str] = Field(default=None, max_length=8)
    lead_time_days: Optional[int] = Field(default=None, ge=0)
    specs: Optional[dict] = None
    description: Optional[str] = None


class QuoteItemResponse(BaseModel):
    id: str
    quote_id: str
    line_number: int
    product_name: str
    product_code: Optional[str]
    product_category: Optional[str]
    quantity: int
    unit: str
    unit_price: float
    currency: str
    line_total: float
    lead_time_days: Optional[int]
    specs: Optional[dict]
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class QuoteBase(BaseModel):
    quote_number: Optional[str] = Field(default=None, max_length=50)
    supplier_id: str = Field(min_length=1, max_length=36)
    demand_title: str = Field(min_length=1, max_length=200)
    currency: str = Field(default="CNY", max_length=8)
    shipping_fee: float = Field(default=0, ge=0)
    tax_rate: float = Field(default=0, ge=0, le=1)
    discount_amount: float = Field(default=0, ge=0)
    status: str = Field(default="draft")
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    terms: Optional[str] = None
    notes: Optional[str] = None
    extra: Optional[dict] = None


class QuoteCreate(QuoteBase):
    items: list[QuoteItemCreate] = Field(min_length=1)


class QuoteUpdate(BaseModel):
    quote_number: Optional[str] = Field(default=None, max_length=50)
    supplier_id: Optional[str] = Field(default=None, min_length=1, max_length=36)
    demand_title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    currency: Optional[str] = Field(default=None, max_length=8)
    shipping_fee: Optional[float] = Field(default=None, ge=0)
    tax_rate: Optional[float] = Field(default=None, ge=0, le=1)
    discount_amount: Optional[float] = Field(default=None, ge=0)
    status: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    terms: Optional[str] = None
    notes: Optional[str] = None
    extra: Optional[dict] = None


class QuoteSubmitRequest(BaseModel):
    pass


class QuoteApproveRequest(BaseModel):
    notes: Optional[str] = None


class QuoteRejectRequest(BaseModel):
    reason: str = Field(min_length=1)


class QuoteResponse(BaseModel):
    id: str
    quote_number: Optional[str]
    supplier_id: str
    user_id: str
    demand_title: str
    currency: str
    item_count: int
    sub_total: float
    shipping_fee: float
    tax_rate: float
    tax_amount: float
    discount_amount: float
    grand_total: float
    status: str
    valid_from: Optional[datetime]
    valid_until: Optional[datetime]
    terms: Optional[str]
    notes: Optional[str]
    extra: Optional[dict]
    submitted_at: Optional[datetime]
    approved_at: Optional[datetime]
    rejected_at: Optional[datetime]
    rejected_reason: Optional[str]
    created_at: datetime
    updated_at: datetime
    items: list[QuoteItemResponse]

    class Config:
        from_attributes = True


class QuoteListResponse(BaseModel):
    total: int
    items: list[QuoteResponse]


class QuoteSummaryResponse(BaseModel):
    total_quotes: int
    total_amount: float
    by_status: dict[str, int]
    by_supplier: dict[str, int]
