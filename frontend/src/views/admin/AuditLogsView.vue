<template>
  <AppLayout>
    <div class="audit-logs-view">
      <a-typography-title :level="2">审计日志</a-typography-title>

      <a-card style="margin-bottom: 16px">
        <a-form layout="inline" :model="filters" @finish="handleSearch">
          <a-form-item label="操作类型">
            <a-input
              v-model:value="filters.action"
              placeholder="例如 auth.login_failed"
              style="width: 200px"
              allow-clear
            />
          </a-form-item>
          <a-form-item label="资源类型">
            <a-input
              v-model:value="filters.resource_type"
              placeholder="例如 user"
              style="width: 160px"
              allow-clear
            />
          </a-form-item>
          <a-form-item label="时间范围">
            <a-range-picker
              v-model:value="dateRange"
              show-time
              style="width: 360px"
            />
          </a-form-item>
          <a-form-item>
            <a-space>
              <a-button type="primary" html-type="submit">查询</a-button>
              <a-button @click="handleReset">重置</a-button>
            </a-space>
          </a-form-item>
        </a-form>
      </a-card>

      <a-table
        :columns="columns"
        :data-source="auditLogsStore.logs"
        :loading="auditLogsStore.loading"
        :pagination="paginationConfig"
        :row-key="(record: AuditLog) => record.id"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'created_at'">
            {{ formatDateTime(record.created_at) }}
          </template>

          <template v-else-if="column.key === 'operator'">
            <a-tag v-if="!record.username" color="default">系统</a-tag>
            <span v-else>{{ record.username }}</span>
          </template>

          <template v-else-if="column.key === 'action'">
            <a-tooltip :title="record.action">
              <a-tag :color="actionMeta(record.action).color">{{ actionMeta(record.action).label }}</a-tag>
            </a-tooltip>
          </template>

          <template v-else-if="column.key === 'resource'">
            <span :title="resourceTitle(record)">{{ resourceLabel(record.resource_type) }}</span>
          </template>

          <template v-else-if="column.key === 'changes'">
            <div v-if="formatAuditDetails(record).length" class="changes-summary">
              <div v-for="line in formatAuditDetails(record)" :key="line" class="changes-line">
                {{ line }}
              </div>
            </div>
            <span v-else style="color: #999">-</span>
          </template>

          <template v-else-if="column.key === 'ip_address'">
            {{ record.ip_address || '-' }}
          </template>
        </template>
      </a-table>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import type { TableProps, TableColumnType } from 'ant-design-vue'
import type { Dayjs } from 'dayjs'
import AppLayout from '@/components/layout/AppLayout.vue'
import { useAuditLogsStore } from '@/stores/auditLogs'
import { formatDateTime } from '@/utils/date'
import type { AuditLog } from '@/types'

const auditLogsStore = useAuditLogsStore()

const currentPage = ref(1)
const pageSize = ref(20)

const filters = reactive({
  action: '',
  resource_type: ''
})
const dateRange = ref<[Dayjs, Dayjs] | undefined>()

const columns: TableColumnType<AuditLog>[] = [
  { title: '时间', key: 'created_at', width: 170 },
  { title: '操作人', key: 'operator', width: 120 },
  { title: '操作', key: 'action', width: 120 },
  { title: '资源', key: 'resource', width: 160 },
  { title: '详情', key: 'changes', width: 420 },
  { title: 'IP 地址', key: 'ip_address', width: 130 }
]

const ACTION_META: Record<string, { label: string; color: string }> = {
  create: { label: '创建', color: 'green' },
  'auth.login_success': { label: '登录', color: 'green' },
  'auth.login_failed': { label: '登录', color: 'red' },
  'auth.login_locked': { label: '登录', color: 'orange' },
  'auth.refresh': { label: '刷新', color: 'blue' },
  'auth.logout': { label: '登出', color: 'default' },
  'user.change_password': { label: '修改密码', color: 'blue' },
  'user.update': { label: '更新', color: 'blue' },
  'user.delete': { label: '删除', color: 'red' },
  'user.reset_password': { label: '重置密码', color: 'orange' },
  'user.disable': { label: '停用', color: 'red' },
  'user.enable': { label: '启用', color: 'green' },
  'user.unlock': { label: '解锁', color: 'orange' },
  'setting.update': { label: '修改', color: 'blue' },
  'role.create': { label: '创建', color: 'green' },
  'role.update': { label: '更新', color: 'blue' },
  'role.delete': { label: '删除', color: 'red' },
  'role.permission_assign': { label: '授权', color: 'green' },
  'role.permission_remove': { label: '取消授权', color: 'red' },
  'user_group.create': { label: '创建', color: 'green' },
  'user_group.update': { label: '更新', color: 'blue' },
  'user_group.delete': { label: '删除', color: 'red' },
  'user_group.member_add': { label: '添加成员', color: 'green' },
  'user_group.member_remove': { label: '移除成员', color: 'red' },
  'navigation_group.create': { label: '创建', color: 'green' },
  'navigation_group.update': { label: '更新', color: 'blue' },
  'navigation_group.delete': { label: '删除', color: 'red' },
  'navigation_group.reorder': { label: '排序', color: 'blue' },
  'navigation_group.sort_order_update': { label: '排序', color: 'blue' },
  'link.create': { label: '创建', color: 'green' },
  'link.update': { label: '更新', color: 'blue' },
  'link.delete': { label: '删除', color: 'red' },
  'link.reorder': { label: '排序', color: 'blue' },
  'link.sort_order_update': { label: '排序', color: 'blue' },
  'permission.grant': { label: '授权', color: 'green' },
  'permission.revoke': { label: '取消授权', color: 'red' },
  'upload.image_create': { label: '上传', color: 'green' },
  'upload.image_delete': { label: '删除', color: 'red' },
  'favorite.add': { label: '收藏', color: 'green' },
  'favorite.remove': { label: '取消收藏', color: 'red' },
  'favorite.reorder': { label: '排序', color: 'blue' },
  'audit_log.list': { label: '查看', color: 'blue' }
}

const RESOURCE_TYPE_LABELS: Record<string, string> = {
  user: '用户',
  role: '角色',
  user_group: '用户组',
  navigation_group: '导航分组',
  link: '链接',
  system_setting: '系统设置',
  upload: '图片',
  favorite: '收藏',
  audit_log: '审计日志',
  link_permissions: '链接权限',
  navigation_group_permissions: '目录权限'
}

const SETTING_LABELS: Record<string, string> = {
  site_title: '站点标题',
  login_title: '登录页标题',
  login_bg_image: '登录背景图',
  links_per_row: '每行链接数',
  copyright_info: '版权信息',
  icp_number: '备案号',
  icp_link: '备案链接',
  password_min_length: '密码最小长度',
  password_require_uppercase: '密码需包含大写字母',
  password_require_lowercase: '密码需包含小写字母',
  password_require_digit: '密码需包含数字',
  password_require_special: '密码需包含特殊字符',
  max_login_attempts: '最大登录失败次数',
  login_lockout_minutes: '锁定时长（分钟）',
  audit_log_retention_days: '审计日志保留时间（天）'
}

const CHANGE_FIELD_LABELS: Record<string, string> = {
  username: '用户名',
  name: '名称',
  description: '描述',
  url: '地址',
  icon_path: '图标',
  icon: '图标',
  sort_order: '排序',
  is_active: '启用状态',
  open_in_new_tab: '新窗口打开',
  navigation_group_id: '导航分组',
  parent_id: '上级分组',
  field: '字段',
  field_changes: '字段变更',
  fields: '修改字段',
  target_column: '目标字段',
  target_value: '目标值',
  user_id: '目标用户',
  user_group_id: '目标用户组',
  role_name: '角色',
  group_name: '用户组',
  link_name: '链接',
  filename: '文件名',
  size: '大小',
  content_type: '内容类型',
  key: '设置项',
  old_value: '旧值',
  new_value: '新值',
  remaining_minutes: '剩余分钟数',
  reason: '原因',
  attempt_count: '尝试次数',
  items: '排序项',
  permissions: '权限',
  permission: '权限',
  permission_id: '权限 ID',
  member_user_id: '成员用户 ID',
  member_username: '成员用户名',
  member_ids: '成员 ID',
  deleted_link_ids: '删除的链接 ID',
  old: '旧值',
  new: '新值'
}

const UPDATE_FIELD_LABELS: Record<string, string> = {
  email: '邮箱',
  full_name: '姓名',
  is_active: '启用状态',
  is_superuser: '管理员权限',
  user_group_ids: '所属用户组',
  name: '名称',
  description: '描述',
  url: '地址',
  icon_path: '图标',
  icon: '图标',
  sort_order: '排序',
  navigation_group_id: '导航分组',
  parent_id: '上级分组',
  open_in_new_tab: '新窗口打开'
}

const PERMISSION_RESOURCE_LABELS: Record<string, string> = {
  users: '用户',
  roles: '角色',
  permissions: '权限',
  navigation_groups: '导航分组',
  links: '链接',
  user_groups: '用户组',
  audit_logs: '审计日志',
  settings: '系统设置'
}

const PERMISSION_ACTION_LABELS: Record<string, string> = {
  read: '查看',
  create: '创建',
  update: '编辑',
  delete: '删除',
  manage: '管理'
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function truncateText(value: string, maxLength = 80): string {
  if (value.length <= maxLength) return value
  return `${value.slice(0, maxLength - 1)}…`
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined || value === '') return '无'
  if (typeof value === 'boolean') return value ? '是' : '否'
  if (typeof value === 'number') return Number.isFinite(value) ? String(value) : '无'
  if (typeof value === 'string') return truncateText(value)
  if (Array.isArray(value)) {
    if (!value.length) return '无'
    return value.map((item) => formatValue(item)).join('、')
  }
  if (isRecord(value)) {
    const entries = Object.entries(value)
    if (!entries.length) return '无'
    return entries.map(([key, item]) => `${CHANGE_FIELD_LABELS[key] || key}：${formatValue(item)}`).join('，')
  }
  return truncateText(String(value))
}

function resourceLabel(resourceType: string): string {
  return RESOURCE_TYPE_LABELS[resourceType] || resourceType
}

function resourceTitle(record: AuditLog): string {
  return record.resource_id ? `${resourceLabel(record.resource_type)} / ${record.resource_id}` : resourceLabel(record.resource_type)
}

function actionMeta(action: string): { label: string; color: string } {
  return ACTION_META[action] || { label: action, color: 'default' }
}

function firstString(changes: Record<string, unknown> | null, keys: string[]): string | null {
  if (!changes) return null
  for (const key of keys) {
    const value = changes[key]
    if (typeof value === 'string' && value.trim()) return value
    if (isRecord(value)) {
      const nested = firstString(value, keys)
      if (nested) return nested
    }
  }
  return null
}

type FieldChange = {
  field: string
  old_value: unknown
  new_value: unknown
}

function isFieldChange(value: unknown): value is FieldChange {
  return isRecord(value) && typeof value.field === 'string'
}

function formatFieldChanges(value: unknown): string[] {
  if (!Array.isArray(value) || !value.length) return []
  return value
    .filter(isFieldChange)
    .map((item) => {
      const label = UPDATE_FIELD_LABELS[item.field] || item.field
      return `${label}：${formatValue(item.old_value)} -> ${formatValue(item.new_value)}`
    })
}

function formatFieldList(fields: unknown): string {
  if (!Array.isArray(fields) || !fields.length) return '无'
  return fields.map((field) => UPDATE_FIELD_LABELS[String(field)] || String(field)).join('、')
}

function formatPermissionCode(permission: string): string {
  const [resourcePart, actionPart] = permission.split(':')
  const resource = PERMISSION_RESOURCE_LABELS[resourcePart] || resourcePart
  const action = PERMISSION_ACTION_LABELS[actionPart] || actionPart
  return `${resource}·${action}`
}

function formatPermissionList(value: unknown): string {
  if (!Array.isArray(value) || !value.length) return '无'
  const labels = value.filter((item): item is string => typeof item === 'string').map(formatPermissionCode)
  if (!labels.length) return '无'
  if (labels.length <= 3) return labels.join('、')
  return `${labels.slice(0, 3).join('、')} 等 ${labels.length} 项`
}

function formatOldNewLines(bucket: unknown, prefix: string): string[] {
  if (!isRecord(bucket)) return []
  const entries = Object.entries(bucket)
  if (!entries.length) return [`${prefix}：无`]
  return entries.map(([key, value]) => `${prefix}${UPDATE_FIELD_LABELS[key] || key}：${formatValue(value)}`)
}

function formatReorderItems(value: unknown, itemLabel: string): string[] {
  if (!Array.isArray(value) || !value.length) return []
  return value.map((item, index) => {
    if (!isRecord(item)) return `${itemLabel}${index + 1}：排序已调整`
    const name = typeof item.name === 'string' && item.name.trim() ? item.name : `${itemLabel}${index + 1}`
    return `${name}：排序 ${formatValue(item.old_sort_order)} -> ${formatValue(item.new_sort_order)}`
  })
}

function formatPermissionSubject(changes: Record<string, unknown>): string {
  if (typeof changes.user_group_name === 'string' && changes.user_group_name.trim()) return `用户组 ${changes.user_group_name}`
  if (typeof changes.user_name === 'string' && changes.user_name.trim()) return `用户 ${changes.user_name}`
  return changes.user_group_id ? '用户组' : '用户'
}

function formatPermissionTarget(record: AuditLog, changes: Record<string, unknown>): string {
  const fallback = record.resource_type === 'link_permissions' ? '链接' : '导航分组'
  if (typeof changes.target_name !== 'string' || !changes.target_name.trim()) return fallback
  if (changes.target_name === '全部导航分组') return '全部导航分组'
  return `${fallback} ${changes.target_name}`
}

function formatGenericChanges(changes: Record<string, unknown> | null): string[] {
  if (!changes) return []
  const lines: string[] = []
  for (const [key, value] of Object.entries(changes)) {
    const label = CHANGE_FIELD_LABELS[key] || key
    if (key === 'field_changes') {
      lines.push(...formatFieldChanges(value))
      continue
    }
    if (key === 'fields') {
      lines.push(`${label}：${formatFieldList(value)}`)
      continue
    }
    if (key === 'permissions') {
      lines.push(`${label}：${formatPermissionList(value)}`)
      continue
    }
    if (key === 'items' && Array.isArray(value)) {
      lines.push(...formatReorderItems(value, label))
      continue
    }
    if (key === 'old') {
      lines.push(...formatOldNewLines(value, '旧'))
      continue
    }
    if (key === 'new') {
      lines.push(...formatOldNewLines(value, '新'))
      continue
    }
    lines.push(`${label}：${formatValue(value)}`)
  }
  return lines
}

function describeAuditLog(record: AuditLog): string[] {
  const changes = record.changes ?? {}
  const entityName = firstString(changes, ['username', 'name', 'role_name', 'group_name', 'link_name', 'filename'])
  const settingKey = typeof changes.key === 'string' ? changes.key : null

  switch (record.action) {
    case 'auth.login_success':
      return ['登录成功']
    case 'auth.login_failed': {
      const reasonMap: Record<string, string> = {
        invalid_credentials: '用户名或密码错误',
        lockout_after_failure: '登录失败次数过多',
        inactive_user: '用户已停用'
      }
      const reason = typeof changes.reason === 'string' ? reasonMap[changes.reason] || changes.reason : null
      const attemptText = typeof changes.attempt_count === 'number' ? `，尝试次数：${changes.attempt_count}` : ''
      return [`登录失败${reason ? `：${reason}` : ''}${attemptText}`]
    }
    case 'auth.login_locked':
      return [`登录失败次数过多，${formatValue(changes.remaining_minutes)} 分钟后可重试`]
    case 'auth.logout':
      return ['登出成功']
    case 'auth.refresh':
      return ['刷新成功']
    case 'user.change_password':
      return ['修改密码成功']
    case 'create':
      return [entityName ? `创建用户${entityName}成功` : '创建用户成功']
    case 'user.update':
      return [entityName ? `更新用户${entityName}信息` : '更新用户信息', ...formatFieldChanges(changes.field_changes)]
    case 'user.delete':
      return [entityName ? `删除用户${entityName}成功` : '删除用户成功']
    case 'user.reset_password':
      return [entityName ? `重置用户${entityName}密码成功` : '重置用户密码成功']
    case 'user.disable':
      return [entityName ? `停用用户${entityName}成功` : '停用用户成功']
    case 'user.enable':
      return [entityName ? `启用用户${entityName}成功` : '启用用户成功']
    case 'user.unlock':
      return [entityName ? `解锁用户${entityName}成功` : '解锁用户成功']
    case 'setting.update':
      return [
        `修改设置：${settingKey ? (SETTING_LABELS[settingKey] || settingKey) : '系统设置'}`,
        ...formatFieldChanges(changes.field_changes)
      ]
    case 'role.create':
      return [entityName ? `创建角色：${entityName}` : '创建角色成功']
    case 'role.update':
      return [entityName ? `更新角色${entityName}信息` : '更新角色信息', ...formatFieldChanges(changes.field_changes)]
    case 'role.delete':
      return [entityName ? `删除角色：${entityName}` : '删除角色成功']
    case 'role.permission_assign': {
      const count = Array.isArray(changes.permissions) ? changes.permissions.length : 0
      return [
        `为角色${changes.role_name ? ` ${changes.role_name}` : ''}授予权限`,
        count ? `权限：${formatPermissionList(changes.permissions)}` : '权限：无'
      ]
    }
    case 'role.permission_remove':
      return [
        `从角色${changes.role_name ? ` ${changes.role_name}` : ''}移除权限`,
        changes.permission ? `权限：${formatPermissionCode(String(changes.permission))}` : '权限：无'
      ]
    case 'user_group.create':
      return [entityName ? `创建用户组：${entityName}` : '创建用户组成功']
    case 'user_group.update':
      return [entityName ? `更新用户组${entityName}信息` : '更新用户组信息', ...formatFieldChanges(changes.field_changes)]
    case 'user_group.delete':
      return [entityName ? `删除用户组：${entityName}` : '删除用户组成功']
    case 'user_group.member_add':
      return [
        `将用户${changes.member_username ? ` ${changes.member_username}` : ''}加入用户组${changes.group_name ? ` ${changes.group_name}` : ''}`
      ]
    case 'user_group.member_remove':
      return [
        `从用户组${changes.group_name ? ` ${changes.group_name}` : ''}移除用户${changes.member_username ? ` ${changes.member_username}` : ''}`
      ]
    case 'navigation_group.create':
      return [entityName ? `创建导航分组：${entityName}` : '创建导航分组成功']
    case 'navigation_group.update':
      return [entityName ? `更新导航分组${entityName}信息` : '更新导航分组信息', ...formatFieldChanges(changes.field_changes)]
    case 'navigation_group.delete':
      return [entityName ? `删除导航分组：${entityName}` : '删除导航分组成功']
    case 'navigation_group.reorder':
      return [
        `调整导航分组排序${Array.isArray(changes.items) ? `（${changes.items.length} 项）` : ''}`,
        ...formatReorderItems(changes.items, '导航分组')
      ]
    case 'navigation_group.sort_order_update':
      return [entityName ? `调整导航分组 ${entityName} 排序` : '调整导航分组排序', ...formatFieldChanges(changes.field_changes)]
    case 'link.create':
      return [entityName ? `创建链接：${entityName}` : '创建链接成功']
    case 'link.update':
      return [entityName ? `更新链接${entityName}信息` : '更新链接信息', ...formatFieldChanges(changes.field_changes)]
    case 'link.delete':
      return [entityName ? `删除链接：${entityName}` : '删除链接成功']
    case 'link.reorder':
      return [
        `调整链接排序${Array.isArray(changes.items) ? `（${changes.items.length} 项）` : ''}`,
        ...formatReorderItems(changes.items, '链接')
      ]
    case 'link.sort_order_update':
      return [entityName ? `调整链接 ${entityName} 排序` : '调整链接排序', ...formatFieldChanges(changes.field_changes)]
    case 'permission.grant': {
      const subject = formatPermissionSubject(changes)
      const target = formatPermissionTarget(record, changes)
      return [`为${subject}授予${target}访问权限`]
    }
    case 'permission.revoke': {
      const subject = formatPermissionSubject(changes)
      const target = formatPermissionTarget(record, changes)
      return [`为${subject}取消${target}访问权限`]
    }
    case 'upload.image_create':
      return [
        entityName ? `上传图片：${entityName}` : '上传图片成功',
        changes.size ? `大小：${formatSize(changes.size)}` : '大小：未知'
      ]
    case 'upload.image_delete':
      return [entityName ? `删除图片：${entityName}` : '删除图片成功']
    case 'favorite.add':
      return [entityName ? `添加收藏：${entityName}` : '添加收藏成功']
    case 'favorite.remove':
      return [entityName ? `取消收藏：${entityName}` : '取消收藏成功']
    case 'favorite.reorder':
      return [`调整收藏排序${Array.isArray(changes.items) ? `（${changes.items.length} 项）` : ''}`]
    default:
      return formatGenericChanges(record.changes)
  }
}

function formatSize(value: unknown): string {
  const raw = Number(value)
  if (!Number.isFinite(raw) || raw < 0) return formatValue(value)
  const units = ['B', 'KB', 'MB', 'GB']
  let size = raw
  let unitIndex = 0
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex += 1
  }
  const precision = unitIndex === 0 || size >= 10 ? 0 : 1
  return `${size.toFixed(precision)} ${units[unitIndex]}`
}

function formatAuditDetails(record: AuditLog): string[] {
  return describeAuditLog(record).filter((line) => line && line !== '无')
}

const paginationConfig = computed(() => ({
  total: auditLogsStore.total,
  current: currentPage.value,
  pageSize: pageSize.value,
  showSizeChanger: true,
  showTotal: (total: number) => `共 ${total} 条记录`
}))

async function loadLogs() {
  try {
    await auditLogsStore.fetchLogs({
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value,
      action: filters.action || undefined,
      resource_type: filters.resource_type || undefined,
      start_time: dateRange.value?.[0]?.toISOString(),
      end_time: dateRange.value?.[1]?.toISOString()
    })
  } catch {
    message.error('加载审计日志失败')
  }
}

onMounted(loadLogs)

const handleSearch = () => {
  currentPage.value = 1
  loadLogs()
}

const handleReset = () => {
  filters.action = ''
  filters.resource_type = ''
  dateRange.value = undefined
  currentPage.value = 1
  loadLogs()
}

const handleTableChange: TableProps['onChange'] = (pagination) => {
  if (pagination.current && pagination.pageSize) {
    currentPage.value = pagination.current
    pageSize.value = pagination.pageSize
    loadLogs()
  }
}
</script>

<style scoped>
.audit-logs-view {
  padding: 24px;
}

.changes-summary {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.changes-line {
  line-height: 1.5;
}
</style>
