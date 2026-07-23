import apiClient from './client'
import type { AuditLog } from '@/types'

export interface AuditLogListParams {
  skip?: number
  limit?: number
  action?: string
  resource_type?: string
  user_id?: string
  start_time?: string
  end_time?: string
}

export const auditLogsApi = {
  async list(params?: AuditLogListParams): Promise<{ logs: AuditLog[]; total: number }> {
    const response = await apiClient.get<AuditLog[]>('/audit-logs/', { params })
    const totalHeader = response.headers['x-total-count']
    const total = totalHeader !== undefined ? Number(totalHeader) : response.data.length
    return { logs: response.data, total }
  }
}
