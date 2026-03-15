import apiClient from './client'
import type { ImportStatus } from './types'

export interface DatabaseCheckResult {
  exists: boolean
  size_mb?: number
  tables?: string[]
  event_count?: number
  schema_type?: string
  error?: string
}

export interface ImportStartResponse {
  job_id: string
  message: string
  db_path: string
}

export const importApi = {
  /**
   * Get status of the most recent import job
   */
  getStatus: async (): Promise<ImportStatus> => {
    const response = await apiClient.get<ImportStatus>('/import/status')
    return response.data
  },

  /**
   * Get status of a specific import job
   */
  getJobStatus: async (jobId: string): Promise<ImportStatus> => {
    const response = await apiClient.get<ImportStatus>(`/import/status/${jobId}`)
    return response.data
  },

  /**
   * Start import using configuration settings
   */
  startImport: async (): Promise<ImportStartResponse> => {
    const response = await apiClient.post<ImportStartResponse>('/import/start')
    return response.data
  },

  /**
   * Start manual import with custom parameters
   */
  startManualImport: async (dbPath: string, afterDate?: string, autoRebuild?: boolean): Promise<ImportStartResponse> => {
    const response = await apiClient.post<ImportStartResponse>('/import/start/manual', null, {
      params: { db_path: dbPath, after_date: afterDate, auto_rebuild: autoRebuild }
    })
    return response.data
  },

  /**
   * Cancel the currently running import job
   */
  cancelImport: async (): Promise<{ message: string; job_id?: string }> => {
    const response = await apiClient.post<{ message: string; job_id?: string }>('/import/cancel')
    return response.data
  },

  /**
   * Check if a database file exists and contains license plate data
   */
  checkDatabase: async (dbPath: string): Promise<DatabaseCheckResult> => {
    const response = await apiClient.get<DatabaseCheckResult>('/import/check', {
      params: { db_path: dbPath }
    })
    return response.data
  }
}
