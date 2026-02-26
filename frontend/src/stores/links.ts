import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { linksApi } from '@/api/links'
import type { Link, CreateLinkRequest, UpdateLinkRequest } from '@/types'

export const useLinksStore = defineStore('links', () => {
  const links = ref<Link[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const linksByGroup = computed(() => {
    const grouped: Record<string, Link[]> = {}
    links.value.forEach(link => {
      if (!grouped[link.navigation_group_id]) {
        grouped[link.navigation_group_id] = []
      }
      grouped[link.navigation_group_id].push(link)
    })
    Object.keys(grouped).forEach(groupId => {
      grouped[groupId].sort((a, b) => a.sort_order - b.sort_order)
    })
    return grouped
  })

  const activeLinks = computed(() =>
    links.value.filter(l => l.is_active).sort((a, b) => a.sort_order - b.sort_order)
  )

  async function fetchLinks(params?: {
    skip?: number
    limit?: number
    navigation_group_id?: string
    is_active?: boolean
  }): Promise<void> {
    try {
      loading.value = true
      error.value = null
      links.value = await linksApi.list(params)
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch links'
      error.value = errorMessage
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createLink(data: CreateLinkRequest): Promise<Link> {
    try {
      loading.value = true
      error.value = null
      const newLink = await linksApi.create(data)
      links.value = [...links.value, newLink]
      return newLink
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create link'
      error.value = errorMessage
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateLink(id: string, data: UpdateLinkRequest): Promise<Link> {
    try {
      loading.value = true
      error.value = null
      const updatedLink = await linksApi.update(id, data)
      links.value = links.value.map(l => l.id === id ? updatedLink : l)
      return updatedLink
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update link'
      error.value = errorMessage
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteLink(id: string): Promise<void> {
    try {
      loading.value = true
      error.value = null
      await linksApi.delete(id)
      links.value = links.value.filter(l => l.id !== id)
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete link'
      error.value = errorMessage
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    links,
    linksByGroup,
    activeLinks,
    loading,
    error,
    fetchLinks,
    createLink,
    updateLink,
    deleteLink
  }
})
