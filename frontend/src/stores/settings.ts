import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { settingsApi, type Setting, type UpdateSettingRequest } from '@/api/settings'
import { withLoading } from '@/utils/withLoading'

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

  // Login & password rule settings
  const maxLoginAttempts = computed(() => {
    const setting = settingsMap.value['max_login_attempts']
    return setting ? parseInt(setting.value, 10) : 3
  })

  const loginLockoutMinutes = computed(() => {
    const setting = settingsMap.value['login_lockout_minutes']
    return setting ? parseInt(setting.value, 10) : 30
  })

  const auditLogRetentionDays = computed(() => {
    const setting = settingsMap.value['audit_log_retention_days']
    return setting ? parseInt(setting.value, 10) : 30
  })

  const passwordMinLength = computed(() => {
    const setting = settingsMap.value['password_min_length']
    return setting ? parseInt(setting.value, 10) : 6
  })

  const passwordRequireUppercase = computed(() => {
    const setting = settingsMap.value['password_require_uppercase']
    return setting ? setting.value === 'true' : true
  })

  const passwordRequireLowercase = computed(() => {
    const setting = settingsMap.value['password_require_lowercase']
    return setting ? setting.value === 'true' : true
  })

  const passwordRequireDigit = computed(() => {
    const setting = settingsMap.value['password_require_digit']
    return setting ? setting.value === 'true' : true
  })

  const passwordRequireSpecial = computed(() => {
    const setting = settingsMap.value['password_require_special']
    return setting ? setting.value === 'true' : true
  })

  // Actions
  async function fetchPublicSettings(): Promise<void> {
    await withLoading(loading, error, 'Failed to fetch public settings', async () => {
      settings.value = await settingsApi.listPublic()
    })
  }

  async function fetchSettings(): Promise<void> {
    await withLoading(loading, error, 'Failed to fetch settings', async () => {
      settings.value = await settingsApi.list()
    })
  }

  async function updateSetting(key: string, data: UpdateSettingRequest): Promise<Setting> {
    return withLoading(loading, error, 'Failed to update setting', async () => {
      const updatedSetting = await settingsApi.update(key, data)
      const exists = settings.value.some(s => s.key === key)
      settings.value = exists
        ? settings.value.map(s => s.key === key ? updatedSetting : s)
        : [...settings.value, updatedSetting]
      return updatedSetting
    })
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
    maxLoginAttempts,
    loginLockoutMinutes,
    auditLogRetentionDays,
    passwordMinLength,
    passwordRequireUppercase,
    passwordRequireLowercase,
    passwordRequireDigit,
    passwordRequireSpecial,
    loading,
    error,
    fetchPublicSettings,
    fetchSettings,
    updateSetting
  }
})
