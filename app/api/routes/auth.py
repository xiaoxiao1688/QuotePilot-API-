from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.jwt import create_access_token
from app.core.password import verify_password
from app.core.security import UserContext, get_current_user, require_admin
from app.db.session import get_db_session
from app.repositories.user import user_repository
from app.schemas.user import UserLoginRequest, UserLoginResponse, UserResponse

router = APIRouter()


@router.post("/login", response_model=UserLoginResponse)
def login(
    payload: UserLoginRequest,
    db: Session = Depends(get_db_session),
) -> UserLoginResponse:
    user = user_repository.get_by_username(db, payload.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "INVALID_CREDENTIALS", "message": "Invalid username or password"},
        )

    if not verify_password(payload.password, user.password_hash):
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

    access_token_expires = timedelta(minutes=1440)
    access_token = create_access_token(
        data={"sub": user.id, "username": user.username, "role": user.role},
        expires_delta=access_token_expires,
    )

    return UserLoginResponse(
        user=UserResponse.model_validate(user),
        token=access_token,
        expires_at=datetime.utcnow() + access_token_expires,
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
) -> UserResponse:
    return current_user


@router.post("/verify", response_model=UserResponse)
def verify_user(
    user_id: str,
    admin_ctx: Annotated[UserContext, Depends(require_admin)],
    db: Session = Depends(get_db_session),
) -> UserResponse:
    user = user_repository.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "USER_NOT_FOUND", "message": "User not found"},
        )
    return UserResponse.model_validate(user)
