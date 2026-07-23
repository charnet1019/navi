<template>
  <div class="nav-node" :data-group-id="group.id">
    <div
      class="nav-node-row"
      :class="{
        active: selectedId === group.id,
        'has-children': hasChildren,
        'nest-enabled': isDragging && isSuperuser && draggedItemId !== group.id,
        'draggable': isSuperuser && selectedId === group.id && !collapsed
      }"
      :style="{ paddingLeft: `${16 + depth * 16}px` }"
      @click="handleClick"
    >
      <span class="toggle-icon" v-if="hasChildren && !collapsed">
        <RightOutlined :class="{ expanded: open }" />
      </span>
      <span class="toggle-placeholder" v-else-if="!collapsed" />

      <img v-if="group.icon" :src="group.icon" :alt="group.name" class="group-icon" />
      <FolderOutlined v-else class="group-icon-default" />

      <span v-if="!collapsed" class="group-name">{{ group.name }}</span>

      <draggable
        v-if="isDragging && isSuperuser && draggedItemId !== group.id && !collapsed"
        v-model="nestZone"
        item-key="id"
        :group="nestGroup"
        :sort="false"
        :animation="0"
        class="nest-zone"
        @add="onNestAdd"
      >
        <template #item="{}"><span /></template>
      </draggable>
    </div>

    <div v-if="hasChildren && open && !collapsed" class="nav-node-children">
      <draggable
        v-model="localChildren"
        item-key="id"
        :disabled="!isSuperuser"
        :animation="150"
        ghost-class="drag-ghost"
        group="nav-groups"
        handle=".draggable"
        @start="onDragStart"
        @end="onDragEnd"
        @change="onChildChange"
      >
        <template #item="{ element }">
          <NavGroupNode
            :group="element"
            :selected-id="selectedId"
            :collapsed="collapsed"
            :depth="depth + 1"
            @select="(id) => emit('select', id)"
          />
        </template>
      </draggable>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { message } from 'ant-design-vue'
import { FolderOutlined, RightOutlined } from '@ant-design/icons-vue'
import draggable from 'vuedraggable'
import { useNavigationStore } from '@/stores/navigation'
import { useAuthStore } from '@/stores/auth'
import { useDragState } from '@/composables/useDragState'
import type { NavigationGroup } from '@/types'

interface Props {
  group: NavigationGroup
  selectedId?: string | null
  collapsed?: boolean
  depth?: number
}

interface Emits {
  (e: 'select', id: string): void
}

const props = withDefaults(defineProps<Props>(), {
  selectedId: null,
  collapsed: false,
  depth: 0,
})

const emit = defineEmits<Emits>()
const navigationStore = useNavigationStore()
const authStore = useAuthStore()
const isSuperuser = computed(() => authStore.isSuperuser)
const { isDragging, draggedItemId } = useDragState()

const hasChildren = computed(() => !!props.group.children?.length)
const localChildren = ref<NavigationGroup[]>([...(props.group.children ?? [])])
const nestZone = ref<NavigationGroup[]>([])

// 静态对象引用，避免每次渲染返回新对象导致 SortableJS 重新初始化
const nestGroupPut = (_to: unknown, _from: unknown, dragEl: HTMLElement) => {
  const movedId = dragEl.closest('[data-group-id]')?.getAttribute('data-group-id')
  if (!movedId) return false
  if (movedId === props.group.id) return false
  if (isDescendantOf(props.group.id, movedId)) return false
  return true
}
const nestGroup = { name: 'nav-groups', pull: false, put: nestGroupPut }

watch(() => props.group.children, (newChildren) => {
  if (!isDragging.value) {
    localChildren.value = [...(newChildren ?? [])]
    open.value = isSelectedPath(props.group, props.selectedId)
  }
})

function isSelectedPath(group: NavigationGroup, id: string | null | undefined): boolean {
  if (!id) return false
  return group.id === id || isDescendantSelected(group, id)
}

function isDescendantSelected(group: NavigationGroup, id: string | null | undefined): boolean {
  if (!id) return false
  return !!group.children?.some(c => c.id === id || isDescendantSelected(c, id))
}

function isDescendantOf(targetId: string, possibleAncestorId: string): boolean {
  const byId = new Map(navigationStore.groups.map(g => [g.id, g]))
  let cursor = byId.get(targetId)
  while (cursor?.parent_id) {
    if (cursor.parent_id === possibleAncestorId) {
      return true
    }
    cursor = byId.get(cursor.parent_id)
  }
  return false
}

const open = ref(isSelectedPath(props.group, props.selectedId))

watch(() => props.selectedId, (id) => {
  open.value = isSelectedPath(props.group, id)
})

const handleClick = () => {
  if (hasChildren.value) {
    open.value = !open.value
  }
  emit('select', props.group.id)
}

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

const onChildChange = async (evt: DragChangeEvent) => {
  if (evt.moved) {
    try {
      await navigationStore.reorderGroups(localChildren.value.map(c => c.id))
    } catch {
      message.error('排序失败')
      localChildren.value = [...(props.group.children ?? [])]
    }
  } else if (evt.added) {
    const movedId = evt.added.element.id
    if (movedId === props.group.id || isDescendantOf(props.group.id, movedId)) {
      await navigationStore.fetchGroups()
      return
    }
    const orderedIds = localChildren.value.map(c => c.id)
    try {
      await navigationStore.updateGroup(movedId, { parent_id: props.group.id })
      await navigationStore.reorderGroups(orderedIds)
    } catch {
      message.error('移动分组失败')
      await navigationStore.fetchGroups()
    }
  }
}

const onNestAdd = async (evt: { newIndex: number }) => {
  const moved = nestZone.value[evt.newIndex]
  nestZone.value = []
  if (!moved) return

  if (moved.id === props.group.id || isDescendantOf(props.group.id, moved.id)) {
    await navigationStore.fetchGroups()
    return
  }

  open.value = true
  try {
    await navigationStore.updateGroup(moved.id, { parent_id: props.group.id })
    await navigationStore.fetchGroups()
  } catch {
    message.error('移动分组失败')
    await navigationStore.fetchGroups()
  }
}
</script>

<style scoped>
.nav-node-row {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
  height: 40px;
  color: rgba(255, 255, 255, 0.65);
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
  user-select: none;
  padding-right: 16px;
}

.nav-node-row.draggable {
  cursor: grab;
}

.nav-node-row.draggable:active {
  cursor: grabbing;
}

.nav-node-row:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.08);
}

.nav-node-row.active {
  color: #fff;
  background: #1677ff;
}

.nav-node-row.nest-enabled {
  outline: 1px dashed rgba(22, 119, 255, 0.35);
  outline-offset: -1px;
}

.nest-zone {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 40px;
  z-index: 10;
  background: rgba(22, 119, 255, 0.15);
  overflow: hidden;
}

/* 压制 SortableJS 在 nest-zone 内插入的 placeholder，防止撑开布局引发闪烁 */
.nest-zone :deep(.sortable-ghost),
.nest-zone :deep(.sortable-chosen),
.nest-zone :deep(.sortable-drag) {
  height: 0 !important;
  padding: 0 !important;
  margin: 0 !important;
  overflow: hidden !important;
  opacity: 0 !important;
}

.toggle-icon {
  display: flex;
  align-items: center;
  flex-shrink: 0;
  font-size: 10px;
  transition: transform 0.2s;
}

.toggle-icon :deep(.anticon) {
  transition: transform 0.2s;
}

.toggle-icon :deep(.anticon.expanded) {
  transform: rotate(90deg);
}

.toggle-placeholder {
  width: 10px;
  flex-shrink: 0;
}

.group-icon {
  width: 14px;
  height: 14px;
  object-fit: contain;
  flex-shrink: 0;
}

.group-icon-default {
  flex-shrink: 0;
  font-size: 14px;
}

.group-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
}

:deep(.drag-ghost) {
  opacity: 0.4;
  background: rgba(255, 255, 255, 0.1);
}
</style>
