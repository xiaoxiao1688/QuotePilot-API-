from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.db.models import CertificateStatus, CertificateType


class SupplierCertificateBase(BaseModel):
    certificate_type: CertificateType
    certificate_no: str = Field(min_length=1, max_length=100)
    issuing_authority: Optional[str] = Field(default=None, max_length=200)
    issue_date: Optional[datetime] = None
    valid_from: datetime
    valid_until: datetime
    scope: Optional[str] = None
    certificate_file: Optional[dict] = None
    notes: Optional[str] = None
    extra: Optional[dict] = None


class SupplierCertificateCreate(SupplierCertificateBase):
    supplier_id: str = Field(min_length=1, max_length=36)


class SupplierCertificateUpdate(BaseModel):
    certificate_type: Optional[CertificateType] = None
    certificate_no: Optional[str] = Field(default=None, min_length=1, max_length=100)
    issuing_authority: Optional[str] = Field(default=None, max_length=200)
    issue_date: Optional[datetime] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    scope: Optional[str] = None
    certificate_file: Optional[dict] = None
    notes: Optional[str] = None
    extra: Optional[dict] = None
    is_renewed: Optional[bool] = None
    renewed_from_id: Optional[str] = Field(default=None, max_length=36)


class CertificateAlertResponse(BaseModel):
    id: str
    certificate_id: str
    alert_type: str
    alert_days: int
    message: str
    is_read: bool
    read_by: Optional[str]
    read_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class SupplierCertificateResponse(BaseModel):
    id: str
    supplier_id: str
    certificate_type: str
    certificate_no: str
    issuing_authority: Optional[str]
    issue_date: Optional[datetime]
    valid_from: datetime
    valid_until: datetime
    scope: Optional[str]
    certificate_file: Optional[dict]
    status: str
    is_renewed: bool
    renewed_from_id: Optional[str]
    created_by: str
    notes: Optional[str]
    extra: Optional[dict]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SupplierCertificateDetailResponse(SupplierCertificateResponse):
    alerts: list[CertificateAlertResponse] = []


class SupplierCertificateListResponse(BaseModel):
    total: int
    items: list[SupplierCertificateResponse]


class CertificateStatusStatistics(BaseModel):
    valid: int = 0
    expiring: int = 0
    expired: int = 0


class CertificateTypeStatistics(BaseModel):
    certificate_type: str
    count: int


class CertificateStatisticsResponse(BaseModel):
    total: int
    by_status: CertificateStatusStatistics
    by_type: list[CertificateTypeStatistics]


class MarkAlertReadRequest(BaseModel):
    is_read: bool = True
