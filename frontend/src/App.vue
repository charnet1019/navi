<template>
  <router-view />
</template>

<script setup lang="ts">
import { watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useIdleTimeout } from '@/composables/useIdleTimeout'

const authStore = useAuthStore()
const { setupListeners, cleanupListeners } = useIdleTimeout()

// Watch auth state to setup/cleanup idle timeout
watch(() => authStore.isAuthenticated, (isAuth) => {
  if (isAuth) {
    setupListeners()
  } else {
    cleanupListeners()
  }
}, { immediate: true })
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
    'Noto Sans', sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol',
    'Noto Color Emoji';
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
</style>
