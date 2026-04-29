from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SupplierBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    short_name: Optional[str] = Field(default=None, max_length=50)
    contact_person: Optional[str] = Field(default=None, max_length=50)
    phone: Optional[str] = Field(default=None, max_length=30)
    email: Optional[str] = Field(default=None, max_length=100)
    address: Optional[str] = Field(default=None, max_length=500)
    tax_id: Optional[str] = Field(default=None, max_length=50)
    bank_name: Optional[str] = Field(default=None, max_length=100)
    bank_account: Optional[str] = Field(default=None, max_length=50)
    status: str = Field(default="active")
    is_verified: bool = Field(default=False)
    notes: Optional[str] = None
    extra: Optional[dict] = None


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    short_name: Optional[str] = Field(default=None, max_length=50)
    contact_person: Optional[str] = Field(default=None, max_length=50)
    phone: Optional[str] = Field(default=None, max_length=30)
    email: Optional[str] = Field(default=None, max_length=100)
    address: Optional[str] = Field(default=None, max_length=500)
    tax_id: Optional[str] = Field(default=None, max_length=50)
    bank_name: Optional[str] = Field(default=None, max_length=100)
    bank_account: Optional[str] = Field(default=None, max_length=50)
    status: Optional[str] = None
    is_verified: Optional[bool] = None
    notes: Optional[str] = None
    extra: Optional[dict] = None


class SupplierResponse(BaseModel):
    id: str
    name: str
    short_name: Optional[str]
    contact_person: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    address: Optional[str]
    tax_id: Optional[str]
    bank_name: Optional[str]
    bank_account: Optional[str]
    rating: float
    status: str
    is_verified: bool
    notes: Optional[str]
    extra: Optional[dict]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SupplierListResponse(BaseModel):
    total: int
    items: list[SupplierResponse]


class SupplierRatingUpdate(BaseModel):
    rating: float = Field(ge=0, le=5)
