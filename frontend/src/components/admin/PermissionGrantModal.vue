<template>
  <a-modal
    :open="open"
    title="授予权限"
    :confirm-loading="loading"
    @ok="handleSubmit"
    @cancel="$emit('cancel')"
  >
    <a-form layout="vertical">
      <a-form-item label="授权对象">
        <a-radio-group v-model:value="grantType">
          <a-radio value="user">用户</a-radio>
          <a-radio value="user_group">用户组</a-radio>
        </a-radio-group>
      </a-form-item>

      <a-form-item v-if="grantType === 'user'" label="选择用户">
        <a-select
          v-model:value="selectedUserId"
          show-search
          placeholder="搜索用户"
          :filter-option="filterOption"
          :options="userOptions"
        />
      </a-form-item>

      <a-form-item v-else label="选择用户组">
        <a-select
          v-model:value="selectedUserGroupId"
          show-search
          placeholder="搜索用户组"
          :filter-option="filterOption"
          :options="userGroupOptions"
        />
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { User, UserGroup, GrantPermissionRequest } from '@/types'

const props = defineProps<{
  open: boolean
  users: User[]
  userGroups: UserGroup[]
  loading: boolean
}>()

const emit = defineEmits<{
  submit: [data: GrantPermissionRequest]
  cancel: []
}>()

const grantType = ref<'user' | 'user_group'>('user')
const selectedUserId = ref<string | undefined>(undefined)
const selectedUserGroupId = ref<string | undefined>(undefined)

const userOptions = computed(() =>
  props.users.map((u) => ({
    value: u.id,
    label: `${u.username} (${u.email})`
  }))
)

const userGroupOptions = computed(() =>
  props.userGroups.map((g) => ({
    value: g.id,
    label: g.name
  }))
)

const filterOption = (input: string, option: { label: string }) =>
  option.label.toLowerCase().includes(input.toLowerCase())

watch(() => props.open, (isOpen) => {
  if (!isOpen) {
    grantType.value = 'user'
    selectedUserId.value = undefined
    selectedUserGroupId.value = undefined
  }
})

const handleSubmit = () => {
  const data: GrantPermissionRequest =
    grantType.value === 'user'
      ? { user_id: selectedUserId.value }
      : { user_group_id: selectedUserGroupId.value }

  if (!data.user_id && !data.user_group_id) return

  emit('submit', data)
}
</script>