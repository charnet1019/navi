<template>
  <div class="nav-node">
    <!-- Row -->
    <div
      class="nav-node-row"
      :class="{ active: selectedId === group.id, 'has-children': hasChildren }"
      :style="{ paddingLeft: `${16 + depth * 16}px` }"
      @click="handleClick"
    >
      <!-- Expand toggle -->
      <span class="toggle-icon" v-if="hasChildren && !collapsed">
        <RightOutlined :class="{ expanded: open }" />
      </span>
      <span class="toggle-placeholder" v-else-if="!collapsed" />

      <!-- Group icon -->
      <img v-if="group.icon" :src="group.icon" :alt="group.name" class="group-icon" />
      <FolderOutlined v-else class="group-icon-default" />

      <!-- Name (hidden when sidebar collapsed) -->
      <span v-if="!collapsed" class="group-name">{{ group.name }}</span>
    </div>

    <!-- Children (inline, never popup) -->
    <div v-if="hasChildren && open && !collapsed" class="nav-node-children">
      <draggable
        v-model="localChildren"
        item-key="id"
        :disabled="!isSuperuser"
        :animation="150"
        ghost-class="drag-ghost"
        @end="onChildReorder"
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
import { FolderOutlined, RightOutlined } from '@ant-design/icons-vue'
import draggable from 'vuedraggable'
import { useNavigationStore } from '@/stores/navigation'
import { useAuthStore } from '@/stores/auth'
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

const hasChildren = computed(() => !!props.group.children?.length)

const localChildren = ref<NavigationGroup[]>([...(props.group.children ?? [])])

watch(() => props.group.children, (newChildren) => {
  localChildren.value = [...(newChildren ?? [])]
}, { deep: true })

// Auto-open if a descendant is selected
function isDescendantSelected(group: NavigationGroup, id: string | null | undefined): boolean {
  if (!id) return false
  return !!group.children?.some(c => c.id === id || isDescendantSelected(c, id))
}

const open = ref(isDescendantSelected(props.group, props.selectedId))

watch(() => props.selectedId, (id) => {
  if (isDescendantSelected(props.group, id)) open.value = true
})

const handleClick = () => {
  if (hasChildren.value) {
    open.value = !open.value
  }
  emit('select', props.group.id)
}

const onChildReorder = async () => {
  try {
    await navigationStore.reorderGroups(localChildren.value.map(c => c.id))
  } catch {
    localChildren.value = [...(props.group.children ?? [])]
  }
}
</script>

<style scoped>
.nav-node-row {
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

.nav-node-row:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.08);
}

.nav-node-row.active {
  color: #fff;
  background: #1677ff;
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
