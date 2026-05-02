from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.db.models import User, UserRole


class UserRepository:
    def get_by_id(self, session: Session, user_id: str) -> User | None:
        return session.scalar(select(User).where(User.id == user_id))

    def get_by_username(self, session: Session, username: str) -> User | None:
        return session.scalar(select(User).where(User.username == username))

    def get_by_email(self, session: Session, email: str) -> User | None:
        return session.scalar(select(User).where(User.email == email))

    def create(
        self,
        session: Session,
        username: str,
        email: str,
        password_hash: str,
        nickname: str | None = None,
        role: str = UserRole.BUYER.value,
        company_id: str | None = None,
    ) -> User:
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            nickname=nickname,
            role=role,
            company_id=company_id,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    def update(
        self,
        session: Session,
        user_id: str,
        **kwargs: Any,
    ) -> User | None:
        user = self.get_by_id(session, user_id)
        if not user:
            return None

        allowed_fields = [
            "email", "nickname", "role", "company_id", "is_active",
            "password_hash", "last_login_at"
        ]
        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(user, key, value)

        session.commit()
        session.refresh(user)
        return user

    def delete(self, session: Session, user_id: str) -> bool:
        user = self.get_by_id(session, user_id)
        if not user:
            return False
        session.delete(user)
        session.commit()
        return True

    def list(
        self,
        session: Session,
        role: str | None = None,
        is_active: bool | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[int, list[User]]:
        query = select(User)

        if role:
            query = query.where(User.role == role)
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                User.username.ilike(search_pattern) |
                User.email.ilike(search_pattern) |
                User.nickname.ilike(search_pattern)
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = session.scalar(count_query) or 0

        query = query.order_by(desc(User.created_at)).limit(limit).offset(offset)
        users = session.scalars(query).all()

        return total, list(users)

    def update_last_login(self, session: Session, user_id: str) -> User | None:
        return self.update(session, user_id, last_login_at=datetime.utcnow())

    def exists_by_username(self, session: Session, username: str) -> bool:
        query = select(func.count()).where(User.username == username)
        return (session.scalar(query) or 0) > 0

    def exists_by_email(self, session: Session, email: str) -> bool:
        query = select(func.count()).where(User.email == email)
        return (session.scalar(query) or 0) > 0


user_repository = UserRepository()
