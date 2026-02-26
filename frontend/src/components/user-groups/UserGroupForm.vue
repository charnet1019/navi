<template>
  <a-form
    :model="formState"
    :rules="rules"
    layout="vertical"
    @finish="handleSubmit"
  >
    <a-form-item label="名称" name="name" required>
      <a-input
        v-model:value="formState.name"
        placeholder="请输入用户组名称"
      />
    </a-form-item>

    <a-form-item label="描述" name="description">
      <a-textarea
        v-model:value="formState.description"
        placeholder="请输入用户组描述"
        :rows="3"
      />
    </a-form-item>

    <a-form-item>
      <a-space>
        <a-button type="primary" html-type="submit" :loading="loading">
          {{ submitText }}
        </a-button>
        <a-button @click="handleCancel">
          取消
        </a-button>
      </a-space>
    </a-form-item>
  </a-form>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'
import type { Rule } from 'ant-design-vue/es/form'
import type { UserGroup, CreateUserGroupRequest, UpdateUserGroupRequest } from '@/types'

interface Props {
  initialValues?: Partial<UserGroup>
  loading?: boolean
  submitText?: string
}

interface Emits {
  (e: 'submit', values: CreateUserGroupRequest | UpdateUserGroupRequest): void
  (e: 'cancel'): void
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  submitText: '提交'
})

const emit = defineEmits<Emits>()

interface FormState {
  name: string
  description?: string
}

const formState = reactive<FormState>({
  name: props.initialValues?.name || '',
  description: props.initialValues?.description || ''
})

const rules: Record<string, Rule[]> = {
  name: [
    { required: true, message: '请输入用户组名称', trigger: 'blur' },
    { min: 1, max: 100, message: '名称长度需在1到100个字符之间', trigger: 'blur' }
  ]
}

watch(() => props.initialValues, (newValues) => {
  if (newValues) {
    formState.name = newValues.name || ''
    formState.description = newValues.description || ''
  }
}, { deep: true })

const handleSubmit = () => {
  const values: CreateUserGroupRequest | UpdateUserGroupRequest = {
    name: formState.name,
    description: formState.description || undefined
  }
  emit('submit', values)
}

const handleCancel = () => {
  emit('cancel')
}
</script>
