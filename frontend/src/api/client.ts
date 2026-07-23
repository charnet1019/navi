import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios'
import type { ApiError } from '@/types'
import { clearClientAuthState, getCsrfToken } from '@/utils/authTokens'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'
const CSRF_HEADER_NAME = import.meta.env.VITE_CSRF_HEADER_NAME || 'X-CSRF-Token'
const UNSAFE_METHODS = new Set(['post', 'put', 'patch', 'delete'])

export type AuthAwareRequestConfig = InternalAxiosRequestConfig & {
  _retry?: boolean
  _skipAuthRefresh?: boolean
}

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json'
  }
})

apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const method = (config.method || 'get').toLowerCase()
    const csrfToken = getCsrfToken()
    if (csrfToken && UNSAFE_METHODS.has(method) && config.headers) {
      config.headers[CSRF_HEADER_NAME] = csrfToken
    }
    return config
  },
  (error) => Promise.reject(error)
)

const AUTH_EXEMPT_PATHS = ['/auth/login', '/auth/refresh', '/auth/logout']

let isRefreshing = false
let failedQueue: Array<{
  resolve: () => void
  reject: (reason?: unknown) => void
}> = []

const redirectToLogin = async () => {
  clearClientAuthState()
  const { default: router } = await import('@/router')
  if (router.currentRoute.value.name !== 'login') {
    await router.replace({
      name: 'login',
      query: { redirect: router.currentRoute.value.fullPath }
    })
  }
}

const processQueue = (error: Error | null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve()
    }
  })
  failedQueue = []
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiError>) => {
    const originalRequest = error.config as AuthAwareRequestConfig | undefined
    const requestPath = originalRequest?.url || ''
    const isAuthExemptRequest = AUTH_EXEMPT_PATHS.some((path) => requestPath.includes(path))

    if (
      error.response?.status === 401
      && originalRequest
      && !originalRequest._retry
      && !originalRequest._skipAuthRefresh
      && !isAuthExemptRequest
    ) {
      if (isRefreshing) {
        return new Promise<void>((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then(() => apiClient(originalRequest))
          .catch((err) => Promise.reject(err))
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        await axios.post(`${API_BASE_URL}/auth/refresh`, undefined, {
          withCredentials: true,
          headers: {
            [CSRF_HEADER_NAME]: getCsrfToken() || ''
          }
        })

        processQueue(null)
        isRefreshing = false

        return apiClient(originalRequest)
      } catch (refreshError) {
        processQueue(refreshError as Error)
        isRefreshing = false
        await redirectToLogin()
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

export default apiClient
