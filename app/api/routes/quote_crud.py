from enum import Enum
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import UserContext, require_admin, require_any_authenticated, require_buyer_or_admin
from app.db.models import Quote, QuoteStatus
from app.db.session import get_db_session
from app.repositories.quote import quote_item_repository, quote_repository
from app.repositories.supplier import supplier_repository
from app.repositories.user import user_repository
from app.schemas.quote_crud import (
    QuoteApproveRequest,
    QuoteCreate,
    QuoteItemCreate,
    QuoteItemResponse,
    QuoteItemUpdate,
    QuoteListResponse,
    QuoteRejectRequest,
    QuoteResponse,
    QuoteSubmitRequest,
    QuoteSummaryResponse,
    QuoteUpdate,
)

router = APIRouter()

QUOTE_STATUS_TRANSITIONS: dict[str, set[str]] = {
    QuoteStatus.DRAFT.value: {QuoteStatus.SUBMITTED.value, QuoteStatus.CANCELLED.value},
    QuoteStatus.SUBMITTED.value: {QuoteStatus.PENDING.value, QuoteStatus.APPROVED.value, QuoteStatus.REJECTED.value},
    QuoteStatus.PENDING.value: {QuoteStatus.APPROVED.value, QuoteStatus.REJECTED.value},
    QuoteStatus.APPROVED.value: {QuoteStatus.CANCELLED.value},
    QuoteStatus.REJECTED.value: {QuoteStatus.DRAFT.value},
    QuoteStatus.EXPIRED.value: set(),
    QuoteStatus.CANCELLED.value: set(),
}


def _enum_value(v: str | Enum | None) -> str | None:
    if v is None:
        return None
    if isinstance(v, Enum):
        return v.value
    return v


def _check_status_transition(current_status: str, target_status: str) -> bool:
    allowed_transitions = QUOTE_STATUS_TRANSITIONS.get(current_status, set())
    return target_status in allowed_transitions


def _check_quote_editable(quote: Quote) -> None:
    if quote.status != QuoteStatus.DRAFT.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "QUOTE_NOT_EDITABLE",
                "message": f"Quote is not editable. Current status: {quote.status}",
            },
        )


def _get_quote_with_items(db: Session, quote_id: str) -> tuple:
    quote, items = quote_repository.get_with_items(db, quote_id)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "QUOTE_NOT_FOUND", "message": "Quote not found"},
        )
    return quote, items


@router.post("", response_model=QuoteResponse, status_code=status.HTTP_201_CREATED)
def create_quote(
    payload: QuoteCreate,
    db: Session = Depends(get_db_session),
    user_ctx: Annotated[UserContext, Depends(require_buyer_or_admin)],
) -> QuoteResponse:
    supplier = supplier_repository.get_by_id(db, payload.supplier_id)
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "SUPPLIER_NOT_FOUND", "message": "Supplier not found"},
        )

    items_data = [item.model_dump() for item in payload.items]

    quote = quote_repository.create(
        session=db,
        supplier_id=payload.supplier_id,
        user_id=user_ctx.user_id,
        demand_title=payload.demand_title,
        currency=payload.currency,
        shipping_fee=payload.shipping_fee,
        tax_rate=payload.tax_rate,
        discount_amount=payload.discount_amount,
        status=_enum_value(payload.status),
        valid_from=payload.valid_from,
        valid_until=payload.valid_until,
        terms=payload.terms,
        notes=payload.notes,
        extra=payload.extra,
        items=items_data,
    )

    quote, items = _get_quote_with_items(db, quote.id)

    response = QuoteResponse.model_validate(quote)
    response.items = [QuoteItemResponse.model_validate(item) for item in items]
    return response


@router.get("", response_model=QuoteListResponse)
def list_quotes(
    supplier_id: str | None = Query(default=None),
    user_id: str | None = Query(default=None),
    status: QuoteStatus | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db_session),
    user_ctx: Annotated[UserContext, require_any_authenticated],
) -> QuoteListResponse:
    filter_user_id = user_id
    if user_id and not user_ctx.is_admin and user_id != user_ctx.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "INSUFFICIENT_PERMISSIONS",
                "message": "You can only filter by your own user_id",
            },
        )

    if not user_ctx.is_admin and not user_id:
        filter_user_id = user_ctx.user_id

    total, quotes = quote_repository.list(
        session=db,
        supplier_id=supplier_id,
        user_id=filter_user_id,
        status=_enum_value(status),
        search=search,
        limit=limit,
        offset=offset,
    )

    responses: list[QuoteResponse] = []
    for quote in quotes:
        items = quote_item_repository.get_by_quote_id(db, quote.id)
        response = QuoteResponse.model_validate(quote)
        response.items = [QuoteItemResponse.model_validate(item) for item in items]
        responses.append(response)

    return QuoteListResponse(
        total=total,
        items=responses,
    )


@router.get("/summary", response_model=QuoteSummaryResponse)
def get_quotes_summary(
    user_id: str | None = Query(default=None),
    db: Session = Depends(get_db_session),
    user_ctx: Annotated[UserContext, require_any_authenticated],
) -> QuoteSummaryResponse:
    filter_user_id = user_id
    if user_id and not user_ctx.is_admin and user_id != user_ctx.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "INSUFFICIENT_PERMISSIONS",
                "message": "You can only filter by your own user_id",
            },
        )

    if not user_ctx.is_admin and not user_id:
        filter_user_id = user_ctx.user_id

    summary = quote_repository.get_summary(db, filter_user_id)
    return QuoteSummaryResponse(**summary)


@router.get("/{quote_id}", response_model=QuoteResponse)
def get_quote(
    quote_id: str,
    db: Session = Depends(get_db_session),
    user_ctx: Annotated[UserContext, require_any_authenticated],
) -> QuoteResponse:
    quote, items = _get_quote_with_items(db, quote_id)

    if not user_ctx.is_admin and quote.user_id != user_ctx.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "INSUFFICIENT_PERMISSIONS",
                "message": "You can only access your own quotes",
            },
        )

    response = QuoteResponse.model_validate(quote)
    response.items = [QuoteItemResponse.model_validate(item) for item in items]
    return response


@router.put("/{quote_id}", response_model=QuoteResponse)
def update_quote(
    quote_id: str,
    payload: QuoteUpdate,
    db: Session = Depends(get_db_session),
    user_ctx: Annotated[UserContext, require_any_authenticated],
) -> QuoteResponse:
    quote = quote_repository.get_by_id(db, quote_id)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "QUOTE_NOT_FOUND", "message": "Quote not found"},
        )

    if not user_ctx.is_admin and quote.user_id != user_ctx.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "INSUFFICIENT_PERMISSIONS",
                "message": "You can only update your own quotes",
            },
        )

    _check_quote_editable(quote)

    update_data = payload.model_dump(exclude_unset=True)

    if "status" in update_data:
        new_status = _enum_value(update_data["status"])
        if new_status is not None and new_status != quote.status:
            if not _check_status_transition(quote.status, new_status):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error_code": "INVALID_STATUS_TRANSITION",
                        "message": f"Cannot transition from '{quote.status}' to '{new_status}'",
                    },
                )
            if not user_ctx.is_admin and new_status in [
                QuoteStatus.APPROVED.value,
                QuoteStatus.REJECTED.value,
            ]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error_code": "INSUFFICIENT_PERMISSIONS",
                        "message": "Only admin can approve or reject quotes",
                    },
                )
        update_data["status"] = new_status

    if "supplier_id" in update_data:
        supplier = supplier_repository.get_by_id(db, update_data["supplier_id"])
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error_code": "SUPPLIER_NOT_FOUND", "message": "Supplier not found"},
            )

    updated_quote = quote_repository.update(db, quote_id, **update_data)
    if not updated_quote:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "UPDATE_FAILED", "message": "Failed to update quote"},
        )

    quote, items = _get_quote_with_items(db, quote_id)

    response = QuoteResponse.model_validate(quote)
    response.items = [QuoteItemResponse.model_validate(item) for item in items]
    return response


@router.delete("/{quote_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_quote(
    quote_id: str,
    db: Session = Depends(get_db_session),
    admin_ctx: Annotated[UserContext, Depends(require_admin)],
) -> None:
    quote = quote_repository.get_by_id(db, quote_id)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "QUOTE_NOT_FOUND", "message": "Quote not found"},
        )

    _check_quote_editable(quote)

    success = quote_repository.delete(db, quote_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "DELETE_FAILED", "message": "Failed to delete quote"},
        )


@router.post("/{quote_id}/submit", response_model=QuoteResponse)
def submit_quote(
    quote_id: str,
    payload: QuoteSubmitRequest,
    db: Session = Depends(get_db_session),
    user_ctx: Annotated[UserContext, Depends(require_buyer_or_admin)],
) -> QuoteResponse:
    quote = quote_repository.get_by_id(db, quote_id)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "QUOTE_NOT_FOUND", "message": "Quote not found"},
        )

    if not user_ctx.is_admin and quote.user_id != user_ctx.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "INSUFFICIENT_PERMISSIONS",
                "message": "You can only submit your own quotes",
            },
        )

    if quote.status != QuoteStatus.DRAFT.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_STATUS",
                "message": f"Only draft quotes can be submitted. Current status: {quote.status}",
            },
        )

    updated_quote = quote_repository.submit(db, quote_id)
    if not updated_quote:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "SUBMIT_FAILED", "message": "Failed to submit quote"},
        )

    quote, items = _get_quote_with_items(db, quote_id)

    response = QuoteResponse.model_validate(quote)
    response.items = [QuoteItemResponse.model_validate(item) for item in items]
    return response


@router.post("/{quote_id}/approve", response_model=QuoteResponse)
def approve_quote(
    quote_id: str,
    payload: QuoteApproveRequest,
    db: Session = Depends(get_db_session),
    admin_ctx: Annotated[UserContext, Depends(require_admin)],
) -> QuoteResponse:
    quote = quote_repository.get_by_id(db, quote_id)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "QUOTE_NOT_FOUND", "message": "Quote not found"},
        )

    if quote.status not in [QuoteStatus.SUBMITTED.value, QuoteStatus.PENDING.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_STATUS",
                "message": f"Only submitted or pending quotes can be approved. Current status: {quote.status}",
            },
        )

    updated_quote = quote_repository.approve(db, quote_id)
    if not updated_quote:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "APPROVE_FAILED", "message": "Failed to approve quote"},
        )

    quote, items = _get_quote_with_items(db, quote_id)

    response = QuoteResponse.model_validate(quote)
    response.items = [QuoteItemResponse.model_validate(item) for item in items]
    return response


@router.post("/{quote_id}/reject", response_model=QuoteResponse)
def reject_quote(
    quote_id: str,
    payload: QuoteRejectRequest,
    db: Session = Depends(get_db_session),
    admin_ctx: Annotated[UserContext, Depends(require_admin)],
) -> QuoteResponse:
    quote = quote_repository.get_by_id(db, quote_id)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "QUOTE_NOT_FOUND", "message": "Quote not found"},
        )

    if quote.status not in [QuoteStatus.SUBMITTED.value, QuoteStatus.PENDING.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_STATUS",
                "message": f"Only submitted or pending quotes can be rejected. Current status: {quote.status}",
            },
        )

    updated_quote = quote_repository.reject(db, quote_id, payload.reason)
    if not updated_quote:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "REJECT_FAILED", "message": "Failed to reject quote"},
        )

    quote, items = _get_quote_with_items(db, quote_id)

    response = QuoteResponse.model_validate(quote)
    response.items = [QuoteItemResponse.model_validate(item) for item in items]
    return response


@router.post("/{quote_id}/items", response_model=QuoteItemResponse, status_code=status.HTTP_201_CREATED)
def add_quote_item(
    quote_id: str,
    payload: QuoteItemCreate,
    db: Session = Depends(get_db_session),
    user_ctx: Annotated[UserContext, Depends(require_buyer_or_admin)],
) -> QuoteItemResponse:
    quote = quote_repository.get_by_id(db, quote_id)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "QUOTE_NOT_FOUND", "message": "Quote not found"},
        )

    if not user_ctx.is_admin and quote.user_id != user_ctx.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "INSUFFICIENT_PERMISSIONS",
                "message": "You can only add items to your own quotes",
            },
        )

    _check_quote_editable(quote)

    item = quote_item_repository.create(
        session=db,
        quote_id=quote_id,
        line_number=payload.line_number,
        product_name=payload.product_name,
        product_code=payload.product_code,
        product_category=payload.product_category,
        quantity=payload.quantity,
        unit=payload.unit,
        unit_price=payload.unit_price,
        currency=payload.currency or quote.currency,
        lead_time_days=payload.lead_time_days,
        specs=payload.specs,
        description=payload.description,
    )

    return QuoteItemResponse.model_validate(item)


@router.put("/{quote_id}/items/{item_id}", response_model=QuoteItemResponse)
def update_quote_item(
    quote_id: str,
    item_id: str,
    payload: QuoteItemUpdate,
    db: Session = Depends(get_db_session),
    user_ctx: Annotated[UserContext, Depends(require_buyer_or_admin)],
) -> QuoteItemResponse:
    quote = quote_repository.get_by_id(db, quote_id)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "QUOTE_NOT_FOUND", "message": "Quote not found"},
        )

    if not user_ctx.is_admin and quote.user_id != user_ctx.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "INSUFFICIENT_PERMISSIONS",
                "message": "You can only update items in your own quotes",
            },
        )

    _check_quote_editable(quote)

    item = quote_item_repository.get_by_id(db, item_id)
    if not item or item.quote_id != quote_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "ITEM_NOT_FOUND", "message": "Quote item not found"},
        )

    update_data = payload.model_dump(exclude_unset=True)
    updated_item = quote_item_repository.update(db, item_id, **update_data)

    if not updated_item:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "UPDATE_FAILED", "message": "Failed to update quote item"},
        )

    return QuoteItemResponse.model_validate(updated_item)


@router.delete("/{quote_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_quote_item(
    quote_id: str,
    item_id: str,
    db: Session = Depends(get_db_session),
    user_ctx: Annotated[UserContext, Depends(require_buyer_or_admin)],
) -> None:
    quote = quote_repository.get_by_id(db, quote_id)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "QUOTE_NOT_FOUND", "message": "Quote not found"},
        )

    if not user_ctx.is_admin and quote.user_id != user_ctx.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "INSUFFICIENT_PERMISSIONS",
                "message": "You can only delete items from your own quotes",
            },
        )

    _check_quote_editable(quote)

    item = quote_item_repository.get_by_id(db, item_id)
    if not item or item.quote_id != quote_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "ITEM_NOT_FOUND", "message": "Quote item not found"},
        )

    success = quote_item_repository.delete(db, item_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "DELETE_FAILED", "message": "Failed to delete quote item"},
        )
