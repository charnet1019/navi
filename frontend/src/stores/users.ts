import { defineStore } from 'pinia'
import { ref } from 'vue'
import { usersApi } from '@/api/users'
import { withLoading } from '@/utils/withLoading'
import type { User, CreateUserRequest, UpdateUserRequest, ResetPasswordRequest } from '@/types'

export const useUsersStore = defineStore('users', () => {
  const users = ref<User[]>([])
  const total = ref(0)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchUsers(params?: {
    skip?: number
    limit?: number
    is_active?: boolean
  }): Promise<void> {
    await withLoading(loading, error, 'Failed to fetch users', async () => {
      const result = await usersApi.list(params)
      users.value = result.users
      total.value = result.total
    })
  }

  async function createUser(data: CreateUserRequest): Promise<User> {
    return withLoading(loading, error, 'Failed to create user', async () => {
      const newUser = await usersApi.create(data)
      users.value = [...users.value, newUser]
      total.value += 1
      return newUser
    })
  }

  async function updateUser(id: string, data: UpdateUserRequest): Promise<User> {
    return withLoading(loading, error, 'Failed to update user', async () => {
      const updatedUser = await usersApi.update(id, data)
      users.value = users.value.map(u => u.id === id ? updatedUser : u)
      return updatedUser
    })
  }

  async function deleteUser(id: string): Promise<void> {
    await withLoading(loading, error, 'Failed to delete user', async () => {
      await usersApi.delete(id)
      users.value = users.value.filter(u => u.id !== id)
      total.value = Math.max(0, total.value - 1)
    })
  }

  async function resetPassword(id: string, data: ResetPasswordRequest): Promise<void> {
    await withLoading(loading, error, 'Failed to reset password', async () => {
      await usersApi.resetPassword(id, data)
    })
  }

  async function disableUser(id: string): Promise<User> {
    return withLoading(loading, error, 'Failed to disable user', async () => {
      const updatedUser = await usersApi.disable(id)
      users.value = users.value.map(u => u.id === id ? updatedUser : u)
      return updatedUser
    })
  }

  async function enableUser(id: string): Promise<User> {
    return withLoading(loading, error, 'Failed to enable user', async () => {
      const updatedUser = await usersApi.enable(id)
      users.value = users.value.map(u => u.id === id ? updatedUser : u)
      return updatedUser
    })
  }

  return {
    users,
    total,
    loading,
    error,
    fetchUsers,
    createUser,
    updateUser,
    deleteUser,
    resetPassword,
    disableUser,
    enableUser
  }
})
