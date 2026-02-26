"""Authentication endpoints."""

from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, PasswordChangeRequest
from app.core.security import (
    verify_password,
    create_tokens,
    verify_token,
    hash_password,
)
from app.api.deps import get_current_active_user
from app.redis import get_redis
from app.utils.time import now_cst
from app.utils.password import validate_password
from app.schemas.user import UserResponse
from app.config import settings
from app.models.system_setting import SystemSetting


router = APIRouter()

LOGIN_ATTEMPT_PREFIX = "login_attempts:"


async def _get_login_settings(db: AsyncSession) -> dict:
    """Load login limit settings from database."""
    keys = ["max_login_attempts", "login_lockout_minutes"]
    stmt = select(SystemSetting).where(SystemSetting.key.in_(keys))
    result = await db.execute(stmt)
    rows = {s.key: s.value for s in result.scalars().all()}
    return {
        "max_attempts": int(rows.get("max_login_attempts", 3)),
        "lockout_minutes": int(rows.get("login_lockout_minutes", 30)),
    }


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Login with username/password, return tokens."""
    login_settings = await _get_login_settings(db)
    max_attempts = login_settings["max_attempts"]
    lockout_minutes = login_settings["lockout_minutes"]

    redis = await get_redis()
    attempt_key = f"{LOGIN_ATTEMPT_PREFIX}{login_data.username}"

    # Check if user is locked out
    attempts = await redis.get(attempt_key)
    if attempts is not None and int(attempts) >= max_attempts:
        ttl = await redis.ttl(attempt_key)
        remaining = max(1, ttl // 60)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"登录失败次数过多，请在{remaining}分钟后重试",
        )

    stmt = select(User).where(User.username == login_data.username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None or not verify_password(login_data.password, user.hashed_password):
        # Increment failed attempt counter
        pipe = redis.pipeline()
        pipe.incr(attempt_key)
        pipe.expire(attempt_key, lockout_minutes * 60)
        await pipe.execute()

        current = int(await redis.get(attempt_key) or 0)
        remaining_attempts = max(0, max_attempts - current)

        if remaining_attempts == 0:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"登录失败次数过多，请在{lockout_minutes}分钟后重试",
            )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"用户名或密码错误，还可尝试{remaining_attempts}次",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    # Login success — clear attempt counter
    await redis.delete(attempt_key)

    user.last_login = now_cst()
    await db.commit()

    tokens = create_tokens(str(user.id))

    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    body: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Refresh access token using refresh token."""
    user_id_str = verify_token(body.refresh_token, token_type="refresh")

    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    redis = await get_redis()
    blacklist_key = f"blacklist:refresh:{body.refresh_token}"
    is_blacklisted = await redis.exists(blacklist_key)

    if is_blacklisted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
        )

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    tokens = create_tokens(str(user.id))

    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
    )


@router.post("/logout")
async def logout(
    body: LogoutRequest,
) -> dict:
    """Logout by blacklisting refresh token in Redis."""
    user_id_str = verify_token(body.refresh_token, token_type="refresh")

    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    redis = await get_redis()
    blacklist_key = f"blacklist:refresh:{body.refresh_token}"
    ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

    try:
        await redis.setex(blacklist_key, ttl, "1")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to logout",
        )

    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserResponse:
    """Get current user info."""
    return UserResponse.model_validate(current_user)


@router.put("/me/password")
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Change own password."""
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password",
        )

    # Validate new password against rules
    errors = await validate_password(password_data.new_password, db)
    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="；".join(errors),
        )

    current_user.hashed_password = hash_password(password_data.new_password)
    await db.commit()

    return {"message": "Password changed successfully"}
