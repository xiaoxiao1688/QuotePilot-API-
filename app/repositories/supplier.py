from __future__ import annotations

from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.db.models import Supplier, SupplierStatus


class SupplierRepository:
    def get_by_id(self, session: Session, supplier_id: str) -> Supplier | None:
        return session.scalar(select(Supplier).where(Supplier.id == supplier_id))

    def get_by_name(self, session: Session, name: str) -> Supplier | None:
        return session.scalar(select(Supplier).where(Supplier.name == name))

    def get_by_short_name(self, session: Session, short_name: str) -> Supplier | None:
        return session.scalar(select(Supplier).where(Supplier.short_name == short_name))

    def create(
        self,
        session: Session,
        name: str,
        short_name: str | None = None,
        contact_person: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        address: str | None = None,
        tax_id: str | None = None,
        bank_name: str | None = None,
        bank_account: str | None = None,
        status: str = SupplierStatus.ACTIVE.value,
        is_verified: bool = False,
        notes: str | None = None,
        extra: dict | None = None,
        created_by: str | None = None,
    ) -> Supplier:
        supplier = Supplier(
            name=name,
            short_name=short_name,
            contact_person=contact_person,
            phone=phone,
            email=email,
            address=address,
            tax_id=tax_id,
            bank_name=bank_name,
            bank_account=bank_account,
            status=status,
            is_verified=is_verified,
            notes=notes,
            extra=extra,
            created_by=created_by,
        )
        session.add(supplier)
        session.commit()
        session.refresh(supplier)
        return supplier

    def update(
        self,
        session: Session,
        supplier_id: str,
        **kwargs: Any,
    ) -> Supplier | None:
        supplier = self.get_by_id(session, supplier_id)
        if not supplier:
            return None

        allowed_fields = [
            "name", "short_name", "contact_person", "phone", "email",
            "address", "tax_id", "bank_name", "bank_account", "rating",
            "status", "is_verified", "notes", "extra"
        ]
        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(supplier, key, value)

        session.commit()
        session.refresh(supplier)
        return supplier

    def delete(self, session: Session, supplier_id: str) -> bool:
        supplier = self.get_by_id(session, supplier_id)
        if not supplier:
            return False
        session.delete(supplier)
        session.commit()
        return True

    def list(
        self,
        session: Session,
        status: str | None = None,
        is_verified: bool | None = None,
        search: str | None = None,
        created_by: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[int, list[Supplier]]:
        query = select(Supplier)

        if status:
            query = query.where(Supplier.status == status)
        if is_verified is not None:
            query = query.where(Supplier.is_verified == is_verified)
        if created_by:
            query = query.where(Supplier.created_by == created_by)
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                Supplier.name.ilike(search_pattern) |
                Supplier.short_name.ilike(search_pattern) |
                Supplier.contact_person.ilike(search_pattern) |
                Supplier.email.ilike(search_pattern)
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = session.scalar(count_query) or 0

        query = query.order_by(desc(Supplier.created_at)).limit(limit).offset(offset)
        suppliers = session.scalars(query).all()

        return total, list(suppliers)

    def update_rating(
        self,
        session: Session,
        supplier_id: str,
        rating: float,
    ) -> Supplier | None:
        return self.update(session, supplier_id, rating=rating)

    def update_status(
        self,
        session: Session,
        supplier_id: str,
        status: SupplierStatus,
    ) -> Supplier | None:
        return self.update(session, supplier_id, status=status.value)

    def exists_by_name(self, session: Session, name: str) -> bool:
        query = select(func.count()).where(Supplier.name == name)
        return (session.scalar(query) or 0) > 0


supplier_repository = SupplierRepository()
