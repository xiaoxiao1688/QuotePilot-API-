from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.db.models import (
    PackagingMethod,
    RiskLevel,
    ShockProofLevel,
    TransportMode,
)


class SensitiveMaterialBase(BaseModel):
    material_code: str = Field(min_length=1, max_length=50)
    material_name: str = Field(min_length=1, max_length=200)
    min_temp: Optional[float] = None
    max_temp: Optional[float] = None
    min_humidity: Optional[float] = None
    max_humidity: Optional[float] = None
    shock_proof_level: Optional[ShockProofLevel] = None
    shelf_life_days: Optional[int] = Field(default=None, ge=0)
    description: Optional[str] = None
    extra: Optional[dict] = None


class SensitiveMaterialCreate(SensitiveMaterialBase):
    pass


class SensitiveMaterialUpdate(BaseModel):
    material_code: Optional[str] = Field(default=None, min_length=1, max_length=50)
    material_name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    min_temp: Optional[float] = None
    max_temp: Optional[float] = None
    min_humidity: Optional[float] = None
    max_humidity: Optional[float] = None
    shock_proof_level: Optional[ShockProofLevel] = None
    shelf_life_days: Optional[int] = Field(default=None, ge=0)
    description: Optional[str] = None
    extra: Optional[dict] = None


class SensitiveMaterialResponse(BaseModel):
    id: str
    material_code: str
    material_name: str
    min_temp: Optional[float]
    max_temp: Optional[float]
    min_humidity: Optional[float]
    max_humidity: Optional[float]
    shock_proof_level: Optional[str]
    shelf_life_days: Optional[int]
    description: Optional[str]
    extra: Optional[dict]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SensitiveMaterialListResponse(BaseModel):
    total: int
    items: list[SensitiveMaterialResponse]


class SupplierPackagingCapabilityBase(BaseModel):
    supplier_id: str = Field(min_length=1, max_length=36)
    packaging_method: Optional[PackagingMethod] = None
    has_desiccant: bool = Field(default=False)
    has_vacuum_pack: bool = Field(default=False)
    has_cold_chain: bool = Field(default=False)
    cold_chain_min_temp: Optional[float] = None
    cold_chain_max_temp: Optional[float] = None
    packaging_material: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = None
    extra: Optional[dict] = None


class SupplierPackagingCapabilityCreate(SupplierPackagingCapabilityBase):
    pass


class SupplierPackagingCapabilityUpdate(BaseModel):
    supplier_id: Optional[str] = Field(default=None, min_length=1, max_length=36)
    packaging_method: Optional[PackagingMethod] = None
    has_desiccant: Optional[bool] = None
    has_vacuum_pack: Optional[bool] = None
    has_cold_chain: Optional[bool] = None
    cold_chain_min_temp: Optional[float] = None
    cold_chain_max_temp: Optional[float] = None
    packaging_material: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = None
    extra: Optional[dict] = None


class SupplierPackagingCapabilityResponse(BaseModel):
    id: str
    supplier_id: str
    packaging_method: Optional[str]
    has_desiccant: bool
    has_vacuum_pack: bool
    has_cold_chain: bool
    cold_chain_min_temp: Optional[float]
    cold_chain_max_temp: Optional[float]
    packaging_material: Optional[str]
    description: Optional[str]
    extra: Optional[dict]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SupplierPackagingCapabilityListResponse(BaseModel):
    total: int
    items: list[SupplierPackagingCapabilityResponse]


class TransportEnvironmentRiskBase(BaseModel):
    route_name: str = Field(min_length=1, max_length=200)
    origin: Optional[str] = Field(default=None, max_length=200)
    destination: Optional[str] = Field(default=None, max_length=200)
    transport_mode: Optional[TransportMode] = None
    estimated_duration_hours: Optional[int] = Field(default=None, ge=0)
    avg_temp: Optional[float] = None
    temp_variation: Optional[float] = None
    avg_humidity: Optional[float] = None
    weather_risk_level: Optional[RiskLevel] = None
    road_condition_risk: Optional[RiskLevel] = None
    description: Optional[str] = None
    extra: Optional[dict] = None


class TransportEnvironmentRiskCreate(TransportEnvironmentRiskBase):
    pass


class TransportEnvironmentRiskUpdate(BaseModel):
    route_name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    origin: Optional[str] = Field(default=None, max_length=200)
    destination: Optional[str] = Field(default=None, max_length=200)
    transport_mode: Optional[TransportMode] = None
    estimated_duration_hours: Optional[int] = Field(default=None, ge=0)
    avg_temp: Optional[float] = None
    temp_variation: Optional[float] = None
    avg_humidity: Optional[float] = None
    weather_risk_level: Optional[RiskLevel] = None
    road_condition_risk: Optional[RiskLevel] = None
    description: Optional[str] = None
    extra: Optional[dict] = None


class TransportEnvironmentRiskResponse(BaseModel):
    id: str
    route_name: str
    origin: Optional[str]
    destination: Optional[str]
    transport_mode: Optional[str]
    estimated_duration_hours: Optional[int]
    avg_temp: Optional[float]
    temp_variation: Optional[float]
    avg_humidity: Optional[float]
    weather_risk_level: Optional[str]
    road_condition_risk: Optional[str]
    description: Optional[str]
    extra: Optional[dict]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TransportEnvironmentRiskListResponse(BaseModel):
    total: int
    items: list[TransportEnvironmentRiskResponse]


class EvaluationRequest(BaseModel):
    material_id: str = Field(description="敏感物料档案ID")
    supplier_packaging_id: str = Field(description="供应商包装能力ID")
    transport_risk_id: Optional[str] = Field(default=None, description="运输环境风险ID（可选）")
    actual_transport_temp: Optional[float] = Field(default=None, description="实际运输环境温度")
    actual_transport_humidity: Optional[float] = Field(default=None, description="实际运输环境湿度")
    transport_duration_hours: Optional[int] = Field(default=None, description="运输时长（小时）")


class EvaluationResponse(BaseModel):
    evaluation_id: Optional[str] = None
    evaluation_no: Optional[str] = None
    risk_level: str
    risk_score: float
    issues: list[str]
    suggestions: list[str]
    evaluated_at: Optional[datetime] = None


class AdaptationEvaluationResponse(BaseModel):
    id: str
    evaluation_no: str
    material_id: str
    supplier_packaging_id: str
    transport_risk_id: Optional[str]
    risk_level: str
    risk_score: float
    issues: Optional[list[str]]
    suggestions: Optional[list[str]]
    evaluator_id: Optional[str]
    evaluated_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AdaptationEvaluationListResponse(BaseModel):
    total: int
    items: list[AdaptationEvaluationResponse]
