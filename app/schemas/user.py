from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.db.models import UserRole


class UserBase(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    email: str = Field(min_length=1, max_length=100)
    nickname: Optional[str] = Field(default=None, max_length=50)
    role: UserRole = Field(default=UserRole.BUYER)
    company_id: Optional[str] = Field(default=None, max_length=36)


class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=128)


class UserUpdate(BaseModel):
    email: Optional[str] = Field(default=None, min_length=1, max_length=100)
    nickname: Optional[str] = Field(default=None, max_length=50)
    role: Optional[UserRole] = None
    company_id: Optional[str] = None
    is_active: Optional[bool] = None


class UserPasswordUpdate(BaseModel):
    old_password: str = Field(min_length=6, max_length=128)
    new_password: str = Field(min_length=6, max_length=128)


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    nickname: Optional[str]
    role: str
    company_id: Optional[str]
    is_active: bool
    last_login_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    total: int
    items: list[UserResponse]


class UserLoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=6, max_length=128)


class UserLoginResponse(BaseModel):
    user: UserResponse
    token: str
    expires_at: datetime
