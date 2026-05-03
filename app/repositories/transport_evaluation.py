from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.db.models import (
    AdaptationEvaluation,
    RiskLevel,
    SensitiveMaterial,
    SupplierPackagingCapability,
    TransportEnvironmentRisk,
)


class SensitiveMaterialRepository:
    def get_by_id(self, session: Session, material_id: str) -> SensitiveMaterial | None:
        return session.scalar(select(SensitiveMaterial).where(SensitiveMaterial.id == material_id))

    def get_by_material_code(self, session: Session, material_code: str) -> SensitiveMaterial | None:
        return session.scalar(select(SensitiveMaterial).where(SensitiveMaterial.material_code == material_code))

    def create(
        self,
        session: Session,
        material_code: str,
        material_name: str,
        min_temp: float | None = None,
        max_temp: float | None = None,
        min_humidity: float | None = None,
        max_humidity: float | None = None,
        shock_proof_level: str | None = None,
        shelf_life_days: int | None = None,
        description: str | None = None,
        extra: dict | None = None,
        created_by: str | None = None,
    ) -> SensitiveMaterial:
        material = SensitiveMaterial(
            material_code=material_code,
            material_name=material_name,
            min_temp=min_temp,
            max_temp=max_temp,
            min_humidity=min_humidity,
            max_humidity=max_humidity,
            shock_proof_level=shock_proof_level,
            shelf_life_days=shelf_life_days,
            description=description,
            extra=extra,
            created_by=created_by,
        )
        session.add(material)
        session.commit()
        session.refresh(material)
        return material

    def update(
        self,
        session: Session,
        material_id: str,
        **kwargs: Any,
    ) -> SensitiveMaterial | None:
        material = self.get_by_id(session, material_id)
        if not material:
            return None

        allowed_fields = [
            "material_code", "material_name", "min_temp", "max_temp",
            "min_humidity", "max_humidity", "shock_proof_level", "shelf_life_days",
            "description", "extra"
        ]
        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(material, key, value)

        session.commit()
        session.refresh(material)
        return material

    def delete(self, session: Session, material_id: str) -> bool:
        material = self.get_by_id(session, material_id)
        if not material:
            return False
        session.delete(material)
        session.commit()
        return True

    def list(
        self,
        session: Session,
        search: str | None = None,
        created_by: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[int, list[SensitiveMaterial]]:
        query = select(SensitiveMaterial)

        if created_by:
            query = query.where(SensitiveMaterial.created_by == created_by)
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                SensitiveMaterial.material_code.ilike(search_pattern) |
                SensitiveMaterial.material_name.ilike(search_pattern)
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = session.scalar(count_query) or 0

        query = query.order_by(desc(SensitiveMaterial.created_at)).limit(limit).offset(offset)
        materials = session.scalars(query).all()

        return total, list(materials)

    def exists_by_material_code(self, session: Session, material_code: str, exclude_id: str | None = None) -> bool:
        query = select(func.count()).where(SensitiveMaterial.material_code == material_code)
        if exclude_id:
            query = query.where(SensitiveMaterial.id != exclude_id)
        return (session.scalar(query) or 0) > 0


class SupplierPackagingCapabilityRepository:
    def get_by_id(self, session: Session, capability_id: str) -> SupplierPackagingCapability | None:
        return session.scalar(select(SupplierPackagingCapability).where(SupplierPackagingCapability.id == capability_id))

    def get_by_supplier_id(self, session: Session, supplier_id: str) -> SupplierPackagingCapability | None:
        return session.scalar(select(SupplierPackagingCapability).where(SupplierPackagingCapability.supplier_id == supplier_id))

    def create(
        self,
        session: Session,
        supplier_id: str,
        packaging_method: str | None = None,
        has_desiccant: bool = False,
        has_vacuum_pack: bool = False,
        has_cold_chain: bool = False,
        cold_chain_min_temp: float | None = None,
        cold_chain_max_temp: float | None = None,
        packaging_material: str | None = None,
        description: str | None = None,
        extra: dict | None = None,
        created_by: str | None = None,
    ) -> SupplierPackagingCapability:
        capability = SupplierPackagingCapability(
            supplier_id=supplier_id,
            packaging_method=packaging_method,
            has_desiccant=has_desiccant,
            has_vacuum_pack=has_vacuum_pack,
            has_cold_chain=has_cold_chain,
            cold_chain_min_temp=cold_chain_min_temp,
            cold_chain_max_temp=cold_chain_max_temp,
            packaging_material=packaging_material,
            description=description,
            extra=extra,
            created_by=created_by,
        )
        session.add(capability)
        session.commit()
        session.refresh(capability)
        return capability

    def update(
        self,
        session: Session,
        capability_id: str,
        **kwargs: Any,
    ) -> SupplierPackagingCapability | None:
        capability = self.get_by_id(session, capability_id)
        if not capability:
            return None

        allowed_fields = [
            "supplier_id", "packaging_method", "has_desiccant", "has_vacuum_pack",
            "has_cold_chain", "cold_chain_min_temp", "cold_chain_max_temp",
            "packaging_material", "description", "extra"
        ]
        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(capability, key, value)

        session.commit()
        session.refresh(capability)
        return capability

    def delete(self, session: Session, capability_id: str) -> bool:
        capability = self.get_by_id(session, capability_id)
        if not capability:
            return False
        session.delete(capability)
        session.commit()
        return True

    def list(
        self,
        session: Session,
        supplier_id: str | None = None,
        has_cold_chain: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[int, list[SupplierPackagingCapability]]:
        query = select(SupplierPackagingCapability)

        if supplier_id:
            query = query.where(SupplierPackagingCapability.supplier_id == supplier_id)
        if has_cold_chain is not None:
            query = query.where(SupplierPackagingCapability.has_cold_chain == has_cold_chain)

        count_query = select(func.count()).select_from(query.subquery())
        total = session.scalar(count_query) or 0

        query = query.order_by(desc(SupplierPackagingCapability.created_at)).limit(limit).offset(offset)
        capabilities = session.scalars(query).all()

        return total, list(capabilities)


class TransportEnvironmentRiskRepository:
    def get_by_id(self, session: Session, risk_id: str) -> TransportEnvironmentRisk | None:
        return session.scalar(select(TransportEnvironmentRisk).where(TransportEnvironmentRisk.id == risk_id))

    def create(
        self,
        session: Session,
        route_name: str,
        origin: str | None = None,
        destination: str | None = None,
        transport_mode: str | None = None,
        estimated_duration_hours: int | None = None,
        avg_temp: float | None = None,
        temp_variation: float | None = None,
        avg_humidity: float | None = None,
        weather_risk_level: str | None = None,
        road_condition_risk: str | None = None,
        description: str | None = None,
        extra: dict | None = None,
        created_by: str | None = None,
    ) -> TransportEnvironmentRisk:
        risk = TransportEnvironmentRisk(
            route_name=route_name,
            origin=origin,
            destination=destination,
            transport_mode=transport_mode,
            estimated_duration_hours=estimated_duration_hours,
            avg_temp=avg_temp,
            temp_variation=temp_variation,
            avg_humidity=avg_humidity,
            weather_risk_level=weather_risk_level,
            road_condition_risk=road_condition_risk,
            description=description,
            extra=extra,
            created_by=created_by,
        )
        session.add(risk)
        session.commit()
        session.refresh(risk)
        return risk

    def update(
        self,
        session: Session,
        risk_id: str,
        **kwargs: Any,
    ) -> TransportEnvironmentRisk | None:
        risk = self.get_by_id(session, risk_id)
        if not risk:
            return None

        allowed_fields = [
            "route_name", "origin", "destination", "transport_mode",
            "estimated_duration_hours", "avg_temp", "temp_variation",
            "avg_humidity", "weather_risk_level", "road_condition_risk",
            "description", "extra"
        ]
        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(risk, key, value)

        session.commit()
        session.refresh(risk)
        return risk

    def delete(self, session: Session, risk_id: str) -> bool:
        risk = self.get_by_id(session, risk_id)
        if not risk:
            return False
        session.delete(risk)
        session.commit()
        return True

    def list(
        self,
        session: Session,
        search: str | None = None,
        transport_mode: str | None = None,
        weather_risk_level: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[int, list[TransportEnvironmentRisk]]:
        query = select(TransportEnvironmentRisk)

        if transport_mode:
            query = query.where(TransportEnvironmentRisk.transport_mode == transport_mode)
        if weather_risk_level:
            query = query.where(TransportEnvironmentRisk.weather_risk_level == weather_risk_level)
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                TransportEnvironmentRisk.route_name.ilike(search_pattern) |
                TransportEnvironmentRisk.origin.ilike(search_pattern) |
                TransportEnvironmentRisk.destination.ilike(search_pattern)
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = session.scalar(count_query) or 0

        query = query.order_by(desc(TransportEnvironmentRisk.created_at)).limit(limit).offset(offset)
        risks = session.scalars(query).all()

        return total, list(risks)


class AdaptationEvaluationRepository:
    def get_by_id(self, session: Session, evaluation_id: str) -> AdaptationEvaluation | None:
        return session.scalar(select(AdaptationEvaluation).where(AdaptationEvaluation.id == evaluation_id))

    def get_by_evaluation_no(self, session: Session, evaluation_no: str) -> AdaptationEvaluation | None:
        return session.scalar(select(AdaptationEvaluation).where(AdaptationEvaluation.evaluation_no == evaluation_no))

    def create(
        self,
        session: Session,
        evaluation_no: str,
        material_id: str,
        supplier_packaging_id: str,
        risk_level: str,
        risk_score: float,
        transport_risk_id: str | None = None,
        issues: list[str] | None = None,
        suggestions: list[str] | None = None,
        evaluator_id: str | None = None,
        evaluated_at: datetime | None = None,
    ) -> AdaptationEvaluation:
        evaluation = AdaptationEvaluation(
            evaluation_no=evaluation_no,
            material_id=material_id,
            supplier_packaging_id=supplier_packaging_id,
            transport_risk_id=transport_risk_id,
            risk_level=risk_level,
            risk_score=risk_score,
            issues=issues,
            suggestions=suggestions,
            evaluator_id=evaluator_id,
            evaluated_at=evaluated_at,
        )
        session.add(evaluation)
        session.commit()
        session.refresh(evaluation)
        return evaluation

    def delete(self, session: Session, evaluation_id: str) -> bool:
        evaluation = self.get_by_id(session, evaluation_id)
        if not evaluation:
            return False
        session.delete(evaluation)
        session.commit()
        return True

    def list(
        self,
        session: Session,
        risk_level: str | None = None,
        material_id: str | None = None,
        supplier_packaging_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[int, list[AdaptationEvaluation]]:
        query = select(AdaptationEvaluation)

        if risk_level:
            query = query.where(AdaptationEvaluation.risk_level == risk_level)
        if material_id:
            query = query.where(AdaptationEvaluation.material_id == material_id)
        if supplier_packaging_id:
            query = query.where(AdaptationEvaluation.supplier_packaging_id == supplier_packaging_id)

        count_query = select(func.count()).select_from(query.subquery())
        total = session.scalar(count_query) or 0

        query = query.order_by(desc(AdaptationEvaluation.created_at)).limit(limit).offset(offset)
        evaluations = session.scalars(query).all()

        return total, list(evaluations)

    def list_high_risk(
        self,
        session: Session,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[int, list[AdaptationEvaluation]]:
        high_risk_levels = [RiskLevel.HIGH.value, RiskLevel.CRITICAL.value]
        query = select(AdaptationEvaluation).where(
            AdaptationEvaluation.risk_level.in_(high_risk_levels)
        )

        count_query = select(func.count()).select_from(query.subquery())
        total = session.scalar(count_query) or 0

        query = query.order_by(desc(AdaptationEvaluation.risk_score), desc(AdaptationEvaluation.created_at)).limit(limit).offset(offset)
        evaluations = session.scalars(query).all()

        return total, list(evaluations)

    def get_latest_evaluation_no(self, session: Session, prefix: str = "EVAL") -> str:
        today = datetime.now().strftime("%Y%m%d")
        pattern = f"{prefix}{today}%"
        query = select(AdaptationEvaluation.evaluation_no).where(
            AdaptationEvaluation.evaluation_no.like(pattern)
        ).order_by(desc(AdaptationEvaluation.evaluation_no)).limit(1)
        result = session.scalar(query)

        if result:
            seq = int(result[-4:]) + 1
        else:
            seq = 1
        return f"{prefix}{today}{seq:04d}"


sensitive_material_repository = SensitiveMaterialRepository()
supplier_packaging_repository = SupplierPackagingCapabilityRepository()
transport_risk_repository = TransportEnvironmentRiskRepository()
adaptation_evaluation_repository = AdaptationEvaluationRepository()
