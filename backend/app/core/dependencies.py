"""Reusable FastAPI dependencies (DB session + authentication)."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import JWTError, TokenType, decode_token
from app.db.session import get_db
from app.models.user import User

# Annotated alias so routes can write `db: SessionDep`.
SessionDep = Annotated[AsyncSession, Depends(get_db)]

# HTTP Bearer scheme — clients send `Authorization: Bearer <access_token>`.
_bearer_scheme = HTTPBearer(auto_error=True, description="JWT access token")

_credentials_exc = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer_scheme)],
    db: SessionDep,
) -> User:
    """Resolve the authenticated user from a Bearer access token."""
    try:
        payload = decode_token(credentials.credentials, expected_type=TokenType.ACCESS)
        subject = payload.get("sub")
        if subject is None:
            raise _credentials_exc
        user_id = int(subject)
    except (JWTError, ValueError, TypeError):
        raise _credentials_exc

    user = await db.get(User, user_id)
    if user is None:
        raise _credentials_exc
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user account"
        )
    return user


# Annotated alias so routes can write `current_user: CurrentUser`.
CurrentUser = Annotated[User, Depends(get_current_user)]


__all__ = ["SessionDep", "CurrentUser", "get_current_user"]
