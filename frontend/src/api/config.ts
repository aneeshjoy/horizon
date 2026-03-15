import apiClient from './client'
import type {
  SystemConfig,
  ConfigValidationResult,
  ReprocessStatus,
} from './types'

export const configApi = {
  // Get configuration
  getConfig: async () => {
    const response = await apiClient.get<SystemConfig>('/config')
    return response.data
  },

  // Update configuration
  updateConfig: async (config: SystemConfig, reprocess = false) => {
    const response = await apiClient.put<SystemConfig>('/config', config, {
      params: { reprocess },
    })
    return response.data
  },

  // Validate configuration
  validateConfig: async (config: SystemConfig) => {
    const response = await apiClient.post<ConfigValidationResult>(
      '/config/validate',
      config
    )
    return response.data
  },

  // Reset configuration
  resetConfig: async () => {
    const response = await apiClient.post<SystemConfig>('/config/reset')
    return response.data
  },

  // Get reprocess status
  getReprocessStatus: async () => {
    const response = await apiClient.get<ReprocessStatus>('/config/reprocess/status')
    return response.data
  },

  // Start reprocessing
  startReprocess: async () => {
    const response = await apiClient.post<{ job_id: string; message: string }>(
      '/config/reprocess/start'
    )
    return response.data
  },

  // Cancel reprocessing
  cancelReprocess: async () => {
    const response = await apiClient.post<{ message: string; job_id?: string }>(
      '/config/reprocess/cancel'
    )
    return response.data
  },
}
