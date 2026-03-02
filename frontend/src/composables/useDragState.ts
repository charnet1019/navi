import { ref } from 'vue'

const isDragging = ref(false)
const draggedItemId = ref<string | null>(null)

// 安全重置：防止 @end 未触发时状态卡住（如拖拽到窗口外松开）
if (typeof document !== 'undefined') {
  document.addEventListener('mouseup', () => {
    if (isDragging.value) {
      // 延迟执行，让 SortableJS 的 @end/@add 先处理完毕
      setTimeout(() => {
        isDragging.value = false
        draggedItemId.value = null
      }, 100)
    }
  })
}

export function useDragState() {
  return { isDragging, draggedItemId }
}
