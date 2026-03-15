import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { configApi } from '@/api/config'
import type { SystemConfig, ConfigValidationResult, ReprocessStatus } from '@/api/types'
import { DEFAULT_REPROCESS_STATUS } from '@/api/types'

export function useConfiguration() {
  const queryClient = useQueryClient()

  // Load current configuration
  const { data: config, isLoading } = useQuery({
    queryKey: ['config'],
    queryFn: configApi.getConfig,
  })

  // Save configuration
  const saveMutation = useMutation({
    mutationFn: async ({ newConfig, reprocess }: { newConfig: SystemConfig; reprocess?: boolean }) => {
      return configApi.updateConfig(newConfig, reprocess || false)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['config'] })
    },
  })

  // Validate configuration
  const validateMutation = useMutation({
    mutationFn: configApi.validateConfig,
  })

  // Reset to defaults
  const resetMutation = useMutation({
    mutationFn: configApi.resetConfig,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['config'] })
    },
  })

  return {
    config,
    isLoading,
    saveConfig: saveMutation.mutateAsync,
    isSaving: saveMutation.isPending,
    validateConfig: validateMutation.mutateAsync,
    isValidating: validateMutation.isPending,
    resetConfig: resetMutation.mutateAsync,
    isResetting: resetMutation.isPending,
  }
}

export function useReprocess() {
  const queryClient = useQueryClient()

  // Get reprocess status
  const { data: status, isLoading } = useQuery({
    queryKey: ['reprocess-status'],
    queryFn: configApi.getReprocessStatus,
    refetchInterval: (query) => query.state.data?.status === 'running' ? 2000 : false,
  })

  // Start reprocessing
  const startMutation = useMutation({
    mutationFn: configApi.startReprocess,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reprocess-status'] })
    },
  })

  // Cancel reprocessing
  const cancelMutation = useMutation({
    mutationFn: configApi.cancelReprocess,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reprocess-status'] })
    },
  })

  // Clear reprocess status (close modal)
  const clearReprocessStatus = () => {
    queryClient.setQueryData(['reprocess-status'], DEFAULT_REPROCESS_STATUS)
  }

  return {
    status,
    isLoading,
    startReprocess: startMutation.mutate,
    isStarting: startMutation.isPending,
    cancelReprocess: cancelMutation.mutate,
    isCancelling: cancelMutation.isPending,
    clearReprocessStatus,
  }
}
