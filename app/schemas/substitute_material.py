from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.db.models import SubstituteMaterialStatus


class SubstituteMaterialApplicationBase(BaseModel):
    original_product_code: str = Field(min_length=1, max_length=100)
    original_product_name: str = Field(min_length=1, max_length=200)
    original_specs: Optional[dict] = None
    substitute_product_code: str = Field(min_length=1, max_length=100)
    substitute_product_name: str = Field(min_length=1, max_length=200)
    substitute_specs: Optional[dict] = None
    original_supplier_id: str = Field(min_length=1, max_length=36)
    substitute_supplier_id: str = Field(min_length=1, max_length=36)
    reason: str = Field(min_length=1)
    advantage: Optional[str] = None
    risk_assessment: Optional[str] = None
    test_report: Optional[dict] = None


class SubstituteMaterialApplicationCreate(SubstituteMaterialApplicationBase):
    pass


class SubstituteMaterialApplicationUpdate(BaseModel):
    original_product_code: Optional[str] = Field(default=None, min_length=1, max_length=100)
    original_product_name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    original_specs: Optional[dict] = None
    substitute_product_code: Optional[str] = Field(default=None, min_length=1, max_length=100)
    substitute_product_name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    substitute_specs: Optional[dict] = None
    original_supplier_id: Optional[str] = Field(default=None, min_length=1, max_length=36)
    substitute_supplier_id: Optional[str] = Field(default=None, min_length=1, max_length=36)
    reason: Optional[str] = None
    advantage: Optional[str] = None
    risk_assessment: Optional[str] = None
    test_report: Optional[dict] = None


class SubstituteMaterialApprovalRequest(BaseModel):
    comment: Optional[str] = None


class SubstituteMaterialRejectionRequest(BaseModel):
    reason: str = Field(min_length=1)


class SubstituteMaterialApprovalRecordResponse(BaseModel):
    id: str
    application_id: str
    approver_id: str
    approval_action: str
    comment: Optional[str]
    before_status: str
    after_status: str
    created_at: datetime

    class Config:
        from_attributes = True


class SubstituteMaterialApplicationResponse(BaseModel):
    id: str
    application_no: str
    original_product_code: str
    original_product_name: str
    original_specs: Optional[dict]
    substitute_product_code: str
    substitute_product_name: str
    substitute_specs: Optional[dict]
    original_supplier_id: str
    substitute_supplier_id: str
    reason: str
    advantage: Optional[str]
    risk_assessment: Optional[str]
    test_report: Optional[dict]
    status: str
    created_by: str
    submitted_at: Optional[datetime]
    approved_at: Optional[datetime]
    rejected_at: Optional[datetime]
    rejected_reason: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SubstituteMaterialApplicationDetailResponse(SubstituteMaterialApplicationResponse):
    approval_records: list[SubstituteMaterialApprovalRecordResponse]


class SubstituteMaterialApplicationListResponse(BaseModel):
    total: int
    items: list[SubstituteMaterialApplicationResponse]
