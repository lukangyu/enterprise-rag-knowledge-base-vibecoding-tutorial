import apiClient from './client'

export interface HybridSearchRequest {
  query: string
  top_k?: number
  keyword_enabled?: boolean
  vector_enabled?: boolean
  filters?: Record<string, unknown>
  keyword_top_k?: number
  vector_top_k?: number
  rrf_k?: number
}

export interface SearchResult {
  doc_id: string
  chunk_id?: string
  content?: string
  score: number
  rank: number
  source: string
  metadata?: Record<string, unknown>
}

export interface HybridSearchResponse {
  results: SearchResult[]
  keyword_time_ms: number
  vector_time_ms: number
  fusion_time_ms: number
  total_time_ms: number
  keyword_result_count: number
  vector_result_count: number
  final_result_count: number
}

export interface KeywordSearchResponse {
  results: SearchResult[]
  time_ms: number
  count: number
}

export interface VectorSearchResponse {
  results: SearchResult[]
  time_ms: number
  count: number
}

export const searchApi = {
  async hybridSearch(request: HybridSearchRequest): Promise<HybridSearchResponse> {
    return apiClient.post<HybridSearchResponse>('/search/hybrid', request)
  },

  async keywordSearch(query: string, topK: number = 20): Promise<KeywordSearchResponse> {
    return apiClient.get<KeywordSearchResponse>('/search/keyword', { query, top_k: topK })
  },

  async vectorSearch(query: string, topK: number = 20): Promise<VectorSearchResponse> {
    return apiClient.post<VectorSearchResponse>('/search/vector', null, {
      params: { query, top_k: topK }
    })
  },

  async healthCheck(): Promise<{
    elasticsearch: { status: string; cluster_name?: string }
    milvus: { status: string }
  }> {
    return apiClient.get('/search/health')
  },
}

export default searchApi
