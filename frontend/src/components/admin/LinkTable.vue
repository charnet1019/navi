<template>
  <div class="link-table">
    <a-table
      :columns="columns"
      :data-source="links"
      :loading="loading"
      :pagination="paginationConfig"
      :row-key="(record: Link) => record.id"
      @change="handleTableChange"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'is_active'">
          <a-tag :color="record.is_active ? 'green' : 'red'">
            {{ record.is_active ? '已启用' : '已禁用' }}
          </a-tag>
        </template>

        <template v-else-if="column.key === 'group'">
          {{ groupMap[record.navigation_group_id] || 'N/A' }}
        </template>

        <template v-else-if="column.key === 'url'">
          <a :href="record.url" target="_blank" rel="noopener noreferrer">
            {{ truncateUrl(record.url) }}
          </a>
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
import type { Link, NavigationGroup } from '@/types'

interface Props {
  links: Link[]
  groups?: NavigationGroup[]
  loading?: boolean
  total?: number
  currentPage?: number
  pageSize?: number
}

interface Emits {
  (e: 'edit', link: Link): void
  (e: 'delete', link: Link): void
  (e: 'pageChange', page: number, pageSize: number): void
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  total: 0,
  currentPage: 1,
  pageSize: 10,
  groups: () => []
})

const emit = defineEmits<Emits>()

const groupMap = computed(() => {
  const map: Record<string, string> = {}
  props.groups.forEach(g => { map[g.id] = g.name })
  return map
})

const columns: TableColumnType<Link>[] = [
  {
    title: 'ID',
    dataIndex: 'id',
    key: 'id',
    width: 80
  },
  {
    title: '名称',
    dataIndex: 'name',
    key: 'name'
  },
  {
    title: '链接地址',
    key: 'url',
    width: 200
  },
  {
    title: '分组',
    key: 'group',
    width: 150
  },
  {
    title: '排序',
    dataIndex: 'sort_order',
    key: 'sort_order',
    width: 80
  },
  {
    title: '状态',
    key: 'is_active',
    width: 100
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 180
  },
  {
    title: '操作',
    key: 'actions',
    width: 150
  }
]

const paginationConfig = computed(() => ({
  total: props.total,
  current: props.currentPage,
  pageSize: props.pageSize,
  showSizeChanger: true,
  showTotal: (total: number) => `共 ${total} 个链接`
}))

import { formatDateTime } from '@/utils/date'

const truncateUrl = (url: string): string => {
  return url.length > 40 ? url.substring(0, 37) + '...' : url
}

const handleEdit = (link: Link) => {
  emit('edit', link)
}

const handleDelete = (link: Link) => {
  emit('delete', link)
}

const handleTableChange: TableProps['onChange'] = (pagination) => {
  if (pagination.current && pagination.pageSize) {
    emit('pageChange', pagination.current, pagination.pageSize)
  }
}
</script>

<style scoped>
.link-table {
  width: 100%;
}
</style>
