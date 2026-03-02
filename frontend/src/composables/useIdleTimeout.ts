import { onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'

const IDLE_TIMEOUT = 30 * 60 * 1000 // 30 minutes in milliseconds
const EVENTS = ['mousedown', 'keydown', 'scroll', 'touchstart', 'click']

export function useIdleTimeout() {
  const authStore = useAuthStore()
  const router = useRouter()
  let timeoutId: number | null = null

  const resetTimer = () => {
    if (timeoutId) {
      clearTimeout(timeoutId)
    }

    timeoutId = window.setTimeout(async () => {
      message.warning('由于长时间未操作，您已被自动登出')
      await authStore.logout()
      router.push('/login')
    }, IDLE_TIMEOUT)
  }

  const setupListeners = () => {
    EVENTS.forEach(event => {
      document.addEventListener(event, resetTimer, true)
    })
    resetTimer()
  }

  const cleanupListeners = () => {
    EVENTS.forEach(event => {
      document.removeEventListener(event, resetTimer, true)
    })
    if (timeoutId) {
      clearTimeout(timeoutId)
    }
  }

  onMounted(() => {
    if (authStore.isAuthenticated) {
      setupListeners()
    }
  })

  onUnmounted(() => {
    cleanupListeners()
  })

  return {
    resetTimer,
    setupListeners,
    cleanupListeners
  }
}
