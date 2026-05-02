import datetime
from typing import Any, Dict, Optional

import jwt

from app.core.config import settings

SECRET_KEY = settings.jwt_secret
ALGORITHM = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes


def create_access_token(data: Dict[str, Any], expires_delta: Optional[datetime.timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError as exc:
        raise ValueError(f"Invalid token: {str(exc)}") from exc


def get_user_id_from_token(token: str) -> str:
    payload = verify_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise ValueError("Invalid token: missing user ID")
    return user_id


def get_token_expiry(token: str) -> datetime.datetime:
    payload = verify_token(token)
    exp = payload.get("exp")
    if not exp:
        raise ValueError("Invalid token: missing expiry")
    return datetime.datetime.fromtimestamp(exp, datetime.timezone.utc)
