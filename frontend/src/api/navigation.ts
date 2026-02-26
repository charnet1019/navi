import apiClient from './client'
import type {
  NavigationGroup,
  CreateNavigationGroupRequest,
  UpdateNavigationGroupRequest
} from '@/types'

export const navigationApi = {
  async list(params?: {
    skip?: number
    limit?: number
    is_active?: boolean
  }): Promise<NavigationGroup[]> {
    const response = await apiClient.get<NavigationGroup[]>('/navigation-groups/', { params })
    return response.data
  },

  async getById(id: string): Promise<NavigationGroup> {
    const response = await apiClient.get<NavigationGroup>(`/navigation-groups/${id}`)
    return response.data
  },

  async create(data: CreateNavigationGroupRequest): Promise<NavigationGroup> {
    const response = await apiClient.post<NavigationGroup>('/navigation-groups/', data)
    return response.data
  },

  async update(id: string, data: UpdateNavigationGroupRequest): Promise<NavigationGroup> {
    const response = await apiClient.put<NavigationGroup>(`/navigation-groups/${id}`, data)
    return response.data
  },

  async delete(id: string): Promise<void> {
    await apiClient.delete(`/navigation-groups/${id}`)
  },

  async reorder(items: { id: string; sort_order: number }[]): Promise<NavigationGroup[]> {
    const response = await apiClient.put<NavigationGroup[]>('/navigation-groups/reorder', items)
    return response.data
  }
}
