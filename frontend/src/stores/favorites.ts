import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { favoritesApi } from '@/api/favorites'
import type { Link } from '@/types'

export const useFavoritesStore = defineStore('favorites', () => {
  const favoriteIds = ref<Set<string>>(new Set())
  const favoriteLinks = ref<Link[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  function isFavorite(linkId: string): boolean {
    return favoriteIds.value.has(linkId)
  }

  async function fetchFavoriteIds(): Promise<void> {
    try {
      error.value = null
      const ids = await favoritesApi.listIds()
      favoriteIds.value = new Set(ids)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch favorite IDs'
      error.value = msg
      throw err
    }
  }

  async function fetchFavoriteLinks(): Promise<void> {
    try {
      loading.value = true
      error.value = null
      favoriteLinks.value = await favoritesApi.list()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch favorites'
      error.value = msg
      throw err
    } finally {
      loading.value = false
    }
  }

  async function toggleFavorite(linkId: string): Promise<void> {
    try {
      error.value = null
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
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to toggle favorite'
      error.value = msg
      throw err
    }
  }

  return {
    favoriteIds,
    favoriteLinks,
    loading,
    error,
    isFavorite,
    fetchFavoriteIds,
    fetchFavoriteLinks,
    toggleFavorite
  }
})
