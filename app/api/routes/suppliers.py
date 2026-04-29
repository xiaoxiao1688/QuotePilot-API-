from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.models import SupplierStatus
from app.db.session import get_db_session
from app.repositories.supplier import supplier_repository
from app.schemas.supplier import (
    SupplierCreate,
    SupplierListResponse,
    SupplierRatingUpdate,
    SupplierResponse,
    SupplierUpdate,
)

router = APIRouter()


def _enum_value(v: str | Enum | None) -> str | None:
    if v is None:
        return None
    if isinstance(v, Enum):
        return v.value
    return v


def get_current_user_id() -> str:
    return "demo-user-001"


@router.post("", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
def create_supplier(
    payload: SupplierCreate,
    db: Session = Depends(get_db_session),
) -> SupplierResponse:
    if supplier_repository.exists_by_name(db, payload.name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error_code": "SUPPLIER_EXISTS", "message": "Supplier name already exists"},
        )

    supplier = supplier_repository.create(
        session=db,
        name=payload.name,
        short_name=payload.short_name,
        contact_person=payload.contact_person,
        phone=payload.phone,
        email=payload.email,
        address=payload.address,
        tax_id=payload.tax_id,
        bank_name=payload.bank_name,
        bank_account=payload.bank_account,
        status=_enum_value(payload.status),
        is_verified=payload.is_verified,
        notes=payload.notes,
        extra=payload.extra,
        created_by=get_current_user_id(),
    )

    return SupplierResponse.model_validate(supplier)


@router.get("", response_model=SupplierListResponse)
def list_suppliers(
    status: SupplierStatus | None = Query(default=None),
    is_verified: bool | None = Query(default=None),
    search: str | None = Query(default=None),
    created_by: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db_session),
) -> SupplierListResponse:
    total, suppliers = supplier_repository.list(
        session=db,
        status=_enum_value(status),
        is_verified=is_verified,
        search=search,
        created_by=created_by,
        limit=limit,
        offset=offset,
    )

    return SupplierListResponse(
        total=total,
        items=[SupplierResponse.model_validate(s) for s in suppliers],
    )


@router.get("/{supplier_id}", response_model=SupplierResponse)
def get_supplier(supplier_id: str, db: Session = Depends(get_db_session)) -> SupplierResponse:
    supplier = supplier_repository.get_by_id(db, supplier_id)
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "SUPPLIER_NOT_FOUND", "message": "Supplier not found"},
        )
    return SupplierResponse.model_validate(supplier)


@router.put("/{supplier_id}", response_model=SupplierResponse)
def update_supplier(
    supplier_id: str,
    payload: SupplierUpdate,
    db: Session = Depends(get_db_session),
) -> SupplierResponse:
    supplier = supplier_repository.get_by_id(db, supplier_id)
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "SUPPLIER_NOT_FOUND", "message": "Supplier not found"},
        )

    update_data = payload.model_dump(exclude_unset=True)

    if "status" in update_data:
        update_data["status"] = _enum_value(update_data["status"])

    if "name" in update_data:
        existing = supplier_repository.get_by_name(db, update_data["name"])
        if existing and existing.id != supplier_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error_code": "SUPPLIER_EXISTS", "message": "Supplier name already exists"},
            )

    updated_supplier = supplier_repository.update(db, supplier_id, **update_data)
    if not updated_supplier:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "UPDATE_FAILED", "message": "Failed to update supplier"},
        )

    return SupplierResponse.model_validate(updated_supplier)


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_supplier(supplier_id: str, db: Session = Depends(get_db_session)) -> None:
    supplier = supplier_repository.get_by_id(db, supplier_id)
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "SUPPLIER_NOT_FOUND", "message": "Supplier not found"},
        )

    success = supplier_repository.delete(db, supplier_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "DELETE_FAILED", "message": "Failed to delete supplier"},
        )


@router.patch("/{supplier_id}/rating", response_model=SupplierResponse)
def update_supplier_rating(
    supplier_id: str,
    payload: SupplierRatingUpdate,
    db: Session = Depends(get_db_session),
) -> SupplierResponse:
    supplier = supplier_repository.get_by_id(db, supplier_id)
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "SUPPLIER_NOT_FOUND", "message": "Supplier not found"},
        )

    updated_supplier = supplier_repository.update_rating(db, supplier_id, payload.rating)
    if not updated_supplier:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "UPDATE_FAILED", "message": "Failed to update supplier rating"},
        )

    return SupplierResponse.model_validate(updated_supplier)
