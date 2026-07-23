<template>
  <AppLayout>
    <div class="nav-groups-view">
      <div class="header">
        <a-typography-title :level="2">导航分组</a-typography-title>
        <a-button type="primary" @click="handleCreate()">
          创建顶级分组
        </a-button>
      </div>

      <a-table
        :columns="columns"
        :data-source="treeData"
        :loading="navigationStore.loading"
        row-key="id"
        :default-expand-all-rows="false"
        :pagination="false"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'is_active'">
            <a-tag :color="record.is_active ? 'green' : 'red'">
              {{ record.is_active ? '已启用' : '已禁用' }}
            </a-tag>
          </template>
          <template v-if="column.key === 'actions'">
            <a-space>
              <a-button size="small" @click="handleAddChild(record)">添加子分组</a-button>
              <a-button size="small" @click="handleEdit(record)">编辑</a-button>
              <a-button size="small" danger @click="handleDelete(record)">删除</a-button>
            </a-space>
          </template>
        </template>
      </a-table>

      <a-modal
        v-model:open="modalOpen"
        :title="modalTitle"
        :footer="null"
        destroy-on-close
      >
        <NavigationGroupForm
          :initial-values="selectedGroup || undefined"
          :default-parent-id="defaultParentId"
          :groups="navigationStore.groups"
          :groups-loading="navigationStore.loading"
          :loading="navigationStore.loading"
          :submit-text="selectedGroup ? '更新' : '创建'"
          @submit="handleSubmit"
          @cancel="handleModalCancel"
        />
      </a-modal>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { confirmAction } from '@/utils/confirm'
import AppLayout from '@/components/layout/AppLayout.vue'
import NavigationGroupForm from '@/components/navigation/NavigationGroupForm.vue'
import { useNavigationStore } from '@/stores/navigation'
import { buildNavigationTree } from '@/utils/navigationTree'
import type { NavigationGroup, CreateNavigationGroupRequest, UpdateNavigationGroupRequest } from '@/types'

const navigationStore = useNavigationStore()

const modalOpen = ref(false)
const selectedGroup = ref<NavigationGroup | null>(null)
const defaultParentId = ref<string | null>(null)

const modalTitle = computed(() => {
  if (selectedGroup.value) return '编辑导航分组'
  if (defaultParentId.value) return '添加子分组'
  return '创建顶级分组'
})

const treeData = computed(() => buildNavigationTree(navigationStore.groups, { omitEmptyChildren: true }))

const columns = [
  { title: '名称', dataIndex: 'name', key: 'name' },
  { title: '描述', dataIndex: 'description', key: 'description' },
  { title: '操作', key: 'actions', width: 220 }
]

onMounted(async () => {
  try {
    await navigationStore.fetchGroups()
  } catch {
    message.error('加载导航分组失败')
  }
})

const handleCreate = () => {
  selectedGroup.value = null
  defaultParentId.value = null
  modalOpen.value = true
}

const handleAddChild = (parent: NavigationGroup) => {
  selectedGroup.value = null
  defaultParentId.value = parent.id
  modalOpen.value = true
}

const handleEdit = (group: NavigationGroup) => {
  selectedGroup.value = group
  defaultParentId.value = null
  modalOpen.value = true
}

const handleSubmit = async (values: CreateNavigationGroupRequest | UpdateNavigationGroupRequest) => {
  try {
    if (selectedGroup.value) {
      await navigationStore.updateGroup(selectedGroup.value.id, values as UpdateNavigationGroupRequest)
      message.success('导航分组已更新')
    } else {
      await navigationStore.createGroup(values as CreateNavigationGroupRequest)
      message.success('导航分组已创建')
    }
    modalOpen.value = false
    selectedGroup.value = null
    defaultParentId.value = null
  } catch {
    message.error(selectedGroup.value ? '更新失败' : '创建失败')
  }
}

const handleModalCancel = () => {
  modalOpen.value = false
  selectedGroup.value = null
  defaultParentId.value = null
}

const handleDelete = (group: NavigationGroup) => {
  confirmAction({
    title: '删除导航分组',
    content: `确定要删除"${group.name}"吗？该分组下的所有链接也将受到影响。`,
    okText: '删除',
    danger: true,
    onOk: async () => {
      try {
        await navigationStore.deleteGroup(group.id)
        message.success('导航分组已删除')
      } catch {
        message.error('删除导航分组失败')
      }
    }
  })
}
</script>

<style scoped>
.nav-groups-view {
  padding: 24px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
</style>
