from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db.models import ComparisonRecord, ParseRecord
from app.schemas.quote import CompareQuotesResponse, ParseQuoteResponse


class QuoteHistoryRepository:
    def save_parse_result(self, session: Session, record: ParseQuoteResponse) -> ParseRecord:
        db_record = ParseRecord(
            supplier_name=record.supplier_name,
            currency=record.currency,
            parse_confidence=record.parse_confidence,
            item_count=len(record.items),
            source_preview=record.source_preview,
            payload=record.model_dump(mode="json"),
        )
        session.add(db_record)
        session.commit()
        session.refresh(db_record)
        return db_record

    def save_comparison_result(self, session: Session, record: CompareQuotesResponse) -> ComparisonRecord:
        db_record = ComparisonRecord(
            demand_title=record.demand_title,
            recommended_supplier=record.recommended_supplier,
            quote_count=len(record.ranked_quotes),
            summary=record.summary,
            payload=record.model_dump(mode="json"),
        )
        session.add(db_record)
        session.commit()
        session.refresh(db_record)
        return db_record

    def get_recent_history(self, session: Session, limit: int = 10) -> dict[str, list[dict]]:
        parse_records = session.scalars(
            select(ParseRecord).order_by(desc(ParseRecord.created_at)).limit(limit)
        ).all()
        comparison_records = session.scalars(
            select(ComparisonRecord).order_by(desc(ComparisonRecord.created_at)).limit(limit)
        ).all()

        return {
            "recent_parses": [
                {
                    "id": record.id,
                    "created_at": record.created_at.isoformat(),
                    "payload": record.payload,
                }
                for record in parse_records
            ],
            "recent_comparisons": [
                {
                    "id": record.id,
                    "created_at": record.created_at.isoformat(),
                    "payload": record.payload,
                }
                for record in comparison_records
            ],
        }


quote_history_repository = QuoteHistoryRepository()
