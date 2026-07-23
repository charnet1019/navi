<template>
  <div class="image-upload">
    <a-upload
      :show-upload-list="false"
      :before-upload="handleBeforeUpload"
      accept=".png,.jpg,.jpeg,.gif,.webp,.ico,.bmp,.tiff,.tif,.avif,.jfif"
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

const { uploading, imageUrl, handleBeforeUpload, handleClear, commit, cleanup } = useImageUpload({
  getModelValue: () => props.modelValue,
  emitValue: value => emit('update:modelValue', value),
  allowedPattern: /\.(png|jpe?g|gif|webp|ico|bmp|tiff?|avif|jfif)$/i,
  allowedMessage: '仅支持 PNG、JPG、GIF、WebP、ICO、BMP、TIFF、AVIF、JFIF 格式的图片',
  maxSizeMB: 10
})

defineExpose({ commit, cleanup })
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
