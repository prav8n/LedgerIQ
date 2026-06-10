"""Pydantic v2 schemas for users and authentication."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

# bcrypt only uses the first 72 bytes; we cap length to avoid silent truncation.
PasswordStr = Field(min_length=8, max_length=72)


# ----------------------------------------------------------------- requests
class UserRegister(BaseModel):
    email: EmailStr
    password: str = PasswordStr
    full_name: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=20)

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class UserLogin(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class UserUpdate(BaseModel):
    """Editable profile fields (all optional / partial update)."""

    full_name: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=20)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    locale: str | None = Field(default=None, max_length=10)
    timezone: str | None = Field(default=None, max_length=40)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = PasswordStr


class ChangeEmailRequest(BaseModel):
    new_email: EmailStr
    current_password: str

    @field_validator("new_email")
    @classmethod
    def _normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class ForgotPasswordRequest(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class RefreshRequest(BaseModel):
    refresh_token: str


# ---------------------------------------------------------------- responses
class UserProfile(BaseModel):
    """Public-facing user representation (never includes the password hash)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str | None
    phone: str | None
    currency: str
    locale: str
    timezone: str
    is_active: bool
    is_verified: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthResponse(BaseModel):
    """Returned by register/login — tokens plus the user profile."""

    user: UserProfile
    tokens: Token


class MessageResponse(BaseModel):
    message: str
    # Populated only in DEBUG so flows are testable without an email service.
    reset_token: str | None = None
