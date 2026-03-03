import apiClient from './client'
import type { Link } from '@/types'

export const favoritesApi = {
  async list(): Promise<Link[]> {
    const response = await apiClient.get<Link[]>('/favorites/')
    return response.data
  },

  async listIds(): Promise<string[]> {
    const response = await apiClient.get<string[]>('/favorites/ids')
    return response.data
  },

  async add(linkId: string): Promise<void> {
    await apiClient.post(`/favorites/${linkId}`)
  },

  async remove(linkId: string): Promise<void> {
    await apiClient.delete(`/favorites/${linkId}`)
  },

  async reorder(items: { link_id: string; sort_order: number }[]): Promise<Link[]> {
    const response = await apiClient.put<Link[]>('/favorites/reorder', items)
    return response.data
  }
}
