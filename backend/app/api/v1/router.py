"""API v1 router."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    users,
    roles,
    user_groups,
    permissions,
    navigation_groups,
    links,
    uploads,
    settings,
    favorites,
    audit_logs,
)


# Create main API router
api_router = APIRouter()

# Mount authentication endpoints
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"],
)

# Mount user management endpoints
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["Users"],
)

# Mount role management endpoints
api_router.include_router(
    roles.router,
    prefix="/roles",
    tags=["Roles"],
)

# Mount user group management endpoints
api_router.include_router(
    user_groups.router,
    prefix="/user-groups",
    tags=["User Groups"],
)

# Mount permission endpoints
api_router.include_router(
    permissions.router,
    prefix="/permissions",
    tags=["Permissions"],
)

# Mount navigation group endpoints
api_router.include_router(
    navigation_groups.router,
    prefix="/navigation-groups",
    tags=["Navigation Groups"],
)

# Mount link endpoints
api_router.include_router(
    links.router,
    prefix="/links",
    tags=["Links"],
)

# Mount upload endpoints
api_router.include_router(
    uploads.router,
    prefix="/uploads",
    tags=["Uploads"],
)

# Mount system settings endpoints
api_router.include_router(
    settings.router,
    prefix="/settings",
    tags=["System Settings"],
)

# Mount favorites endpoints
api_router.include_router(
    favorites.router,
    prefix="/favorites",
    tags=["Favorites"],
)

# Mount audit log endpoints (read-only)
api_router.include_router(
    audit_logs.router,
    prefix="/audit-logs",
    tags=["Audit Logs"],
)
