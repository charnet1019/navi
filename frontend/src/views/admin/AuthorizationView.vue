<template>
  <AppLayout>
    <div class="authorization-view">
      <a-typography-title :level="2">权限管理</a-typography-title>

      <a-tree-select
        v-model:value="selectedGroupId"
        placeholder="请选择导航分组"
        style="width: 100%; max-width: 400px; margin-bottom: 24px"
        :tree-data="groupTreeOptions"
        :field-names="{ label: 'name', value: 'id', children: 'children' }"
        tree-default-expand-all
        allow-clear
        @change="handleGroupChange"
      />

      <template v-if="selectedGroupId">
        <a-card
          :title="selectedGroupId === ALL_PERMISSION_KEY ? '全部导航分组权限' : '导航分组权限'"
          style="margin-bottom: 24px"
        >
          <template #extra>
            <a-button type="primary" size="small" @click="openNavGroupGrant">
              授权
            </a-button>
          </template>
          <a-table
            :columns="permissionColumns"
            :data-source="navGroupPermissions"
            :loading="loadingNavPerms"
            :pagination="false"
            row-key="id"
            size="small"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'target'">
                {{ record.user_name || record.user_group_name }}
              </template>
              <template v-if="column.key === 'type'">
                <a-tag :color="record.user_id ? 'blue' : 'green'">
                  {{ record.user_id ? '用户' : '用户组' }}
                </a-tag>
              </template>
              <template v-if="column.key === 'granted_at'">
                {{ formatDateTime(record.granted_at) }}
              </template>
              <template v-if="column.key === 'action'">
                <a-popconfirm
                  title="确定要撤销此权限吗？"
                  @confirm="revokeNavGroupPerm(record.id)"
                >
                  <a-button type="link" danger size="small">撤销</a-button>
                </a-popconfirm>
              </template>
            </template>
          </a-table>
        </a-card>

        <a-card v-if="selectedGroupId !== ALL_PERMISSION_KEY" title="链接权限">
          <a-collapse
            v-if="groupLinks.length > 0"
            accordion
            @change="(key: string | string[]) => { const id = Array.isArray(key) ? key[0] : key; if (id) loadLinkPermissions(id) }"
          >
            <a-collapse-panel
              v-for="link in groupLinks"
              :key="link.id"
              :header="link.name"
            >
              <template #extra>
                <a-button
                  type="primary"
                  size="small"
                  @click.stop="openLinkGrant(link.id)"
                >
                  授权
                </a-button>
              </template>
              <a-table
                :columns="permissionColumns"
                :data-source="linkPermissionsMap[link.id] || []"
                :loading="loadingLinkPerms[link.id]"
                :pagination="false"
                row-key="id"
                size="small"
              >
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'target'">
                    {{ record.user_name || record.user_group_name }}
                  </template>
                  <template v-if="column.key === 'type'">
                    <a-tag :color="record.user_id ? 'blue' : 'green'">
                      {{ record.user_id ? '用户' : '用户组' }}
                    </a-tag>
                  </template>
                  <template v-if="column.key === 'granted_at'">
                    {{ formatDateTime(record.granted_at) }}
                  </template>
                  <template v-if="column.key === 'action'">
                    <a-popconfirm
                      title="确定要撤销此权限吗？"
                      @confirm="revokeLinkPerm(link.id, record.id)"
                    >
                      <a-button type="link" danger size="small">撤销</a-button>
                    </a-popconfirm>
                  </template>
                </template>
              </a-table>
            </a-collapse-panel>
          </a-collapse>
          <a-empty v-else description="该分组下暂无链接" />
        </a-card>
      </template>

      <a-empty v-else description="请选择一个导航分组来管理权限" />

      <PermissionGrantModal
        :open="grantModalOpen"
        :users="users"
        :user-groups="userGroups"
        :loading="granting"
        @submit="handleGrant"
        @cancel="grantModalOpen = false"
      />
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import AppLayout from '@/components/layout/AppLayout.vue'
import PermissionGrantModal from '@/components/admin/PermissionGrantModal.vue'
import { formatDateTime } from '@/utils/date'
import { navigationApi } from '@/api/navigation'
import { linksApi } from '@/api/links'
import { authorizationApi } from '@/api/authorization'
import { usersApi } from '@/api/users'
import { userGroupsApi } from '@/api/userGroups'
import type {
  NavigationGroup,
  Link,
  User,
  UserGroup,
  NavGroupPermission,
  LinkPermission,
  GrantPermissionRequest
} from '@/types'

const navGroups = ref<NavigationGroup[]>([])
const users = ref<User[]>([])
const userGroups = ref<UserGroup[]>([])
const selectedGroupId = ref<string | undefined>(undefined)
const groupLinks = ref<Link[]>([])
const navGroupPermissions = ref<NavGroupPermission[]>([])
const linkPermissionsMap = reactive<Record<string, LinkPermission[]>>({})
const loadingNavPerms = ref(false)
const loadingLinkPerms = reactive<Record<string, boolean>>({})
const granting = ref(false)
const grantModalOpen = ref(false)
const grantTarget = ref<{ type: 'nav_group' | 'link'; id: string }>({
  type: 'nav_group',
  id: ''
})

const ALL_PERMISSION_KEY = '__all__'

const groupTreeOptions = computed(() => {
  const map = new Map<string, NavigationGroup & { children?: NavigationGroup[] }>()
  const roots: (NavigationGroup & { children?: NavigationGroup[] })[] = []
  navGroups.value.forEach(g => map.set(g.id, { ...g, children: [] }))
  map.forEach(g => {
    if (g.parent_id && map.has(g.parent_id)) {
      map.get(g.parent_id)!.children!.push(g)
    } else {
      roots.push(g)
    }
  })
  // Remove empty children arrays so leaf nodes don't show expand icon
  function clean(nodes: (NavigationGroup & { children?: NavigationGroup[] })[]): NavigationGroup[] {
    return nodes.map(n => ({
      ...n,
      children: n.children?.length ? clean(n.children as (NavigationGroup & { children?: NavigationGroup[] })[]) : undefined
    }))
  }
  const tree = clean(roots).sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0))
  return [
    { id: ALL_PERMISSION_KEY, name: '全部（所有导航分组）' },
    ...tree
  ]
})

const permissionColumns = [
  { title: '名称', key: 'target', dataIndex: 'target' },
  { title: '类型', key: 'type', dataIndex: 'type', width: 120 },
  { title: '授权时间', dataIndex: 'granted_at', key: 'granted_at', width: 180 },
  { title: '', key: 'action', width: 100 }
]

onMounted(async () => {
  try {
    const [groups, allUsers, allGroups] = await Promise.all([
      navigationApi.list(),
      usersApi.list({ limit: 100 }),
      userGroupsApi.list({ limit: 100 })
    ])
    navGroups.value = groups
    users.value = allUsers
    userGroups.value = allGroups
  } catch {
    message.error('加载数据失败')
  }
})

const handleGroupChange = async (groupId: string) => {
  selectedGroupId.value = groupId
  loadingNavPerms.value = true
  try {
    if (groupId === ALL_PERMISSION_KEY) {
      navGroupPermissions.value = await authorizationApi.listAllNavGroupPermissions()
      groupLinks.value = []
    } else {
      const [perms, links] = await Promise.all([
        authorizationApi.listNavGroupPermissions(groupId),
        linksApi.listByGroup(groupId)
      ])
      navGroupPermissions.value = perms
      groupLinks.value = links
    }
  } catch {
    message.error('加载权限失败')
  } finally {
    loadingNavPerms.value = false
  }
}

const loadLinkPermissions = async (linkId: string) => {
  loadingLinkPerms[linkId] = true
  try {
    linkPermissionsMap[linkId] = await authorizationApi.listLinkPermissions(linkId)
  } catch {
    message.error('加载链接权限失败')
  } finally {
    loadingLinkPerms[linkId] = false
  }
}

const openNavGroupGrant = () => {
  if (!selectedGroupId.value) return
  grantTarget.value = { type: 'nav_group', id: selectedGroupId.value }
  grantModalOpen.value = true
}

const openLinkGrant = (linkId: string) => {
  grantTarget.value = { type: 'link', id: linkId }
  grantModalOpen.value = true
}

const handleGrant = async (data: GrantPermissionRequest) => {
  granting.value = true
  try {
    if (grantTarget.value.type === 'nav_group') {
      if (grantTarget.value.id === ALL_PERMISSION_KEY) {
        await authorizationApi.grantAllNavGroupPermission(data)
        navGroupPermissions.value = await authorizationApi.listAllNavGroupPermissions()
      } else {
        await authorizationApi.grantNavGroupPermission(grantTarget.value.id, data)
        navGroupPermissions.value = await authorizationApi.listNavGroupPermissions(
          grantTarget.value.id
        )
      }
    } else {
      await authorizationApi.grantLinkPermission(grantTarget.value.id, data)
      linkPermissionsMap[grantTarget.value.id] =
        await authorizationApi.listLinkPermissions(grantTarget.value.id)
    }
    grantModalOpen.value = false
    message.success('权限已授予')
  } catch {
    message.error('授权失败')
  } finally {
    granting.value = false
  }
}

const revokeNavGroupPerm = async (permissionId: string) => {
  if (!selectedGroupId.value) return
  try {
    if (selectedGroupId.value === ALL_PERMISSION_KEY) {
      await authorizationApi.revokeAllNavGroupPermission(permissionId)
    } else {
      await authorizationApi.revokeNavGroupPermission(selectedGroupId.value, permissionId)
    }
    navGroupPermissions.value = navGroupPermissions.value.filter(
      (p) => p.id !== permissionId
    )
    message.success('权限已撤销')
  } catch {
    message.error('撤销权限失败')
  }
}

const revokeLinkPerm = async (linkId: string, permissionId: string) => {
  try {
    await authorizationApi.revokeLinkPermission(linkId, permissionId)
    linkPermissionsMap[linkId] = (linkPermissionsMap[linkId] || []).filter(
      (p) => p.id !== permissionId
    )
    message.success('权限已撤销')
  } catch {
    message.error('撤销权限失败')
  }
}
</script>

<style scoped>
.authorization-view {
  padding: 24px;
}
</style>