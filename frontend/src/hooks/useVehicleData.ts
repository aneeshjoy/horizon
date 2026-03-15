import { useQuery } from '@tanstack/react-query'
import { vehiclesApi } from '../api/vehicles'
import type { VehicleSummary, PatternGrid } from '../api/types'

export function useVehicleSummary(plate: string, fuzzy = false) {
  return useQuery({
    queryKey: ['vehicle', 'summary', plate, fuzzy],
    queryFn: () => vehiclesApi.getSummary(plate, fuzzy),
    enabled: !!plate,
  })
}

export function useVehicleGrid(plate: string, fuzzy = false) {
  return useQuery({
    queryKey: ['vehicle', 'grid', plate, fuzzy],
    queryFn: () => vehiclesApi.getGrid(plate, fuzzy),
    enabled: !!plate,
  })
}

export function useVehicleList(params?: {
  limit?: number
  offset?: number
  classification?: string
  sort_by?: string
}) {
  return useQuery({
    queryKey: ['vehicles', 'list', params],
    queryFn: () => vehiclesApi.list(params),
  })
}
