<template>
  <div class="user-table">
    <a-table
      :columns="columns"
      :data-source="users"
      :loading="loading"
      :pagination="paginationConfig"
      :row-key="(record) => record.id"
      @change="handleTableChange"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'is_active'">
          <a-tag :color="record.is_active ? 'green' : 'red'">
            {{ record.is_active ? '已激活' : '未激活' }}
          </a-tag>
        </template>

        <template v-else-if="column.key === 'is_superuser'">
          <a-tag :color="record.is_superuser ? 'blue' : 'default'">
            {{ record.is_superuser ? '超级管理员' : '普通用户' }}
          </a-tag>
        </template>

        <template v-else-if="column.key === 'user_groups'">
          <a-tag v-for="g in (record.user_groups || [])" :key="g.id" color="purple">
            {{ g.name }}
          </a-tag>
          <span v-if="!record.user_groups?.length" style="color: #999">-</span>
        </template>

        <template v-else-if="column.key === 'created_at'">
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
              @click="handleViewAssets(record)"
            >
              已授权资产
            </a-button>
            <a-button
              type="link"
              size="small"
              @click="handleResetPassword(record)"
            >
              重置密码
            </a-button>
            <a-button
              v-if="record.is_active"
              type="link"
              size="small"
              danger
              @click="handleDisable(record)"
            >
              禁用
            </a-button>
            <a-button
              v-else
              type="link"
              size="small"
              @click="handleEnable(record)"
            >
              启用
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
import { computed } from 'vue'
import type { TableProps, TableColumnType } from 'ant-design-vue'
import type { User } from '@/types'

interface Props {
  users: User[]
  loading?: boolean
  total?: number
  currentPage?: number
  pageSize?: number
}

interface Emits {
  (e: 'edit', user: User): void
  (e: 'delete', user: User): void
  (e: 'resetPassword', user: User): void
  (e: 'disable', user: User): void
  (e: 'enable', user: User): void
  (e: 'viewAssets', user: User): void
  (e: 'pageChange', page: number, pageSize: number): void
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  total: 0,
  currentPage: 1,
  pageSize: 10
})

const emit = defineEmits<Emits>()

const columns: TableColumnType<User>[] = [
  {
    title: '用户名',
    dataIndex: 'username',
    key: 'username'
  },
  {
    title: '邮箱',
    dataIndex: 'email',
    key: 'email'
  },
  {
    title: '姓名',
    dataIndex: 'full_name',
    key: 'full_name'
  },
  {
    title: '状态',
    key: 'is_active',
    width: 100
  },
  {
    title: '角色',
    key: 'is_superuser',
    width: 120
  },
  {
    title: '用户组',
    key: 'user_groups',
    width: 180
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 180
  },
  {
    title: '操作',
    key: 'actions',
    width: 420
  }
]

const paginationConfig = computed(() => ({
  total: props.total,
  current: props.currentPage,
  pageSize: props.pageSize,
  showSizeChanger: true,
  showTotal: (total: number) => `共 ${total} 个用户`
}))

import { formatDateTime } from '@/utils/date'

const handleEdit = (user: User) => {
  emit('edit', user)
}

const handleDelete = (user: User) => {
  emit('delete', user)
}

const handleResetPassword = (user: User) => {
  emit('resetPassword', user)
}

const handleDisable = (user: User) => {
  emit('disable', user)
}

const handleEnable = (user: User) => {
  emit('enable', user)
}

const handleViewAssets = (user: User) => {
  emit('viewAssets', user)
}

const handleTableChange: TableProps['onChange'] = (pagination) => {
  if (pagination.current && pagination.pageSize) {
    emit('pageChange', pagination.current, pagination.pageSize)
  }
}
</script>

<style scoped>
.user-table {
  width: 100%;
}
</style>
