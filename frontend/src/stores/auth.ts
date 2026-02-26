import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import type { User, LoginRequest, ChangePasswordRequest } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const accessToken = ref<string | null>(localStorage.getItem('access_token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refresh_token'))
  const loading = ref(false)
  const error = ref<string | null>(null)

  const isAuthenticated = computed(() => !!accessToken.value && !!user.value)
  const isSuperuser = computed(() => user.value?.is_superuser ?? false)

  async function login(credentials: LoginRequest): Promise<void> {
    try {
      loading.value = true
      error.value = null

      const response = await authApi.login(credentials)

      accessToken.value = response.access_token
      refreshToken.value = response.refresh_token

      localStorage.setItem('access_token', response.access_token)
      localStorage.setItem('refresh_token', response.refresh_token)

      await fetchCurrentUser()
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Login failed'
      error.value = errorMessage
      throw err
    } finally {
      loading.value = false
    }
  }

  async function logout(): Promise<void> {
    try {
      if (refreshToken.value) {
        await authApi.logout(refreshToken.value)
      }
    } catch (err) {
      // Ignore errors during logout
    } finally {
      user.value = null
      accessToken.value = null
      refreshToken.value = null
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    }
  }

  async function fetchCurrentUser(): Promise<void> {
    try {
      loading.value = true
      error.value = null
      user.value = await authApi.getMe()
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch user'
      error.value = errorMessage
      throw err
    } finally {
      loading.value = false
    }
  }

  async function changePassword(data: ChangePasswordRequest): Promise<void> {
    try {
      loading.value = true
      error.value = null
      await authApi.changePassword(data)
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to change password'
      error.value = errorMessage
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    user,
    accessToken,
    refreshToken,
    loading,
    error,
    isAuthenticated,
    isSuperuser,
    login,
    logout,
    fetchCurrentUser,
    changePassword
  }
})
