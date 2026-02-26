<template>
  <div class="image-upload">
    <a-upload
      :show-upload-list="false"
      :before-upload="handleBeforeUpload"
      accept=".png,.jpg,.jpeg,.gif,.webp"
    >
      <div v-if="imageUrl" class="image-preview">
        <img :src="imageUrl" alt="preview" class="preview-img" />
        <div class="image-overlay">
          <ReloadOutlined />
        </div>
      </div>
      <div v-else class="image-placeholder">
        <LoadingOutlined v-if="uploading" />
        <PlusOutlined v-else />
        <div class="upload-text">上传图片</div>
      </div>
    </a-upload>
    <a-button
      v-if="imageUrl"
      type="link"
      danger
      size="small"
      style="margin-top: 4px"
      @click="handleClear"
    >
      清除
    </a-button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
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

const imageUrl = computed(() => props.modelValue || '')

const handleBeforeUpload = async (file: File) => {
  const isValidType = /\.(png|jpe?g|gif|webp)$/i.test(file.name)
  if (!isValidType) {
    message.error('仅支持 PNG、JPG、GIF、WebP 格式的图片')
    return false
  }
  const isLt10M = file.size / 1024 / 1024 < 10
  if (!isLt10M) {
    message.error('图片大小不能超过 10MB')
    return false
  }

  uploading.value = true
  try {
    const res = await uploadsApi.uploadImage(file)
    emit('update:modelValue', res.url)
  } catch {
    message.error('上传失败')
  } finally {
    uploading.value = false
  }
  return false
}

const handleClear = () => {
  emit('update:modelValue', '')
}
</script>

<style scoped>
.image-upload {
  display: inline-block;
}

.image-preview {
  position: relative;
  width: 200px;
  height: 120px;
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

.image-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.4);
  color: #fff;
  font-size: 20px;
  opacity: 0;
  transition: opacity 0.2s;
}

.image-preview:hover .image-overlay {
  opacity: 1;
}

.image-placeholder {
  width: 200px;
  height: 120px;
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

.image-placeholder:hover {
  border-color: #1890ff;
  color: #1890ff;
}

.upload-text {
  font-size: 12px;
  margin-top: 4px;
}
</style>
