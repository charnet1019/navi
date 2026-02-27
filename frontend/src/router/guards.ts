import type { NavigationGuardNext, RouteLocationNormalized } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

async function ensureUser(): Promise<boolean> {
  const authStore = useAuthStore()
  if (authStore.accessToken && !authStore.user) {
    try {
      await authStore.fetchCurrentUser()
    } catch {
      await authStore.logout()
      return false
    }
  }
  return authStore.isAuthenticated
}

export async function authGuard(
  to: RouteLocationNormalized,
  _from: RouteLocationNormalized,
  next: NavigationGuardNext
): Promise<void> {
  const authenticated = await ensureUser()

  if (!authenticated) {
    next({ name: 'login', query: { redirect: to.fullPath } })
  } else {
    next()
  }
}

export async function adminGuard(
  to: RouteLocationNormalized,
  _from: RouteLocationNormalized,
  next: NavigationGuardNext
): Promise<void> {
  const authenticated = await ensureUser()
  const authStore = useAuthStore()

  if (!authenticated) {
    next({ name: 'login', query: { redirect: to.fullPath } })
  } else if (!authStore.isSuperuser) {
    next({ name: 'home' })
  } else {
    next()
  }
}

export async function guestGuard(
  _to: RouteLocationNormalized,
  _from: RouteLocationNormalized,
  next: NavigationGuardNext
): Promise<void> {
  const authenticated = await ensureUser()

  if (authenticated) {
    next({ name: 'home' })
  } else {
    next()
  }
}
