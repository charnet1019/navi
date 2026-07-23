import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { navigationApi } from '@/api/navigation'
import { buildNavigationTree } from '@/utils/navigationTree'
import { withLoading } from '@/utils/withLoading'
import type { NavigationGroup, CreateNavigationGroupRequest, UpdateNavigationGroupRequest } from '@/types'

export const useNavigationStore = defineStore('navigation', () => {
  const groups = ref<NavigationGroup[]>([])
  const selectedGroupId = ref<string | null>(localStorage.getItem('nav_selected_group'))
  const loading = ref(false)
  const fetched = ref(false)
  const error = ref<string | null>(null)
  const reordering = ref(false)

  const selectedGroup = computed(() =>
    groups.value.find(g => g.id === selectedGroupId.value) ?? null
  )

  const activeGroups = computed(() =>
    groups.value.filter(g => g.is_active).sort((a, b) => a.sort_order - b.sort_order)
  )

  const groupTree = computed(() =>
    buildNavigationTree(groups.value.filter(g => g.is_active))
  )

  const lastFetchKey = ref<string | null>(null)

  async function fetchGroups(params?: { skip?: number; limit?: number; is_active?: boolean }): Promise<void> {
    try {
      if (!fetched.value) loading.value = true
      error.value = null
      groups.value = await navigationApi.list(params)
      fetched.value = true
      lastFetchKey.value = JSON.stringify(params ?? {})
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch groups'
      error.value = errorMessage
      throw err
    } finally {
      loading.value = false
    }
  }

  async function ensureGroups(params?: { skip?: number; limit?: number; is_active?: boolean }): Promise<void> {
    const key = JSON.stringify(params ?? {})
    if (fetched.value && lastFetchKey.value === key) return
    await fetchGroups(params)
  }

  async function createGroup(data: CreateNavigationGroupRequest): Promise<NavigationGroup> {
    return withLoading(loading, error, 'Failed to create group', async () => {
      const newGroup = await navigationApi.create(data)
      groups.value = [...groups.value, newGroup]
      return newGroup
    })
  }

  async function updateGroup(id: string, data: UpdateNavigationGroupRequest): Promise<NavigationGroup> {
    return withLoading(loading, error, 'Failed to update group', async () => {
      const updatedGroup = await navigationApi.update(id, data)
      groups.value = groups.value.map(g => g.id === id ? updatedGroup : g)
      return updatedGroup
    })
  }

  async function deleteGroup(id: string): Promise<void> {
    await withLoading(loading, error, 'Failed to delete group', async () => {
      await navigationApi.delete(id)
      groups.value = groups.value.filter(g => g.id !== id)
      if (selectedGroupId.value === id) {
        selectedGroupId.value = null
        localStorage.removeItem('nav_selected_group')
      }
    })
  }

  function selectGroup(id: string | null): void {
    selectedGroupId.value = id
    if (id) {
      localStorage.setItem('nav_selected_group', id)
    } else {
      localStorage.removeItem('nav_selected_group')
    }
  }

  async function reorderGroups(orderedIds: string[]): Promise<void> {
    if (reordering.value) return
    const items = orderedIds.map((id, index) => ({ id, sort_order: index }))
    await withLoading(reordering, error, 'Failed to reorder groups', async () => {
      const updated = await navigationApi.reorder(items)
      const updatedMap = new Map(updated.map(group => [group.id, group]))
      groups.value = groups.value.map(group => updatedMap.get(group.id) ?? group)
    })
  }

  return {
    groups,
    selectedGroupId,
    selectedGroup,
    activeGroups,
    groupTree,
    loading,
    reordering,
    fetched,
    error,
    fetchGroups,
    ensureGroups,
    createGroup,
    updateGroup,
    deleteGroup,
    selectGroup,
    reorderGroups
  }
})
