import { defineStore } from 'pinia'
import { ref } from 'vue'
import { userGroupsApi } from '@/api/userGroups'
import type { UserGroup, UserGroupWithMembers, CreateUserGroupRequest, UpdateUserGroupRequest } from '@/types'

export const useUserGroupsStore = defineStore('userGroups', () => {
  // State
  const userGroups = ref<UserGroup[]>([])
  const currentGroup = ref<UserGroupWithMembers | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Actions
  async function fetchUserGroups(params?: {
    skip?: number
    limit?: number
  }): Promise<void> {
    try {
      loading.value = true
      error.value = null
      userGroups.value = await userGroupsApi.list(params)
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch user groups'
      error.value = errorMessage
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchUserGroupById(id: string): Promise<UserGroupWithMembers> {
    try {
      loading.value = true
      error.value = null
      const group = await userGroupsApi.getById(id)
      currentGroup.value = group
      return group
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch user group'
      error.value = errorMessage
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createUserGroup(data: CreateUserGroupRequest): Promise<UserGroup> {
    try {
      loading.value = true
      error.value = null
      const newGroup = await userGroupsApi.create(data)
      userGroups.value = [...userGroups.value, newGroup]
      return newGroup
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create user group'
      error.value = errorMessage
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateUserGroup(id: string, data: UpdateUserGroupRequest): Promise<UserGroup> {
    try {
      loading.value = true
      error.value = null
      const updatedGroup = await userGroupsApi.update(id, data)
      userGroups.value = userGroups.value.map(g => g.id === id ? updatedGroup : g)
      return updatedGroup
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update user group'
      error.value = errorMessage
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteUserGroup(id: string): Promise<void> {
    try {
      loading.value = true
      error.value = null
      await userGroupsApi.delete(id)
      userGroups.value = userGroups.value.filter(g => g.id !== id)
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete user group'
      error.value = errorMessage
      throw err
    } finally {
      loading.value = false
    }
  }

  async function addMember(groupId: string, userId: string): Promise<UserGroupWithMembers> {
    try {
      loading.value = true
      error.value = null
      const updatedGroup = await userGroupsApi.addMember(groupId, userId)
      currentGroup.value = updatedGroup
      return updatedGroup
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to add member'
      error.value = errorMessage
      throw err
    } finally {
      loading.value = false
    }
  }

  async function removeMember(groupId: string, userId: string): Promise<UserGroupWithMembers> {
    try {
      loading.value = true
      error.value = null
      const updatedGroup = await userGroupsApi.removeMember(groupId, userId)
      currentGroup.value = updatedGroup
      return updatedGroup
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to remove member'
      error.value = errorMessage
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    userGroups,
    currentGroup,
    loading,
    error,
    fetchUserGroups,
    fetchUserGroupById,
    createUserGroup,
    updateUserGroup,
    deleteUserGroup,
    addMember,
    removeMember
  }
})
