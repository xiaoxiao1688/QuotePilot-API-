from typing import Annotated, Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.jwt import get_user_id_from_token
from app.db.models import User, UserRole
from app.db.session import get_db_session
from app.repositories.user import user_repository


class UserContext:
    def __init__(self, user: User):
        self._user = user

    @property
    def user_id(self) -> str:
        return self._user.id

    @property
    def username(self) -> str:
        return self._user.username

    @property
    def role(self) -> str:
        return self._user.role

    @property
    def is_admin(self) -> bool:
        return self._user.role == UserRole.ADMIN.value

    @property
    def is_buyer(self) -> bool:
        return self._user.role == UserRole.BUYER.value

    @property
    def is_supplier(self) -> bool:
        return self._user.role == UserRole.SUPPLIER.value

    @property
    def user(self) -> User:
        return self._user

    def has_role(self, *roles: UserRole) -> bool:
        return self._user.role in {role.value for role in roles}

    def is_owner_or_admin(self, owner_id: str | None) -> bool:
        if self.is_admin:
            return True
        if owner_id is None:
            return False
        return self.user_id == owner_id


def get_user_context(
    authorization: Annotated[Optional[str], Header(alias="Authorization")] = None,
    db: Session = Depends(get_db_session),
) -> UserContext:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "AUTH_REQUIRED",
                "message": "Authentication required. Provide Authorization header with Bearer token.",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "INVALID_AUTH_FORMAT",
                "message": "Invalid authorization format. Use 'Bearer <token>'.",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(" ", 1)[1]

    try:
        user_id = get_user_id_from_token(token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "INVALID_TOKEN",
                "message": str(exc),
            },
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = user_repository.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "INVALID_USER",
                "message": f"User with ID {user_id} not found or inactive.",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "USER_INACTIVE",
                "message": "User account is inactive.",
            },
        )

    return UserContext(user)


def require_roles(*required_roles: UserRole):
    def role_checker(
        user_ctx: UserContext = Depends(get_user_context),
    ) -> UserContext:
        if not user_ctx.has_role(*required_roles):
            role_names = ", ".join(role.value for role in required_roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error_code": "INSUFFICIENT_PERMISSIONS",
                    "message": f"Insufficient permissions. Required roles: {role_names}",
                },
            )
        return user_ctx

    return role_checker


require_admin = require_roles(UserRole.ADMIN)
require_buyer_or_admin = require_roles(UserRole.BUYER, UserRole.ADMIN)
require_any_authenticated = Depends(get_user_context)


def get_current_user(user_ctx: UserContext = Depends(get_user_context)) -> User:
    return user_ctx.user


def get_current_user_id(user_ctx: UserContext = Depends(get_user_context)) -> str:
    return user_ctx.user_id
