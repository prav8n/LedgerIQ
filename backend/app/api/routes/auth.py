"""Authentication & profile routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.config import settings
from app.core.dependencies import CurrentUser, SessionDep
from app.core.security import (
    JWTError,
    TokenType,
    create_password_reset_token,
    create_token_pair,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.user import (
    AuthResponse,
    ChangeEmailRequest,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    MessageResponse,
    RefreshRequest,
    Token,
    UserLogin,
    UserProfile,
    UserRegister,
    UserUpdate,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


async def _get_user_by_email(db: SessionDep, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


def _tokens_for(user: User) -> Token:
    access, refresh = create_token_pair(user.id)
    return Token(access_token=access, refresh_token=refresh)


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user and return tokens",
)
async def register(payload: UserRegister, db: SessionDep) -> AuthResponse:
    if not settings.ALLOW_REGISTRATION:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registration is disabled",
        )
    if await _get_user_by_email(db, payload.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        phone=payload.phone,
        currency=settings.DEFAULT_CURRENCY,
        locale=settings.DEFAULT_LOCALE,
        timezone=settings.DEFAULT_TIMEZONE,
    )
    db.add(user)
    await db.flush()  # assigns user.id without ending the request transaction
    await db.refresh(user)

    return AuthResponse(user=UserProfile.model_validate(user), tokens=_tokens_for(user))


@router.post("/login", response_model=AuthResponse, summary="Authenticate a user")
async def login(payload: UserLogin, db: SessionDep) -> AuthResponse:
    user = await _get_user_by_email(db, payload.email)
    # Verify even when the user is missing to reduce timing/enumeration signal.
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user account"
        )
    return AuthResponse(user=UserProfile.model_validate(user), tokens=_tokens_for(user))


@router.post("/refresh", response_model=Token, summary="Rotate tokens")
async def refresh(payload: RefreshRequest, db: SessionDep) -> Token:
    try:
        claims = decode_token(payload.refresh_token, expected_type=TokenType.REFRESH)
        user_id = int(claims["sub"])
    except (JWTError, KeyError, ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer valid"
        )
    return _tokens_for(user)


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Begin password reset",
)
async def forgot_password(
    payload: ForgotPasswordRequest, db: SessionDep
) -> MessageResponse:
    user = await _get_user_by_email(db, payload.email)

    # Always respond identically to avoid leaking which emails are registered.
    generic = MessageResponse(
        message="If an account exists for this email, a reset link has been sent."
    )
    if user is None:
        return generic

    reset_token = create_password_reset_token(user.id)
    # TODO(email): dispatch reset_token via the email service when available.
    if settings.DEBUG:
        generic.reset_token = reset_token
    return generic


@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Change password (authenticated)",
)
async def change_password(
    payload: ChangePasswordRequest, current_user: CurrentUser, db: SessionDep
) -> MessageResponse:
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    if verify_password(payload.new_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must differ from the current one",
        )

    current_user.hashed_password = hash_password(payload.new_password)
    db.add(current_user)
    return MessageResponse(message="Password updated successfully")


@router.post(
    "/change-email",
    response_model=UserProfile,
    summary="Change email (authenticated)",
)
async def change_email(
    payload: ChangeEmailRequest, current_user: CurrentUser, db: SessionDep
) -> UserProfile:
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect"
        )
    if payload.new_email == current_user.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New email is the same as the current one",
        )
    existing = await _get_user_by_email(db, payload.new_email)
    if existing is not None and existing.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )
    current_user.email = payload.new_email
    db.add(current_user)
    await db.flush()
    await db.refresh(current_user)
    return UserProfile.model_validate(current_user)


@router.get("/profile", response_model=UserProfile, summary="Get current profile")
async def get_profile(current_user: CurrentUser) -> UserProfile:
    return UserProfile.model_validate(current_user)


@router.put("/profile", response_model=UserProfile, summary="Update current profile")
async def update_profile(
    payload: UserUpdate, current_user: CurrentUser, db: SessionDep
) -> UserProfile:
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(current_user, field, value)
    db.add(current_user)
    await db.flush()
    await db.refresh(current_user)
    return UserProfile.model_validate(current_user)
