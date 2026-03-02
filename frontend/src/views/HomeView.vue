<template>
  <AppLayout>
    <div class="home-view">
      <div v-if="selectedGroup" class="group-content">
        <div class="group-toolbar">
          <a-button
            v-if="authStore.isSuperuser"
            type="primary"
            @click="showCreateModal = true"
          >
            <template #icon><PlusOutlined /></template>
            创建链接
          </a-button>
        </div>

        <LinkGrid
          :links="filteredLinks"
          :loading="linksStore.loading"
          :columns="settingsStore.linksPerRow"
          :editable="authStore.isSuperuser"
          :favorite-ids="favoritesStore.favoriteIds"
          @edit="handleEditLink"
          @delete="handleDeleteLink"
          @toggle-favorite="handleToggleFavorite"
          @reorder="handleReorderLinks"
        />
      </div>
      <div v-else class="favorites-section">
        <a-typography-title :level="4" style="padding: 8px 4px 0">
          收藏夹
        </a-typography-title>
        <LinkGrid
          :links="favoritesStore.favoriteLinks"
          :loading="favoritesStore.loading"
          :columns="settingsStore.linksPerRow"
          :favorite-ids="favoritesStore.favoriteIds"
          @toggle-favorite="handleToggleFavorite"
        />
      </div>

      <LinkModal
        :open="showCreateModal"
        :link="editingLink"
        :groups="navigationStore.groups"
        :loading="linksStore.loading"
        :default-group-id="selectedGroup?.id"
        @submit="handleLinkSubmit"
        @cancel="handleModalCancel"
      />
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import { message, Modal } from 'ant-design-vue'
import AppLayout from '@/components/layout/AppLayout.vue'
import LinkGrid from '@/components/links/LinkGrid.vue'
import LinkModal from '@/components/admin/LinkModal.vue'
import { useAuthStore } from '@/stores/auth'
import { useNavigationStore } from '@/stores/navigation'
import { useLinksStore } from '@/stores/links'
import { useSettingsStore } from '@/stores/settings'
import { useFavoritesStore } from '@/stores/favorites'
import type { Link, CreateLinkRequest, UpdateLinkRequest } from '@/types'

const authStore = useAuthStore()
const navigationStore = useNavigationStore()
const linksStore = useLinksStore()
const settingsStore = useSettingsStore()
const favoritesStore = useFavoritesStore()

const showCreateModal = ref(false)
const editingLink = ref<Link | null>(null)

const selectedGroup = computed(() => navigationStore.selectedGroup)

const filteredLinks = computed(() => {
  if (!selectedGroup.value) return []
  return linksStore.links
    .filter(link => link.navigation_group_id === selectedGroup.value?.id && link.is_active)
    .sort((a, b) => a.sort_order - b.sort_order)
})

onMounted(async () => {
  try {
    await Promise.all([
      linksStore.fetchLinks({ is_active: true }),
      settingsStore.fetchPublicSettings(),
      favoritesStore.fetchFavoriteIds(),
      favoritesStore.fetchFavoriteLinks()
    ])
  } catch (error) {
    message.error('加载数据失败')
  }
})

watch(() => navigationStore.selectedGroupId, async (newGroupId) => {
  try {
    if (newGroupId) {
      await linksStore.fetchLinks({ navigation_group_id: newGroupId, is_active: true })
    } else {
      await favoritesStore.fetchFavoriteLinks()
    }
  } catch (error) {
    message.error('加载链接失败')
  }
})

const handleLinkSubmit = async (values: CreateLinkRequest | UpdateLinkRequest) => {
  try {
    if (editingLink.value) {
      await linksStore.updateLink(editingLink.value.id, values as UpdateLinkRequest)
      message.success('链接已更新')
    } else {
      const data = {
        ...values,
        navigation_group_id: values.navigation_group_id || selectedGroup.value?.id
      } as CreateLinkRequest
      await linksStore.createLink(data)
      message.success('链接已创建')
    }
    showCreateModal.value = false
    editingLink.value = null
  } catch (error) {
    message.error('保存链接失败')
  }
}

const handleModalCancel = () => {
  showCreateModal.value = false
  editingLink.value = null
}

const handleEditLink = (link: Link) => {
  editingLink.value = link
  showCreateModal.value = true
}

const handleDeleteLink = (link: Link) => {
  Modal.confirm({
    title: '删除链接',
    content: `确定要删除"${link.name}"吗？`,
    okText: '删除',
    okType: 'danger',
    onOk: async () => {
      try {
        await linksStore.deleteLink(link.id)
        message.success('链接已删除')
      } catch {
        message.error('删除链接失败')
      }
    }
  })
}

const handleToggleFavorite = async (linkId: string) => {
  try {
    await favoritesStore.toggleFavorite(linkId)
    await favoritesStore.fetchFavoriteLinks()
  } catch {
    message.error('更新收藏失败')
  }
}

const handleReorderLinks = async (orderedIds: string[]) => {
  try {
    await linksStore.reorderLinks(orderedIds)
  } catch {
    message.error('排序失败')
  }
}
</script>

<style scoped>
.home-view {
  min-height: 100%;
}

.group-toolbar {
  display: flex;
  justify-content: flex-end;
  padding: 8px 4px 0;
}

.favorites-section {
  padding: 0;
}
</style>
