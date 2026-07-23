import apiClient from './client'
import type { AuthAwareRequestConfig } from './client'
import type {
  LoginRequest,
  LoginResponse,
  User,
  ChangePasswordRequest
} from '@/types'

export const authApi = {
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await apiClient.post<LoginResponse>('/auth/login', credentials)
    return response.data
  },

  async refresh(): Promise<LoginResponse> {
    const response = await apiClient.post<LoginResponse>('/auth/refresh')
    return response.data
  },

  async logout(): Promise<void> {
    await apiClient.post('/auth/logout')
  },

  async getMe(options: { skipAuthRefresh?: boolean } = {}): Promise<User> {
    const config = options.skipAuthRefresh
      ? ({ _skipAuthRefresh: true } as AuthAwareRequestConfig)
      : undefined
    const response = await apiClient.get<User>('/auth/me', config)
    return response.data
  },

  async changePassword(data: ChangePasswordRequest): Promise<void> {
    await apiClient.put('/auth/me/password', data)
  }
}
