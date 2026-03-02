<template>
  <AppLayout>
    <div class="users-view">
      <div class="header">
        <a-typography-title :level="2">用户</a-typography-title>
        <a-button type="primary" @click="handleCreate">
          创建用户
        </a-button>
      </div>

      <UserTable
        :users="usersStore.users"
        :loading="usersStore.loading"
        @edit="handleEdit"
        @delete="handleDelete"
        @reset-password="handleResetPassword"
        @disable="handleDisable"
        @enable="handleEnable"
        @view-assets="handleViewAssets"
        @unlock="handleUnlock"
      />

      <UserModal
        :open="modalOpen"
        :user="selectedUser"
        :user-groups="userGroupsStore.userGroups"
        :loading="usersStore.loading"
        @submit="handleSubmit"
        @cancel="handleModalCancel"
      />

      <a-modal
        v-model:open="resetPasswordModalOpen"
        title="重置密码"
        @ok="handleResetPasswordSubmit"
        @cancel="resetPasswordModalOpen = false"
      >
        <a-form layout="vertical">
          <a-form-item label="新密码" required>
            <a-input-password
              v-model:value="newPassword"
              placeholder="请输入新密码"
            />
          </a-form-item>
        </a-form>
      </a-modal>

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
import { ref, onMounted } from 'vue'
import { Modal, message } from 'ant-design-vue'
import AppLayout from '@/components/layout/AppLayout.vue'
import UserTable from '@/components/users/UserTable.vue'
import UserModal from '@/components/users/UserModal.vue'
import AuthorizedAssetsModal from '@/components/admin/AuthorizedAssetsModal.vue'
import { useUsersStore } from '@/stores/users'
import { useUserGroupsStore } from '@/stores/userGroups'
import { usersApi } from '@/api/users'
import { authorizationApi } from '@/api/authorization'
import type { User, CreateUserRequest, UpdateUserRequest, AuthorizedAssets, NavGroupAsset, LinkAsset } from '@/types'

const usersStore = useUsersStore()
const userGroupsStore = useUserGroupsStore()

const modalOpen = ref(false)
const selectedUser = ref<User | null>(null)
const resetPasswordModalOpen = ref(false)
const resetPasswordUserId = ref<string | null>(null)
const newPassword = ref('')
const assetsModalOpen = ref(false)
const assetsTargetName = ref('')
const assetsTargetUser = ref<User | null>(null)
const authorizedAssets = ref<AuthorizedAssets | null>(null)
const assetsLoading = ref(false)

onMounted(async () => {
  try {
    await Promise.all([
      usersStore.fetchUsers(),
      userGroupsStore.fetchUserGroups()
    ])
  } catch (error) {
    message.error('加载用户失败')
  }
})

const handleCreate = () => {
  selectedUser.value = null
  modalOpen.value = true
}

const handleEdit = (user: User) => {
  selectedUser.value = user
  modalOpen.value = true
}

const handleSubmit = async (values: CreateUserRequest | UpdateUserRequest) => {
  try {
    if (selectedUser.value) {
      await usersStore.updateUser(selectedUser.value.id, values as UpdateUserRequest)
      message.success('用户更新成功')
    } else {
      await usersStore.createUser(values as CreateUserRequest)
      message.success('用户创建成功')
    }
    modalOpen.value = false
    selectedUser.value = null
  } catch (err: unknown) {
    const axiosErr = err as { response?: { data?: { detail?: string } } }
    message.error(axiosErr.response?.data?.detail || (selectedUser.value ? '更新用户失败' : '创建用户失败'))
  }
}

const handleModalCancel = () => {
  modalOpen.value = false
  selectedUser.value = null
}

const handleDelete = (user: User) => {
  Modal.confirm({
    title: '删除用户',
    content: `确定要删除用户"${user.username}"吗？此操作不可撤销。`,
    okText: '删除',
    okType: 'danger',
    onOk: async () => {
      try {
        await usersStore.deleteUser(user.id)
        message.success('用户已删除')
      } catch (error) {
        message.error('删除用户失败')
      }
    }
  })
}

const handleResetPassword = (user: User) => {
  resetPasswordUserId.value = user.id
  newPassword.value = ''
  resetPasswordModalOpen.value = true
}

const handleResetPasswordSubmit = async () => {
  if (!resetPasswordUserId.value || !newPassword.value) {
    message.error('请输入新密码')
    return
  }

  try {
    await usersStore.resetPassword(resetPasswordUserId.value, {
      new_password: newPassword.value
    })
    message.success('密码重置成功')
    resetPasswordModalOpen.value = false
    resetPasswordUserId.value = null
    newPassword.value = ''
  } catch (err: unknown) {
    const axiosErr = err as { response?: { data?: { detail?: string } } }
    message.error(axiosErr.response?.data?.detail || '重置密码失败')
  }
}

const handleDisable = (user: User) => {
  Modal.confirm({
    title: '禁用用户',
    content: `确定要禁用用户"${user.username}"吗？`,
    okText: '禁用',
    okType: 'danger',
    onOk: async () => {
      try {
        await usersStore.disableUser(user.id)
        message.success('用户已禁用')
      } catch (error) {
        message.error('禁用用户失败')
      }
    }
  })
}

const handleEnable = (user: User) => {
  Modal.confirm({
    title: '启用用户',
    content: `确定要启用用户"${user.username}"吗？`,
    okText: '启用',
    onOk: async () => {
      try {
        await usersStore.enableUser(user.id)
        message.success('用户已启用')
      } catch (error) {
        message.error('启用用户失败')
      }
    }
  })
}

const handleViewAssets = async (user: User) => {
  assetsTargetUser.value = user
  assetsTargetName.value = user.username
  assetsModalOpen.value = true
  assetsLoading.value = true
  try {
    authorizedAssets.value = await usersApi.getAuthorizedAssets(user.id)
  } catch (error) {
    message.error('加载已授权资产失败')
  } finally {
    assetsLoading.value = false
  }
}

const reloadAssets = async () => {
  if (!assetsTargetUser.value) return
  assetsLoading.value = true
  try {
    authorizedAssets.value = await usersApi.getAuthorizedAssets(assetsTargetUser.value.id)
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

const handleUnlock = (user: User) => {
  Modal.confirm({
    title: '解锁用户',
    content: `确定要解锁用户"${user.username}"吗？这将清除登录失败次数限制。`,
    okText: '解锁',
    onOk: async () => {
      try {
        await usersApi.unlock(user.id)
        message.success('用户已解锁')
      } catch (error) {
        message.error('解锁用户失败')
      }
    }
  })
}
</script>

<style scoped>
.users-view {
  padding: 24px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
</style>
