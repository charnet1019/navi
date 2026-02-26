import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { navigationApi } from '@/api/navigation'
import type { NavigationGroup, CreateNavigationGroupRequest, UpdateNavigationGroupRequest } from '@/types'

export const useNavigationStore = defineStore('navigation', () => {
  const groups = ref<NavigationGroup[]>([])
  const selectedGroupId = ref<string | null>(null)
  const loading = ref(false)
  const fetched = ref(false)
  const error = ref<string | null>(null)

  const selectedGroup = computed(() =>
    groups.value.find(g => g.id === selectedGroupId.value) ?? null
  )

  const activeGroups = computed(() =>
    groups.value.filter(g => g.is_active).sort((a, b) => a.sort_order - b.sort_order)
  )

  async function fetchGroups(params?: { skip?: number; limit?: number; is_active?: boolean }): Promise<void> {
    try {
      if (!fetched.value) loading.value = true
      error.value = null
      groups.value = await navigationApi.list(params)
      fetched.value = true
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch groups'
      error.value = errorMessage
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createGroup(data: CreateNavigationGroupRequest): Promise<NavigationGroup> {
    try {
      loading.value = true
      error.value = null
      const newGroup = await navigationApi.create(data)
      groups.value = [...groups.value, newGroup]
      return newGroup
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create group'
      error.value = errorMessage
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateGroup(id: string, data: UpdateNavigationGroupRequest): Promise<NavigationGroup> {
    try {
      loading.value = true
      error.value = null
      const updatedGroup = await navigationApi.update(id, data)
      groups.value = groups.value.map(g => g.id === id ? updatedGroup : g)
      return updatedGroup
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update group'
      error.value = errorMessage
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteGroup(id: string): Promise<void> {
    try {
      loading.value = true
      error.value = null
      await navigationApi.delete(id)
      groups.value = groups.value.filter(g => g.id !== id)
      if (selectedGroupId.value === id) {
        selectedGroupId.value = null
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete group'
      error.value = errorMessage
      throw err
    } finally {
      loading.value = false
    }
  }

  function selectGroup(id: string | null): void {
    selectedGroupId.value = id
  }

  async function reorderGroups(orderedIds: string[]): Promise<void> {
    const items = orderedIds.map((id, index) => ({ id, sort_order: index }))
    try {
      const updated = await navigationApi.reorder(items)
      groups.value = groups.value.map(g => {
        const u = updated.find(x => x.id === g.id)
        return u ?? g
      })
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to reorder groups'
      error.value = errorMessage
      throw err
    }
  }

  return {
    groups,
    selectedGroupId,
    selectedGroup,
    activeGroups,
    loading,
    fetched,
    error,
    fetchGroups,
    createGroup,
    updateGroup,
    deleteGroup,
    selectGroup,
    reorderGroups
  }
})
