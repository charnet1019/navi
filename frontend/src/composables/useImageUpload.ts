import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { message } from 'ant-design-vue'
import { uploadsApi } from '@/api/uploads'

interface UseImageUploadOptions {
  getModelValue: () => string | undefined
  emitValue: (value: string) => void
  allowedPattern: RegExp
  allowedMessage: string
  maxSizeMB: number
}

export function useImageUpload(options: UseImageUploadOptions) {
  const uploading = ref(false)
  const savedUrl = ref(options.getModelValue() || '')
  const pendingUrl = ref('')

  const imageUrl = computed(() => options.getModelValue() || '')

  watch(options.getModelValue, (newVal) => {
    const val = newVal || ''
    if (val !== pendingUrl.value) {
      savedUrl.value = val
    }
  })

  const handleBeforeUpload = async (file: File) => {
    if (!options.allowedPattern.test(file.name)) {
      message.error(options.allowedMessage)
      return false
    }

    if (file.size / 1024 / 1024 >= options.maxSizeMB) {
      message.error(`图片大小不能超过 ${options.maxSizeMB}MB`)
      return false
    }

    uploading.value = true
    try {
      if (pendingUrl.value) {
        try { await uploadsApi.deleteImage(pendingUrl.value) } catch { /* ignore */ }
      }
      const res = await uploadsApi.uploadImage(file)
      pendingUrl.value = res.url
      options.emitValue(res.url)
    } catch {
      message.error('上传失败')
    } finally {
      uploading.value = false
    }
    return false
  }

  const handleClear = async () => {
    const current = options.getModelValue() || ''
    if (current === pendingUrl.value && pendingUrl.value) {
      try { await uploadsApi.deleteImage(pendingUrl.value) } catch { /* ignore */ }
      pendingUrl.value = ''
    }
    options.emitValue('')
  }

  const commit = () => {
    const currentUrl = options.getModelValue() || ''
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
      options.emitValue(savedUrl.value)
    }
  }

  onBeforeUnmount(() => {
    cleanup()
  })

  return {
    uploading,
    imageUrl,
    handleBeforeUpload,
    handleClear,
    commit,
    cleanup
  }
}
