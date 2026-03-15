import apiClient from './client'
import type {
  VehicleSummary,
  VehicleListItem,
  PatternGrid,
} from './types'

export const vehiclesApi = {
  // Get vehicle summary
  getSummary: async (plate: string, fuzzy = false) => {
    const response = await apiClient.get<VehicleSummary>(`/vehicles/${plate}`, {
      params: { fuzzy },
    })
    return response.data
  },

  // Get pattern grid
  getGrid: async (plate: string, fuzzy = false) => {
    const response = await apiClient.get<PatternGrid>(`/vehicles/${plate}/grid`, {
      params: { fuzzy },
    })
    return response.data
  },

  // List vehicles
  list: async (params?: {
    limit?: number
    offset?: number
    classification?: string
    sort_by?: string
  }) => {
    const response = await apiClient.get<VehicleListItem[]>('/vehicles', { params })
    return response.data
  },
}
