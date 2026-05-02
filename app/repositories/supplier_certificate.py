from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import and_, desc, func, select
from sqlalchemy.orm import Session, joinedload

from app.db.models import CertificateAlert, CertificateStatus, SupplierCertificate

ALERT_TYPE_EXPIRING = "expiring"
ALERT_TYPE_EXPIRED = "expired"


def get_certificate_status(valid_until: datetime, expiring_days: int = 30) -> str:
    now = datetime.now(timezone.utc)
    if valid_until.tzinfo is None:
        valid_until = valid_until.replace(tzinfo=timezone.utc)

    if valid_until < now:
        return CertificateStatus.EXPIRED.value
    elif valid_until <= now + timedelta(days=expiring_days):
        return CertificateStatus.EXPIRING.value
    else:
        return CertificateStatus.VALID.value


def calculate_days_remaining(valid_until: datetime) -> int:
    now = datetime.now(timezone.utc)
    if valid_until.tzinfo is None:
        valid_until = valid_until.replace(tzinfo=timezone.utc)

    delta = valid_until - now
    return max(0, delta.days) if delta.days >= 0 else delta.days


def build_alert_message(
    certificate: SupplierCertificate,
    alert_type: str,
    days: int,
) -> str:
    cert_type_display = certificate.certificate_type.upper().replace("_", " ")

    if alert_type == ALERT_TYPE_EXPIRING:
        if days == 1:
            return f"证书 [{cert_type_display}] 编号 [{certificate.certificate_no}] 将于明天过期"
        else:
            return f"证书 [{cert_type_display}] 编号 [{certificate.certificate_no}] 将于 {days} 天后过期"
    else:
        if days == -1:
            return f"证书 [{cert_type_display}] 编号 [{certificate.certificate_no}] 已于昨天过期"
        elif days < -1:
            return f"证书 [{cert_type_display}] 编号 [{certificate.certificate_no}] 已过期 {abs(days)} 天"
        else:
            return f"证书 [{cert_type_display}] 编号 [{certificate.certificate_no}] 已过期"


class SupplierCertificateRepository:
    def get_by_id(self, session: Session, certificate_id: str) -> SupplierCertificate | None:
        return session.scalar(
            select(SupplierCertificate).where(SupplierCertificate.id == certificate_id)
        )

    def get_by_id_with_alerts(
        self, session: Session, certificate_id: str
    ) -> SupplierCertificate | None:
        return session.scalar(
            select(SupplierCertificate)
            .options(joinedload(SupplierCertificate.alerts))
            .where(SupplierCertificate.id == certificate_id)
        )

    def _sync_alerts_for_certificate(
        self,
        session: Session,
        certificate: SupplierCertificate,
    ) -> int:
        """
        同步单个证书的预警记录：
        - valid 状态：删除所有预警
        - expiring 状态：确保有一个 expiring 预警，删除 expired 预警
        - expired 状态：确保有一个 expired 预警，删除 expiring 预警
        """
        alert_repo = CertificateAlertRepository()
        created_count = 0

        status = get_certificate_status(certificate.valid_until)
        days_remaining = calculate_days_remaining(certificate.valid_until)

        if status == CertificateStatus.VALID.value:
            alert_repo.delete_by_certificate_id(session, certificate.id)
            return 0

        existing_alerts = alert_repo.get_by_certificate_id(session, certificate.id)

        if status == CertificateStatus.EXPIRING.value:
            alert_repo.delete_by_type(session, certificate.id, ALERT_TYPE_EXPIRED)
            has_expiring_alert = any(
                a.alert_type == ALERT_TYPE_EXPIRING for a in existing_alerts
            )
            if not has_expiring_alert:
                message = build_alert_message(certificate, ALERT_TYPE_EXPIRING, days_remaining)
                alert_repo.create_no_commit(
                    session, certificate.id, ALERT_TYPE_EXPIRING, days_remaining, message
                )
                created_count = 1
            session.commit()

        elif status == CertificateStatus.EXPIRED.value:
            alert_repo.delete_by_type(session, certificate.id, ALERT_TYPE_EXPIRING)
            has_expired_alert = any(
                a.alert_type == ALERT_TYPE_EXPIRED for a in existing_alerts
            )
            if not has_expired_alert:
                message = build_alert_message(certificate, ALERT_TYPE_EXPIRED, days_remaining)
                alert_repo.create_no_commit(
                    session, certificate.id, ALERT_TYPE_EXPIRED, days_remaining, message
                )
                created_count = 1
            session.commit()

        return created_count

    def create(
        self,
        session: Session,
        supplier_id: str,
        certificate_type: str,
        certificate_no: str,
        valid_from: datetime,
        valid_until: datetime,
        issuing_authority: str | None = None,
        issue_date: datetime | None = None,
        scope: str | None = None,
        certificate_file: dict | None = None,
        created_by: str | None = None,
        notes: str | None = None,
        extra: dict | None = None,
        is_renewed: bool = False,
        renewed_from_id: str | None = None,
    ) -> SupplierCertificate:
        status = get_certificate_status(valid_until)
        certificate = SupplierCertificate(
            supplier_id=supplier_id,
            certificate_type=certificate_type,
            certificate_no=certificate_no,
            issuing_authority=issuing_authority,
            issue_date=issue_date,
            valid_from=valid_from,
            valid_until=valid_until,
            scope=scope,
            certificate_file=certificate_file,
            status=status,
            is_renewed=is_renewed,
            renewed_from_id=renewed_from_id,
            created_by=created_by,
            notes=notes,
            extra=extra,
        )
        session.add(certificate)
        session.commit()
        session.refresh(certificate)

        self._sync_alerts_for_certificate(session, certificate)

        return certificate

    def update(
        self,
        session: Session,
        certificate_id: str,
        **kwargs: Any,
    ) -> SupplierCertificate | None:
        certificate = self.get_by_id(session, certificate_id)
        if not certificate:
            return None

        old_valid_until = certificate.valid_until

        allowed_fields = [
            "certificate_type",
            "certificate_no",
            "issuing_authority",
            "issue_date",
            "valid_from",
            "valid_until",
            "scope",
            "certificate_file",
            "notes",
            "extra",
            "is_renewed",
            "renewed_from_id",
        ]
        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(certificate, key, value)

        if "valid_until" in kwargs:
            certificate.status = get_certificate_status(kwargs["valid_until"])

        session.commit()
        session.refresh(certificate)

        if "valid_until" in kwargs and kwargs["valid_until"] != old_valid_until:
            self._sync_alerts_for_certificate(session, certificate)

        return certificate

    def update_status(self, session: Session, certificate_id: str, status: str) -> SupplierCertificate | None:
        certificate = self.get_by_id(session, certificate_id)
        if not certificate:
            return None
        certificate.status = status
        session.commit()
        session.refresh(certificate)
        return certificate

    def refresh_certificate_status(self, session: Session, certificate_id: str) -> SupplierCertificate | None:
        certificate = self.get_by_id(session, certificate_id)
        if not certificate:
            return None

        old_status = certificate.status
        certificate.status = get_certificate_status(certificate.valid_until)
        session.commit()
        session.refresh(certificate)

        if old_status != certificate.status:
            self._sync_alerts_for_certificate(session, certificate)

        return certificate

    def refresh_all_certificate_statuses(self, session: Session) -> int:
        query = select(SupplierCertificate).where(
            SupplierCertificate.status != CertificateStatus.EXPIRED.value
        )
        certificates = session.scalars(query).all()

        updated_count = 0
        for cert in certificates:
            old_status = cert.status
            new_status = get_certificate_status(cert.valid_until)
            if new_status != old_status:
                cert.status = new_status
                self._sync_alerts_for_certificate(session, cert)
                updated_count += 1

        return updated_count

    def delete(self, session: Session, certificate_id: str) -> bool:
        certificate = self.get_by_id(session, certificate_id)
        if not certificate:
            return False

        alert_repo = CertificateAlertRepository()
        alert_repo.delete_by_certificate_id(session, certificate_id)

        session.delete(certificate)
        session.commit()
        return True

    def list(
        self,
        session: Session,
        supplier_id: str | None = None,
        certificate_type: str | None = None,
        status: str | None = None,
        search: str | None = None,
        created_by: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[int, list[SupplierCertificate]]:
        query = select(SupplierCertificate)

        if supplier_id:
            query = query.where(SupplierCertificate.supplier_id == supplier_id)
        if certificate_type:
            query = query.where(SupplierCertificate.certificate_type == certificate_type)
        if status:
            query = query.where(SupplierCertificate.status == status)
        if created_by:
            query = query.where(SupplierCertificate.created_by == created_by)
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                SupplierCertificate.certificate_no.ilike(search_pattern)
                | SupplierCertificate.issuing_authority.ilike(search_pattern)
                | SupplierCertificate.scope.ilike(search_pattern)
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = session.scalar(count_query) or 0

        query = query.order_by(desc(SupplierCertificate.valid_until)).limit(limit).offset(offset)
        certificates = session.scalars(query).all()

        return total, list(certificates)

    def get_expiring_certificates(
        self,
        session: Session,
        days: int = 30,
        supplier_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[int, list[SupplierCertificate]]:
        now = datetime.now(timezone.utc)
        cutoff_date = now + timedelta(days=days)

        query = select(SupplierCertificate).where(
            and_(
                SupplierCertificate.valid_until >= now,
                SupplierCertificate.valid_until <= cutoff_date,
            )
        )

        if supplier_id:
            query = query.where(SupplierCertificate.supplier_id == supplier_id)

        count_query = select(func.count()).select_from(query.subquery())
        total = session.scalar(count_query) or 0

        query = query.order_by(SupplierCertificate.valid_until).limit(limit).offset(offset)
        certificates = session.scalars(query).all()

        return total, list(certificates)

    def get_expired_certificates(
        self,
        session: Session,
        supplier_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[int, list[SupplierCertificate]]:
        now = datetime.now(timezone.utc)

        query = select(SupplierCertificate).where(SupplierCertificate.valid_until < now)

        if supplier_id:
            query = query.where(SupplierCertificate.supplier_id == supplier_id)

        count_query = select(func.count()).select_from(query.subquery())
        total = session.scalar(count_query) or 0

        query = query.order_by(desc(SupplierCertificate.valid_until)).limit(limit).offset(offset)
        certificates = session.scalars(query).all()

        return total, list(certificates)

    def get_statistics(
        self,
        session: Session,
        supplier_id: str | None = None,
    ) -> dict[str, Any]:
        base_query = select(SupplierCertificate)
        if supplier_id:
            base_query = base_query.where(SupplierCertificate.supplier_id == supplier_id)

        count_query = select(func.count()).select_from(base_query.subquery())
        total = session.scalar(count_query) or 0

        status_query = base_query.with_only_columns(
            SupplierCertificate.status,
            func.count().label("count"),
        ).group_by(SupplierCertificate.status)
        status_results = session.execute(status_query).all()

        by_status = {"valid": 0, "expiring": 0, "expired": 0}
        for row in status_results:
            status = row[0]
            count = row[1]
            if status == CertificateStatus.VALID.value:
                by_status["valid"] = count
            elif status == CertificateStatus.EXPIRING.value:
                by_status["expiring"] = count
            elif status == CertificateStatus.EXPIRED.value:
                by_status["expired"] = count

        type_query = base_query.with_only_columns(
            SupplierCertificate.certificate_type,
            func.count().label("count"),
        ).group_by(SupplierCertificate.certificate_type)
        type_results = session.execute(type_query).all()

        by_type = [{"certificate_type": row[0], "count": row[1]} for row in type_results]

        return {"total": total, "by_status": by_status, "by_type": by_type}

    def exists_by_unique_key(
        self,
        session: Session,
        supplier_id: str,
        certificate_type: str,
        certificate_no: str,
        exclude_id: str | None = None,
    ) -> bool:
        query = select(func.count()).where(
            and_(
                SupplierCertificate.supplier_id == supplier_id,
                SupplierCertificate.certificate_type == certificate_type,
                SupplierCertificate.certificate_no == certificate_no,
            )
        )
        if exclude_id:
            query = query.where(SupplierCertificate.id != exclude_id)
        return (session.scalar(query) or 0) > 0


class CertificateAlertRepository:
    def get_by_id(self, session: Session, alert_id: str) -> CertificateAlert | None:
        return session.scalar(select(CertificateAlert).where(CertificateAlert.id == alert_id))

    def get_by_certificate_id(
        self, session: Session, certificate_id: str, is_read: bool | None = None
    ) -> list[CertificateAlert]:
        query = select(CertificateAlert).where(CertificateAlert.certificate_id == certificate_id)
        if is_read is not None:
            query = query.where(CertificateAlert.is_read == is_read)
        query = query.order_by(desc(CertificateAlert.created_at))
        return list(session.scalars(query).all())

    def delete_by_certificate_id(self, session: Session, certificate_id: str) -> int:
        query = select(CertificateAlert).where(CertificateAlert.certificate_id == certificate_id)
        alerts = session.scalars(query).all()
        count = len(alerts)
        for alert in alerts:
            session.delete(alert)
        session.commit()
        return count

    def delete_by_type(self, session: Session, certificate_id: str, alert_type: str) -> int:
        query = select(CertificateAlert).where(
            and_(
                CertificateAlert.certificate_id == certificate_id,
                CertificateAlert.alert_type == alert_type,
            )
        )
        alerts = session.scalars(query).all()
        count = len(alerts)
        for alert in alerts:
            session.delete(alert)
        session.commit()
        return count

    def create(
        self,
        session: Session,
        certificate_id: str,
        alert_type: str,
        alert_days: int,
        message: str,
    ) -> CertificateAlert:
        alert = CertificateAlert(
            certificate_id=certificate_id,
            alert_type=alert_type,
            alert_days=alert_days,
            message=message,
            is_read=False,
        )
        session.add(alert)
        session.commit()
        session.refresh(alert)
        return alert

    def create_no_commit(
        self,
        session: Session,
        certificate_id: str,
        alert_type: str,
        alert_days: int,
        message: str,
    ) -> CertificateAlert:
        alert = CertificateAlert(
            certificate_id=certificate_id,
            alert_type=alert_type,
            alert_days=alert_days,
            message=message,
            is_read=False,
        )
        session.add(alert)
        return alert

    def mark_as_read(
        self,
        session: Session,
        alert_id: str,
        read_by: str | None = None,
    ) -> CertificateAlert | None:
        alert = self.get_by_id(session, alert_id)
        if not alert:
            return None
        alert.is_read = True
        alert.read_by = read_by
        alert.read_at = func.now()
        session.commit()
        session.refresh(alert)
        return alert

    def mark_as_unread(self, session: Session, alert_id: str) -> CertificateAlert | None:
        alert = self.get_by_id(session, alert_id)
        if not alert:
            return None
        alert.is_read = False
        alert.read_by = None
        alert.read_at = None
        session.commit()
        session.refresh(alert)
        return alert

    def list(
        self,
        session: Session,
        certificate_id: str | None = None,
        is_read: bool | None = None,
        alert_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[int, list[CertificateAlert]]:
        query = select(CertificateAlert)

        if certificate_id:
            query = query.where(CertificateAlert.certificate_id == certificate_id)
        if is_read is not None:
            query = query.where(CertificateAlert.is_read == is_read)
        if alert_type:
            query = query.where(CertificateAlert.alert_type == alert_type)

        count_query = select(func.count()).select_from(query.subquery())
        total = session.scalar(count_query) or 0

        query = query.order_by(desc(CertificateAlert.created_at)).limit(limit).offset(offset)
        alerts = session.scalars(query).all()

        return total, list(alerts)


supplier_certificate_repository = SupplierCertificateRepository()
certificate_alert_repository = CertificateAlertRepository()
