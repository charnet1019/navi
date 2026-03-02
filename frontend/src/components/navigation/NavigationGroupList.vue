<template>
  <div class="navigation-group-list">
    <a-spin :spinning="loading">
      <draggable
        v-model="localGroups"
        item-key="id"
        :disabled="!isSuperuser"
        :animation="150"
        ghost-class="drag-ghost"
        group="nav-groups"
        handle=".draggable"
        @start="onDragStart"
        @end="onDragEnd"
        @change="onChange"
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
import { useDragState } from '@/composables/useDragState'
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
const { isDragging, draggedItemId } = useDragState()

const localGroups = ref<NavigationGroup[]>([...props.groups])

watch(() => props.groups, (newGroups) => {
  if (!isDragging.value) {
    localGroups.value = [...newGroups]
  }
})

const onDragStart = (evt: { item: HTMLElement }) => {
  isDragging.value = true
  const groupId = evt.item.closest('[data-group-id]')?.getAttribute('data-group-id')
  if (groupId) {
    draggedItemId.value = groupId
  }
}

type DragChangeEvent = {
  moved?: { element: NavigationGroup; oldIndex: number; newIndex: number }
  added?: { element: NavigationGroup; newIndex: number }
}

const onDragEnd = () => {
  isDragging.value = false
  draggedItemId.value = null
}

const onChange = async (evt: DragChangeEvent) => {
  if (evt.moved) {
    try {
      await navigationStore.reorderGroups(localGroups.value.map(g => g.id))
    } catch {
      localGroups.value = [...props.groups]
    }
  } else if (evt.added) {
    const movedId = evt.added.element.id
    const orderedIds = localGroups.value.map(g => g.id)
    try {
      await navigationStore.updateGroup(movedId, { parent_id: null })
      await navigationStore.reorderGroups(orderedIds)
    } catch {
      await navigationStore.fetchGroups()
    }
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
