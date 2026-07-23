<template>
  <AppLayout>
    <div class="settings-view">
      <a-typography-title :level="2">系统设置</a-typography-title>

      <a-spin :spinning="loading">
        <a-card title="基本设置">
          <a-form layout="vertical">
            <a-form-item label="站点标题">
              <a-input
                v-model:value="formState.site_title"
                placeholder="请输入站点标题"
                style="max-width: 400px"
              />
              <div class="field-hint">显示在页面左上角的标题文字</div>
            </a-form-item>

            <a-form-item label="登录页标题">
              <a-input
                v-model:value="formState.login_title"
                placeholder="留空则使用站点标题"
                style="max-width: 400px"
              />
              <div class="field-hint">登录页面登录框上方显示的标题，留空则使用站点标题</div>
            </a-form-item>

            <a-form-item label="登录页背景图片">
              <ImageUpload ref="imageUploadRef" v-model="formState.login_bg_image" />
              <div class="field-hint">上传登录页面的背景图片，留空则使用默认背景色</div>
            </a-form-item>

            <a-form-item label="每行链接数">
              <a-input-number
                v-model:value="formState.links_per_row"
                :min="1"
                :max="12"
                style="width: 200px"
              />
              <div class="field-hint">首页每行显示的链接卡片数量</div>
            </a-form-item>

            <a-form-item label="版权信息">
              <a-input
                v-model:value="formState.copyright_info"
                placeholder="留空则不显示"
                style="max-width: 400px"
              />
              <div class="field-hint">登录页底部显示的版权或版本信息</div>
            </a-form-item>

            <a-form-item label="备案号">
              <a-input
                v-model:value="formState.icp_number"
                placeholder="留空则不显示"
                style="max-width: 400px"
              />
              <div class="field-hint">登录页底部显示的ICP备案号</div>
            </a-form-item>

            <a-form-item label="备案链接">
              <a-input
                v-model:value="formState.icp_link"
                placeholder="例如 https://beian.miit.gov.cn/"
                style="max-width: 400px"
              />
              <div class="field-hint">点击备案号跳转的链接地址</div>
            </a-form-item>

            <a-form-item>
              <a-button type="primary" :loading="saving" @click="handleSave">
                保存
              </a-button>
            </a-form-item>
          </a-form>
        </a-card>
        <a-card title="登录限制" style="margin-top: 24px">
          <a-form layout="vertical">
            <a-form-item label="最大登录失败次数">
              <a-input-number
                v-model:value="formState.max_login_attempts"
                :min="1"
                :max="20"
                style="width: 200px"
              />
              <div class="field-hint">连续登录失败达到此次数后，账号将被临时锁定</div>
            </a-form-item>

            <a-form-item label="锁定时间（分钟）">
              <a-input-number
                v-model:value="formState.login_lockout_minutes"
                :min="1"
                :max="1440"
                style="width: 200px"
              />
              <div class="field-hint">账号被锁定后需要等待的时间</div>
            </a-form-item>

            <a-form-item>
              <a-button type="primary" :loading="saving" @click="handleSave">
                保存
              </a-button>
            </a-form-item>
          </a-form>
        </a-card>

        <a-card title="审计日志" style="margin-top: 24px">
          <a-form layout="vertical">
            <a-form-item label="日志保留时间（天）">
              <a-input-number
                v-model:value="formState.audit_log_retention_days"
                :min="1"
                :max="3650"
                style="width: 200px"
              />
              <div class="field-hint">系统仅保留最近指定天数的审计日志，默认 30 天</div>
            </a-form-item>

            <a-form-item>
              <a-button type="primary" :loading="saving" @click="handleSave">
                保存
              </a-button>
            </a-form-item>
          </a-form>
        </a-card>

        <a-card title="密码规则" style="margin-top: 24px">
          <a-form layout="vertical">
            <a-form-item label="密码最小长度">
              <a-input-number
                v-model:value="formState.password_min_length"
                :min="4"
                :max="32"
                style="width: 200px"
              />
            </a-form-item>

            <a-form-item label="必须包含大写字母">
              <a-switch v-model:checked="formState.password_require_uppercase" />
            </a-form-item>

            <a-form-item label="必须包含小写字母">
              <a-switch v-model:checked="formState.password_require_lowercase" />
            </a-form-item>

            <a-form-item label="必须包含数字">
              <a-switch v-model:checked="formState.password_require_digit" />
            </a-form-item>

            <a-form-item label="必须包含特殊字符">
              <a-switch v-model:checked="formState.password_require_special" />
            </a-form-item>

            <a-form-item>
              <a-button type="primary" :loading="saving" @click="handleSave">
                保存
              </a-button>
            </a-form-item>
          </a-form>
        </a-card>
      </a-spin>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { reactive, ref, watch, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import AppLayout from '@/components/layout/AppLayout.vue'
import ImageUpload from '@/components/common/ImageUpload.vue'
import { useSettingsStore } from '@/stores/settings'

const settingsStore = useSettingsStore()

const loading = ref(false)
const saving = ref(false)
const imageUploadRef = ref<InstanceType<typeof ImageUpload>>()
const bgImageLoaded = ref(false)

const formState = reactive({
  site_title: 'Navi',
  login_title: '',
  login_bg_image: '',
  links_per_row: 5,
  copyright_info: '',
  icp_number: '',
  icp_link: '',
  max_login_attempts: 3,
  login_lockout_minutes: 30,
  audit_log_retention_days: 30,
  password_min_length: 6,
  password_require_uppercase: true,
  password_require_lowercase: true,
  password_require_digit: true,
  password_require_special: true,
})

onMounted(async () => {
  try {
    loading.value = true
    await settingsStore.fetchSettings()
    formState.site_title = settingsStore.siteTitle
    formState.login_title = settingsStore.loginTitle
    formState.login_bg_image = settingsStore.loginBgImage
    formState.links_per_row = settingsStore.linksPerRow
    formState.copyright_info = settingsStore.copyrightInfo
    formState.icp_number = settingsStore.icpNumber
    formState.icp_link = settingsStore.icpLink
    formState.max_login_attempts = settingsStore.maxLoginAttempts
    formState.login_lockout_minutes = settingsStore.loginLockoutMinutes
    formState.audit_log_retention_days = settingsStore.auditLogRetentionDays
    formState.password_min_length = settingsStore.passwordMinLength
    formState.password_require_uppercase = settingsStore.passwordRequireUppercase
    formState.password_require_lowercase = settingsStore.passwordRequireLowercase
    formState.password_require_digit = settingsStore.passwordRequireDigit
    formState.password_require_special = settingsStore.passwordRequireSpecial
    bgImageLoaded.value = true
  } catch {
    message.error('加载设置失败')
  } finally {
    loading.value = false
  }
})

// Auto-save background image on upload/clear so changes persist immediately
watch(() => formState.login_bg_image, async (newVal) => {
  if (!bgImageLoaded.value) return
  try {
    await settingsStore.updateSetting('login_bg_image', { value: newVal })
    imageUploadRef.value?.commit()
  } catch { /* will be saved with the form */ }
})

const handleSave = async () => {
  try {
    saving.value = true
    await Promise.all([
      settingsStore.updateSetting('site_title', { value: formState.site_title }),
      settingsStore.updateSetting('login_title', { value: formState.login_title }),
      settingsStore.updateSetting('login_bg_image', { value: formState.login_bg_image }),
      settingsStore.updateSetting('links_per_row', { value: String(formState.links_per_row) }),
      settingsStore.updateSetting('copyright_info', { value: formState.copyright_info }),
      settingsStore.updateSetting('icp_number', { value: formState.icp_number }),
      settingsStore.updateSetting('icp_link', { value: formState.icp_link }),
      settingsStore.updateSetting('max_login_attempts', { value: String(formState.max_login_attempts) }),
      settingsStore.updateSetting('login_lockout_minutes', { value: String(formState.login_lockout_minutes) }),
      settingsStore.updateSetting('audit_log_retention_days', { value: String(formState.audit_log_retention_days) }),
      settingsStore.updateSetting('password_min_length', { value: String(formState.password_min_length) }),
      settingsStore.updateSetting('password_require_uppercase', { value: String(formState.password_require_uppercase) }),
      settingsStore.updateSetting('password_require_lowercase', { value: String(formState.password_require_lowercase) }),
      settingsStore.updateSetting('password_require_digit', { value: String(formState.password_require_digit) }),
      settingsStore.updateSetting('password_require_special', { value: String(formState.password_require_special) }),
    ])
    message.success('设置已保存')
    imageUploadRef.value?.commit()
  } catch {
    message.error('保存设置失败')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.settings-view {
  padding: 24px;
}

.field-hint {
  color: #999;
  font-size: 12px;
  margin-top: 4px;
}
</style>
