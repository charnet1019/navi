// User types
export interface UserGroupBrief {
  id: string
  name: string
}

export interface User {
  id: string
  username: string
  email: string
  full_name: string | null
  is_active: boolean
  is_superuser: boolean
  created_at: string
  updated_at: string
  last_login: string | null
  roles?: Role[]
  user_groups?: UserGroupBrief[]
}

export interface Role {
  id: string
  name: string
  description: string | null
  is_system: boolean
  created_at: string
  updated_at: string
  permissions?: Permission[]
}

export interface Permission {
  id: string
  name: string
  resource: string
  action: string
  description: string | null
}

// Authentication types
export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface TokenRefreshRequest {
  refresh_token: string
}

export interface ChangePasswordRequest {
  current_password: string
  new_password: string
}

// Navigation Group types
export interface NavigationGroup {
  id: string
  name: string
  description: string | null
  icon: string | null
  sort_order: number
  is_active: boolean
  parent_id: string | null
  created_by: string | null
  created_at: string
  updated_at: string
  children?: NavigationGroup[]
}

export interface CreateNavigationGroupRequest {
  name: string
  description?: string
  icon?: string
  sort_order?: number
  is_active?: boolean
  parent_id?: string | null
}

export interface UpdateNavigationGroupRequest {
  name?: string
  description?: string
  icon?: string
  sort_order?: number
  is_active?: boolean
  parent_id?: string | null
}

// Link types
export interface Link {
  id: string
  name: string
  url: string
  description: string | null
  icon_path: string | null
  sort_order: number
  is_active: boolean
  open_in_new_tab: boolean
  navigation_group_id: string
  created_by: string | null
  created_at: string
  updated_at: string
}

export interface CreateLinkRequest {
  name: string
  url: string
  description?: string
  icon_path?: string
  sort_order?: number
  is_active?: boolean
  open_in_new_tab?: boolean
  navigation_group_id: string
}

export interface UpdateLinkRequest {
  name?: string
  url?: string
  description?: string
  icon_path?: string
  sort_order?: number
  is_active?: boolean
  open_in_new_tab?: boolean
  navigation_group_id?: string
}

// User management types
export interface CreateUserRequest {
  username: string
  email: string
  password: string
  full_name?: string
  is_active?: boolean
  is_superuser?: boolean
  user_group_ids?: string[]
}

export interface UpdateUserRequest {
  email?: string
  full_name?: string
  is_active?: boolean
  is_superuser?: boolean
  user_group_ids?: string[]
}

export interface ResetPasswordRequest {
  new_password: string
}

// User Group types
export interface UserGroup {
  id: string
  name: string
  description: string | null
  created_at: string
  updated_at: string
}

export interface UserGroupMember {
  id: string
  username: string
  email: string
  full_name: string | null
}

export interface UserGroupWithMembers extends UserGroup {
  members: UserGroupMember[]
}

export interface CreateUserGroupRequest {
  name: string
  description?: string
}

export interface UpdateUserGroupRequest {
  name?: string
  description?: string
}

// API Response types
export interface ApiError {
  detail: string
}

// Fine-grained permission types
export interface NavGroupPermission {
  id: string
  navigation_group_id: string | null
  user_id: string | null
  user_group_id: string | null
  user_name: string | null
  user_group_name: string | null
  granted_at: string
  granted_by: string | null
}

export interface LinkPermission {
  id: string
  link_id: string
  user_id: string | null
  user_group_id: string | null
  user_name: string | null
  user_group_name: string | null
  granted_at: string
  granted_by: string | null
}

export interface GrantPermissionRequest {
  user_id?: string
  user_group_id?: string
}

// Authorized assets types
export interface NavGroupAsset {
  permission_id: string
  navigation_group_id: string | null
  navigation_group_name: string
  granted_at: string
}

export interface LinkAsset {
  permission_id: string
  link_id: string
  link_name: string
  navigation_group_name: string | null
  granted_at: string
}

export interface AuthorizedAssets {
  nav_group_permissions: NavGroupAsset[]
  link_permissions: LinkAsset[]
}
