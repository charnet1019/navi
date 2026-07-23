import apiClient from './client'
import type {
  User,
  CreateUserRequest,
  UpdateUserRequest,
  ResetPasswordRequest,
  AuthorizedAssets
} from '@/types'

export const usersApi = {
  async list(params?: {
    skip?: number
    limit?: number
    is_active?: boolean
  }): Promise<{ users: User[]; total: number }> {
    const response = await apiClient.get<User[]>('/users/', { params })
    const totalHeader = response.headers['x-total-count']
    const total = totalHeader !== undefined ? Number(totalHeader) : response.data.length
    return { users: response.data, total }
  },

  async getById(id: string): Promise<User> {
    const response = await apiClient.get<User>(`/users/${id}`)
    return response.data
  },

  async create(data: CreateUserRequest): Promise<User> {
    const response = await apiClient.post<User>('/users/', data)
    return response.data
  },

  async update(id: string, data: UpdateUserRequest): Promise<User> {
    const response = await apiClient.put<User>(`/users/${id}`, data)
    return response.data
  },

  async delete(id: string): Promise<void> {
    await apiClient.delete(`/users/${id}`)
  },

  async resetPassword(id: string, data: ResetPasswordRequest): Promise<void> {
    await apiClient.post(`/users/${id}/reset-password`, data)
  },

  async disable(id: string): Promise<User> {
    const response = await apiClient.post<User>(`/users/${id}/disable`)
    return response.data
  },

  async enable(id: string): Promise<User> {
    const response = await apiClient.post<User>(`/users/${id}/enable`)
    return response.data
  },

  async getAuthorizedAssets(id: string): Promise<AuthorizedAssets> {
    const response = await apiClient.get<AuthorizedAssets>(`/users/${id}/authorized-assets`)
    return response.data
  },

  async unlock(id: string): Promise<void> {
    await apiClient.post(`/users/${id}/unlock`)
  }
}
