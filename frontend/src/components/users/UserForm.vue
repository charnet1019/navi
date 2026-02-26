<template>
  <a-form
    :model="formState"
    :rules="rules"
    layout="vertical"
    @finish="handleSubmit"
  >
    <a-form-item label="用户名" name="username" required>
      <a-input
        v-model:value="formState.username"
        placeholder="请输入用户名"
        :disabled="isEdit"
      />
    </a-form-item>

    <a-form-item label="邮箱" name="email" required>
      <a-input
        v-model:value="formState.email"
        placeholder="请输入邮箱地址"
        type="email"
      />
    </a-form-item>

    <a-form-item label="姓名" name="full_name" required>
      <a-input
        v-model:value="formState.full_name"
        placeholder="请输入姓名"
      />
    </a-form-item>

    <a-form-item v-if="!isEdit" label="密码" name="password" required>
      <a-input-password
        v-model:value="formState.password"
        placeholder="请输入密码"
      />
    </a-form-item>

    <a-row :gutter="16">
      <a-col :span="12">
        <a-form-item label="激活" name="is_active">
          <a-switch v-model:checked="formState.is_active" />
        </a-form-item>
      </a-col>
      <a-col :span="12">
        <a-form-item label="超级管理员" name="is_superuser">
          <a-switch v-model:checked="formState.is_superuser" />
        </a-form-item>
      </a-col>
    </a-row>

    <a-form-item label="用户组" name="user_group_ids">
      <a-select
        v-model:value="formState.user_group_ids"
        mode="multiple"
        placeholder="请选择用户组"
        :options="groupOptions"
        :filter-option="filterOption"
        show-search
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
import { reactive, watch, computed } from 'vue'
import type { Rule } from 'ant-design-vue/es/form'
import type { User, UserGroup, CreateUserRequest, UpdateUserRequest } from '@/types'

interface Props {
  initialValues?: Partial<User>
  userGroups?: UserGroup[]
  loading?: boolean
  submitText?: string
}

interface Emits {
  (e: 'submit', values: CreateUserRequest | UpdateUserRequest): void
  (e: 'cancel'): void
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  submitText: '提交'
})

const emit = defineEmits<Emits>()

const isEdit = computed(() => !!props.initialValues?.id)

const groupOptions = computed(() =>
  (props.userGroups || []).map(g => ({ value: g.id, label: g.name }))
)

const filterOption = (input: string, option: { label: string }) =>
  option.label.toLowerCase().includes(input.toLowerCase())

interface FormState {
  username: string
  email: string
  full_name: string
  password: string
  is_active: boolean
  is_superuser: boolean
  user_group_ids: string[]
}

const formState = reactive<FormState>({
  username: props.initialValues?.username || '',
  email: props.initialValues?.email || '',
  full_name: props.initialValues?.full_name || '',
  password: '',
  is_active: props.initialValues?.is_active ?? true,
  is_superuser: props.initialValues?.is_superuser ?? false,
  user_group_ids: props.initialValues?.user_groups?.map(g => g.id) || []
})

const rules: Record<string, Rule[]> = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度需在3到50个字符之间', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
  full_name: [
    { required: true, message: '请输入姓名', trigger: 'blur' },
    { min: 1, max: 100, message: '姓名长度需在1到100个字符之间', trigger: 'blur' }
  ],
  password: [
    { required: !isEdit.value, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '密码至少需要8个字符', trigger: 'blur' }
  ]
}

watch(() => props.initialValues, (newValues) => {
  if (newValues) {
    formState.username = newValues.username || ''
    formState.email = newValues.email || ''
    formState.full_name = newValues.full_name || ''
    formState.is_active = newValues.is_active ?? true
    formState.is_superuser = newValues.is_superuser ?? false
    formState.user_group_ids = newValues.user_groups?.map(g => g.id) || []
  }
}, { deep: true })

const handleSubmit = () => {
  if (isEdit.value) {
    const values: UpdateUserRequest = {
      email: formState.email,
      full_name: formState.full_name,
      is_active: formState.is_active,
      is_superuser: formState.is_superuser,
      user_group_ids: formState.user_group_ids
    }
    emit('submit', values)
  } else {
    const values: CreateUserRequest = {
      username: formState.username,
      email: formState.email,
      full_name: formState.full_name,
      password: formState.password,
      is_active: formState.is_active,
      is_superuser: formState.is_superuser,
      user_group_ids: formState.user_group_ids
    }
    emit('submit', values)
  }
}

const handleCancel = () => {
  emit('cancel')
}
</script>
