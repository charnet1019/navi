<template>
  <div class="login-container" :style="containerStyle">
    <a-card class="login-card" :title="`登录 ${loginTitle}`">
      <a-form
        :model="formState"
        :rules="rules"
        @finish="handleSubmit"
        layout="vertical"
      >
        <a-form-item label="用户名" name="username">
          <a-input
            v-model:value="formState.username"
            placeholder="请输入用户名"
            size="large"
          >
            <template #prefix>
              <UserOutlined />
            </template>
          </a-input>
        </a-form-item>

        <a-form-item label="密码" name="password">
          <a-input-password
            v-model:value="formState.password"
            placeholder="请输入密码"
            size="large"
          >
            <template #prefix>
              <LockOutlined />
            </template>
          </a-input-password>
        </a-form-item>

        <a-form-item>
          <a-button
            type="primary"
            html-type="submit"
            size="large"
            block
            :loading="authStore.loading"
          >
            登录
</a-button>
        </a-form-item>
      </a-form>
    </a-card>
    <div v-if="copyrightInfo || icpNumber" class="login-footer">
      <span v-if="copyrightInfo">{{ copyrightInfo }}</span>
      <span v-if="icpNumber">
        <a v-if="icpLink" :href="icpLink" target="_blank" rel="noopener noreferrer">{{ icpNumber }}</a>
        <template v-else>{{ icpNumber }}</template>
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { UserOutlined, LockOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { useAuthStore } from '@/stores/auth'
import { useSettingsStore } from '@/stores/settings'
import type { Rule } from 'ant-design-vue/es/form'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const settingsStore = useSettingsStore()

onMounted(() => {
  settingsStore.fetchPublicSettings().catch(() => {})
})

const loginTitle = computed(() => settingsStore.loginTitle || settingsStore.siteTitle || 'Navi')
const loginBgImage = computed(() => settingsStore.loginBgImage)
const copyrightInfo = computed(() => settingsStore.copyrightInfo)
const icpNumber = computed(() => settingsStore.icpNumber)
const icpLink = computed(() => settingsStore.icpLink)

const containerStyle = computed(() => {
  if (!loginBgImage.value) return {}
  return {
    backgroundImage: `url(${loginBgImage.value})`,
    backgroundSize: 'cover',
    backgroundPosition: 'center',
    backgroundRepeat: 'no-repeat',
  }
})

const formState = reactive({
  username: '',
  password: ''
})

const rules: Record<string, Rule[]> = {
  username: [{ required: true, message: '请输入用户名' }],
  password: [{ required: true, message: '请输入密码' }]
}

const handleSubmit = async () => {
  try {
    await authStore.login(formState)
    message.success('登录成功')
    const redirect = route.query.redirect as string || '/'
    router.push(redirect)
  } catch (err: unknown) {
    const axiosErr = err as { response?: { data?: { detail?: string } } }
    const detail = axiosErr.response?.data?.detail
    message.error(detail || '登录失败，请检查用户名和密码')
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: #f0f2f5;
}

.login-card {
  width: 400px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.login-footer {
  position: absolute;
  bottom: 24px;
  left: 0;
  right: 0;
  text-align: center;
  color: rgba(0, 0, 0, 0.45);
  font-size: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.login-footer a {
  color: inherit;
  text-decoration: none;
}
</style>

