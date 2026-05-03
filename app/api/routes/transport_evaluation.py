from datetime import datetime
from enum import Enum
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import UserContext, require_any_authenticated, require_buyer_or_admin
from app.db.models import RiskLevel, TransportMode
from app.repositories.supplier import supplier_repository
from app.db.session import get_db_session
from app.repositories.transport_evaluation import (
    adaptation_evaluation_repository,
    sensitive_material_repository,
    supplier_packaging_repository,
    transport_risk_repository,
)
from app.schemas.transport_evaluation import (
    AdaptationEvaluationListResponse,
    AdaptationEvaluationResponse,
    EvaluationRequest,
    EvaluationResponse,
    SensitiveMaterialCreate,
    SensitiveMaterialListResponse,
    SensitiveMaterialResponse,
    SensitiveMaterialUpdate,
    SupplierPackagingCapabilityCreate,
    SupplierPackagingCapabilityListResponse,
    SupplierPackagingCapabilityResponse,
    SupplierPackagingCapabilityUpdate,
    TransportEnvironmentRiskCreate,
    TransportEnvironmentRiskListResponse,
    TransportEnvironmentRiskResponse,
    TransportEnvironmentRiskUpdate,
)

router = APIRouter()


def _enum_value(v: str | Enum | None) -> str | None:
    if v is None:
        return None
    if isinstance(v, Enum):
        return v.value
    return v


def _evaluate_adaptation(
    material,
    packaging,
    transport_risk,
    actual_temp: float | None = None,
    actual_humidity: float | None = None,
    transport_duration: int | None = None,
) -> tuple[RiskLevel, float, list[str], list[str]]:
    issues: list[str] = []
    suggestions: list[str] = []
    risk_score = 0.0

    effective_temp = actual_temp
    effective_humidity = actual_humidity
    effective_duration = transport_duration

    if transport_risk:
        if effective_temp is None:
            effective_temp = transport_risk.avg_temp
        if effective_humidity is None:
            effective_humidity = transport_risk.avg_humidity
        if effective_duration is None:
            effective_duration = transport_risk.estimated_duration_hours

    if material.min_temp is not None and material.max_temp is not None:
        if effective_temp is not None:
            if effective_temp < material.min_temp or effective_temp > material.max_temp:
                issues.append(f"运输温度({effective_temp}°C)超出物料要求范围({material.min_temp}°C ~ {material.max_temp}°C)")
                risk_score += 25
                if not packaging.has_cold_chain:
                    issues.append("供应商不具备冷链运输能力，无法控制运输温度")
                    risk_score += 20
                    suggestions.append("建议选择具备冷链运输能力的供应商，或使用保温箱/冰袋等温控包装")
                else:
                    if (packaging.cold_chain_min_temp is not None and effective_temp < packaging.cold_chain_min_temp) or \
                       (packaging.cold_chain_max_temp is not None and effective_temp > packaging.cold_chain_max_temp):
                        issues.append("供应商冷链能力无法覆盖当前运输温度要求")
                        risk_score += 15
                        suggestions.append("建议验证供应商冷链能力范围是否满足需求")
            else:
                if packaging.has_cold_chain:
                    suggestions.append("供应商具备冷链能力，可满足温度控制要求")
    elif material.min_temp is not None or material.max_temp is not None:
        if effective_temp is not None:
            if material.min_temp is not None and effective_temp < material.min_temp:
                issues.append(f"运输温度({effective_temp}°C)低于物料最低要求({material.min_temp}°C)")
                risk_score += 20
                if not packaging.has_cold_chain:
                    issues.append("供应商不具备冷链运输能力")
                    risk_score += 15
                    suggestions.append("建议使用保温包装材料，或选择具备加热/保温能力的运输服务商")
            if material.max_temp is not None and effective_temp > material.max_temp:
                issues.append(f"运输温度({effective_temp}°C)高于物料最高要求({material.max_temp}°C)")
                risk_score += 20
                if not packaging.has_cold_chain:
                    issues.append("供应商不具备冷链运输能力")
                    risk_score += 15
                    suggestions.append("建议使用冷链运输，并配置适当数量的冰袋/干冰")

    if material.min_humidity is not None and material.max_humidity is not None:
        if effective_humidity is not None:
            if effective_humidity < material.min_humidity or effective_humidity > material.max_humidity:
                issues.append(f"运输湿度({effective_humidity}%)超出物料要求范围({material.min_humidity}% ~ {material.max_humidity}%)")
                risk_score += 15
                if effective_humidity > material.max_humidity and not packaging.has_desiccant:
                    issues.append("高湿度环境下未使用干燥剂")
                    risk_score += 10
                    suggestions.append("建议在包装中添加干燥剂，并使用防潮包装材料")
                if effective_humidity < material.min_humidity:
                    suggestions.append("建议使用保湿包装，避免物料过度干燥")

    if material.shock_proof_level:
        shock_scores = {"level_1": 5, "level_2": 10, "level_3": 15, "level_4": 20, "level_5": 25}
        shock_level_score = shock_scores.get(material.shock_proof_level, 10)

        if packaging.packaging_method:
            protective_methods = ["foam", "bubble_wrap", "custom"]
            if packaging.packaging_method not in protective_methods:
                issues.append(f"物料防震等级要求为{material.shock_proof_level}，但包装方式({packaging.packaging_method})可能无法提供足够保护")
                risk_score += shock_level_score
                suggestions.append("建议使用泡沫、气泡垫等缓冲材料进行包装")
            else:
                suggestions.append("包装方式具备一定缓冲能力")
        else:
            issues.append("未指定包装方式，无法评估防震能力")
            risk_score += 5

    if material.shelf_life_days and effective_duration:
        shelf_life_hours = material.shelf_life_days * 24
        duration_ratio = effective_duration / shelf_life_hours

        if duration_ratio > 0.5:
            issues.append(f"运输时长({effective_duration}小时)占保质期({material.shelf_life_days}天)的比例超过50%")
            risk_score += 15
            suggestions.append("建议选择更快的运输方式（如空运），或使用冷链延长保质期")
        elif duration_ratio > 0.3:
            suggestions.append("运输时长占保质期比例较高，建议关注物料状态")

    if transport_risk:
        if transport_risk.weather_risk_level in ["high", "critical"]:
            issues.append(f"运输路线天气风险等级为{transport_risk.weather_risk_level}")
            risk_score += 10
            suggestions.append("建议关注天气预报，考虑调整运输时间或路线")

        if transport_risk.road_condition_risk in ["high", "critical"]:
            issues.append(f"运输路线路况风险等级为{transport_risk.road_condition_risk}")
            risk_score += 10
            suggestions.append("建议使用减震车辆，或选择路况更好的路线")

    if not packaging.has_vacuum_pack and (material.min_humidity or material.max_humidity):
        suggestions.append("建议考虑真空包装以更好地控制湿度环境")

    if not issues:
        issues.append("未发现明显风险项")
        suggestions.append("当前配置可满足运输要求，建议持续监控运输过程")

    risk_score = min(100.0, max(0.0, risk_score))

    if risk_score >= 60:
        risk_level = RiskLevel.CRITICAL
    elif risk_score >= 40:
        risk_level = RiskLevel.HIGH
    elif risk_score >= 20:
        risk_level = RiskLevel.MEDIUM
    else:
        risk_level = RiskLevel.LOW

    return risk_level, risk_score, issues, suggestions


@router.post("/sensitive-materials", response_model=SensitiveMaterialResponse, status_code=status.HTTP_201_CREATED)
def create_sensitive_material(
    payload: SensitiveMaterialCreate,
    user_ctx: Annotated[UserContext, Depends(require_buyer_or_admin)],
    db: Session = Depends(get_db_session),
) -> SensitiveMaterialResponse:
    if sensitive_material_repository.exists_by_material_code(db, payload.material_code):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error_code": "MATERIAL_EXISTS", "message": "Material code already exists"},
        )

    material = sensitive_material_repository.create(
        session=db,
        material_code=payload.material_code,
        material_name=payload.material_name,
        min_temp=payload.min_temp,
        max_temp=payload.max_temp,
        min_humidity=payload.min_humidity,
        max_humidity=payload.max_humidity,
        shock_proof_level=_enum_value(payload.shock_proof_level),
        shelf_life_days=payload.shelf_life_days,
        description=payload.description,
        extra=payload.extra,
        created_by=user_ctx.user_id,
    )

    return SensitiveMaterialResponse.model_validate(material)


@router.get("/sensitive-materials", response_model=SensitiveMaterialListResponse)
def list_sensitive_materials(
    user_ctx: Annotated[UserContext, Depends(require_any_authenticated)],
    search: str | None = Query(default=None),
    created_by: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db_session),
) -> SensitiveMaterialListResponse:
    if created_by and not user_ctx.is_admin and created_by != user_ctx.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error_code": "INSUFFICIENT_PERMISSIONS", "message": "You can only filter by your own created_by"},
        )

    total, materials = sensitive_material_repository.list(
        session=db,
        search=search,
        created_by=created_by,
        limit=limit,
        offset=offset,
    )

    return SensitiveMaterialListResponse(
        total=total,
        items=[SensitiveMaterialResponse.model_validate(m) for m in materials],
    )


@router.get("/sensitive-materials/{material_id}", response_model=SensitiveMaterialResponse)
def get_sensitive_material(
    material_id: str,
    user_ctx: Annotated[UserContext, Depends(require_any_authenticated)],
    db: Session = Depends(get_db_session),
) -> SensitiveMaterialResponse:
    material = sensitive_material_repository.get_by_id(db, material_id)
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "MATERIAL_NOT_FOUND", "message": "Sensitive material not found"},
        )
    return SensitiveMaterialResponse.model_validate(material)


@router.put("/sensitive-materials/{material_id}", response_model=SensitiveMaterialResponse)
def update_sensitive_material(
    material_id: str,
    payload: SensitiveMaterialUpdate,
    user_ctx: Annotated[UserContext, Depends(require_any_authenticated)],
    db: Session = Depends(get_db_session),
) -> SensitiveMaterialResponse:
    material = sensitive_material_repository.get_by_id(db, material_id)
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "MATERIAL_NOT_FOUND", "message": "Sensitive material not found"},
        )

    if not user_ctx.is_admin and material.created_by != user_ctx.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error_code": "INSUFFICIENT_PERMISSIONS", "message": "You can only update materials you created"},
        )

    update_data = payload.model_dump(exclude_unset=True)

    if "shock_proof_level" in update_data:
        update_data["shock_proof_level"] = _enum_value(update_data["shock_proof_level"])

    if "material_code" in update_data:
        if sensitive_material_repository.exists_by_material_code(db, update_data["material_code"], exclude_id=material_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error_code": "MATERIAL_EXISTS", "message": "Material code already exists"},
            )

    updated_material = sensitive_material_repository.update(db, material_id, **update_data)
    if not updated_material:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "UPDATE_FAILED", "message": "Failed to update sensitive material"},
        )

    return SensitiveMaterialResponse.model_validate(updated_material)


@router.delete("/sensitive-materials/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sensitive_material(
    material_id: str,
    admin_ctx: Annotated[UserContext, Depends(require_buyer_or_admin)],
    db: Session = Depends(get_db_session),
) -> None:
    material = sensitive_material_repository.get_by_id(db, material_id)
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "MATERIAL_NOT_FOUND", "message": "Sensitive material not found"},
        )

    success = sensitive_material_repository.delete(db, material_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "DELETE_FAILED", "message": "Failed to delete sensitive material"},
        )


@router.post("/packaging-capabilities", response_model=SupplierPackagingCapabilityResponse, status_code=status.HTTP_201_CREATED)
def create_packaging_capability(
    payload: SupplierPackagingCapabilityCreate,
    user_ctx: Annotated[UserContext, Depends(require_buyer_or_admin)],
    db: Session = Depends(get_db_session),
) -> SupplierPackagingCapabilityResponse:
    supplier = supplier_repository.get_by_id(db, payload.supplier_id)
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "SUPPLIER_NOT_FOUND", "message": "Supplier not found"},
        )

    existing = supplier_packaging_repository.get_by_supplier_id(db, payload.supplier_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error_code": "CAPABILITY_EXISTS", "message": "Packaging capability already exists for this supplier"},
        )

    capability = supplier_packaging_repository.create(
        session=db,
        supplier_id=payload.supplier_id,
        packaging_method=_enum_value(payload.packaging_method),
        has_desiccant=payload.has_desiccant,
        has_vacuum_pack=payload.has_vacuum_pack,
        has_cold_chain=payload.has_cold_chain,
        cold_chain_min_temp=payload.cold_chain_min_temp,
        cold_chain_max_temp=payload.cold_chain_max_temp,
        packaging_material=payload.packaging_material,
        description=payload.description,
        extra=payload.extra,
        created_by=user_ctx.user_id,
    )

    return SupplierPackagingCapabilityResponse.model_validate(capability)


@router.get("/packaging-capabilities", response_model=SupplierPackagingCapabilityListResponse)
def list_packaging_capabilities(
    user_ctx: Annotated[UserContext, Depends(require_any_authenticated)],
    supplier_id: str | None = Query(default=None),
    has_cold_chain: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db_session),
) -> SupplierPackagingCapabilityListResponse:
    total, capabilities = supplier_packaging_repository.list(
        session=db,
        supplier_id=supplier_id,
        has_cold_chain=has_cold_chain,
        limit=limit,
        offset=offset,
    )

    return SupplierPackagingCapabilityListResponse(
        total=total,
        items=[SupplierPackagingCapabilityResponse.model_validate(c) for c in capabilities],
    )


@router.get("/packaging-capabilities/{capability_id}", response_model=SupplierPackagingCapabilityResponse)
def get_packaging_capability(
    capability_id: str,
    user_ctx: Annotated[UserContext, Depends(require_any_authenticated)],
    db: Session = Depends(get_db_session),
) -> SupplierPackagingCapabilityResponse:
    capability = supplier_packaging_repository.get_by_id(db, capability_id)
    if not capability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "CAPABILITY_NOT_FOUND", "message": "Packaging capability not found"},
        )
    return SupplierPackagingCapabilityResponse.model_validate(capability)


@router.put("/packaging-capabilities/{capability_id}", response_model=SupplierPackagingCapabilityResponse)
def update_packaging_capability(
    capability_id: str,
    payload: SupplierPackagingCapabilityUpdate,
    user_ctx: Annotated[UserContext, Depends(require_any_authenticated)],
    db: Session = Depends(get_db_session),
) -> SupplierPackagingCapabilityResponse:
    capability = supplier_packaging_repository.get_by_id(db, capability_id)
    if not capability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "CAPABILITY_NOT_FOUND", "message": "Packaging capability not found"},
        )

    if not user_ctx.is_admin and capability.created_by != user_ctx.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error_code": "INSUFFICIENT_PERMISSIONS", "message": "You can only update capabilities you created"},
        )

    update_data = payload.model_dump(exclude_unset=True)

    if "packaging_method" in update_data:
        update_data["packaging_method"] = _enum_value(update_data["packaging_method"])

    if "supplier_id" in update_data:
        supplier = supplier_repository.get_by_id(db, update_data["supplier_id"])
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error_code": "SUPPLIER_NOT_FOUND", "message": "Supplier not found"},
            )
        existing = supplier_packaging_repository.get_by_supplier_id(db, update_data["supplier_id"])
        if existing and existing.id != capability_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error_code": "CAPABILITY_EXISTS", "message": "Packaging capability already exists for this supplier"},
            )

    updated_capability = supplier_packaging_repository.update(db, capability_id, **update_data)
    if not updated_capability:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "UPDATE_FAILED", "message": "Failed to update packaging capability"},
        )

    return SupplierPackagingCapabilityResponse.model_validate(updated_capability)


@router.delete("/packaging-capabilities/{capability_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_packaging_capability(
    capability_id: str,
    admin_ctx: Annotated[UserContext, Depends(require_buyer_or_admin)],
    db: Session = Depends(get_db_session),
) -> None:
    capability = supplier_packaging_repository.get_by_id(db, capability_id)
    if not capability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "CAPABILITY_NOT_FOUND", "message": "Packaging capability not found"},
        )

    success = supplier_packaging_repository.delete(db, capability_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "DELETE_FAILED", "message": "Failed to delete packaging capability"},
        )


@router.post("/transport-risks", response_model=TransportEnvironmentRiskResponse, status_code=status.HTTP_201_CREATED)
def create_transport_risk(
    payload: TransportEnvironmentRiskCreate,
    user_ctx: Annotated[UserContext, Depends(require_buyer_or_admin)],
    db: Session = Depends(get_db_session),
) -> TransportEnvironmentRiskResponse:
    risk = transport_risk_repository.create(
        session=db,
        route_name=payload.route_name,
        origin=payload.origin,
        destination=payload.destination,
        transport_mode=_enum_value(payload.transport_mode),
        estimated_duration_hours=payload.estimated_duration_hours,
        avg_temp=payload.avg_temp,
        temp_variation=payload.temp_variation,
        avg_humidity=payload.avg_humidity,
        weather_risk_level=_enum_value(payload.weather_risk_level),
        road_condition_risk=_enum_value(payload.road_condition_risk),
        description=payload.description,
        extra=payload.extra,
        created_by=user_ctx.user_id,
    )

    return TransportEnvironmentRiskResponse.model_validate(risk)


@router.get("/transport-risks", response_model=TransportEnvironmentRiskListResponse)
def list_transport_risks(
    user_ctx: Annotated[UserContext, Depends(require_any_authenticated)],
    search: str | None = Query(default=None),
    transport_mode: TransportMode | None = Query(default=None),
    weather_risk_level: RiskLevel | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db_session),
) -> TransportEnvironmentRiskListResponse:
    total, risks = transport_risk_repository.list(
        session=db,
        search=search,
        transport_mode=_enum_value(transport_mode),
        weather_risk_level=_enum_value(weather_risk_level),
        limit=limit,
        offset=offset,
    )

    return TransportEnvironmentRiskListResponse(
        total=total,
        items=[TransportEnvironmentRiskResponse.model_validate(r) for r in risks],
    )


@router.get("/transport-risks/{risk_id}", response_model=TransportEnvironmentRiskResponse)
def get_transport_risk(
    risk_id: str,
    user_ctx: Annotated[UserContext, Depends(require_any_authenticated)],
    db: Session = Depends(get_db_session),
) -> TransportEnvironmentRiskResponse:
    risk = transport_risk_repository.get_by_id(db, risk_id)
    if not risk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "RISK_NOT_FOUND", "message": "Transport risk not found"},
        )
    return TransportEnvironmentRiskResponse.model_validate(risk)


@router.put("/transport-risks/{risk_id}", response_model=TransportEnvironmentRiskResponse)
def update_transport_risk(
    risk_id: str,
    payload: TransportEnvironmentRiskUpdate,
    user_ctx: Annotated[UserContext, Depends(require_any_authenticated)],
    db: Session = Depends(get_db_session),
) -> TransportEnvironmentRiskResponse:
    risk = transport_risk_repository.get_by_id(db, risk_id)
    if not risk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "RISK_NOT_FOUND", "message": "Transport risk not found"},
        )

    if not user_ctx.is_admin and risk.created_by != user_ctx.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error_code": "INSUFFICIENT_PERMISSIONS", "message": "You can only update risks you created"},
        )

    update_data = payload.model_dump(exclude_unset=True)

    if "transport_mode" in update_data:
        update_data["transport_mode"] = _enum_value(update_data["transport_mode"])
    if "weather_risk_level" in update_data:
        update_data["weather_risk_level"] = _enum_value(update_data["weather_risk_level"])
    if "road_condition_risk" in update_data:
        update_data["road_condition_risk"] = _enum_value(update_data["road_condition_risk"])

    updated_risk = transport_risk_repository.update(db, risk_id, **update_data)
    if not updated_risk:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "UPDATE_FAILED", "message": "Failed to update transport risk"},
        )

    return TransportEnvironmentRiskResponse.model_validate(updated_risk)


@router.delete("/transport-risks/{risk_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transport_risk(
    risk_id: str,
    admin_ctx: Annotated[UserContext, Depends(require_buyer_or_admin)],
    db: Session = Depends(get_db_session),
) -> None:
    risk = transport_risk_repository.get_by_id(db, risk_id)
    if not risk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "RISK_NOT_FOUND", "message": "Transport risk not found"},
        )

    success = transport_risk_repository.delete(db, risk_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "DELETE_FAILED", "message": "Failed to delete transport risk"},
        )


@router.post("/evaluate", response_model=EvaluationResponse, status_code=status.HTTP_200_OK)
def evaluate_adaptation(
    payload: EvaluationRequest,
    user_ctx: Annotated[UserContext, Depends(require_any_authenticated)],
    db: Session = Depends(get_db_session),
    save_evaluation: bool = Query(default=False, description="是否保存评估记录"),
) -> EvaluationResponse:
    material = sensitive_material_repository.get_by_id(db, payload.material_id)
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "MATERIAL_NOT_FOUND", "message": "Sensitive material not found"},
        )

    packaging = supplier_packaging_repository.get_by_id(db, payload.supplier_packaging_id)
    if not packaging:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "PACKAGING_NOT_FOUND", "message": "Supplier packaging capability not found"},
        )

    transport_risk = None
    if payload.transport_risk_id:
        transport_risk = transport_risk_repository.get_by_id(db, payload.transport_risk_id)
        if not transport_risk:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error_code": "TRANSPORT_RISK_NOT_FOUND", "message": "Transport risk not found"},
            )

    risk_level, risk_score, issues, suggestions = _evaluate_adaptation(
        material=material,
        packaging=packaging,
        transport_risk=transport_risk,
        actual_temp=payload.actual_transport_temp,
        actual_humidity=payload.actual_transport_humidity,
        transport_duration=payload.transport_duration_hours,
    )

    evaluation_id = None
    evaluation_no = None
    evaluated_at = None

    if save_evaluation:
        evaluation_no = adaptation_evaluation_repository.get_latest_evaluation_no(db)
        evaluated_at = datetime.now()
        evaluation = adaptation_evaluation_repository.create(
            session=db,
            evaluation_no=evaluation_no,
            material_id=payload.material_id,
            supplier_packaging_id=payload.supplier_packaging_id,
            transport_risk_id=payload.transport_risk_id,
            risk_level=risk_level.value,
            risk_score=risk_score,
            issues=issues,
            suggestions=suggestions,
            evaluator_id=user_ctx.user_id,
            evaluated_at=evaluated_at,
        )
        evaluation_id = evaluation.id

    return EvaluationResponse(
        evaluation_id=evaluation_id,
        evaluation_no=evaluation_no,
        risk_level=risk_level.value,
        risk_score=risk_score,
        issues=issues,
        suggestions=suggestions,
        evaluated_at=evaluated_at,
    )


@router.get("/evaluations", response_model=AdaptationEvaluationListResponse)
def list_evaluations(
    user_ctx: Annotated[UserContext, Depends(require_any_authenticated)],
    risk_level: RiskLevel | None = Query(default=None),
    material_id: str | None = Query(default=None),
    supplier_packaging_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db_session),
) -> AdaptationEvaluationListResponse:
    total, evaluations = adaptation_evaluation_repository.list(
        session=db,
        risk_level=_enum_value(risk_level),
        material_id=material_id,
        supplier_packaging_id=supplier_packaging_id,
        limit=limit,
        offset=offset,
    )

    return AdaptationEvaluationListResponse(
        total=total,
        items=[AdaptationEvaluationResponse.model_validate(e) for e in evaluations],
    )


@router.get("/evaluations/high-risk", response_model=AdaptationEvaluationListResponse)
def list_high_risk_evaluations(
    user_ctx: Annotated[UserContext, Depends(require_any_authenticated)],
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db_session),
) -> AdaptationEvaluationListResponse:
    total, evaluations = adaptation_evaluation_repository.list_high_risk(
        session=db,
        limit=limit,
        offset=offset,
    )

    return AdaptationEvaluationListResponse(
        total=total,
        items=[AdaptationEvaluationResponse.model_validate(e) for e in evaluations],
    )


@router.get("/evaluations/{evaluation_id}", response_model=AdaptationEvaluationResponse)
def get_evaluation(
    evaluation_id: str,
    user_ctx: Annotated[UserContext, Depends(require_any_authenticated)],
    db: Session = Depends(get_db_session),
) -> AdaptationEvaluationResponse:
    evaluation = adaptation_evaluation_repository.get_by_id(db, evaluation_id)
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "EVALUATION_NOT_FOUND", "message": "Adaptation evaluation not found"},
        )
    return AdaptationEvaluationResponse.model_validate(evaluation)
