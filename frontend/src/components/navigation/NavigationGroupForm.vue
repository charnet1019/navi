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
        placeholder="请输入分组名称"
      />
    </a-form-item>

    <a-form-item label="描述" name="description">
      <a-textarea
        v-model:value="formState.description"
        placeholder="请输入分组描述"
        :rows="2"
      />
    </a-form-item>

    <a-row :gutter="16" align="bottom">
      <a-col :span="6">
        <a-form-item label="图标" name="icon">
          <IconUpload ref="iconUploadRef" v-model="formState.icon" />
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
import type { NavigationGroup, CreateNavigationGroupRequest, UpdateNavigationGroupRequest } from '@/types'

interface Props {
  initialValues?: Partial<NavigationGroup>
  loading?: boolean
  submitText?: string
}

interface Emits {
  (e: 'submit', values: CreateNavigationGroupRequest | UpdateNavigationGroupRequest): void
  (e: 'cancel'): void
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  submitText: '提交'
})

const emit = defineEmits<Emits>()
const iconUploadRef = ref<InstanceType<typeof IconUpload>>()

interface FormState {
  name: string
  description?: string
  icon?: string
  sort_order: number
}

const formState = reactive<FormState>({
  name: props.initialValues?.name || '',
  description: props.initialValues?.description || '',
  icon: props.initialValues?.icon || '',
  sort_order: props.initialValues?.sort_order || 0
})

const rules: Record<string, Rule[]> = {
  name: [
    { required: true, message: '请输入名称', trigger: 'blur' },
    { min: 1, max: 100, message: '名称长度需在1到100个字符之间', trigger: 'blur' }
  ]
}

watch(() => props.initialValues, (newValues) => {
  if (newValues) {
    formState.name = newValues.name || ''
    formState.description = newValues.description || ''
    formState.icon = newValues.icon || ''
    formState.sort_order = newValues.sort_order || 0
  }
}, { deep: true })

const handleSubmit = () => {
  const values: CreateNavigationGroupRequest | UpdateNavigationGroupRequest = {
    name: formState.name,
    description: formState.description || undefined,
    icon: formState.icon || undefined,
    sort_order: formState.sort_order
  }
  iconUploadRef.value?.commit()
  emit('submit', values)
}

const handleCancel = () => {
  iconUploadRef.value?.cleanup()
  emit('cancel')
}
</script>

