import { defineStore } from 'pinia'
import { ref } from 'vue'
import { usersApi } from '@/api/users'
import type { User, CreateUserRequest, UpdateUserRequest, ResetPasswordRequest } from '@/types'

export const useUsersStore = defineStore('users', () => {
  const users = ref<User[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchUsers(params?: {
    skip?: number
    limit?: number
    is_active?: boolean
  }): Promise<void> {
    try {
      loading.value = true
      error.value = null
      users.value = await usersApi.list(params)
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch users'
      error.value = errorMessage
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createUser(data: CreateUserRequest): Promise<User> {
    try {
      loading.value = true
      error.value = null
      const newUser = await usersApi.create(data)
      users.value = [...users.value, newUser]
      return newUser
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create user'
      error.value = errorMessage
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateUser(id: string, data: UpdateUserRequest): Promise<User> {
    try {
      loading.value = true
      error.value = null
      const updatedUser = await usersApi.update(id, data)
      users.value = users.value.map(u => u.id === id ? updatedUser : u)
      return updatedUser
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update user'
      error.value = errorMessage
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteUser(id: string): Promise<void> {
    try {
      loading.value = true
      error.value = null
      await usersApi.delete(id)
      users.value = users.value.filter(u => u.id !== id)
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete user'
      error.value = errorMessage
      throw err
    } finally {
      loading.value = false
    }
  }

  async function resetPassword(id: string, data: ResetPasswordRequest): Promise<void> {
    try {
      loading.value = true
      error.value = null
      await usersApi.resetPassword(id, data)
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to reset password'
      error.value = errorMessage
      throw err
    } finally {
      loading.value = false
    }
  }

  async function disableUser(id: string): Promise<User> {
    try {
      loading.value = true
      error.value = null
      const updatedUser = await usersApi.disable(id)
      users.value = users.value.map(u => u.id === id ? updatedUser : u)
      return updatedUser
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to disable user'
      error.value = errorMessage
      throw err
    } finally {
      loading.value = false
    }
  }

  async function enableUser(id: string): Promise<User> {
    try {
      loading.value = true
      error.value = null
      const updatedUser = await usersApi.enable(id)
      users.value = users.value.map(u => u.id === id ? updatedUser : u)
      return updatedUser
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to enable user'
      error.value = errorMessage
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    users,
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
