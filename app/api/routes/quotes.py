from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.repositories.quote_history import quote_history_repository
from app.schemas.quote import (
    CompareQuotesRequest,
    CompareQuotesResponse,
    ParseQuoteRequest,
    ParseQuoteResponse,
    QuoteHistoryResponse,
)
from app.services.quote_parser import QuoteParserService
from app.services.recommendation import RecommendationService

router = APIRouter()

parser_service = QuoteParserService()
recommendation_service = RecommendationService()


@router.post("/parse", response_model=ParseQuoteResponse)
def parse_quote(payload: ParseQuoteRequest, db: Session = Depends(get_db_session)) -> ParseQuoteResponse:
    parsed = parser_service.parse(payload)
    quote_history_repository.save_parse_result(db, parsed)
    return parsed


@router.post("/compare", response_model=CompareQuotesResponse)
def compare_quotes(payload: CompareQuotesRequest, db: Session = Depends(get_db_session)) -> CompareQuotesResponse:
    result = recommendation_service.compare(payload)
    quote_history_repository.save_comparison_result(db, result)
    return result


@router.get("/history", response_model=QuoteHistoryResponse)
def get_history(db: Session = Depends(get_db_session)) -> QuoteHistoryResponse:
    history = quote_history_repository.get_recent_history(db)
    return QuoteHistoryResponse(**history)
