import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { linksApi } from '@/api/links'
import { withLoading } from '@/utils/withLoading'
import type { Link, CreateLinkRequest, UpdateLinkRequest } from '@/types'

export const useLinksStore = defineStore('links', () => {
  const links = ref<Link[]>([])
  const loading = ref(false)
  const reordering = ref(false)
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
    await withLoading(loading, error, 'Failed to fetch links', async () => {
      links.value = await linksApi.list(params)
    })
  }

  async function createLink(data: CreateLinkRequest): Promise<Link> {
    return withLoading(loading, error, 'Failed to create link', async () => {
      const newLink = await linksApi.create(data)
      links.value = [...links.value, newLink]
      return newLink
    })
  }

  async function updateLink(id: string, data: UpdateLinkRequest): Promise<Link> {
    return withLoading(loading, error, 'Failed to update link', async () => {
      const updatedLink = await linksApi.update(id, data)
      links.value = links.value.map(l => l.id === id ? updatedLink : l)
      return updatedLink
    })
  }

  async function deleteLink(id: string): Promise<void> {
    await withLoading(loading, error, 'Failed to delete link', async () => {
      await linksApi.delete(id)
      links.value = links.value.filter(l => l.id !== id)
    })
  }

  async function reorderLinks(orderedIds: string[]): Promise<void> {
    if (reordering.value) return
    const items = orderedIds.map((id, index) => ({ id, sort_order: index }))
    await withLoading(reordering, error, 'Failed to reorder links', async () => {
      const updated = await linksApi.reorder(items)
      const updatedMap = new Map(updated.map(link => [link.id, link]))
      links.value = links.value.map(link => updatedMap.get(link.id) ?? link)
    })
  }

  return {
    links,
    linksByGroup,
    activeLinks,
    loading,
    reordering,
    error,
    fetchLinks,
    createLink,
    updateLink,
    deleteLink,
    reorderLinks
  }
})
