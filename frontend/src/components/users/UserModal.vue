<template>
  <a-modal
    :open="open"
    :title="title"
    :width="600"
    :footer="null"
    @cancel="handleCancel"
  >
    <UserForm
      :initial-values="initialValues"
      :user-groups="userGroups"
      :loading="loading"
      :submit-text="submitText"
      @submit="handleSubmit"
      @cancel="handleCancel"
    />
  </a-modal>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import UserForm from './UserForm.vue'
import type { User, UserGroup, CreateUserRequest, UpdateUserRequest } from '@/types'

interface Props {
  open: boolean
  user?: User | null
  userGroups?: UserGroup[]
  loading?: boolean
}

interface Emits {
  (e: 'submit', values: CreateUserRequest | UpdateUserRequest): void
  (e: 'cancel'): void
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  user: null,
  userGroups: () => []
})

const emit = defineEmits<Emits>()

const title = computed(() => props.user ? '编辑用户' : '创建用户')
const submitText = computed(() => props.user ? '更新' : '创建')
const initialValues = computed(() => props.user || undefined)

const handleSubmit = (values: CreateUserRequest | UpdateUserRequest) => {
  emit('submit', values)
}

const handleCancel = () => {
  emit('cancel')
}
</script>
