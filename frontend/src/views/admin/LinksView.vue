<template>
  <AppLayout>
    <div class="admin-links-view">
      <div class="header">
        <a-typography-title :level="2">链接管理</a-typography-title>
        <a-button type="primary" @click="handleCreate">
          创建链接
        </a-button>
      </div>

      <div class="filters">
        <a-space>
          <a-select
            v-model:value="selectedGroupId"
            placeholder="按分组筛选"
            style="width: 200px"
            allow-clear
            @change="handleFilterChange"
          >
            <a-select-option
              v-for="group in navigationStore.groups"
              :key="group.id"
              :value="group.id"
            >
              {{ group.name }}
            </a-select-option>
          </a-select>

          <a-select
            v-model:value="selectedStatus"
            placeholder="按状态筛选"
            style="width: 150px"
            allow-clear
            @change="handleFilterChange"
          >
            <a-select-option :value="true">已启用</a-select-option>
            <a-select-option :value="false">已禁用</a-select-option>
          </a-select>
        </a-space>
      </div>

      <LinkTable
        :links="linksStore.links"
        :groups="navigationStore.groups"
        :loading="linksStore.loading"
        :total="linksStore.links.length"
        :current-page="currentPage"
        :page-size="pageSize"
        @edit="handleEdit"
        @delete="handleDelete"
        @page-change="handlePageChange"
      />

      <LinkModal
        :open="modalOpen"
        :link="selectedLink"
        :groups="navigationStore.groups"
        :groups-loading="navigationStore.loading"
        :loading="linksStore.loading"
        @submit="handleSubmit"
        @cancel="handleModalCancel"
      />
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { confirmAction } from '@/utils/confirm'
import AppLayout from '@/components/layout/AppLayout.vue'
import LinkTable from '@/components/admin/LinkTable.vue'
import LinkModal from '@/components/admin/LinkModal.vue'
import { useLinksStore } from '@/stores/links'
import { useNavigationStore } from '@/stores/navigation'
import type { Link, CreateLinkRequest, UpdateLinkRequest } from '@/types'

const linksStore = useLinksStore()
const navigationStore = useNavigationStore()

const modalOpen = ref(false)
const selectedLink = ref<Link | null>(null)
const selectedGroupId = ref<string | undefined>(undefined)
const selectedStatus = ref<boolean | undefined>(undefined)
const currentPage = ref(1)
const pageSize = ref(10)

onMounted(async () => {
  try {
    await Promise.all([
      handleFilterChange(),
      navigationStore.fetchGroups()
    ])
  } catch (error) {
    message.error('加载数据失败')
  }
})

const handleCreate = () => {
  selectedLink.value = null
  modalOpen.value = true
}

const handleEdit = (link: Link) => {
  selectedLink.value = link
  modalOpen.value = true
}

const handleSubmit = async (values: CreateLinkRequest | UpdateLinkRequest) => {
  try {
    if (selectedLink.value) {
      await linksStore.updateLink(selectedLink.value.id, values as UpdateLinkRequest)
      message.success('链接已更新')
    } else {
      await linksStore.createLink(values as CreateLinkRequest)
      message.success('链接已创建')
    }
    modalOpen.value = false
    selectedLink.value = null
    await handleFilterChange()
  } catch (error) {
    message.error(selectedLink.value ? '更新链接失败' : '创建链接失败')
  }
}

const handleModalCancel = () => {
  modalOpen.value = false
  selectedLink.value = null
}

const handleDelete = (link: Link) => {
  confirmAction({
    title: '删除链接',
    content: `确定要删除链接 "${link.name}" 吗？此操作不可撤销。`,
    okText: '删除',
    danger: true,
    onOk: async () => {
      try {
        await linksStore.deleteLink(link.id)
        message.success('链接已删除')
      } catch (error) {
        message.error('删除链接失败')
      }
    }
  })
}

const handleFilterChange = async () => {
  try {
    await linksStore.fetchLinks({
      navigation_group_id: selectedGroupId.value,
      is_active: selectedStatus.value
    })
  } catch (error) {
    message.error('加载链接失败')
  }
}

const handlePageChange = (page: number, size: number) => {
  currentPage.value = page
  pageSize.value = size
}
</script>

<style scoped>
.admin-links-view {
  padding: 24px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.filters {
  margin-bottom: 16px;
}
</style>
