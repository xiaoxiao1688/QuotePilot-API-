from enum import Enum
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import UserContext, require_admin, require_any_authenticated, require_buyer_or_admin
from app.db.models import CertificateStatus, CertificateType
from app.db.session import get_db_session
from app.repositories.supplier import supplier_repository
from app.repositories.supplier_certificate import (
    certificate_alert_repository,
    supplier_certificate_repository,
)
from app.schemas.supplier_certificate import (
    CertificateAlertResponse,
    CertificateStatisticsResponse,
    CertificateStatusStatistics,
    CertificateTypeStatistics,
    MarkAlertReadRequest,
    SupplierCertificateCreate,
    SupplierCertificateDetailResponse,
    SupplierCertificateListResponse,
    SupplierCertificateResponse,
    SupplierCertificateUpdate,
)

router = APIRouter()


def _enum_value(v: str | Enum | None) -> str | None:
    if v is None:
        return None
    if isinstance(v, Enum):
        return v.value
    return v


@router.post("", response_model=SupplierCertificateResponse, status_code=status.HTTP_201_CREATED)
def create_supplier_certificate(
    payload: SupplierCertificateCreate,
    user_ctx: Annotated[UserContext, Depends(require_buyer_or_admin)],
    db: Session = Depends(get_db_session),
) -> SupplierCertificateResponse:
    supplier = supplier_repository.get_by_id(db, payload.supplier_id)
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "SUPPLIER_NOT_FOUND", "message": "Supplier not found"},
        )

    if supplier_certificate_repository.exists_by_unique_key(
        db,
        supplier_id=payload.supplier_id,
        certificate_type=_enum_value(payload.certificate_type),
        certificate_no=payload.certificate_no,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error_code": "CERTIFICATE_EXISTS",
                "message": "Certificate with same supplier, type and number already exists",
            },
        )

    if payload.valid_until < payload.valid_from:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_DATE_RANGE",
                "message": "valid_until must be after valid_from",
            },
        )

    certificate = supplier_certificate_repository.create(
        session=db,
        supplier_id=payload.supplier_id,
        certificate_type=_enum_value(payload.certificate_type),
        certificate_no=payload.certificate_no,
        issuing_authority=payload.issuing_authority,
        issue_date=payload.issue_date,
        valid_from=payload.valid_from,
        valid_until=payload.valid_until,
        scope=payload.scope,
        certificate_file=payload.certificate_file,
        created_by=user_ctx.user_id,
        notes=payload.notes,
        extra=payload.extra,
    )

    return SupplierCertificateResponse.model_validate(certificate)


@router.get("", response_model=SupplierCertificateListResponse)
def list_supplier_certificates(
    user_ctx: Annotated[UserContext, require_any_authenticated],
    supplier_id: str | None = Query(default=None),
    certificate_type: CertificateType | None = Query(default=None),
    status: CertificateStatus | None = Query(default=None),
    search: str | None = Query(default=None),
    created_by: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db_session),
) -> SupplierCertificateListResponse:
    if created_by and not user_ctx.is_admin and created_by != user_ctx.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "INSUFFICIENT_PERMISSIONS",
                "message": "You can only filter by your own created_by",
            },
        )

    total, certificates = supplier_certificate_repository.list(
        session=db,
        supplier_id=supplier_id,
        certificate_type=_enum_value(certificate_type),
        status=_enum_value(status),
        search=search,
        created_by=created_by,
        limit=limit,
        offset=offset,
    )

    return SupplierCertificateListResponse(
        total=total,
        items=[SupplierCertificateResponse.model_validate(c) for c in certificates],
    )


@router.get("/expiring", response_model=SupplierCertificateListResponse)
def get_expiring_certificates(
    user_ctx: Annotated[UserContext, require_any_authenticated],
    days: int = Query(default=30, ge=1, le=365),
    supplier_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db_session),
) -> SupplierCertificateListResponse:
    total, certificates = supplier_certificate_repository.get_expiring_certificates(
        session=db,
        days=days,
        supplier_id=supplier_id,
        limit=limit,
        offset=offset,
    )

    return SupplierCertificateListResponse(
        total=total,
        items=[SupplierCertificateResponse.model_validate(c) for c in certificates],
    )


@router.get("/expired", response_model=SupplierCertificateListResponse)
def get_expired_certificates(
    user_ctx: Annotated[UserContext, require_any_authenticated],
    supplier_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db_session),
) -> SupplierCertificateListResponse:
    total, certificates = supplier_certificate_repository.get_expired_certificates(
        session=db,
        supplier_id=supplier_id,
        limit=limit,
        offset=offset,
    )

    return SupplierCertificateListResponse(
        total=total,
        items=[SupplierCertificateResponse.model_validate(c) for c in certificates],
    )


@router.get("/statistics", response_model=CertificateStatisticsResponse)
def get_certificate_statistics(
    user_ctx: Annotated[UserContext, require_any_authenticated],
    supplier_id: str | None = Query(default=None),
    db: Session = Depends(get_db_session),
) -> CertificateStatisticsResponse:
    stats = supplier_certificate_repository.get_statistics(session=db, supplier_id=supplier_id)

    return CertificateStatisticsResponse(
        total=stats["total"],
        by_status=CertificateStatusStatistics(**stats["by_status"]),
        by_type=[CertificateTypeStatistics(**t) for t in stats["by_type"]],
    )


@router.get("/{certificate_id}", response_model=SupplierCertificateDetailResponse)
def get_supplier_certificate(
    certificate_id: str,
    user_ctx: Annotated[UserContext, require_any_authenticated],
    db: Session = Depends(get_db_session),
) -> SupplierCertificateDetailResponse:
    certificate = supplier_certificate_repository.get_by_id_with_alerts(db, certificate_id)
    if not certificate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "CERTIFICATE_NOT_FOUND", "message": "Certificate not found"},
        )

    alerts = certificate_alert_repository.get_by_certificate_id(db, certificate_id)

    response = SupplierCertificateDetailResponse.model_validate(certificate)
    response.alerts = [CertificateAlertResponse.model_validate(a) for a in alerts]
    return response


@router.put("/{certificate_id}", response_model=SupplierCertificateResponse)
def update_supplier_certificate(
    certificate_id: str,
    payload: SupplierCertificateUpdate,
    user_ctx: Annotated[UserContext, require_any_authenticated],
    db: Session = Depends(get_db_session),
) -> SupplierCertificateResponse:
    certificate = supplier_certificate_repository.get_by_id(db, certificate_id)
    if not certificate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "CERTIFICATE_NOT_FOUND", "message": "Certificate not found"},
        )

    if not user_ctx.is_admin and certificate.created_by != user_ctx.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "INSUFFICIENT_PERMISSIONS",
                "message": "You can only update certificates you created",
            },
        )

    update_data = payload.model_dump(exclude_unset=True)

    if "certificate_type" in update_data or "certificate_no" in update_data:
        certificate_type = _enum_value(update_data.get("certificate_type")) or certificate.certificate_type
        certificate_no = update_data.get("certificate_no") or certificate.certificate_no
        supplier_id = certificate.supplier_id

        if supplier_certificate_repository.exists_by_unique_key(
            db,
            supplier_id=supplier_id,
            certificate_type=certificate_type,
            certificate_no=certificate_no,
            exclude_id=certificate_id,
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error_code": "CERTIFICATE_EXISTS",
                    "message": "Certificate with same supplier, type and number already exists",
                },
            )

    if "valid_from" in update_data and "valid_until" not in update_data:
        valid_from = update_data["valid_from"]
        valid_until = certificate.valid_until
        if valid_until < valid_from:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error_code": "INVALID_DATE_RANGE",
                    "message": "valid_until must be after valid_from",
                },
            )

    if "valid_until" in update_data:
        valid_from = update_data.get("valid_from") or certificate.valid_from
        valid_until = update_data["valid_until"]
        if valid_until < valid_from:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error_code": "INVALID_DATE_RANGE",
                    "message": "valid_until must be after valid_from",
                },
            )

    updated_certificate = supplier_certificate_repository.update(db, certificate_id, **update_data)
    if not updated_certificate:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "UPDATE_FAILED", "message": "Failed to update certificate"},
        )

    return SupplierCertificateResponse.model_validate(updated_certificate)


@router.delete("/{certificate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_supplier_certificate(
    certificate_id: str,
    user_ctx: Annotated[UserContext, require_any_authenticated],
    db: Session = Depends(get_db_session),
) -> None:
    certificate = supplier_certificate_repository.get_by_id(db, certificate_id)
    if not certificate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "CERTIFICATE_NOT_FOUND", "message": "Certificate not found"},
        )

    if not user_ctx.is_admin and certificate.created_by != user_ctx.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "INSUFFICIENT_PERMISSIONS",
                "message": "You can only delete certificates you created",
            },
        )

    success = supplier_certificate_repository.delete(db, certificate_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "DELETE_FAILED", "message": "Failed to delete certificate"},
        )


@router.post("/refresh-status", status_code=status.HTTP_200_OK)
def refresh_all_certificate_statuses(
    admin_ctx: Annotated[UserContext, Depends(require_admin)],
    db: Session = Depends(get_db_session),
) -> dict[str, int]:
    updated_count = supplier_certificate_repository.refresh_all_certificate_statuses(db)
    return {"updated_count": updated_count}


@router.get("/{certificate_id}/refresh-status", response_model=SupplierCertificateResponse)
def refresh_certificate_status(
    certificate_id: str,
    user_ctx: Annotated[UserContext, require_any_authenticated],
    db: Session = Depends(get_db_session),
) -> SupplierCertificateResponse:
    certificate = supplier_certificate_repository.get_by_id(db, certificate_id)
    if not certificate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "CERTIFICATE_NOT_FOUND", "message": "Certificate not found"},
        )

    updated_certificate = supplier_certificate_repository.refresh_certificate_status(db, certificate_id)
    if not updated_certificate:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "REFRESH_FAILED", "message": "Failed to refresh certificate status"},
        )

    return SupplierCertificateResponse.model_validate(updated_certificate)


@router.get("/alerts", response_model=list[CertificateAlertResponse])
def list_certificate_alerts(
    user_ctx: Annotated[UserContext, require_any_authenticated],
    certificate_id: str | None = Query(default=None),
    is_read: bool | None = Query(default=None),
    alert_type: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db_session),
) -> list[CertificateAlertResponse]:
    total, alerts = certificate_alert_repository.list(
        session=db,
        certificate_id=certificate_id,
        is_read=is_read,
        alert_type=alert_type,
        limit=limit,
        offset=offset,
    )

    return [CertificateAlertResponse.model_validate(a) for a in alerts]


@router.patch("/alerts/{alert_id}/read", response_model=CertificateAlertResponse)
def mark_alert_read(
    alert_id: str,
    payload: MarkAlertReadRequest,
    user_ctx: Annotated[UserContext, require_any_authenticated],
    db: Session = Depends(get_db_session),
) -> CertificateAlertResponse:
    alert = certificate_alert_repository.get_by_id(db, alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "ALERT_NOT_FOUND", "message": "Alert not found"},
        )

    if payload.is_read:
        updated_alert = certificate_alert_repository.mark_as_read(db, alert_id, read_by=user_ctx.user_id)
    else:
        updated_alert = certificate_alert_repository.mark_as_unread(db, alert_id)

    if not updated_alert:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "UPDATE_FAILED", "message": "Failed to update alert"},
        )

    return CertificateAlertResponse.model_validate(updated_alert)
