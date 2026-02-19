import { create } from 'zustand'
import { SystemStatus, Statistics, SystemConfig } from '../api/system'

interface SystemState {
  status: SystemStatus | null
  statistics: Statistics | null
  config: SystemConfig | null
  isLoading: boolean
  error: string | null

  setStatus: (status: SystemStatus) => void
  setStatistics: (statistics: Statistics) => void
  setConfig: (config: SystemConfig) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  clearAll: () => void
}

export const useSystemStore = create<SystemState>((set) => ({
  status: null,
  statistics: null,
  config: null,
  isLoading: false,
  error: null,

  setStatus: (status) => set({ status }),
  setStatistics: (statistics) => set({ statistics }),
  setConfig: (config) => set({ config }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
  clearAll: () =>
    set({
      status: null,
      statistics: null,
      config: null,
      error: null,
    }),
}))
