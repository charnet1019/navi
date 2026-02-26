<template>
  <a-modal
    :open="open"
    :title="`已授权资产 - ${targetName}`"
    :footer="null"
    width="700px"
    @cancel="$emit('cancel')"
  >
    <a-spin :spinning="loading">
      <a-typography-title :level="5" style="margin-top: 0">导航分组权限</a-typography-title>
      <a-table
        :columns="navGroupColumns"
        :data-source="assets?.nav_group_permissions || []"
        :pagination="false"
        row-key="permission_id"
        size="small"
        style="margin-bottom: 24px"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'granted_at'">
            {{ formatDateTime(record.granted_at) }}
          </template>
          <template v-if="column.key === 'action'">
            <a-popconfirm
              title="确定要撤销此权限吗？"
              @confirm="handleRevokeNavGroup(record)"
            >
              <a-button type="link" danger size="small">撤销</a-button>
            </a-popconfirm>
          </template>
        </template>
        <template #emptyText>
          <a-empty description="暂无导航分组权限" :image="simpleImage" />
        </template>
      </a-table>

      <a-typography-title :level="5">链接权限</a-typography-title>
      <a-table
        :columns="linkColumns"
        :data-source="assets?.link_permissions || []"
        :pagination="false"
        row-key="permission_id"
        size="small"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'granted_at'">
            {{ formatDateTime(record.granted_at) }}
          </template>
          <template v-if="column.key === 'action'">
            <a-popconfirm
              title="确定要撤销此权限吗？"
              @confirm="handleRevokeLink(record)"
            >
              <a-button type="link" danger size="small">撤销</a-button>
            </a-popconfirm>
          </template>
        </template>
        <template #emptyText>
          <a-empty description="暂无链接权限" :image="simpleImage" />
        </template>
      </a-table>
    </a-spin>
  </a-modal>
</template>

<script setup lang="ts">
import { Empty } from 'ant-design-vue'
import type { AuthorizedAssets, NavGroupAsset, LinkAsset } from '@/types'

const simpleImage = Empty.PRESENTED_IMAGE_SIMPLE

interface Props {
  open: boolean
  targetName: string
  assets: AuthorizedAssets | null
  loading?: boolean
}

interface Emits {
  (e: 'cancel'): void
  (e: 'revokeNavGroup', asset: NavGroupAsset): void
  (e: 'revokeLink', asset: LinkAsset): void
}

withDefaults(defineProps<Props>(), {
  loading: false
})

const emit = defineEmits<Emits>()

const navGroupColumns = [
  { title: '导航分组', dataIndex: 'navigation_group_name', key: 'name' },
  { title: '授权时间', key: 'granted_at', width: 180 },
  { title: '', key: 'action', width: 80 }
]

const linkColumns = [
  { title: '链接名称', dataIndex: 'link_name', key: 'name' },
  { title: '所属分组', dataIndex: 'navigation_group_name', key: 'group' },
  { title: '授权时间', key: 'granted_at', width: 180 },
  { title: '', key: 'action', width: 80 }
]

import { formatDateTime } from '@/utils/date'

const handleRevokeNavGroup = (asset: NavGroupAsset) => {
  emit('revokeNavGroup', asset)
}

const handleRevokeLink = (asset: LinkAsset) => {
  emit('revokeLink', asset)
}
</script>
