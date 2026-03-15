import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { importApi } from '@/api/import'
import type { ImportStatus } from '@/api/types'

export const DEFAULT_IMPORT_STATUS: ImportStatus = {
  job_id: '',
  status: 'none',
  progress: 0,
  total_events: 0,
  processed_events: 0,
  filtered_events: 0,
  plates_created: 0,
  started_at: null,
  completed_at: null,
  error_message: null,
  db_path: '',
  db_size_mb: 0,
  rebuild_triggered: false
}

export function useImport() {
  const queryClient = useQueryClient()

  // Get import status
  const { data: status, isLoading } = useQuery({
    queryKey: ['import-status'],
    queryFn: importApi.getStatus,
    refetchInterval: (query) => {
      const data = query.state.data as ImportStatus | undefined
      // Poll every 2 seconds when running, otherwise no refresh
      return data?.status === 'running' ? 2000 : false
    }
  })

  // Start import
  const startMutation = useMutation({
    mutationFn: importApi.startImport,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['import-status'] })
    }
  })

  // Start manual import
  const startManualMutation = useMutation({
    mutationFn: ({ dbPath, afterDate }: { dbPath: string; afterDate?: string }) =>
      importApi.startManualImport(dbPath, afterDate),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['import-status'] })
    }
  })

  // Cancel import
  const cancelMutation = useMutation({
    mutationFn: importApi.cancelImport,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['import-status'] })
    }
  })

  // Clear import status (close modal)
  const clearImportStatus = () => {
    queryClient.setQueryData(['import-status'], DEFAULT_IMPORT_STATUS)
  }

  return {
    status,
    isLoading,
    startImport: startMutation.mutate,
    isStarting: startMutation.isPending,
    startManualImport: startManualMutation.mutate,
    isStartingManual: startManualMutation.isPending,
    cancelImport: cancelMutation.mutate,
    isCancelling: cancelMutation.isPending,
    clearImportStatus
  }
}
