<template>
  <a-layout-header class="app-header">
    <div class="header-content">
      <div class="logo">
        <h1>{{ settingsStore.siteTitle }}</h1>
      </div>
      <div class="header-actions">
        <a-dropdown>
          <a-button type="text">
            <UserOutlined />
            {{ authStore.user?.username }}
          </a-button>
          <template #overlay>
            <a-menu>
              <a-menu-item key="profile" @click="goToProfile">
                <UserOutlined />
                个人资料
              </a-menu-item>
              <a-menu-divider />
              <a-menu-item key="logout" @click="handleLogout">
                <LogoutOutlined />
                退出登录
              </a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
      </div>
    </div>
  </a-layout-header>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { UserOutlined, LogoutOutlined } from '@ant-design/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useSettingsStore } from '@/stores/settings'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'

const authStore = useAuthStore()
const settingsStore = useSettingsStore()
const router = useRouter()

onMounted(() => {
  if (!settingsStore.settings.length) {
    settingsStore.fetchPublicSettings()
  }
})

const goToProfile = () => {
  router.push({ name: 'profile' })
}

const handleLogout = async () => {
  try {
    await authStore.logout()
    message.success('已成功退出登录')
    router.push({ name: 'login' })
  } catch (error) {
    message.error('退出登录失败')
  }
}
</script>

<style scoped>
.app-header {
  background: #001529;
  padding: 0 24px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
}

.logo h1 {
  color: #fff;
  margin: 0;
  font-size: 20px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-actions .ant-btn {
  color: rgba(255, 255, 255, 0.85);
}

.header-actions .ant-btn:hover {
  color: #fff;
}
</style>
