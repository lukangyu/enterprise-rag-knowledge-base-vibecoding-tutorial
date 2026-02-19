import apiClient from './client'

export interface SystemConfig {
  general: {
    site_name: string
    site_description: string
    max_upload_size: number
    supported_formats: string[]
  }
  search: {
    default_top_k: number
    max_top_k: number
    default_threshold: number
    enable_hybrid_search: boolean
  }
  llm: {
    default_model: string
    max_tokens: number
    default_temperature: number
  }
  kg: {
    default_max_hops: number
    default_min_confidence: number
    enable_auto_extraction: boolean
  }
}

export interface ComponentStatus {
  name: string
  status: string
  latency_ms?: number
  message?: string
}

export interface SystemStatus {
  status: string
  version: string
  uptime: string
  components: ComponentStatus[]
  resources: {
    cpu_usage: number
    memory_usage: number
    disk_usage: number
    gpu_usage?: number
  }
  statistics: {
    total_documents: number
    total_chunks: number
    total_entities: number
    total_relations: number
    total_users: number
    queries_today: number
  }
}

export interface Statistics {
  period: string
  document_stats: {
    total: number
    new_this_period: number
    by_type: Record<string, number>
    by_status: Record<string, number>
  }
  query_stats: {
    total_queries: number
    avg_response_time_ms: number
    avg_satisfaction: number
    by_day: Array<{ date: string; count: number }>
  }
  kg_stats: {
    total_entities: number
    total_relations: number
    entity_types: Record<string, number>
    relation_types: Record<string, number>
  }
  user_stats: {
    total_users: number
    active_users: number
    new_users_this_period: number
  }
}

export interface AuditLog {
  id: string
  user_id: string
  username: string
  action: string
  resource_type: string
  resource_id?: string
  details?: Record<string, unknown>
  ip_address: string
  status: string
  created_at: string
}

export const systemApi = {
  async getConfig(): Promise<SystemConfig> {
    return apiClient.get<SystemConfig>('/system/config')
  },

  async updateConfig(config: Partial<SystemConfig>): Promise<void> {
    await apiClient.put('/system/config', config)
  },

  async getStatus(): Promise<SystemStatus> {
    return apiClient.get<SystemStatus>('/system/status')
  },

  async getStatistics(period: string = '7d'): Promise<Statistics> {
    return apiClient.get<Statistics>(`/system/statistics?period=${period}`)
  },

  async getAuditLogs(params: {
    page?: number
    size?: number
    action?: string
    user_id?: string
  }): Promise<{ items: AuditLog[]; total: number }> {
    const response = await apiClient.get<{ items: AuditLog[]; pagination: { total: number } }>(
      '/system/audit-logs',
      params
    )
    return {
      items: response.items,
      total: response.pagination.total,
    }
  },

  async healthCheck(): Promise<{ status: string }> {
    return apiClient.get<{ status: string }>('/system/health')
  },
}

export default systemApi
