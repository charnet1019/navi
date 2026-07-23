import { defineStore } from 'pinia'
import { ref } from 'vue'
import { auditLogsApi, type AuditLogListParams } from '@/api/auditLogs'
import { withLoading } from '@/utils/withLoading'
import type { AuditLog } from '@/types'

export const useAuditLogsStore = defineStore('auditLogs', () => {
  const logs = ref<AuditLog[]>([])
  const total = ref(0)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchLogs(params?: AuditLogListParams): Promise<void> {
    await withLoading(loading, error, 'Failed to fetch audit logs', async () => {
      const result = await auditLogsApi.list(params)
      logs.value = result.logs
      total.value = result.total
    })
  }

  return {
    logs,
    total,
    loading,
    error,
    fetchLogs
  }
})
