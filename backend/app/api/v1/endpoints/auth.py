"""Authentication endpoints."""

import logging
import secrets
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from redis.exceptions import RedisError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_active_user
from app.config import settings
from app.core.security import (
    create_tokens,
    hash_password,
    verify_password,
    verify_token,
)
from app.database import get_db
from app.models.system_setting import SystemSetting
from app.models.user import User
from app.redis import get_redis
from app.schemas.auth import AuthResponse, LoginRequest, PasswordChangeRequest
from app.schemas.user import UserResponse
from app.services.audit import record_audit_log
from app.utils.password import validate_password
from app.utils.time import now_cst

logger = logging.getLogger(__name__)

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


async def _get_required_redis():
    try:
        redis = await get_redis()
        await redis.ping()
        return redis
    except RedisError:
        logger.error("Redis unavailable for auth request", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="认证缓存服务不可用，请稍后重试",
        )


def _cookie_options(max_age: int) -> dict:
    return {
        "max_age": max_age,
        "httponly": True,
        "secure": settings.AUTH_COOKIE_SECURE,
        "samesite": settings.auth_cookie_samesite,
        "domain": settings.auth_cookie_domain,
        "path": "/",
    }


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    response.set_cookie(
        settings.AUTH_ACCESS_COOKIE_NAME,
        access_token,
        **_cookie_options(settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60),
    )
    response.set_cookie(
        settings.AUTH_REFRESH_COOKIE_NAME,
        refresh_token,
        **_cookie_options(settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60),
    )
    response.set_cookie(
        settings.AUTH_CSRF_COOKIE_NAME,
        secrets.token_urlsafe(32),
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        httponly=False,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.auth_cookie_samesite,
        domain=settings.auth_cookie_domain,
        path="/",
    )


def _clear_auth_cookies(response: Response) -> None:
    for name in (
        settings.AUTH_ACCESS_COOKIE_NAME,
        settings.AUTH_REFRESH_COOKIE_NAME,
        settings.AUTH_CSRF_COOKIE_NAME,
    ):
        response.delete_cookie(
            name,
            domain=settings.auth_cookie_domain,
            path="/",
            secure=settings.AUTH_COOKIE_SECURE,
            samesite=settings.auth_cookie_samesite,
        )


@router.post("/login", response_model=AuthResponse)
async def login(
    login_data: LoginRequest,
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuthResponse:
    """Login with username/password and set HttpOnly auth cookies."""
    login_settings = await _get_login_settings(db)
    max_attempts = login_settings["max_attempts"]
    lockout_minutes = login_settings["lockout_minutes"]

    redis = await _get_required_redis()
    attempt_key = f"{LOGIN_ATTEMPT_PREFIX}{login_data.username}"

    attempts = await redis.get(attempt_key)
    if attempts is not None and int(attempts) >= max_attempts:
        ttl = await redis.ttl(attempt_key)
        remaining = max(1, ttl // 60)
        await record_audit_log(
            db,
            user_id=None,
            action="auth.login_locked",
            resource_type="user",
            changes={"username": login_data.username, "remaining_minutes": remaining},
            request=request,
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"登录失败次数过多，请在{remaining}分钟后重试",
        )

    stmt = select(User).where(User.username == login_data.username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None or not verify_password(login_data.password, user.hashed_password):
        pipe = redis.pipeline()
        pipe.incr(attempt_key)
        pipe.expire(attempt_key, lockout_minutes * 60)
        current = int((await pipe.execute())[0] or 0)

        if current >= max_attempts:
            await record_audit_log(
                db,
                user_id=user.id if user else None,
                action="auth.login_failed",
                resource_type="user",
                resource_id=user.id if user else None,
                changes={
                    "username": login_data.username,
                    "reason": "lockout_after_failure",
                    "attempt_count": current,
                },
                request=request,
            )
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"登录失败次数过多，请在{lockout_minutes}分钟后重试",
            )

        await record_audit_log(
            db,
            user_id=user.id if user else None,
            action="auth.login_failed",
            resource_type="user",
            resource_id=user.id if user else None,
            changes={
                "username": login_data.username,
                "reason": "invalid_credentials",
                "attempt_count": current,
            },
            request=request,
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    if not user.is_active:
        await record_audit_log(
            db,
            user_id=user.id,
            action="auth.login_failed",
            resource_type="user",
            resource_id=user.id,
            changes={"username": user.username, "reason": "inactive_user"},
            request=request,
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    user.last_login = now_cst()
    await record_audit_log(
        db,
        user_id=user.id,
        action="auth.login_success",
        resource_type="user",
        resource_id=user.id,
        changes={"username": user.username},
        request=request,
    )
    await db.commit()

    await redis.delete(attempt_key)

    tokens = create_tokens(str(user.id))
    _set_auth_cookies(response, tokens.access_token, tokens.refresh_token)

    return AuthResponse(message="登录成功")


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    refresh_token_cookie: Annotated[str | None, Cookie(alias=settings.AUTH_REFRESH_COOKIE_NAME)] = None,
) -> AuthResponse:
    """Refresh auth cookies using the HttpOnly refresh cookie."""
    if not refresh_token_cookie:
        _clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id_str = verify_token(refresh_token_cookie, token_type="refresh")

    if user_id_str is None:
        _clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    redis = await _get_required_redis()
    blacklist_key = f"blacklist:refresh:{refresh_token_cookie}"
    is_blacklisted = await redis.exists(blacklist_key)

    if is_blacklisted:
        _clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        _clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
        )

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        _clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    await redis.setex(blacklist_key, ttl, "1")

    await record_audit_log(
        db,
        user_id=user.id,
        action="auth.refresh",
        resource_type="user",
        resource_id=user.id,
        request=request,
    )
    await db.commit()

    tokens = create_tokens(str(user.id))
    _set_auth_cookies(response, tokens.access_token, tokens.refresh_token)

    return AuthResponse(message="刷新成功")


@router.post("/logout", response_model=AuthResponse)
async def logout(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    refresh_token_cookie: Annotated[str | None, Cookie(alias=settings.AUTH_REFRESH_COOKIE_NAME)] = None,
) -> AuthResponse:
    """Logout by blacklisting refresh cookie and clearing auth cookies."""
    user_id: UUID | None = None
    if refresh_token_cookie:
        user_id_str = verify_token(refresh_token_cookie, token_type="refresh")
        if user_id_str is not None:
            try:
                user_id = UUID(user_id_str)
            except ValueError:
                user_id = None

            redis = await _get_required_redis()
            blacklist_key = f"blacklist:refresh:{refresh_token_cookie}"
            ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
            try:
                await redis.setex(blacklist_key, ttl, "1")
            except RedisError:
                logger.error("Failed to blacklist refresh token on logout", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="认证缓存服务不可用，请稍后重试",
                )

    if user_id is not None:
        existing_user_id = await db.scalar(select(User.id).where(User.id == user_id))
        await record_audit_log(
            db,
            user_id=existing_user_id,
            action="auth.logout",
            resource_type="user",
            resource_id=user_id,
            request=request,
        )
        await db.commit()

    _clear_auth_cookies(response)
    return AuthResponse(message="退出成功")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    """Get current user info."""
    stmt = select(User).where(User.id == current_user.id).options(selectinload(User.user_groups))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return UserResponse.model_validate(user)


@router.put("/me/password", response_model=AuthResponse)
async def change_password(
    password_data: PasswordChangeRequest,
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuthResponse:
    """Change own password."""
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password",
        )

    errors = await validate_password(password_data.new_password, db)
    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="；".join(errors),
        )

    current_user.hashed_password = hash_password(password_data.new_password)
    await record_audit_log(
        db,
        user_id=current_user.id,
        action="user.change_password",
        resource_type="user",
        resource_id=current_user.id,
        request=request,
    )
    await db.commit()

    try:
        redis = await get_redis()
        await redis.delete(f"{LOGIN_ATTEMPT_PREFIX}{current_user.username}")
    except RedisError:
        logger.warning(
            "Failed to clear login attempt counter after password change for user %s",
            current_user.username,
            exc_info=True,
        )

    return AuthResponse(message="Password changed successfully")
