<template>
  <AppLayout>
    <div class="links-view">
      <div class="links-header">
        <a-typography-title :level="2">所有链接</a-typography-title>
        <a-space>
          <a-select
            v-model:value="selectedGroupFilter"
            placeholder="按分组筛选"
            style="width: 200px"
            allow-clear
          >
            <a-select-option
              v-for="group in navigationStore.groups"
              :key="group.id"
              :value="group.id"
            >
              {{ group.name }}
            </a-select-option>
          </a-select>
        </a-space>
      </div>

      <LinkGrid
        :links="filteredLinks"
        :loading="linksStore.loading"
        :columns="settingsStore.linksPerRow"
      />
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import AppLayout from '@/components/layout/AppLayout.vue'
import LinkGrid from '@/components/links/LinkGrid.vue'
import { useNavigationStore } from '@/stores/navigation'
import { useLinksStore } from '@/stores/links'
import { useSettingsStore } from '@/stores/settings'

const navigationStore = useNavigationStore()
const linksStore = useLinksStore()
const settingsStore = useSettingsStore()

const selectedGroupFilter = ref<string | undefined>(undefined)

const filteredLinks = computed(() => {
  if (!selectedGroupFilter.value) {
    return linksStore.activeLinks
  }
  return linksStore.links.filter(link =>
    link.navigation_group_id === selectedGroupFilter.value && link.is_active
  )
})

onMounted(async () => {
  try {
    await Promise.all([
      navigationStore.fetchGroups(),
      linksStore.fetchLinks({ is_active: true }),
      settingsStore.fetchPublicSettings()
    ])
  } catch (error) {
    message.error('加载数据失败')
  }
})
</script>

<style scoped>
.links-view {
  min-height: 100%;
}

.links-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 24px 0;
  margin-bottom: 0;
}
</style>
