import apiClient from './client'

export interface Document {
  id: string
  title: string
  doc_type: string
  file_size: number
  status: string
  chunk_count: number
  entity_count: number
  created_at: string
  updated_at: string
}

export interface DocumentQueryParams {
  pageNum?: number
  pageSize?: number
  status?: string
  doc_type?: string
  keyword?: string
}

export interface DocumentUploadResponse {
  id: string
  title: string
  status: string
}

export interface DocumentProgress {
  id: string
  status: string
  progress: number
  message: string
}

export const documentApi = {
  async list(params?: DocumentQueryParams): Promise<{ list: Document[]; total: number }> {
    const response = await apiClient.post<{ list: Document[]; total: number }>(
      '/documents/list',
      params
    )
    return response
  },

  async get(id: string): Promise<Document> {
    return apiClient.get<Document>(`/documents/${id}`)
  },

  async upload(file: File, metadata?: Record<string, unknown>): Promise<DocumentUploadResponse> {
    const formData = new FormData()
    formData.append('file', file)
    if (metadata) {
      formData.append('metadata', JSON.stringify(metadata))
    }

    const token = localStorage.getItem('token')
    const headers: Record<string, string> = {}
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    const response = await fetch('/api/v1/documents/upload', {
      method: 'POST',
      headers,
      body: formData,
    })

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.status}`)
    }

    const result = await response.json()
    return result.data
  },

  async delete(id: string): Promise<void> {
    await apiClient.delete(`/documents/${id}`)
  },

  async batchDelete(ids: string[]): Promise<void> {
    await apiClient.post('/documents/batch-delete', { ids })
  },

  async reprocess(id: string): Promise<void> {
    await apiClient.post(`/documents/${id}/reprocess`)
  },

  async getProgress(id: string): Promise<DocumentProgress> {
    return apiClient.get<DocumentProgress>(`/documents/${id}/progress`)
  },

  async download(id: string): Promise<Blob> {
    const token = localStorage.getItem('token')
    const headers: Record<string, string> = {}
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    const response = await fetch(`/api/v1/documents/${id}/download`, { headers })
    if (!response.ok) {
      throw new Error(`Download failed: ${response.status}`)
    }
    return response.blob()
  },
}

export default documentApi
