<template>
  <AppLayout>
    <div class="groups-view">
      <div class="header">
        <a-typography-title :level="2">用户组</a-typography-title>
        <a-button type="primary" @click="handleCreate">
          创建用户组
        </a-button>
      </div>

      <UserGroupTable
        :user-groups="userGroupsStore.userGroups"
        :loading="userGroupsStore.loading"
        @edit="handleEdit"
        @delete="handleDelete"
        @manage-members="handleManageMembers"
        @view-assets="handleViewAssets"
      />

      <UserGroupModal
        :open="modalOpen"
        :group="selectedGroup"
        :loading="userGroupsStore.loading"
        @submit="handleSubmit"
        @cancel="handleModalCancel"
      />

      <UserGroupMembersModal
        :open="membersModalOpen"
        :group="selectedGroup"
        :members="currentMembers"
        :all-users="usersStore.users"
        :loading="userGroupsStore.loading"
        @add-member="handleAddMember"
        @remove-member="handleRemoveMember"
        @cancel="handleMembersModalCancel"
      />

      <AuthorizedAssetsModal
        :open="assetsModalOpen"
        :target-name="assetsTargetName"
        :assets="authorizedAssets"
        :loading="assetsLoading"
        @cancel="assetsModalOpen = false"
        @revoke-nav-group="handleRevokeNavGroup"
        @revoke-link="handleRevokeLink"
      />
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { confirmAction } from '@/utils/confirm'
import AppLayout from '@/components/layout/AppLayout.vue'
import UserGroupTable from '@/components/user-groups/UserGroupTable.vue'
import UserGroupModal from '@/components/user-groups/UserGroupModal.vue'
import UserGroupMembersModal from '@/components/user-groups/UserGroupMembersModal.vue'
import AuthorizedAssetsModal from '@/components/admin/AuthorizedAssetsModal.vue'
import { useUserGroupsStore } from '@/stores/userGroups'
import { useUsersStore } from '@/stores/users'
import { userGroupsApi } from '@/api/userGroups'
import { authorizationApi } from '@/api/authorization'
import type { UserGroup, CreateUserGroupRequest, UpdateUserGroupRequest, AuthorizedAssets, NavGroupAsset, LinkAsset } from '@/types'

const userGroupsStore = useUserGroupsStore()
const usersStore = useUsersStore()

const modalOpen = ref(false)
const membersModalOpen = ref(false)
const selectedGroup = ref<UserGroup | null>(null)
const assetsModalOpen = ref(false)
const assetsTargetName = ref('')
const assetsTargetGroup = ref<UserGroup | null>(null)
const authorizedAssets = ref<AuthorizedAssets | null>(null)
const assetsLoading = ref(false)

const currentMembers = computed(() => {
  return userGroupsStore.currentGroup?.members || []
})

onMounted(async () => {
  try {
    await Promise.all([
      userGroupsStore.fetchUserGroups(),
      usersStore.fetchUsers({ limit: 100 })
    ])
  } catch (error) {
    message.error('加载数据失败')
  }
})

const handleCreate = () => {
  selectedGroup.value = null
  modalOpen.value = true
}

const handleEdit = (group: UserGroup) => {
  selectedGroup.value = group
  modalOpen.value = true
}

const handleSubmit = async (values: CreateUserGroupRequest | UpdateUserGroupRequest) => {
  try {
    if (selectedGroup.value) {
      await userGroupsStore.updateUserGroup(selectedGroup.value.id, values as UpdateUserGroupRequest)
      message.success('用户组更新成功')
    } else {
      await userGroupsStore.createUserGroup(values as CreateUserGroupRequest)
      message.success('用户组创建成功')
    }
    modalOpen.value = false
    selectedGroup.value = null
  } catch (error) {
    message.error(selectedGroup.value ? '更新用户组失败' : '创建用户组失败')
  }
}

const handleModalCancel = () => {
  modalOpen.value = false
  selectedGroup.value = null
}

const handleDelete = (group: UserGroup) => {
  confirmAction({
    title: '删除用户组',
    content: `确定要删除用户组"${group.name}"吗？此操作不可撤销。`,
    okText: '删除',
    danger: true,
    onOk: async () => {
      try {
        await userGroupsStore.deleteUserGroup(group.id)
        message.success('用户组已删除')
      } catch (error) {
        message.error('删除用户组失败')
      }
    }
  })
}

const handleManageMembers = async (group: UserGroup) => {
  try {
    selectedGroup.value = group
    await userGroupsStore.fetchUserGroupById(group.id)
    membersModalOpen.value = true
  } catch (error) {
    message.error('加载用户组成员失败')
  }
}

const handleAddMember = async (userId: string) => {
  if (!selectedGroup.value) return

  try {
    await userGroupsStore.addMember(selectedGroup.value.id, userId)
    message.success('成员添加成功')
  } catch (error) {
    message.error('添加成员失败')
  }
}

const handleRemoveMember = async (userId: string) => {
  if (!selectedGroup.value) return

  confirmAction({
    title: '移除成员',
    content: '确定要将该成员从用户组中移除吗？',
    okText: '移除',
    danger: true,
    onOk: async () => {
      try {
        await userGroupsStore.removeMember(selectedGroup.value!.id, userId)
        message.success('成员已移除')
      } catch (error) {
        message.error('移除成员失败')
      }
    }
  })
}

const handleMembersModalCancel = () => {
  membersModalOpen.value = false
  selectedGroup.value = null
}

const handleViewAssets = async (group: UserGroup) => {
  assetsTargetGroup.value = group
  assetsTargetName.value = group.name
  assetsModalOpen.value = true
  assetsLoading.value = true
  try {
    authorizedAssets.value = await userGroupsApi.getAuthorizedAssets(group.id)
  } catch (error) {
    message.error('加载已授权资产失败')
  } finally {
    assetsLoading.value = false
  }
}

const reloadAssets = async () => {
  if (!assetsTargetGroup.value) return
  assetsLoading.value = true
  try {
    authorizedAssets.value = await userGroupsApi.getAuthorizedAssets(assetsTargetGroup.value.id)
  } catch (error) {
    message.error('刷新已授权资产失败')
  } finally {
    assetsLoading.value = false
  }
}

const handleRevokeNavGroup = async (asset: NavGroupAsset) => {
  try {
    if (asset.navigation_group_id) {
      await authorizationApi.revokeNavGroupPermission(asset.navigation_group_id, asset.permission_id)
    } else {
      await authorizationApi.revokeAllNavGroupPermission(asset.permission_id)
    }
    message.success('权限已撤销')
    await reloadAssets()
  } catch (error) {
    message.error('撤销权限失败')
  }
}

const handleRevokeLink = async (asset: LinkAsset) => {
  try {
    await authorizationApi.revokeLinkPermission(asset.link_id, asset.permission_id)
    message.success('权限已撤销')
    await reloadAssets()
  } catch (error) {
    message.error('撤销权限失败')
  }
}
</script>

<style scoped>
.groups-view {
  padding: 24px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
</style>
