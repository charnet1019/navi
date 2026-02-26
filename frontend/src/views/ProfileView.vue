<template>
  <AppLayout>
    <div class="profile-view">
      <a-typography-title :level="2">个人资料</a-typography-title>

      <a-row :gutter="24">
        <a-col :xs="24" :lg="12">
          <a-card title="用户信息" class="profile-card">
            <a-descriptions bordered :column="1">
              <a-descriptions-item label="用户名">
                {{ authStore.user?.username }}
              </a-descriptions-item>
              <a-descriptions-item label="邮箱">
                {{ authStore.user?.email }}
              </a-descriptions-item>
              <a-descriptions-item label="姓名">
                {{ authStore.user?.full_name || '未设置' }}
              </a-descriptions-item>
              <a-descriptions-item label="角色">
                <a-tag :color="authStore.isSuperuser ? 'red' : 'blue'">
                  {{ authStore.isSuperuser ? '超级管理员' : '普通用户' }}
                </a-tag>
              </a-descriptions-item>
              <a-descriptions-item label="状态">
                <a-tag :color="authStore.user?.is_active ? 'green' : 'default'">
                  {{ authStore.user?.is_active ? '已激活' : '未激活' }}
                </a-tag>
              </a-descriptions-item>
            </a-descriptions>
          </a-card>
        </a-col>

        <a-col :xs="24" :lg="12">
          <a-card title="修改密码" class="profile-card">
            <a-form
              :model="passwordForm"
              :rules="passwordRules"
              layout="vertical"
              @finish="handlePasswordChange"
            >
              <a-form-item label="当前密码" name="current_password" required>
                <a-input-password
                  v-model:value="passwordForm.current_password"
                  placeholder="请输入当前密码"
                />
              </a-form-item>

              <a-form-item label="新密码" name="new_password" required>
                <a-input-password
                  v-model:value="passwordForm.new_password"
                  placeholder="请输入新密码"
                />
              </a-form-item>

              <a-form-item label="确认新密码" name="confirm_password" required>
                <a-input-password
                  v-model:value="passwordForm.confirm_password"
                  placeholder="请再次输入新密码"
                />
              </a-form-item>

              <a-form-item>
                <a-button type="primary" html-type="submit" :loading="loading">
                  修改密码
                </a-button>
              </a-form-item>
            </a-form>
          </a-card>
        </a-col>
      </a-row>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import type { Rule } from 'ant-design-vue/es/form'
import AppLayout from '@/components/layout/AppLayout.vue'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api/auth'

const authStore = useAuthStore()
const loading = ref(false)

interface PasswordForm {
  current_password: string
  new_password: string
  confirm_password: string
}

const passwordForm = reactive<PasswordForm>({
  current_password: '',
  new_password: '',
  confirm_password: ''
})

const validateConfirmPassword = (_rule: Rule, value: string) => {
  if (value && value !== passwordForm.new_password) {
    return Promise.reject('两次输入的密码不一致')
  }
  return Promise.resolve()
}

const passwordRules: Record<string, Rule[]> = {
  current_password: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, message: '密码至少需要8个字符', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const handlePasswordChange = async () => {
  try {
    loading.value = true
    await authApi.changePassword({
      current_password: passwordForm.current_password,
      new_password: passwordForm.new_password
    })
    message.success('密码修改成功')
    passwordForm.current_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm_password = ''
  } catch (error) {
    message.error('修改密码失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.profile-view {
  padding: 24px;
}

.profile-card {
  margin-bottom: 24px;
}
</style>
