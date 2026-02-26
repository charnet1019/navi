import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { settingsApi, type Setting, type UpdateSettingRequest } from '@/api/settings'

export const useSettingsStore = defineStore('settings', () => {
  // State
  const settings = ref<Setting[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const settingsMap = computed(() => {
    const map: Record<string, Setting> = {}
    settings.value.forEach(setting => {
      map[setting.key] = setting
    })
    return map
  })

  const linksPerRow = computed(() => {
    const setting = settingsMap.value['links_per_row']
    return setting ? parseInt(setting.value, 10) : 5
  })

  const cachedSiteTitle = ref(localStorage.getItem('site_title') || 'Navi')

  const siteTitle = computed(() => {
    const setting = settingsMap.value['site_title']
    if (setting) {
      cachedSiteTitle.value = setting.value
      localStorage.setItem('site_title', setting.value)
      return setting.value
    }
    return cachedSiteTitle.value
  })

  const loginTitle = computed(() => {
    const setting = settingsMap.value['login_title']
    return setting?.value || ''
  })

  const loginBgImage = computed(() => {
    const setting = settingsMap.value['login_bg_image']
    return setting?.value || ''
  })

  const copyrightInfo = computed(() => {
    const setting = settingsMap.value['copyright_info']
    return setting?.value || ''
  })

  const icpNumber = computed(() => {
    const setting = settingsMap.value['icp_number']
    return setting?.value || ''
  })

  const icpLink = computed(() => {
    const setting = settingsMap.value['icp_link']
    return setting?.value || ''
  })

  // Actions
  async function fetchPublicSettings(): Promise<void> {
    try {
      loading.value = true
      error.value = null
      settings.value = await settingsApi.listPublic()
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch public settings'
      error.value = errorMessage
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchSettings(): Promise<void> {
    try {
      loading.value = true
      error.value = null
      settings.value = await settingsApi.list()
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch settings'
      error.value = errorMessage
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateSetting(key: string, data: UpdateSettingRequest): Promise<Setting> {
    try {
      loading.value = true
      error.value = null
      const updatedSetting = await settingsApi.update(key, data)
      const exists = settings.value.some(s => s.key === key)
      settings.value = exists
        ? settings.value.map(s => s.key === key ? updatedSetting : s)
        : [...settings.value, updatedSetting]
      return updatedSetting
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update setting'
      error.value = errorMessage
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    settings,
    settingsMap,
    linksPerRow,
    siteTitle,
    loginTitle,
    loginBgImage,
    copyrightInfo,
    icpNumber,
    icpLink,
    loading,
    error,
    fetchPublicSettings,
    fetchSettings,
    updateSetting
  }
})
