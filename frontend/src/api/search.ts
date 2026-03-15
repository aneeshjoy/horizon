import apiClient from './client'
import type { VehicleListItem } from './types'

export const searchApi = {
  // Search vehicles
  search: async (query: string, limit = 10) => {
    const response = await apiClient.get<VehicleListItem[]>('/search', {
      params: { q: query, limit },
    })
    return response.data
  },
}
