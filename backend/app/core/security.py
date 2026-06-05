"""Security primitives: password hashing and JWT token handling.

Centralizes all cryptographic concerns so the rest of the app never touches
bcrypt or JWT internals directly.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

# bcrypt only considers the first 72 bytes of a password and raises on longer
# inputs in recent versions, so we always truncate the encoded bytes to 72.
_BCRYPT_MAX_BYTES = 72


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"
    RESET = "reset"


# --------------------------------------------------------------- passwords
def _encode(password: str) -> bytes:
    return password.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def hash_password(plain_password: str) -> str:
    """Return a bcrypt hash for the given plaintext password."""
    return bcrypt.hashpw(_encode(plain_password), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a plaintext password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(
            _encode(plain_password), hashed_password.encode("utf-8")
        )
    except ValueError:
        return False


# ------------------------------------------------------------------ tokens
def _create_token(
    subject: str | int,
    token_type: TokenType,
    expires_delta: timedelta,
) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": token_type.value,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_access_token(subject: str | int) -> str:
    return _create_token(
        subject,
        TokenType.ACCESS,
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(subject: str | int) -> str:
    return _create_token(
        subject,
        TokenType.REFRESH,
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def create_token_pair(subject: str | int) -> tuple[str, str]:
    """Return ``(access_token, refresh_token)`` for a subject."""
    return create_access_token(subject), create_refresh_token(subject)


def create_password_reset_token(subject: str | int) -> str:
    """Short-lived token used to authorize a password reset."""
    return _create_token(subject, TokenType.RESET, timedelta(minutes=30))


def decode_token(token: str, expected_type: TokenType | None = None) -> dict[str, Any]:
    """Decode and validate a JWT.

    Raises ``JWTError`` if the signature/expiry is invalid or if the token type
    does not match ``expected_type``.
    """
    payload = jwt.decode(
        token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
    )
    if expected_type is not None and payload.get("type") != expected_type.value:
        raise JWTError(
            f"Invalid token type: expected {expected_type.value!r}, "
            f"got {payload.get('type')!r}"
        )
    return payload


__all__ = [
    "TokenType",
    "JWTError",
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "create_token_pair",
    "create_password_reset_token",
    "decode_token",
]
