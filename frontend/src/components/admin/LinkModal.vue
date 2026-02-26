<template>
  <a-modal
    :open="open"
    :title="title"
    :width="700"
    :footer="null"
    @cancel="handleCancel"
  >
    <LinkForm
      :initial-values="initialValues"
      :groups="groups"
      :groups-loading="groupsLoading"
      :loading="loading"
      :submit-text="submitText"
      :default-group-id="defaultGroupId"
      @submit="handleSubmit"
      @cancel="handleCancel"
    />
  </a-modal>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import LinkForm from '@/components/links/LinkForm.vue'
import type { Link, NavigationGroup, CreateLinkRequest, UpdateLinkRequest } from '@/types'

interface Props {
  open: boolean
  link?: Link | null
  groups: NavigationGroup[]
  groupsLoading?: boolean
  loading?: boolean
  defaultGroupId?: string
}

interface Emits {
  (e: 'submit', values: CreateLinkRequest | UpdateLinkRequest): void
  (e: 'cancel'): void
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  groupsLoading: false,
  link: null,
  defaultGroupId: undefined
})

const emit = defineEmits<Emits>()

const title = computed(() => props.link ? '编辑链接' : '创建链接')
const submitText = computed(() => props.link ? '更新' : '创建')
const initialValues = computed(() => props.link || undefined)

const handleSubmit = (values: CreateLinkRequest | UpdateLinkRequest) => {
  emit('submit', values)
}

const handleCancel = () => {
  emit('cancel')
}
</script>
