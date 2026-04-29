from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.db.models import Quote, QuoteItem, QuoteStatus


class QuoteRepository:
    def get_by_id(self, session: Session, quote_id: str) -> Quote | None:
        return session.scalar(select(Quote).where(Quote.id == quote_id))

    def get_by_quote_number(self, session: Session, quote_number: str) -> Quote | None:
        return session.scalar(select(Quote).where(Quote.quote_number == quote_number))

    def get_with_items(self, session: Session, quote_id: str) -> tuple[Quote | None, list[QuoteItem]]:
        quote = self.get_by_id(session, quote_id)
        if not quote:
            return None, []

        items = session.scalars(
            select(QuoteItem)
            .where(QuoteItem.quote_id == quote_id)
            .order_by(QuoteItem.line_number)
        ).all()

        return quote, list(items)

    def create(
        self,
        session: Session,
        supplier_id: str,
        user_id: str,
        demand_title: str,
        currency: str = "CNY",
        shipping_fee: float = 0,
        tax_rate: float = 0,
        discount_amount: float = 0,
        status: str = QuoteStatus.DRAFT.value,
        valid_from: datetime | None = None,
        valid_until: datetime | None = None,
        terms: str | None = None,
        notes: str | None = None,
        extra: dict | None = None,
        items: list[dict[str, Any]] | None = None,
    ) -> Quote:
        sub_total = 0.0
        item_count = 0

        if items:
            for item in items:
                quantity = item.get("quantity", 1)
                unit_price = item.get("unit_price", 0)
                sub_total += quantity * unit_price
                item_count += 1

        tax_amount = sub_total * tax_rate
        grand_total = sub_total + shipping_fee + tax_amount - discount_amount

        quote = Quote(
            supplier_id=supplier_id,
            user_id=user_id,
            demand_title=demand_title,
            currency=currency,
            item_count=item_count,
            sub_total=sub_total,
            shipping_fee=shipping_fee,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            discount_amount=discount_amount,
            grand_total=grand_total,
            status=status,
            valid_from=valid_from,
            valid_until=valid_until,
            terms=terms,
            notes=notes,
            extra=extra,
        )
        session.add(quote)
        session.flush()

        if items:
            for idx, item_data in enumerate(items):
                line_number = item_data.get("line_number", idx + 1)
                quantity = item_data.get("quantity", 1)
                unit_price = item_data.get("unit_price", 0)
                line_total = quantity * unit_price

                quote_item = QuoteItem(
                    quote_id=quote.id,
                    line_number=line_number,
                    product_name=item_data["product_name"],
                    product_code=item_data.get("product_code"),
                    product_category=item_data.get("product_category"),
                    quantity=quantity,
                    unit=item_data.get("unit", "pc"),
                    unit_price=unit_price,
                    currency=item_data.get("currency", currency),
                    line_total=line_total,
                    lead_time_days=item_data.get("lead_time_days"),
                    specs=item_data.get("specs"),
                    description=item_data.get("description"),
                )
                session.add(quote_item)

        session.commit()
        session.refresh(quote)
        return quote

    def update(
        self,
        session: Session,
        quote_id: str,
        **kwargs: Any,
    ) -> Quote | None:
        quote = self.get_by_id(session, quote_id)
        if not quote:
            return None

        allowed_fields = [
            "quote_number", "supplier_id", "demand_title", "currency",
            "shipping_fee", "tax_rate", "discount_amount", "status",
            "valid_from", "valid_until", "terms", "notes", "extra",
            "submitted_at", "approved_at", "rejected_at", "rejected_reason"
        ]

        need_recalculate = False
        recalculate_fields = ["shipping_fee", "tax_rate", "discount_amount"]
        for field in recalculate_fields:
            if field in kwargs:
                need_recalculate = True
                break

        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(quote, key, value)

        if need_recalculate:
            items = session.scalars(
                select(QuoteItem).where(QuoteItem.quote_id == quote_id)
            ).all()
            sub_total = sum(item.line_total for item in items)
            tax_amount = sub_total * quote.tax_rate
            grand_total = sub_total + quote.shipping_fee + tax_amount - quote.discount_amount

            quote.sub_total = sub_total
            quote.tax_amount = tax_amount
            quote.grand_total = grand_total

        session.commit()
        session.refresh(quote)
        return quote

    def delete(self, session: Session, quote_id: str) -> bool:
        quote = self.get_by_id(session, quote_id)
        if not quote:
            return False

        session.execute(select(QuoteItem).where(QuoteItem.quote_id == quote_id))
        items = session.scalars(
            select(QuoteItem).where(QuoteItem.quote_id == quote_id)
        ).all()
        for item in items:
            session.delete(item)

        session.delete(quote)
        session.commit()
        return True

    def list(
        self,
        session: Session,
        supplier_id: str | None = None,
        user_id: str | None = None,
        status: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[int, list[Quote]]:
        query = select(Quote)

        if supplier_id:
            query = query.where(Quote.supplier_id == supplier_id)
        if user_id:
            query = query.where(Quote.user_id == user_id)
        if status:
            query = query.where(Quote.status == status)
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                Quote.quote_number.ilike(search_pattern) |
                Quote.demand_title.ilike(search_pattern)
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = session.scalar(count_query) or 0

        query = query.order_by(desc(Quote.created_at)).limit(limit).offset(offset)
        quotes = session.scalars(query).all()

        return total, list(quotes)

    def submit(self, session: Session, quote_id: str) -> Quote | None:
        return self.update(
            session,
            quote_id,
            status=QuoteStatus.SUBMITTED.value,
            submitted_at=datetime.utcnow(),
        )

    def approve(self, session: Session, quote_id: str) -> Quote | None:
        return self.update(
            session,
            quote_id,
            status=QuoteStatus.APPROVED.value,
            approved_at=datetime.utcnow(),
        )

    def reject(self, session: Session, quote_id: str, reason: str) -> Quote | None:
        return self.update(
            session,
            quote_id,
            status=QuoteStatus.REJECTED.value,
            rejected_at=datetime.utcnow(),
            rejected_reason=reason,
        )

    def get_summary(
        self,
        session: Session,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        query = select(Quote)
        if user_id:
            query = query.where(Quote.user_id == user_id)

        total_count = session.scalar(
            select(func.count()).select_from(query.subquery())
        ) or 0

        total_amount = session.scalar(
            select(func.sum(Quote.grand_total)).select_from(query.subquery())
        ) or 0

        status_query = select(Quote.status, func.count()).select_from(query.subquery())
        status_query = status_query.group_by(Quote.status)
        status_results = session.execute(status_query).all()
        by_status = {row[0]: row[1] for row in status_results}

        supplier_query = select(Quote.supplier_id, func.count()).select_from(query.subquery())
        supplier_query = supplier_query.group_by(Quote.supplier_id)
        supplier_results = session.execute(supplier_query).all()
        by_supplier = {row[0]: row[1] for row in supplier_results}

        return {
            "total_quotes": total_count,
            "total_amount": total_amount,
            "by_status": by_status,
            "by_supplier": by_supplier,
        }


class QuoteItemRepository:
    def get_by_id(self, session: Session, item_id: str) -> QuoteItem | None:
        return session.scalar(select(QuoteItem).where(QuoteItem.id == item_id))

    def get_by_quote_id(self, session: Session, quote_id: str) -> list[QuoteItem]:
        items = session.scalars(
            select(QuoteItem)
            .where(QuoteItem.quote_id == quote_id)
            .order_by(QuoteItem.line_number)
        ).all()
        return list(items)

    def create(
        self,
        session: Session,
        quote_id: str,
        product_name: str,
        line_number: int = 1,
        product_code: str | None = None,
        product_category: str | None = None,
        quantity: int = 1,
        unit: str = "pc",
        unit_price: float = 0,
        currency: str = "CNY",
        lead_time_days: int | None = None,
        specs: dict | None = None,
        description: str | None = None,
    ) -> QuoteItem:
        line_total = quantity * unit_price

        item = QuoteItem(
            quote_id=quote_id,
            line_number=line_number,
            product_name=product_name,
            product_code=product_code,
            product_category=product_category,
            quantity=quantity,
            unit=unit,
            unit_price=unit_price,
            currency=currency,
            line_total=line_total,
            lead_time_days=lead_time_days,
            specs=specs,
            description=description,
        )
        session.add(item)
        session.commit()
        session.refresh(item)

        self._update_quote_totals(session, quote_id)

        return item

    def update(
        self,
        session: Session,
        item_id: str,
        **kwargs: Any,
    ) -> QuoteItem | None:
        item = self.get_by_id(session, item_id)
        if not item:
            return None

        allowed_fields = [
            "line_number", "product_name", "product_code", "product_category",
            "quantity", "unit", "unit_price", "currency", "lead_time_days",
            "specs", "description"
        ]

        need_recalculate = False
        recalculate_fields = ["quantity", "unit_price"]
        for field in recalculate_fields:
            if field in kwargs:
                need_recalculate = True
                break

        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(item, key, value)

        if need_recalculate:
            item.line_total = item.quantity * item.unit_price

        session.commit()
        session.refresh(item)

        self._update_quote_totals(session, item.quote_id)

        return item

    def delete(self, session: Session, item_id: str) -> bool:
        item = self.get_by_id(session, item_id)
        if not item:
            return False

        quote_id = item.quote_id
        session.delete(item)
        session.commit()

        self._update_quote_totals(session, quote_id)

        return True

    def _update_quote_totals(self, session: Session, quote_id: str) -> None:
        quote = session.scalar(select(Quote).where(Quote.id == quote_id))
        if not quote:
            return

        items = self.get_by_quote_id(session, quote_id)
        sub_total = sum(item.line_total for item in items)
        tax_amount = sub_total * quote.tax_rate
        grand_total = sub_total + quote.shipping_fee + tax_amount - quote.discount_amount

        quote.sub_total = sub_total
        quote.tax_amount = tax_amount
        quote.grand_total = grand_total
        quote.item_count = len(items)

        session.commit()


quote_repository = QuoteRepository()
quote_item_repository = QuoteItemRepository()
