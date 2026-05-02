from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, joinedload

from app.db.models import (
    SubstituteMaterialApplication,
    SubstituteMaterialApprovalRecord,
    SubstituteMaterialStatus,
)


class SubstituteMaterialApplicationRepository:
    def get_by_id(self, session: Session, application_id: str) -> SubstituteMaterialApplication | None:
        return session.scalar(
            select(SubstituteMaterialApplication).where(
                SubstituteMaterialApplication.id == application_id
            )
        )

    def get_by_id_with_records(
        self, session: Session, application_id: str
    ) -> SubstituteMaterialApplication | None:
        return session.scalar(
            select(SubstituteMaterialApplication)
            .options(joinedload(SubstituteMaterialApplication.approval_records))
            .where(SubstituteMaterialApplication.id == application_id)
        )

    def get_by_application_no(
        self, session: Session, application_no: str
    ) -> SubstituteMaterialApplication | None:
        return session.scalar(
            select(SubstituteMaterialApplication).where(
                SubstituteMaterialApplication.application_no == application_no
            )
        )

    def create(
        self,
        session: Session,
        original_product_code: str,
        original_product_name: str,
        substitute_product_code: str,
        substitute_product_name: str,
        original_supplier_id: str,
        substitute_supplier_id: str,
        reason: str,
        original_specs: dict | None = None,
        substitute_specs: dict | None = None,
        advantage: str | None = None,
        risk_assessment: str | None = None,
        test_report: dict | None = None,
        created_by: str | None = None,
    ) -> SubstituteMaterialApplication:
        application_no = f"SMA-{datetime.now().strftime('%Y%m%d')}-{str(uuid4())[:8].upper()}"
        application = SubstituteMaterialApplication(
            application_no=application_no,
            original_product_code=original_product_code,
            original_product_name=original_product_name,
            original_specs=original_specs,
            substitute_product_code=substitute_product_code,
            substitute_product_name=substitute_product_name,
            substitute_specs=substitute_specs,
            original_supplier_id=original_supplier_id,
            substitute_supplier_id=substitute_supplier_id,
            reason=reason,
            advantage=advantage,
            risk_assessment=risk_assessment,
            test_report=test_report,
            created_by=created_by,
            status=SubstituteMaterialStatus.DRAFT.value,
        )
        session.add(application)
        session.commit()
        session.refresh(application)
        return application

    def update(
        self,
        session: Session,
        application_id: str,
        **kwargs: Any,
    ) -> SubstituteMaterialApplication | None:
        application = self.get_by_id(session, application_id)
        if not application:
            return None

        allowed_fields = [
            "original_product_code",
            "original_product_name",
            "original_specs",
            "substitute_product_code",
            "substitute_product_name",
            "substitute_specs",
            "original_supplier_id",
            "substitute_supplier_id",
            "reason",
            "advantage",
            "risk_assessment",
            "test_report",
        ]
        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(application, key, value)

        session.commit()
        session.refresh(application)
        return application

    def submit(self, session: Session, application_id: str) -> SubstituteMaterialApplication | None:
        application = self.get_by_id(session, application_id)
        if not application or application.status != SubstituteMaterialStatus.DRAFT.value:
            return None

        application.status = SubstituteMaterialStatus.PENDING.value
        application.submitted_at = func.now()
        session.commit()
        session.refresh(application)
        return application

    def approve(
        self,
        session: Session,
        application_id: str,
        approver_id: str,
        comment: str | None = None,
    ) -> SubstituteMaterialApplication | None:
        application = self.get_by_id(session, application_id)
        if not application or application.status != SubstituteMaterialStatus.PENDING.value:
            return None

        before_status = application.status
        application.status = SubstituteMaterialStatus.APPROVED.value
        application.approved_at = func.now()

        approval_record = SubstituteMaterialApprovalRecord(
            application_id=application_id,
            approver_id=approver_id,
            approval_action="approve",
            comment=comment,
            before_status=before_status,
            after_status=SubstituteMaterialStatus.APPROVED.value,
        )
        session.add(approval_record)

        session.commit()
        session.refresh(application)
        return application

    def reject(
        self,
        session: Session,
        application_id: str,
        approver_id: str,
        reason: str,
    ) -> SubstituteMaterialApplication | None:
        application = self.get_by_id(session, application_id)
        if not application or application.status != SubstituteMaterialStatus.PENDING.value:
            return None

        before_status = application.status
        application.status = SubstituteMaterialStatus.REJECTED.value
        application.rejected_at = func.now()
        application.rejected_reason = reason

        approval_record = SubstituteMaterialApprovalRecord(
            application_id=application_id,
            approver_id=approver_id,
            approval_action="reject",
            comment=reason,
            before_status=before_status,
            after_status=SubstituteMaterialStatus.REJECTED.value,
        )
        session.add(approval_record)

        session.commit()
        session.refresh(application)
        return application

    def delete(self, session: Session, application_id: str) -> bool:
        application = self.get_by_id(session, application_id)
        if not application:
            return False
        if application.status != SubstituteMaterialStatus.DRAFT.value:
            return False
        session.delete(application)
        session.commit()
        return True

    def list(
        self,
        session: Session,
        status: str | None = None,
        original_supplier_id: str | None = None,
        substitute_supplier_id: str | None = None,
        created_by: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[int, list[SubstituteMaterialApplication]]:
        query = select(SubstituteMaterialApplication)

        if status:
            query = query.where(SubstituteMaterialApplication.status == status)
        if original_supplier_id:
            query = query.where(SubstituteMaterialApplication.original_supplier_id == original_supplier_id)
        if substitute_supplier_id:
            query = query.where(SubstituteMaterialApplication.substitute_supplier_id == substitute_supplier_id)
        if created_by:
            query = query.where(SubstituteMaterialApplication.created_by == created_by)
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                SubstituteMaterialApplication.application_no.ilike(search_pattern)
                | SubstituteMaterialApplication.original_product_code.ilike(search_pattern)
                | SubstituteMaterialApplication.original_product_name.ilike(search_pattern)
                | SubstituteMaterialApplication.substitute_product_code.ilike(search_pattern)
                | SubstituteMaterialApplication.substitute_product_name.ilike(search_pattern)
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = session.scalar(count_query) or 0

        query = query.order_by(desc(SubstituteMaterialApplication.created_at)).limit(limit).offset(offset)
        applications = session.scalars(query).all()

        return total, list(applications)


class SubstituteMaterialApprovalRecordRepository:
    def get_by_application_id(
        self, session: Session, application_id: str
    ) -> list[SubstituteMaterialApprovalRecord]:
        query = (
            select(SubstituteMaterialApprovalRecord)
            .where(SubstituteMaterialApprovalRecord.application_id == application_id)
            .order_by(SubstituteMaterialApprovalRecord.created_at)
        )
        return list(session.scalars(query).all())


substitute_material_application_repository = SubstituteMaterialApplicationRepository()
substitute_material_approval_record_repository = SubstituteMaterialApprovalRecordRepository()
