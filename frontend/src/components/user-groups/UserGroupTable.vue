<template>
  <div class="user-group-table">
    <a-table
      :columns="columns"
      :data-source="userGroups"
      :loading="loading"
      :row-key="(record: UserGroup) => record.id"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'created_at'">
          {{ formatDateTime(record.created_at) }}
        </template>

        <template v-else-if="column.key === 'actions'">
          <a-space>
            <a-button
              type="link"
              size="small"
              @click="handleEdit(record)"
            >
              编辑
            </a-button>
            <a-button
              type="link"
              size="small"
              @click="handleManageMembers(record)"
            >
              管理成员
            </a-button>
            <a-button
              type="link"
              size="small"
              @click="handleViewAssets(record)"
            >
              已授权资产
            </a-button>
            <a-button
              type="link"
              size="small"
              danger
              @click="handleDelete(record)"
            >
              删除
            </a-button>
          </a-space>
        </template>
      </template>
    </a-table>
  </div>
</template>

<script setup lang="ts">
import type { TableColumnType } from 'ant-design-vue'
import type { UserGroup } from '@/types'

interface Props {
  userGroups: UserGroup[]
  loading?: boolean
}

interface Emits {
  (e: 'edit', group: UserGroup): void
  (e: 'delete', group: UserGroup): void
  (e: 'manageMembers', group: UserGroup): void
  (e: 'viewAssets', group: UserGroup): void
}

withDefaults(defineProps<Props>(), {
  loading: false
})

const emit = defineEmits<Emits>()

const columns: TableColumnType<UserGroup>[] = [
  {
    title: '名称',
    dataIndex: 'name',
    key: 'name'
  },
  {
    title: '描述',
    dataIndex: 'description',
    key: 'description'
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 180
  },
  {
    title: '操作',
    key: 'actions',
    width: 380
  }
]

import { formatDateTime } from '@/utils/date'

const handleEdit = (group: UserGroup) => {
  emit('edit', group)
}

const handleDelete = (group: UserGroup) => {
  emit('delete', group)
}

const handleManageMembers = (group: UserGroup) => {
  emit('manageMembers', group)
}

const handleViewAssets = (group: UserGroup) => {
  emit('viewAssets', group)
}
</script>

<style scoped>
.user-group-table {
  width: 100%;
}
</style>
