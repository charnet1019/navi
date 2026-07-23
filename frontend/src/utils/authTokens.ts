export const AUTH_CLEARED_EVENT = 'auth:cleared'
const CSRF_COOKIE_NAME = import.meta.env.VITE_CSRF_COOKIE_NAME || 'navi_csrf_token'

export function getCookieValue(name: string): string | null {
  const cookie = document.cookie
    .split('; ')
    .find(item => item.startsWith(`${encodeURIComponent(name)}=`))

  return cookie ? decodeURIComponent(cookie.split('=').slice(1).join('=')) : null
}

export function getCsrfToken(): string | null {
  return getCookieValue(CSRF_COOKIE_NAME)
}

export function clearClientAuthState(): void {
  window.dispatchEvent(new Event(AUTH_CLEARED_EVENT))
}
