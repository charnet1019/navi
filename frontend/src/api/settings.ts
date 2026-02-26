import apiClient from './client'

export interface Setting {
  id: string
  key: string
  value: string
  description?: string
  updated_at: string
  updated_by?: string
}

export interface UpdateSettingRequest {
  value: string
}

export const settingsApi = {
  async list(): Promise<Setting[]> {
    const response = await apiClient.get('/settings/')
    return response.data
  },

  async listPublic(): Promise<Setting[]> {
    const response = await apiClient.get('/settings/public')
    return response.data
  },

  async getByKey(key: string): Promise<Setting> {
    const response = await apiClient.get(`/settings/${key}`)
    return response.data
  },

  async update(key: string, data: UpdateSettingRequest): Promise<Setting> {
    const response = await apiClient.put(`/settings/${key}`, data)
    return response.data
  }
}
