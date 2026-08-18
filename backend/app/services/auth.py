# app/services/auth.py
"""
Password hashing (via bcrypt directly, not passlib — passlib has known
compatibility issues with recent bcrypt versions) and JWT creation/verification.
Two token 'types' encoded in the JWT payload: "user" (real account) and
"guest" (quota-limited). /chat's auth dependency reads this to decide
whether to enforce the guest question limit.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
import bcrypt
from jose import jwt, JWTError

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("medbot.auth")

BCRYPT_MAX_BYTES = 72  # bcrypt's hard limit — longer inputs are truncated safely below


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")[:BCRYPT_MAX_BYTES]
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = plain_password.encode("utf-8")[:BCRYPT_MAX_BYTES]
    return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))


def create_access_token(data: dict, expires_minutes: Optional[int] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.jwt_expire_minutes
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as e:
        logger.warning(f"Token decode failed: {e}")
        return None
