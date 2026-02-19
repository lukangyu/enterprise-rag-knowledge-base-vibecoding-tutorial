import { create } from 'zustand'
import { ChatMessage, SourceReference } from '../api/chat'

interface ChatState {
  messages: ChatMessage[]
  sources: SourceReference[]
  isLoading: boolean
  isStreaming: boolean
  conversationId: string | null
  error: string | null

  addMessage: (message: ChatMessage) => void
  updateLastMessage: (content: string) => void
  setSources: (sources: SourceReference[]) => void
  setLoading: (loading: boolean) => void
  setStreaming: (streaming: boolean) => void
  setConversationId: (id: string) => void
  setError: (error: string | null) => void
  clearMessages: () => void
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  sources: [],
  isLoading: false,
  isStreaming: false,
  conversationId: null,
  error: null,

  addMessage: (message) =>
    set((state) => ({
      messages: [...state.messages, message],
    })),

  updateLastMessage: (content) =>
    set((state) => {
      const messages = [...state.messages]
      if (messages.length > 0) {
        messages[messages.length - 1] = {
          ...messages[messages.length - 1],
          content,
        }
      }
      return { messages }
    }),

  setSources: (sources) => set({ sources }),

  setLoading: (loading) => set({ isLoading: loading }),

  setStreaming: (streaming) => set({ isStreaming: streaming }),

  setConversationId: (id) => set({ conversationId: id }),

  setError: (error) => set({ error }),

  clearMessages: () =>
    set({
      messages: [],
      sources: [],
      conversationId: null,
      error: null,
    }),
}))
