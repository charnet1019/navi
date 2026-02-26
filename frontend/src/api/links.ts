import apiClient from './client'
import type {
  Link,
  CreateLinkRequest,
  UpdateLinkRequest
} from '@/types'

export const linksApi = {
  async list(params?: {
    skip?: number
    limit?: number
    navigation_group_id?: string
    is_active?: boolean
  }): Promise<Link[]> {
    const response = await apiClient.get<Link[]>('/links/', { params })
    return response.data
  },

  async getById(id: string): Promise<Link> {
    const response = await apiClient.get<Link>(`/links/${id}`)
    return response.data
  },

  async create(data: CreateLinkRequest): Promise<Link> {
    const response = await apiClient.post<Link>('/links/', data)
    return response.data
  },

  async update(id: string, data: UpdateLinkRequest): Promise<Link> {
    const response = await apiClient.put<Link>(`/links/${id}`, data)
    return response.data
  },

  async delete(id: string): Promise<void> {
    await apiClient.delete(`/links/${id}`)
  },

  async listByGroup(groupId: string): Promise<Link[]> {
    const response = await apiClient.get<Link[]>(`/links/by-group/${groupId}`)
    return response.data
  }
}
