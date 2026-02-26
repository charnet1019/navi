<template>
  <a-card
    :hoverable="true"
    class="link-card"
    @click="handleClick"
  >
    <div class="link-card-top-actions" @click.stop>
      <a-button
        type="text"
        size="small"
        class="favorite-btn"
        :class="{ 'is-favorited': favorited }"
        @click="handleToggleFavorite"
      >
        <template #icon>
          <StarFilled v-if="favorited" />
          <StarOutlined v-else />
        </template>
      </a-button>
      <template v-if="editable">
        <a-button type="text" size="small" @click="handleEdit">
          <template #icon><EditOutlined /></template>
        </a-button>
        <a-button type="text" size="small" danger @click="handleDelete">
          <template #icon><DeleteOutlined /></template>
        </a-button>
      </template>
    </div>
    <div class="link-card-content">
      <div class="link-card-header">
        <div class="link-card-icon">
          <img v-if="link.icon_path" :src="link.icon_path" :alt="link.name" />
          <LinkOutlined v-else />
        </div>
        <div class="link-card-title">
          {{ link.name }}
        </div>
      </div>
      <div v-if="link.description" class="link-card-description">
        {{ link.description }}
      </div>
    </div>
  </a-card>
</template>

<script setup lang="ts">
import { LinkOutlined, EditOutlined, DeleteOutlined, StarOutlined, StarFilled } from '@ant-design/icons-vue'
import type { Link } from '@/types'

interface Props {
  link: Link
  editable?: boolean
  favorited?: boolean
}

interface Emits {
  (e: 'edit', link: Link): void
  (e: 'delete', link: Link): void
  (e: 'toggleFavorite', linkId: string): void
}

const props = withDefaults(defineProps<Props>(), {
  editable: false,
  favorited: false
})

const emit = defineEmits<Emits>()

const handleClick = () => {
  const target = props.link.open_in_new_tab ? '_blank' : '_self'
  window.open(props.link.url, target, 'noopener,noreferrer')
}

const handleEdit = () => emit('edit', props.link)
const handleDelete = () => emit('delete', props.link)
const handleToggleFavorite = () => emit('toggleFavorite', props.link.id)
</script>

<style scoped>
.link-card {
  cursor: pointer;
  position: relative;
  transition: all 0.3s ease;
}

.link-card :deep(.ant-card-body) {
  padding: 12px;
}

.link-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
}

.link-card-top-actions {
  position: absolute;
  top: 4px;
  right: 4px;
  display: flex;
  gap: 2px;
  opacity: 0;
  transition: opacity 0.2s;
  z-index: 1;
}

.link-card:hover .link-card-top-actions {
  opacity: 1;
}

.favorite-btn.is-favorited {
  opacity: 1 !important;
  color: #faad14;
}

.link-card .favorite-btn.is-favorited {
  opacity: 1;
}

.link-card-content {
  display: flex;
  flex-direction: column;
}

.link-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.link-card-icon {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: #1890ff;
}

.link-card-icon img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.link-card-title {
  flex: 1;
  font-size: 14px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.85);
  line-height: 1.4;
  word-break: break-word;
}

.link-card-description {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.55);
  line-height: 1.4;
  margin-top: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
</style>
