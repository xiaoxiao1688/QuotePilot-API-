from enum import Enum
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import UserContext, require_admin, require_any_authenticated, require_buyer_or_admin
from app.db.models import SubstituteMaterialStatus
from app.db.session import get_db_session
from app.repositories.substitute_material import (
    substitute_material_application_repository,
    substitute_material_approval_record_repository,
)
from app.repositories.supplier import supplier_repository
from app.schemas.substitute_material import (
    SubstituteMaterialApplicationCreate,
    SubstituteMaterialApplicationDetailResponse,
    SubstituteMaterialApplicationListResponse,
    SubstituteMaterialApplicationResponse,
    SubstituteMaterialApplicationUpdate,
    SubstituteMaterialApprovalRecordResponse,
    SubstituteMaterialApprovalRequest,
    SubstituteMaterialRejectionRequest,
)

router = APIRouter()


def _enum_value(v: str | Enum | None) -> str | None:
    if v is None:
        return None
    if isinstance(v, Enum):
        return v.value
    return v


@router.post("", response_model=SubstituteMaterialApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_substitute_material_application(
    payload: SubstituteMaterialApplicationCreate,
    user_ctx: Annotated[UserContext, Depends(require_buyer_or_admin)],
    db: Session = Depends(get_db_session),
) -> SubstituteMaterialApplicationResponse:
    original_supplier = supplier_repository.get_by_id(db, payload.original_supplier_id)
    if not original_supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "ORIGINAL_SUPPLIER_NOT_FOUND", "message": "Original supplier not found"},
        )

    substitute_supplier = supplier_repository.get_by_id(db, payload.substitute_supplier_id)
    if not substitute_supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "SUBSTITUTE_SUPPLIER_NOT_FOUND", "message": "Substitute supplier not found"},
        )

    application = substitute_material_application_repository.create(
        session=db,
        original_product_code=payload.original_product_code,
        original_product_name=payload.original_product_name,
        original_specs=payload.original_specs,
        substitute_product_code=payload.substitute_product_code,
        substitute_product_name=payload.substitute_product_name,
        substitute_specs=payload.substitute_specs,
        original_supplier_id=payload.original_supplier_id,
        substitute_supplier_id=payload.substitute_supplier_id,
        reason=payload.reason,
        advantage=payload.advantage,
        risk_assessment=payload.risk_assessment,
        test_report=payload.test_report,
        created_by=user_ctx.user_id,
    )

    return SubstituteMaterialApplicationResponse.model_validate(application)


@router.get("", response_model=SubstituteMaterialApplicationListResponse)
def list_substitute_material_applications(
    user_ctx: Annotated[UserContext, require_any_authenticated],
    status: SubstituteMaterialStatus | None = Query(default=None),
    original_supplier_id: str | None = Query(default=None),
    substitute_supplier_id: str | None = Query(default=None),
    created_by: str | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db_session),
) -> SubstituteMaterialApplicationListResponse:
    if created_by and not user_ctx.is_admin and created_by != user_ctx.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "INSUFFICIENT_PERMISSIONS",
                "message": "You can only filter by your own created_by",
            },
        )

    total, applications = substitute_material_application_repository.list(
        session=db,
        status=_enum_value(status),
        original_supplier_id=original_supplier_id,
        substitute_supplier_id=substitute_supplier_id,
        created_by=created_by,
        search=search,
        limit=limit,
        offset=offset,
    )

    return SubstituteMaterialApplicationListResponse(
        total=total,
        items=[SubstituteMaterialApplicationResponse.model_validate(a) for a in applications],
    )


@router.get("/{application_id}", response_model=SubstituteMaterialApplicationDetailResponse)
def get_substitute_material_application(
    application_id: str,
    user_ctx: Annotated[UserContext, require_any_authenticated],
    db: Session = Depends(get_db_session),
) -> SubstituteMaterialApplicationDetailResponse:
    application = substitute_material_application_repository.get_by_id_with_records(db, application_id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "APPLICATION_NOT_FOUND", "message": "Application not found"},
        )

    approval_records = substitute_material_approval_record_repository.get_by_application_id(db, application_id)

    response = SubstituteMaterialApplicationDetailResponse.model_validate(application)
    response.approval_records = [
        SubstituteMaterialApprovalRecordResponse.model_validate(r) for r in approval_records
    ]
    return response


@router.put("/{application_id}", response_model=SubstituteMaterialApplicationResponse)
def update_substitute_material_application(
    application_id: str,
    payload: SubstituteMaterialApplicationUpdate,
    user_ctx: Annotated[UserContext, require_any_authenticated],
    db: Session = Depends(get_db_session),
) -> SubstituteMaterialApplicationResponse:
    application = substitute_material_application_repository.get_by_id(db, application_id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "APPLICATION_NOT_FOUND", "message": "Application not found"},
        )

    if not user_ctx.is_admin and application.created_by != user_ctx.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "INSUFFICIENT_PERMISSIONS",
                "message": "You can only update applications you created",
            },
        )

    if application.status != SubstituteMaterialStatus.DRAFT.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_STATUS",
                "message": "Only draft applications can be updated",
            },
        )

    update_data = payload.model_dump(exclude_unset=True)

    if "original_supplier_id" in update_data:
        original_supplier = supplier_repository.get_by_id(db, update_data["original_supplier_id"])
        if not original_supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error_code": "ORIGINAL_SUPPLIER_NOT_FOUND", "message": "Original supplier not found"},
            )

    if "substitute_supplier_id" in update_data:
        substitute_supplier = supplier_repository.get_by_id(db, update_data["substitute_supplier_id"])
        if not substitute_supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error_code": "SUBSTITUTE_SUPPLIER_NOT_FOUND", "message": "Substitute supplier not found"},
            )

    updated_application = substitute_material_application_repository.update(db, application_id, **update_data)
    if not updated_application:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "UPDATE_FAILED", "message": "Failed to update application"},
        )

    return SubstituteMaterialApplicationResponse.model_validate(updated_application)


@router.post("/{application_id}/submit", response_model=SubstituteMaterialApplicationResponse)
def submit_substitute_material_application(
    application_id: str,
    user_ctx: Annotated[UserContext, require_any_authenticated],
    db: Session = Depends(get_db_session),
) -> SubstituteMaterialApplicationResponse:
    application = substitute_material_application_repository.get_by_id(db, application_id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "APPLICATION_NOT_FOUND", "message": "Application not found"},
        )

    if not user_ctx.is_admin and application.created_by != user_ctx.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "INSUFFICIENT_PERMISSIONS",
                "message": "You can only submit applications you created",
            },
        )

    if application.status != SubstituteMaterialStatus.DRAFT.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_STATUS",
                "message": "Only draft applications can be submitted",
            },
        )

    submitted_application = substitute_material_application_repository.submit(db, application_id)
    if not submitted_application:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "SUBMIT_FAILED", "message": "Failed to submit application"},
        )

    return SubstituteMaterialApplicationResponse.model_validate(submitted_application)


@router.post("/{application_id}/approve", response_model=SubstituteMaterialApplicationResponse)
def approve_substitute_material_application(
    application_id: str,
    payload: SubstituteMaterialApprovalRequest,
    admin_ctx: Annotated[UserContext, Depends(require_admin)],
    db: Session = Depends(get_db_session),
) -> SubstituteMaterialApplicationResponse:
    application = substitute_material_application_repository.get_by_id(db, application_id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "APPLICATION_NOT_FOUND", "message": "Application not found"},
        )

    if application.status != SubstituteMaterialStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_STATUS",
                "message": "Only pending applications can be approved",
            },
        )

    approved_application = substitute_material_application_repository.approve(
        session=db,
        application_id=application_id,
        approver_id=admin_ctx.user_id,
        comment=payload.comment,
    )
    if not approved_application:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "APPROVE_FAILED", "message": "Failed to approve application"},
        )

    return SubstituteMaterialApplicationResponse.model_validate(approved_application)


@router.post("/{application_id}/reject", response_model=SubstituteMaterialApplicationResponse)
def reject_substitute_material_application(
    application_id: str,
    payload: SubstituteMaterialRejectionRequest,
    admin_ctx: Annotated[UserContext, Depends(require_admin)],
    db: Session = Depends(get_db_session),
) -> SubstituteMaterialApplicationResponse:
    application = substitute_material_application_repository.get_by_id(db, application_id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "APPLICATION_NOT_FOUND", "message": "Application not found"},
        )

    if application.status != SubstituteMaterialStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_STATUS",
                "message": "Only pending applications can be rejected",
            },
        )

    rejected_application = substitute_material_application_repository.reject(
        session=db,
        application_id=application_id,
        approver_id=admin_ctx.user_id,
        reason=payload.reason,
    )
    if not rejected_application:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "REJECT_FAILED", "message": "Failed to reject application"},
        )

    return SubstituteMaterialApplicationResponse.model_validate(rejected_application)


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_substitute_material_application(
    application_id: str,
    user_ctx: Annotated[UserContext, require_any_authenticated],
    db: Session = Depends(get_db_session),
) -> None:
    application = substitute_material_application_repository.get_by_id(db, application_id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "APPLICATION_NOT_FOUND", "message": "Application not found"},
        )

    if not user_ctx.is_admin and application.created_by != user_ctx.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "INSUFFICIENT_PERMISSIONS",
                "message": "You can only delete applications you created",
            },
        )

    if application.status != SubstituteMaterialStatus.DRAFT.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_STATUS",
                "message": "Only draft applications can be deleted",
            },
        )

    success = substitute_material_application_repository.delete(db, application_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "DELETE_FAILED", "message": "Failed to delete application"},
        )
