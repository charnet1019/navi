<template>
  <div class="icon-upload">
    <a-upload
      :show-upload-list="false"
      :before-upload="handleBeforeUpload"
      accept=".png,.jpg,.jpeg,.gif,.webp,.ico,.bmp,.tiff,.tif,.avif,.jfif"
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
import { PlusOutlined, LoadingOutlined, ReloadOutlined } from '@ant-design/icons-vue'
import { useImageUpload } from '@/composables/useImageUpload'

interface Props {
  modelValue?: string
}

interface Emits {
  (e: 'update:modelValue', value: string): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const { uploading, imageUrl, handleBeforeUpload, commit, cleanup } = useImageUpload({
  getModelValue: () => props.modelValue,
  emitValue: value => emit('update:modelValue', value),
  allowedPattern: /\.(png|jpe?g|gif|webp|ico|bmp|tiff?|avif|jfif)$/i,
  allowedMessage: '仅支持 PNG、JPG、GIF、WebP、ICO、BMP、TIFF、AVIF、JFIF 格式的图片',
  maxSizeMB: 5
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
