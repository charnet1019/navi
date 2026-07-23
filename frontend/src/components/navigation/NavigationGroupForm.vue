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

    <a-form-item label="父级分组" name="parent_id">
      <a-tree-select
        v-model:value="formState.parent_id"
        :tree-data="parentTreeData"
        :loading="groupsLoading"
        placeholder="不选则为顶级分组"
        allow-clear
        tree-default-expand-all
        :field-names="{ label: 'name', value: 'id', children: 'children' }"
        style="width: 100%"
      />
    </a-form-item>

    <a-row :gutter="16" align="bottom">
      <a-col :span="6">
        <a-form-item label="图标" name="icon">
          <IconUpload ref="iconUploadRef" v-model="formState.icon" />
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
import { reactive, ref, watch, computed } from 'vue'
import type { Rule } from 'ant-design-vue/es/form'
import IconUpload from '@/components/common/IconUpload.vue'
import type { NavigationGroup, CreateNavigationGroupRequest, UpdateNavigationGroupRequest } from '@/types'

interface Props {
  initialValues?: Partial<NavigationGroup>
  defaultParentId?: string | null
  groups?: NavigationGroup[]
  groupsLoading?: boolean
  loading?: boolean
  submitText?: string
}

interface Emits {
  (e: 'submit', values: CreateNavigationGroupRequest | UpdateNavigationGroupRequest): void
  (e: 'cancel'): void
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  submitText: '提交',
  groups: () => [],
  groupsLoading: false,
  defaultParentId: null,
})

const emit = defineEmits<Emits>()
const iconUploadRef = ref<InstanceType<typeof IconUpload>>()

// Build tree excluding the current group (can't be its own parent)
const parentTreeData = computed(() => {
  const currentId = props.initialValues?.id
  const eligible = props.groups.filter(g => g.id !== currentId)
  const map = new Map<string, NavigationGroup & { children: NavigationGroup[] }>()
  const roots: (NavigationGroup & { children: NavigationGroup[] })[] = []
  eligible.forEach(g => map.set(g.id, { ...g, children: [] }))
  map.forEach(g => {
    if (g.parent_id && map.has(g.parent_id)) {
      map.get(g.parent_id)!.children.push(g)
    } else {
      roots.push(g)
    }
  })
  return roots.sort((a, b) => a.sort_order - b.sort_order)
})

interface FormState {
  name: string
  description?: string
  icon?: string
  sort_order: number
  parent_id?: string | null
}

const formState = reactive<FormState>({
  name: props.initialValues?.name || '',
  description: props.initialValues?.description || '',
  icon: props.initialValues?.icon || '',
  sort_order: props.initialValues?.sort_order || 0,
  parent_id: props.initialValues?.parent_id ?? props.defaultParentId ?? null,
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
    formState.parent_id = newValues.parent_id || null
  }
})

const handleSubmit = () => {
  const values: CreateNavigationGroupRequest | UpdateNavigationGroupRequest = {
    name: formState.name,
    description: formState.description || undefined,
    icon: formState.icon || undefined,
    sort_order: formState.sort_order,
    parent_id: formState.parent_id || null,
  }
  iconUploadRef.value?.commit()
  emit('submit', values)
}

const handleCancel = () => {
  iconUploadRef.value?.cleanup()
  emit('cancel')
}
</script>
