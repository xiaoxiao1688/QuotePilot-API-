from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

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


def get_current_user_id() -> str:
    return "demo-user-001"


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
) -> QuoteResponse:
    supplier = supplier_repository.get_by_id(db, payload.supplier_id)
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "SUPPLIER_NOT_FOUND", "message": "Supplier not found"},
        )

    user_id = get_current_user_id()

    items_data = [item.model_dump() for item in payload.items]

    quote = quote_repository.create(
        session=db,
        supplier_id=payload.supplier_id,
        user_id=user_id,
        demand_title=payload.demand_title,
        currency=payload.currency,
        shipping_fee=payload.shipping_fee,
        tax_rate=payload.tax_rate,
        discount_amount=payload.discount_amount,
        status=payload.status,
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
    status: str | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db_session),
) -> QuoteListResponse:
    total, quotes = quote_repository.list(
        session=db,
        supplier_id=supplier_id,
        user_id=user_id,
        status=status,
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
) -> QuoteSummaryResponse:
    summary = quote_repository.get_summary(db, user_id)
    return QuoteSummaryResponse(**summary)


@router.get("/{quote_id}", response_model=QuoteResponse)
def get_quote(quote_id: str, db: Session = Depends(get_db_session)) -> QuoteResponse:
    quote, items = _get_quote_with_items(db, quote_id)

    response = QuoteResponse.model_validate(quote)
    response.items = [QuoteItemResponse.model_validate(item) for item in items]
    return response


@router.put("/{quote_id}", response_model=QuoteResponse)
def update_quote(
    quote_id: str,
    payload: QuoteUpdate,
    db: Session = Depends(get_db_session),
) -> QuoteResponse:
    quote = quote_repository.get_by_id(db, quote_id)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "QUOTE_NOT_FOUND", "message": "Quote not found"},
        )

    update_data = payload.model_dump(exclude_unset=True)

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
def delete_quote(quote_id: str, db: Session = Depends(get_db_session)) -> None:
    quote = quote_repository.get_by_id(db, quote_id)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "QUOTE_NOT_FOUND", "message": "Quote not found"},
        )

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
) -> QuoteResponse:
    quote = quote_repository.get_by_id(db, quote_id)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "QUOTE_NOT_FOUND", "message": "Quote not found"},
        )

    if quote.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "INVALID_STATUS", "message": "Only draft quotes can be submitted"},
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
) -> QuoteResponse:
    quote = quote_repository.get_by_id(db, quote_id)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "QUOTE_NOT_FOUND", "message": "Quote not found"},
        )

    if quote.status not in ["submitted", "pending"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "INVALID_STATUS", "message": "Only submitted quotes can be approved"},
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
) -> QuoteResponse:
    quote = quote_repository.get_by_id(db, quote_id)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "QUOTE_NOT_FOUND", "message": "Quote not found"},
        )

    if quote.status not in ["submitted", "pending"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "INVALID_STATUS", "message": "Only submitted quotes can be rejected"},
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
) -> QuoteItemResponse:
    quote = quote_repository.get_by_id(db, quote_id)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "QUOTE_NOT_FOUND", "message": "Quote not found"},
        )

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
) -> QuoteItemResponse:
    quote = quote_repository.get_by_id(db, quote_id)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "QUOTE_NOT_FOUND", "message": "Quote not found"},
        )

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
) -> None:
    quote = quote_repository.get_by_id(db, quote_id)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "QUOTE_NOT_FOUND", "message": "Quote not found"},
        )

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
