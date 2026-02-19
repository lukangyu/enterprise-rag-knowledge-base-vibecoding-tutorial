import apiClient from './client'

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp?: string
}

export interface SourceReference {
  source_id: string
  doc_id: string
  chunk_id?: string
  content: string
  score: number
  metadata?: Record<string, unknown>
}

export interface ChatRequest {
  query: string
  conversation_id?: string
  history?: ChatMessage[]
  top_k?: number
  use_graph?: boolean
  use_rerank?: boolean
  stream?: boolean
  filters?: Record<string, unknown>
}

export interface ChatResponse {
  answer: string
  sources: SourceReference[]
  conversation_id: string
  query: string
  latency_ms: number
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export const chatApi = {
  async chat(request: ChatRequest): Promise<ChatResponse> {
    return apiClient.post<ChatResponse>('/qa/chat', {
      ...request,
      stream: false,
    })
  },

  chatStream(request: ChatRequest, token?: string): EventSource {
    const url = `${API_BASE_URL}/qa/chat/stream`
    const eventSource = new EventSource(url, {
      withCredentials: true,
    })
    return eventSource
  },

  async chatStreamPost(
    request: ChatRequest,
    onMessage: (data: unknown) => void,
    onError: (error: Error) => void,
    onComplete: () => void,
    token?: string
  ): Promise<void> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    const response = await fetch(`${API_BASE_URL}/qa/chat/stream`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        ...request,
        stream: true,
      }),
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const reader = response.body?.getReader()
    const decoder = new TextDecoder()

    if (!reader) {
      throw new Error('No reader available')
    }

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data.trim()) {
              try {
                const parsed = JSON.parse(data)
                onMessage(parsed)
              } catch {
                console.warn('Failed to parse SSE data:', data)
              }
            }
          }
        }
      }
    } catch (error) {
      onError(error as Error)
    } finally {
      onComplete()
    }
  },

  async simpleChat(query: string, stream: boolean = true): Promise<Response> {
    const token = localStorage.getItem('token')
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    const response = await fetch(`${API_BASE_URL}/qa/simple`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ query, stream }),
    })
    return response
  },
}

export default chatApi
