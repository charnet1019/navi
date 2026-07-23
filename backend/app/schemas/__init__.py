"""Pydantic schemas for request/response validation."""

from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
)
from app.schemas.auth import (
    LoginRequest,
    AuthResponse,
    PasswordChangeRequest,
)
from app.schemas.role import (
    RoleBase,
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    RoleWithPermissions,
)
from app.schemas.permission import (
    PermissionBase,
    PermissionResponse,
    GrantPermissionRequest,
    NavGroupPermissionResponse,
    LinkPermissionResponse,
)
from app.schemas.user_group import (
    UserGroupBase,
    UserGroupCreate,
    UserGroupUpdate,
    UserGroupResponse,
    UserGroupWithMembers,
    UserGroupMember,
)
from app.schemas.navigation_group import (
    NavigationGroupBase,
    NavigationGroupCreate,
    NavigationGroupUpdate,
    NavigationGroupResponse,
    NavigationGroupWithLinks,
)
from app.schemas.link import (
    LinkBase,
    LinkCreate,
    LinkUpdate,
    LinkResponse,
)
from app.schemas.system_setting import (
    SystemSettingBase,
    SystemSettingUpdate,
    SystemSettingResponse,
)

__all__ = [
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "LoginRequest",
    "AuthResponse",
    "PasswordChangeRequest",
    "RoleBase",
    "RoleCreate",
    "RoleUpdate",
    "RoleResponse",
    "RoleWithPermissions",
    "PermissionBase",
    "PermissionResponse",
    "GrantPermissionRequest",
    "NavGroupPermissionResponse",
    "LinkPermissionResponse",
    "UserGroupBase",
    "UserGroupCreate",
    "UserGroupUpdate",
    "UserGroupResponse",
    "UserGroupWithMembers",
    "UserGroupMember",
    "NavigationGroupBase",
    "NavigationGroupCreate",
    "NavigationGroupUpdate",
    "NavigationGroupResponse",
    "NavigationGroupWithLinks",
    "LinkBase",
    "LinkCreate",
    "LinkUpdate",
    "LinkResponse",
    "SystemSettingBase",
    "SystemSettingUpdate",
    "SystemSettingResponse",
]
