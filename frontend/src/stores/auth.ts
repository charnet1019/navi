import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import { withLoading } from '@/utils/withLoading'
import type { User, LoginRequest, ChangePasswordRequest } from '@/types'
import { AUTH_CLEARED_EVENT, clearClientAuthState } from '@/utils/authTokens'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const isAuthenticated = computed(() => !!user.value)
  const isSuperuser = computed(() => user.value?.is_superuser ?? false)

  if (typeof window !== 'undefined') {
    window.addEventListener(AUTH_CLEARED_EVENT, () => {
      user.value = null
    })
  }

  async function login(credentials: LoginRequest): Promise<void> {
    await withLoading(loading, error, 'Login failed', async () => {
      await authApi.login(credentials)
      await fetchCurrentUser()
    })
  }

  async function logout(): Promise<void> {
    try {
      await authApi.logout()
    } catch (err) {
      // Ignore errors during logout
    } finally {
      user.value = null
      clearClientAuthState()
    }
  }

  function clearSession(): void {
    user.value = null
    clearClientAuthState()
  }

  async function fetchCurrentUser(options: { skipAuthRefresh?: boolean } = {}): Promise<void> {
    try {
      loading.value = true
      error.value = null
      user.value = await authApi.getMe({ skipAuthRefresh: options.skipAuthRefresh })
    } catch (err: unknown) {
      user.value = null
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch user'
      error.value = errorMessage
      throw err
    } finally {
      loading.value = false
    }
  }

  async function changePassword(data: ChangePasswordRequest): Promise<void> {
    await withLoading(loading, error, 'Failed to change password', async () => {
      await authApi.changePassword(data)
    })
  }

  return {
    user,
    loading,
    error,
    isAuthenticated,
    isSuperuser,
    login,
    logout,
    clearSession,
    fetchCurrentUser,
    changePassword
  }
})
