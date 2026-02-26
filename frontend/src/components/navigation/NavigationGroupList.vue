<template>
  <div class="navigation-group-list">
    <a-spin :spinning="loading">
      <draggable
        v-if="draggable"
        v-model="localGroups"
        item-key="id"
        :animation="200"
        handle=".drag-handle"
        @end="handleDragEnd"
      >
        <template #item="{ element }">
          <div
            class="group-item"
            :class="{ active: selectedGroupId === element.id.toString() }"
            @click="handleGroupClick(element.id.toString())"
          >
            <HolderOutlined class="drag-handle" />
            <img
              v-if="element.icon"
              :src="element.icon"
              :alt="element.name"
              class="group-icon"
            />
            <FolderOutlined v-else class="group-item-icon" />
            <span v-if="!collapsed" class="group-name">{{ element.name }}</span>
          </div>
        </template>
      </draggable>

      <template v-else>
        <div
          v-for="group in groups"
          :key="group.id"
          class="group-item"
          :class="{ active: selectedGroupId === group.id.toString() }"
          @click="handleGroupClick(group.id.toString())"
        >
          <img
            v-if="group.icon"
            :src="group.icon"
            :alt="group.name"
            class="group-icon"
          />
          <FolderOutlined v-else class="group-item-icon" />
          <span v-if="!collapsed" class="group-name">{{ group.name }}</span>
        </div>
      </template>
    </a-spin>

    <div v-if="showAddButton" class="add-group-button">
      <a-button type="primary" block @click="handleAdd">
        <template #icon><PlusOutlined /></template>
        添加分组
      </a-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import draggable from 'vuedraggable'
import { FolderOutlined, PlusOutlined, HolderOutlined } from '@ant-design/icons-vue'
import type { NavigationGroup } from '@/types'

interface Props {
  groups: NavigationGroup[]
  selectedGroupId?: string | null
  loading?: boolean
  showAddButton?: boolean
  collapsed?: boolean
  draggable?: boolean
}

interface Emits {
  (e: 'select', groupId: string): void
  (e: 'add'): void
  (e: 'reorder', orderedIds: string[]): void
}

const props = withDefaults(defineProps<Props>(), {
  selectedGroupId: null,
  loading: false,
  showAddButton: false,
  collapsed: false,
  draggable: false
})

const emit = defineEmits<Emits>()

const localGroups = ref<NavigationGroup[]>([])

watch(() => props.groups, (val) => {
  localGroups.value = [...val]
}, { immediate: true })

const handleGroupClick = (key: string) => {
  emit('select', key)
}

const handleAdd = () => {
  emit('add')
}

const handleDragEnd = () => {
  const orderedIds = localGroups.value.map(g => g.id.toString())
  emit('reorder', orderedIds)
}
</script>

<style scoped>
.navigation-group-list {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.group-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px 8px 24px;
  color: rgba(255, 255, 255, 0.65);
  cursor: pointer;
  transition: all 0.2s;
  user-select: none;
}

.group-item:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.08);
}

.group-item.active {
  color: #fff;
  background: #1677ff;
}

.group-icon {
  width: 16px;
  height: 16px;
  object-fit: contain;
  flex-shrink: 0;
}

.group-item-icon {
  flex-shrink: 0;
}

.group-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.drag-handle {
  cursor: grab;
  color: rgba(255, 255, 255, 0.3);
  flex-shrink: 0;
}

.drag-handle:hover {
  color: rgba(255, 255, 255, 0.65);
}

.add-group-button {
  padding: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  margin-top: auto;
}
</style>

