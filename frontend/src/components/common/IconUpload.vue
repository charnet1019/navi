<template>
  <div class="icon-upload">
    <a-upload
      :show-upload-list="false"
      :before-upload="handleBeforeUpload"
      accept=".png,.jpg,.jpeg,.gif,.svg"
    >
      <div v-if="imageUrl" class="icon-preview">
        <img :src="imageUrl" alt="icon" class="preview-img" />
        <div class="icon-overlay">
          <ReloadOutlined />
        </div>
      </div>
      <div v-else class="icon-placeholder">
        <LoadingOutlined v-if="uploading" />
        <PlusOutlined v-else />
        <div class="upload-text">上传</div>
      </div>
    </a-upload>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onBeforeUnmount } from 'vue'
import { PlusOutlined, LoadingOutlined, ReloadOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { uploadsApi } from '@/api/uploads'

interface Props {
  modelValue?: string
}

interface Emits {
  (e: 'update:modelValue', value: string): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const uploading = ref(false)
const savedUrl = ref(props.modelValue || '')
const pendingUrl = ref('')

const imageUrl = computed(() => props.modelValue || '')

// Sync savedUrl when parent sets value (e.g. from DB fetch)
watch(() => props.modelValue, (newVal) => {
  const val = newVal || ''
  if (val !== pendingUrl.value) {
    savedUrl.value = val
  }
})

const handleBeforeUpload = async (file: File) => {
  const isValidType = /\.(png|jpe?g|gif|svg)$/i.test(file.name)
  if (!isValidType) {
    message.error('仅支持 PNG、JPG、GIF、SVG 格式的图片')
    return false
  }
  const isLt5M = file.size / 1024 / 1024 < 5
  if (!isLt5M) {
    message.error('图片大小不能超过 5MB')
    return false
  }

  uploading.value = true
  try {
    if (pendingUrl.value) {
      try { await uploadsApi.deleteImage(pendingUrl.value) } catch { /* ignore */ }
    }
    const res = await uploadsApi.uploadImage(file)
    pendingUrl.value = res.url
    emit('update:modelValue', res.url)
  } catch {
    message.error('上传失败')
  } finally {
    uploading.value = false
  }
  return false
}

const commit = () => {
  const currentUrl = props.modelValue || ''
  const oldSavedUrl = savedUrl.value
  if (oldSavedUrl && oldSavedUrl !== currentUrl) {
    uploadsApi.deleteImage(oldSavedUrl).catch(() => { /* ignore */ })
  }
  savedUrl.value = currentUrl
  pendingUrl.value = ''
}

const cleanup = async () => {
  if (pendingUrl.value && pendingUrl.value !== savedUrl.value) {
    try { await uploadsApi.deleteImage(pendingUrl.value) } catch { /* ignore */ }
    pendingUrl.value = ''
    emit('update:modelValue', savedUrl.value)
  }
}

onBeforeUnmount(() => {
  cleanup()
})

defineExpose({ commit, cleanup })
</script>

<style scoped>
.icon-upload {
  display: inline-block;
}

.icon-preview {
  position: relative;
  width: 80px;
  height: 80px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  overflow: hidden;
  cursor: pointer;
}

.preview-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.icon-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.4);
  color: #fff;
  font-size: 18px;
  opacity: 0;
  transition: opacity 0.2s;
}

.icon-preview:hover .icon-overlay {
  opacity: 1;
}

.icon-placeholder {
  width: 80px;
  height: 80px;
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #999;
  transition: border-color 0.2s;
}

.icon-placeholder:hover {
  border-color: #1890ff;
  color: #1890ff;
}

.upload-text {
  font-size: 12px;
  margin-top: 4px;
}
</style>
