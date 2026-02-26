import apiClient from './client'
import type {
  NavGroupPermission,
  LinkPermission,
  GrantPermissionRequest
} from '@/types'

export const authorizationApi = {
  async listNavGroupPermissions(groupId: string): Promise<NavGroupPermission[]> {
    const response = await apiClient.get<NavGroupPermission[]>(
      `/navigation-groups/${groupId}/permissions`
    )
    return response.data
  },

  async grantNavGroupPermission(
    groupId: string,
    data: GrantPermissionRequest
  ): Promise<{ message: string; permission_id: string }> {
    const response = await apiClient.post(
      `/navigation-groups/${groupId}/permissions`,
      data
    )
    return response.data
  },

  async revokeNavGroupPermission(groupId: string, permissionId: string): Promise<void> {
    await apiClient.delete(`/navigation-groups/${groupId}/permissions/${permissionId}`)
  },

  async listAllNavGroupPermissions(): Promise<NavGroupPermission[]> {
    const response = await apiClient.get<NavGroupPermission[]>(
      '/navigation-groups/all-permissions'
    )
    return response.data
  },

  async grantAllNavGroupPermission(
    data: GrantPermissionRequest
  ): Promise<{ message: string; permission_id: string }> {
    const response = await apiClient.post('/navigation-groups/all-permissions', data)
    return response.data
  },

  async revokeAllNavGroupPermission(permissionId: string): Promise<void> {
    await apiClient.delete(`/navigation-groups/all-permissions/${permissionId}`)
  },

  async listLinkPermissions(linkId: string): Promise<LinkPermission[]> {
    const response = await apiClient.get<LinkPermission[]>(
      `/links/${linkId}/permissions`
    )
    return response.data
  },

  async grantLinkPermission(
    linkId: string,
    data: GrantPermissionRequest
  ): Promise<{ message: string; permission_id: string }> {
    const response = await apiClient.post(`/links/${linkId}/permissions`, data)
    return response.data
  },

  async revokeLinkPermission(linkId: string, permissionId: string): Promise<void> {
    await apiClient.delete(`/links/${linkId}/permissions/${permissionId}`)
  }
}
