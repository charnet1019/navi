import { defineStore } from 'pinia'
import { ref } from 'vue'
import { userGroupsApi } from '@/api/userGroups'
import { withLoading } from '@/utils/withLoading'
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
    userGroups.value = await withLoading(loading, error, 'Failed to fetch user groups', () => userGroupsApi.list(params))
  }

  async function fetchUserGroupById(id: string): Promise<UserGroupWithMembers> {
    const group = await withLoading(loading, error, 'Failed to fetch user group', () => userGroupsApi.getById(id))
    currentGroup.value = group
    return group
  }

  async function createUserGroup(data: CreateUserGroupRequest): Promise<UserGroup> {
    const newGroup = await withLoading(loading, error, 'Failed to create user group', () => userGroupsApi.create(data))
    userGroups.value = [...userGroups.value, newGroup]
    return newGroup
  }

  async function updateUserGroup(id: string, data: UpdateUserGroupRequest): Promise<UserGroup> {
    const updatedGroup = await withLoading(loading, error, 'Failed to update user group', () => userGroupsApi.update(id, data))
    userGroups.value = userGroups.value.map(g => g.id === id ? updatedGroup : g)
    return updatedGroup
  }

  async function deleteUserGroup(id: string): Promise<void> {
    await withLoading(loading, error, 'Failed to delete user group', () => userGroupsApi.delete(id))
    userGroups.value = userGroups.value.filter(g => g.id !== id)
  }

  async function addMember(groupId: string, userId: string): Promise<UserGroupWithMembers> {
    const updatedGroup = await withLoading(loading, error, 'Failed to add member', () => userGroupsApi.addMember(groupId, userId))
    currentGroup.value = updatedGroup
    return updatedGroup
  }

  async function removeMember(groupId: string, userId: string): Promise<UserGroupWithMembers> {
    const updatedGroup = await withLoading(loading, error, 'Failed to remove member', () => userGroupsApi.removeMember(groupId, userId))
    currentGroup.value = updatedGroup
    return updatedGroup
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
