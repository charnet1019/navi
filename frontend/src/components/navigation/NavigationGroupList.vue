<template>
  <div class="navigation-group-list">
    <a-spin :spinning="loading">
      <draggable
        v-model="localGroups"
        item-key="id"
        :disabled="!isSuperuser"
        :animation="150"
        ghost-class="drag-ghost"
        @end="onReorder"
      >
        <template #item="{ element }">
          <NavGroupNode
            :group="element"
            :selected-id="selectedGroupId"
            :collapsed="collapsed"
            :depth="0"
            @select="(id) => emit('select', id)"
          />
        </template>
      </draggable>
    </a-spin>

    <div v-if="showAddButton" class="add-group-button">
      <a-button type="primary" block @click="emit('add')">
        <template #icon><PlusOutlined /></template>
        添加分组
      </a-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import draggable from 'vuedraggable'
import NavGroupNode from './NavGroupNode.vue'
import { useNavigationStore } from '@/stores/navigation'
import { useAuthStore } from '@/stores/auth'
import type { NavigationGroup } from '@/types'

interface Props {
  groups: NavigationGroup[]
  selectedGroupId?: string | null
  loading?: boolean
  showAddButton?: boolean
  collapsed?: boolean
}

interface Emits {
  (e: 'select', groupId: string): void
  (e: 'add'): void
}

const props = withDefaults(defineProps<Props>(), {
  selectedGroupId: null,
  loading: false,
  showAddButton: false,
  collapsed: false,
})

const emit = defineEmits<Emits>()
const navigationStore = useNavigationStore()
const authStore = useAuthStore()
const isSuperuser = computed(() => authStore.isSuperuser)

const localGroups = ref<NavigationGroup[]>([...props.groups])

watch(() => props.groups, (newGroups) => {
  localGroups.value = [...newGroups]
}, { deep: true })

const onReorder = async () => {
  try {
    await navigationStore.reorderGroups(localGroups.value.map(g => g.id))
  } catch {
    localGroups.value = [...props.groups]
  }
}
</script>

<style scoped>
.navigation-group-list {
  display: flex;
  flex-direction: column;
  padding: 4px 0;
}

.add-group-button {
  padding: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  margin-top: auto;
}

:deep(.drag-ghost) {
  opacity: 0.4;
  background: rgba(255, 255, 255, 0.1);
}
</style>
