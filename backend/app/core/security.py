"""
认证安全 — JWT & 密码哈希
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.config import settings


def _password_digest(password: str) -> bytes:
    return hashlib.sha256(password.encode("utf-8")).hexdigest().encode("ascii")


def hash_password(password: str) -> str:
    """对密码进行 bcrypt 哈希"""
    return bcrypt.hashpw(_password_digest(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """校验密码"""
    return bcrypt.checkpw(_password_digest(plain_password), hashed_password.encode("utf-8"))


def create_access_token(sub: str, extra_claims: dict | None = None) -> str:
    """创建 JWT Token"""
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    payload = {
        "sub": sub,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """解码 JWT Token"""
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        raise ValueError("Invalid or expired token")
