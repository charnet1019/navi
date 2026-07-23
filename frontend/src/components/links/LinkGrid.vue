<template>
  <div class="link-grid-container">
    <a-spin :spinning="loading">
      <template v-if="links.length > 0">
        <draggable
          v-model="localLinks"
          item-key="id"
          :disabled="!editable"
          :animation="150"
          ghost-class="drag-ghost"
          class="link-grid"
          :style="gridStyle"
          @end="onReorder"
        >
          <template #item="{ element }">
            <LinkCard
              :link="element"
              :editable="editable"
              :favorited="favoriteIds.has(element.id)"
              @edit="handleEdit"
              @delete="handleDelete"
              @toggle-favorite="handleToggleFavorite"
            />
          </template>
        </draggable>
      </template>
      <a-empty
        v-else
        description="暂无链接"
        :image="Empty.PRESENTED_IMAGE_SIMPLE"
      >
        <a-button v-if="showAddButton" type="primary" @click="handleAdd">
          <template #icon><PlusOutlined /></template>
          添加链接
        </a-button>
      </a-empty>
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Empty } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import draggable from 'vuedraggable'
import LinkCard from './LinkCard.vue'
import type { Link } from '@/types'

interface Props {
  links: Link[]
  loading?: boolean
  columns?: number
  showAddButton?: boolean
  editable?: boolean
  favoriteIds?: Set<string>
}

interface Emits {
  (e: 'add'): void
  (e: 'edit', link: Link): void
  (e: 'delete', link: Link): void
  (e: 'toggleFavorite', linkId: string): void
  (e: 'reorder', orderedIds: string[]): void
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  columns: 5,
  showAddButton: false,
  editable: false,
  favoriteIds: () => new Set<string>()
})

const emit = defineEmits<Emits>()

const localLinks = ref<Link[]>([...props.links])

watch(() => props.links, (newLinks) => {
  localLinks.value = [...newLinks]
})

const gridStyle = computed(() => ({
  '--grid-columns': props.columns
}))

const onReorder = () => {
  emit('reorder', localLinks.value.map(l => l.id))
}

const handleAdd = () => emit('add')
const handleEdit = (link: Link) => emit('edit', link)
const handleDelete = (link: Link) => emit('delete', link)
const handleToggleFavorite = (linkId: string) => emit('toggleFavorite', linkId)
</script>

<style scoped>
.link-grid-container {
  width: 100%;
  padding: 8px 4px 8px;
}

.link-grid {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(var(--grid-columns, 5), 1fr);
}

.drag-ghost {
  opacity: 0.4;
}

@media (max-width: 768px) {
  .link-grid {
    grid-template-columns: repeat(2, 1fr) !important;
  }
}

@media (max-width: 480px) {
  .link-grid {
    grid-template-columns: repeat(1, 1fr) !important;
  }

  .link-grid-container {
    padding: 8px 12px 12px;
  }
}
</style>
