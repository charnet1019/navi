import { defineStore } from 'pinia'
import { ref } from 'vue'
import { favoritesApi } from '@/api/favorites'
import { withLoading } from '@/utils/withLoading'
import type { Link } from '@/types'

export const useFavoritesStore = defineStore('favorites', () => {
  const favoriteIds = ref<Set<string>>(new Set())
  const favoriteLinks = ref<Link[]>([])
  const loading = ref(false)
  const reordering = ref(false)
  const error = ref<string | null>(null)

  function isFavorite(linkId: string): boolean {
    return favoriteIds.value.has(linkId)
  }

  async function fetchFavoriteIds(): Promise<void> {
    await withLoading(null, error, 'Failed to fetch favorite IDs', async () => {
      const ids = await favoritesApi.listIds()
      favoriteIds.value = new Set(ids)
    })
  }

  async function fetchFavoriteLinks(): Promise<void> {
    await withLoading(loading, error, 'Failed to fetch favorites', async () => {
      favoriteLinks.value = await favoritesApi.list()
    })
  }

  async function toggleFavorite(linkId: string): Promise<void> {
    await withLoading(null, error, 'Failed to toggle favorite', async () => {
      if (favoriteIds.value.has(linkId)) {
        await favoritesApi.remove(linkId)
        const next = new Set(favoriteIds.value)
        next.delete(linkId)
        favoriteIds.value = next
        favoriteLinks.value = favoriteLinks.value.filter(l => l.id !== linkId)
      } else {
        await favoritesApi.add(linkId)
        favoriteIds.value = new Set([...favoriteIds.value, linkId])
      }
    })
  }

  async function reorderFavorites(orderedIds: string[]): Promise<void> {
    if (reordering.value) return
    const items = orderedIds.map((id, index) => ({
      link_id: id,
      sort_order: index
    }))
    await withLoading(reordering, error, 'Failed to reorder favorites', async () => {
      favoriteLinks.value = await favoritesApi.reorder(items)
    })
  }

  return {
    favoriteIds,
    favoriteLinks,
    loading,
    reordering,
    error,
    isFavorite,
    fetchFavoriteIds,
    fetchFavoriteLinks,
    toggleFavorite,
    reorderFavorites
  }
})
