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
        placeholder="请输入链接名称"
      />
    </a-form-item>

    <a-form-item label="链接地址" name="url" required>
      <a-input
        v-model:value="formState.url"
        placeholder="https://example.com"
      />
    </a-form-item>

    <a-form-item label="描述" name="description">
      <a-textarea
        v-model:value="formState.description"
        placeholder="请输入链接描述"
        :rows="2"
      />
    </a-form-item>

    <a-form-item label="导航分组" name="navigation_group_id" required>
      <a-select
        v-model:value="formState.navigation_group_id"
        placeholder="请选择导航分组"
        :loading="groupsLoading"
      >
        <a-select-option
          v-for="group in groups"
          :key="group.id"
          :value="group.id"
        >
          {{ group.name }}
        </a-select-option>
      </a-select>
    </a-form-item>

    <a-row :gutter="16" align="bottom">
      <a-col :span="4">
        <a-form-item label="图标" name="icon_path">
          <IconUpload ref="iconUploadRef" v-model="formState.icon_path" />
        </a-form-item>
      </a-col>
      <a-col :span="8">
        <a-form-item label="排序" name="sort_order">
          <a-input-number
            v-model:value="formState.sort_order"
            :min="0"
            style="width: 100%"
          />
        </a-form-item>
      </a-col>
      <a-col :span="6">
        <a-form-item label="新窗口打开" name="open_in_new_tab">
          <a-switch v-model:checked="formState.open_in_new_tab" />
        </a-form-item>
      </a-col>
    </a-row>

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
import { reactive, ref, watch } from 'vue'
import type { Rule } from 'ant-design-vue/es/form'
import IconUpload from '@/components/common/IconUpload.vue'
import type { Link, CreateLinkRequest, UpdateLinkRequest, NavigationGroup } from '@/types'

interface Props {
  initialValues?: Partial<Link>
  groups: NavigationGroup[]
  groupsLoading?: boolean
  loading?: boolean
  submitText?: string
  defaultGroupId?: string
}

interface Emits {
  (e: 'submit', values: CreateLinkRequest | UpdateLinkRequest): void
  (e: 'cancel'): void
}

const props = withDefaults(defineProps<Props>(), {
  groupsLoading: false,
  loading: false,
  submitText: '提交',
  defaultGroupId: undefined
})

const emit = defineEmits<Emits>()
const iconUploadRef = ref<InstanceType<typeof IconUpload>>()

interface FormState {
  name: string
  url: string
  description?: string
  icon_path?: string
  sort_order: number
  open_in_new_tab: boolean
  navigation_group_id?: string
}

const formState = reactive<FormState>({
  name: props.initialValues?.name || '',
  url: props.initialValues?.url || '',
  description: props.initialValues?.description || '',
  icon_path: props.initialValues?.icon_path || '',
  sort_order: props.initialValues?.sort_order || 0,
  open_in_new_tab: props.initialValues?.open_in_new_tab ?? true,
  navigation_group_id: props.initialValues?.navigation_group_id || props.defaultGroupId
})

const rules: Record<string, Rule[]> = {
  name: [
    { required: true, message: '请输入名称', trigger: 'blur' },
    { min: 1, max: 100, message: '名称长度需在1到100个字符之间', trigger: 'blur' }
  ],
  url: [
    { required: true, message: '请输入链接地址', trigger: 'blur' }
  ],
  navigation_group_id: [
    { required: true, message: '请选择导航分组', trigger: 'change' }
  ]
}

watch(() => props.defaultGroupId, (newId) => {
  if (!props.initialValues && newId) {
    formState.navigation_group_id = newId
  }
})

watch(() => props.initialValues, (newValues) => {
  if (newValues) {
    formState.name = newValues.name || ''
    formState.url = newValues.url || ''
    formState.description = newValues.description || ''
    formState.icon_path = newValues.icon_path || ''
    formState.sort_order = newValues.sort_order || 0
    formState.open_in_new_tab = newValues.open_in_new_tab ?? true
    formState.navigation_group_id = newValues.navigation_group_id
  } else {
    formState.name = ''
    formState.url = ''
    formState.description = ''
    formState.icon_path = ''
    formState.sort_order = 0
    formState.open_in_new_tab = true
    formState.navigation_group_id = props.defaultGroupId
  }
}, { deep: true })

const handleSubmit = () => {
  const values: CreateLinkRequest | UpdateLinkRequest = {
    name: formState.name,
    url: formState.url,
    description: formState.description || undefined,
    icon_path: formState.icon_path || undefined,
    sort_order: formState.sort_order,
    open_in_new_tab: formState.open_in_new_tab,
    navigation_group_id: formState.navigation_group_id!
  }
  iconUploadRef.value?.commit()
  emit('submit', values)
}

const handleCancel = () => {
  iconUploadRef.value?.cleanup()
  emit('cancel')
}
</script>
