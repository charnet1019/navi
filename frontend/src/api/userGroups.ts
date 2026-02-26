import apiClient from './client'
import type {
  UserGroup,
  UserGroupWithMembers,
  CreateUserGroupRequest,
  UpdateUserGroupRequest,
  AuthorizedAssets
} from '@/types'

export const userGroupsApi = {
  // List user groups
  async list(params?: {
    skip?: number
    limit?: number
  }): Promise<UserGroup[]> {
    const response = await apiClient.get<UserGroup[]>('/user-groups/', { params })
    return response.data
  },

  // Get user group by ID with members
  async getById(id: string): Promise<UserGroupWithMembers> {
    const response = await apiClient.get<UserGroupWithMembers>(`/user-groups/${id}`)
    return response.data
  },

  // Create user group
  async create(data: CreateUserGroupRequest): Promise<UserGroup> {
    const response = await apiClient.post<UserGroup>('/user-groups/', data)
    return response.data
  },

  // Update user group
  async update(id: string, data: UpdateUserGroupRequest): Promise<UserGroup> {
    const response = await apiClient.put<UserGroup>(`/user-groups/${id}`, data)
    return response.data
  },

  // Delete user group
  async delete(id: string): Promise<void> {
    await apiClient.delete(`/user-groups/${id}`)
  },

  // Add user to group
  async addMember(groupId: string, userId: string): Promise<UserGroupWithMembers> {
    const response = await apiClient.post<UserGroupWithMembers>(
      `/user-groups/${groupId}/members`,
      null,
      { params: { user_id: userId } }
    )
    return response.data
  },

  // Remove user from group
  async removeMember(groupId: string, userId: string): Promise<UserGroupWithMembers> {
    const response = await apiClient.delete<UserGroupWithMembers>(
      `/user-groups/${groupId}/members/${userId}`
    )
    return response.data
  },

  async getAuthorizedAssets(groupId: string): Promise<AuthorizedAssets> {
    const response = await apiClient.get<AuthorizedAssets>(
      `/user-groups/${groupId}/authorized-assets`
    )
    return response.data
  }
}
