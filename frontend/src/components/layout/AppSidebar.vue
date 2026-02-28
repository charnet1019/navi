<template>
  <a-layout-sider v-model:collapsed="collapsed" collapsible class="app-sidebar">
    <div class="sidebar-content">
      <a-menu
        v-model:selectedKeys="mainMenuKeys"
        mode="inline"
        theme="dark"
        @click="handleMainMenuClick"
      >
        <a-menu-item key="home">
          <HomeOutlined />
          <span>首页</span>
        </a-menu-item>
      </a-menu>

      <div class="navigation-groups-section">
        <NavigationGroupList
          :groups="navigationStore.groupTree"
          :selected-group-id="navigationStore.selectedGroupId"
          :loading="navigationStore.loading"
          :collapsed="collapsed"
          @select="handleGroupSelect"
        />
      </div>

      <a-divider v-if="authStore.isSuperuser" style="margin: 12px 0; border-color: rgba(255, 255, 255, 0.1)" />
      <a-menu
        v-if="authStore.isSuperuser"
        v-model:selectedKeys="adminMenuKeys"
        :open-keys="adminOpenKeys"
        mode="inline"
        theme="dark"
        @click="handleAdminMenuClick"
        @openChange="(keys: string[]) => adminOpenKeys = keys"
      >
        <a-sub-menu key="admin">
          <template #title>
            <SettingOutlined />
            <span>管理</span>
          </template>
          <a-menu-item key="admin-users">用户</a-menu-item>
          <a-menu-item key="admin-user-groups">用户组</a-menu-item>
          <a-menu-item key="admin-nav-groups">导航分组</a-menu-item>
          <a-menu-item key="admin-authorization">权限管理</a-menu-item>
          <a-menu-item key="admin-settings">系统设置</a-menu-item>
        </a-sub-menu>
      </a-menu>
    </div>
  </a-layout-sider>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { HomeOutlined, SettingOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { useAuthStore } from '@/stores/auth'
import { useNavigationStore } from '@/stores/navigation'
import NavigationGroupList from '@/components/navigation/NavigationGroupList.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const navigationStore = useNavigationStore()

const collapsed = ref(false)
const mainMenuKeys = ref<string[]>([])
const adminMenuKeys = ref<string[]>([])
const adminOpenKeys = ref<string[]>([])

function syncSelectionFromRoute(name: string) {
  const adminRoutes = ['admin-users', 'admin-user-groups', 'admin-nav-groups', 'admin-authorization', 'admin-settings']
  if (adminRoutes.includes(name)) {
    adminMenuKeys.value = [name]
    adminOpenKeys.value = ['admin']
    mainMenuKeys.value = []
    navigationStore.selectGroup(null)
  } else if (name === 'home' && (navigationStore.selectedGroupId || route.query.group)) {
    mainMenuKeys.value = []
    adminMenuKeys.value = []
  } else {
    mainMenuKeys.value = [name]
    adminMenuKeys.value = []
  }
}

syncSelectionFromRoute(route.name as string)

watch(() => route.name, (newName) => {
  if (newName) syncSelectionFromRoute(newName as string)
})

onMounted(async () => {
  try {
    await navigationStore.fetchGroups({ is_active: true })
    const groupId = route.query.group as string | undefined
    if (groupId) {
      navigationStore.selectGroup(groupId)
    }
  } catch (error) {
    message.error('加载导航分组失败')
  }
})

const handleMainMenuClick = ({ key }: { key: string }) => {
  adminMenuKeys.value = []
  navigationStore.selectGroup(null)
  router.push({ name: key })
}

const handleGroupSelect = (groupId: string) => {
  mainMenuKeys.value = []
  adminMenuKeys.value = []
  navigationStore.selectGroup(groupId)
  router.push({ name: 'home', query: { group: groupId } })
}

const handleAdminMenuClick = ({ key }: { key: string }) => {
  mainMenuKeys.value = []
  navigationStore.selectGroup(null)
  router.push({ name: key })
}


</script>

<style scoped>
.app-sidebar {
  height: 100%;
}

.app-sidebar :deep(.ant-layout-sider-trigger) {
  background: #001529;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-content {
  height: calc(100% - 48px);
  overflow-y: auto;
}

.navigation-groups-section {
  padding: 4px 0;
}
</style>
