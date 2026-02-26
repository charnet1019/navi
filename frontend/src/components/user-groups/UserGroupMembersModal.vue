<template>
  <a-modal
    :open="open"
    :title="`管理成员 - ${group?.name || ''}`"
    :width="800"
    :footer="null"
    @cancel="handleCancel"
  >
    <div class="members-modal">
      <div class="add-member-section">
        <a-typography-title :level="5">添加成员</a-typography-title>
        <a-space>
          <a-select
            v-model:value="selectedUserId"
            placeholder="请选择用户"
            style="width: 300px"
            show-search
            :filter-option="filterOption"
          >
            <a-select-option
              v-for="user in availableUsers"
              :key="user.id"
              :value="user.id"
            >
              {{ user.username }} ({{ user.email }})
            </a-select-option>
          </a-select>
          <a-button
            type="primary"
            :loading="loading"
            :disabled="!selectedUserId"
            @click="handleAddMember"
          >
            添加
          </a-button>
        </a-space>
      </div>

      <a-divider />

      <div class="members-list-section">
        <a-typography-title :level="5">当前成员</a-typography-title>
        <a-list
          :data-source="members"
          :loading="loading"
        >
          <template #renderItem="{ item }">
            <a-list-item>
              <template #actions>
                <a-button
                  type="link"
                  danger
                  size="small"
                  @click="handleRemoveMember(item)"
                >
                  移除
                </a-button>
              </template>
              <a-list-item-meta
                :title="item.username"
                :description="item.email"
              >
                <template #avatar>
                  <a-avatar>{{ item.username.charAt(0).toUpperCase() }}</a-avatar>
                </template>
              </a-list-item-meta>
            </a-list-item>
          </template>
        </a-list>
      </div>
    </div>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { UserGroup, UserGroupMember, User } from '@/types'

interface Props {
  open: boolean
  group: UserGroup | null
  members: UserGroupMember[]
  allUsers: User[]
  loading?: boolean
}

interface Emits {
  (e: 'addMember', userId: string): void
  (e: 'removeMember', userId: string): void
  (e: 'cancel'): void
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const emit = defineEmits<Emits>()

const selectedUserId = ref<string | undefined>(undefined)

const availableUsers = computed(() => {
  const memberIds = new Set(props.members.map(m => m.id))
  return props.allUsers.filter(u => !memberIds.has(u.id.toString()))
})

const filterOption = (input: string, option: any) => {
  const text = option.children?.[0]?.children || ''
  return text.toLowerCase().includes(input.toLowerCase())
}

const handleAddMember = () => {
  if (selectedUserId.value) {
    emit('addMember', selectedUserId.value)
    selectedUserId.value = undefined
  }
}

const handleRemoveMember = (member: UserGroupMember) => {
  emit('removeMember', member.id)
}

const handleCancel = () => {
  selectedUserId.value = undefined
  emit('cancel')
}
</script>

<style scoped>
.members-modal {
  padding: 16px 0;
}

.add-member-section {
  margin-bottom: 16px;
}

.members-list-section {
  margin-top: 16px;
}
</style>
