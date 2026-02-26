<template>
  <a-modal
    :open="open"
    :title="title"
    :width="600"
    :footer="null"
    @cancel="handleCancel"
  >
    <UserGroupForm
      :initial-values="initialValues"
      :loading="loading"
      :submit-text="submitText"
      @submit="handleSubmit"
      @cancel="handleCancel"
    />
  </a-modal>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import UserGroupForm from './UserGroupForm.vue'
import type { UserGroup, CreateUserGroupRequest, UpdateUserGroupRequest } from '@/types'

interface Props {
  open: boolean
  group?: UserGroup | null
  loading?: boolean
}

interface Emits {
  (e: 'submit', values: CreateUserGroupRequest | UpdateUserGroupRequest): void
  (e: 'cancel'): void
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  group: null
})

const emit = defineEmits<Emits>()

const title = computed(() => props.group ? '编辑用户组' : '创建用户组')
const submitText = computed(() => props.group ? '更新' : '创建')
const initialValues = computed(() => props.group || undefined)

const handleSubmit = (values: CreateUserGroupRequest | UpdateUserGroupRequest) => {
  emit('submit', values)
}

const handleCancel = () => {
  emit('cancel')
}
</script>
