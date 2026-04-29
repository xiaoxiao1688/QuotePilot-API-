import hashlib
import secrets
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.models import UserRole
from app.db.session import get_db_session
from app.repositories.user import user_repository
from app.schemas.user import (
    UserCreate,
    UserListResponse,
    UserLoginRequest,
    UserLoginResponse,
    UserPasswordUpdate,
    UserResponse,
    UserUpdate,
)

router = APIRouter()


def _hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    if salt is None:
        salt = secrets.token_hex(16)
    password_salt = f"{password}{salt}"
    password_hash = hashlib.sha256(password_salt.encode("utf-8")).hexdigest()
    return f"sha256:{salt}:{password_hash}", salt


def _verify_password(password: str, stored_hash: str) -> bool:
    if not stored_hash.startswith("sha256:"):
        return False
    parts = stored_hash.split(":")
    if len(parts) != 3:
        return False
    _, salt, _ = parts
    expected_hash, _ = _hash_password(password, salt)
    return secrets.compare_digest(stored_hash, expected_hash)


def get_current_user_id() -> str:
    return "demo-user-001"


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db_session)) -> UserResponse:
    if user_repository.exists_by_username(db, payload.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error_code": "USERNAME_EXISTS", "message": "Username already exists"},
        )

    if user_repository.exists_by_email(db, payload.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error_code": "EMAIL_EXISTS", "message": "Email already exists"},
        )

    password_hash, _ = _hash_password(payload.password)

    user = user_repository.create(
        session=db,
        username=payload.username,
        email=payload.email,
        password_hash=password_hash,
        nickname=payload.nickname,
        role=payload.role.value if isinstance(payload.role, UserRole) else payload.role,
        company_id=payload.company_id,
    )

    return UserResponse.model_validate(user)


@router.get("", response_model=UserListResponse)
def list_users(
    role: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db_session),
) -> UserListResponse:
    total, users = user_repository.list(
        session=db,
        role=role,
        is_active=is_active,
        search=search,
        limit=limit,
        offset=offset,
    )

    return UserListResponse(
        total=total,
        items=[UserResponse.model_validate(u) for u in users],
    )


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: str, db: Session = Depends(get_db_session)) -> UserResponse:
    user = user_repository.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "USER_NOT_FOUND", "message": "User not found"},
        )
    return UserResponse.model_validate(user)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    payload: UserUpdate,
    db: Session = Depends(get_db_session),
) -> UserResponse:
    user = user_repository.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "USER_NOT_FOUND", "message": "User not found"},
        )

    update_data = payload.model_dump(exclude_unset=True)

    if "email" in update_data:
        existing = user_repository.get_by_email(db, update_data["email"])
        if existing and existing.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error_code": "EMAIL_EXISTS", "message": "Email already exists"},
            )

    updated_user = user_repository.update(db, user_id, **update_data)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "UPDATE_FAILED", "message": "Failed to update user"},
        )

    return UserResponse.model_validate(updated_user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: str, db: Session = Depends(get_db_session)) -> None:
    user = user_repository.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "USER_NOT_FOUND", "message": "User not found"},
        )

    success = user_repository.delete(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "DELETE_FAILED", "message": "Failed to delete user"},
        )


@router.post("/{user_id}/change-password", response_model=UserResponse)
def change_password(
    user_id: str,
    payload: UserPasswordUpdate,
    db: Session = Depends(get_db_session),
) -> UserResponse:
    user = user_repository.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "USER_NOT_FOUND", "message": "User not found"},
        )

    if not _verify_password(payload.old_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "INVALID_PASSWORD", "message": "Current password is incorrect"},
        )

    new_password_hash, _ = _hash_password(payload.new_password)
    updated_user = user_repository.update(db, user_id, password_hash=new_password_hash)

    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "UPDATE_FAILED", "message": "Failed to update password"},
        )

    return UserResponse.model_validate(updated_user)


@router.post("/login", response_model=UserLoginResponse)
def login(payload: UserLoginRequest, db: Session = Depends(get_db_session)) -> UserLoginResponse:
    from datetime import datetime, timedelta

    user = user_repository.get_by_username(db, payload.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "INVALID_CREDENTIALS", "message": "Invalid username or password"},
        )

    if not _verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "INVALID_CREDENTIALS", "message": "Invalid username or password"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error_code": "USER_INACTIVE", "message": "User account is inactive"},
        )

    user_repository.update_last_login(db, user.id)

    expires_at = datetime.utcnow() + timedelta(hours=24)
    token_payload = f"{user.id}:{int(expires_at.timestamp())}"
    token_hash = hashlib.sha256((token_payload + secrets.token_hex(16)).encode("utf-8")).hexdigest()
    token = f"jwt_{user.id}_{token_hash}"

    return UserLoginResponse(
        user=UserResponse.model_validate(user),
        token=token,
        expires_at=expires_at,
    )
