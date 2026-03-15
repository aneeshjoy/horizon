import { X, Loader2, CheckCircle, XCircle, AlertCircle } from 'lucide-react'
import type { ReprocessStatus } from '@/api/types'

interface ReprocessStatusModalProps {
  status: ReprocessStatus
  onCancel: () => void
  onClose: () => void
  mode?: 'reprocess' | 'rebuild'
}

export function ReprocessStatusModal({ status, onCancel, onClose, mode = 'rebuild' }: ReprocessStatusModalProps) {
  const isRebuild = mode === 'rebuild'
  const itemLabel = isRebuild ? 'events' : 'vehicles'
  const titleLabel = isRebuild ? 'Rebuilding Profiles' : 'Reprocessing Vehicle Profiles'
  const getStatusIcon = () => {
    switch (status.status) {
      case 'running':
        return <Loader2 className="h-6 w-6 animate-spin" />
      case 'completed':
        return <CheckCircle className="h-6 w-6" />
      case 'failed':
        return <XCircle className="h-6 w-6" />
      case 'cancelled':
        return <AlertCircle className="h-6 w-6" />
      default:
        return <Loader2 className="h-6 w-6 animate-spin" />
    }
  }

  const getStatusText = () => {
    switch (status.status) {
      case 'running':
        return 'Processing...'
      case 'completed':
        return 'Completed'
      case 'failed':
        return 'Failed'
      case 'cancelled':
        return 'Cancelled'
      default:
        return 'Processing...'
    }
  }

  const getStatusColor = () => {
    switch (status.status) {
      case 'running':
        return 'text-blue-600'
      case 'completed':
        return 'text-green-600'
      case 'failed':
        return 'text-red-600'
      case 'cancelled':
        return 'text-yellow-600'
      default:
        return 'text-blue-600'
    }
  }

  const progressPercent = Math.round(status.progress * 100)

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-md rounded-lg border bg-background shadow-lg">
        {/* Header */}
        <div className="flex items-center justify-between border-b p-4">
          <div className="flex items-center gap-3">
            {getStatusIcon()}
            <div>
              <h3 className="font-semibold">{titleLabel}</h3>
              <p className={`text-sm font-medium ${getStatusColor()}`}>{getStatusText()}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded p-1 hover:bg-muted"
            disabled={status.status === 'running'}
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {status.status === 'running' && (
            <>
              {/* Progress bar */}
              <div className="mb-6">
                <div className="mb-2 flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Processing {itemLabel}</span>
                  <span className="font-medium">{progressPercent}%</span>
                </div>
                <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
                  <div
                    className="h-full bg-primary transition-all duration-300"
                    style={{ width: `${progressPercent}%` }}
                  />
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-2 gap-4 text-center">
                <div className="rounded-lg bg-muted/50 p-4">
                  <div className="text-2xl font-bold">{status.processed_vehicles}</div>
                  <div className="text-xs text-muted-foreground">
                    {isRebuild ? 'events processed' : `of ${status.total_vehicles} ${itemLabel}`}
                  </div>
                </div>
                <div className="rounded-lg bg-muted/50 p-4">
                  <div className="text-2xl font-bold">
                    {status.total_vehicles - status.processed_vehicles}
                  </div>
                  <div className="text-xs text-muted-foreground">remaining</div>
                </div>
              </div>
            </>
          )}

          {status.status === 'completed' && (
            <div className="text-center">
              <CheckCircle className="mx-auto mb-4 h-12 w-12 text-green-600" />
              <h3 className="text-lg font-semibold mb-2">{isRebuild ? 'Rebuild Complete!' : 'Reprocessing Complete!'}</h3>
              <p className="text-muted-foreground mb-4">
                {isRebuild
                  ? `Successfully processed ${status.processed_vehicles} events and rebuilt all profiles`
                  : `Successfully processed ${status.total_vehicles} vehicle profiles with new configuration`}
              </p>
              <div className="rounded-lg bg-muted/50 p-4 text-left">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">{isRebuild ? 'Events processed:' : 'Total vehicles:'}</span>
                    <span className="ml-auto font-medium">{isRebuild ? status.processed_vehicles : status.total_vehicles}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Duration:</span>
                    <span className="ml-auto font-medium">
                      {status.started_at && status.completed_at
                        ? `${Math.round((new Date(status.completed_at).getTime() - new Date(status.started_at).getTime()) / 1000)}s`
                        : '-'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {status.status === 'failed' && (
            <div className="text-center">
              <XCircle className="mx-auto mb-4 h-12 w-12 text-red-600" />
              <h3 className="text-lg font-semibold mb-2">Reprocessing Failed</h3>
              <p className="text-muted-foreground">
                {status.error_message || 'An error occurred during reprocessing'}
              </p>
            </div>
          )}

          {status.status === 'cancelled' && (
            <div className="text-center">
              <AlertCircle className="mx-auto mb-4 h-12 w-12 text-yellow-600" />
              <h3 className="text-lg font-semibold mb-2">{isRebuild ? 'Rebuild Cancelled' : 'Reprocessing Cancelled'}</h3>
              <p className="text-muted-foreground">
                {isRebuild
                  ? `${status.processed_vehicles} events were processed before cancellation`
                  : `${status.processed_vehicles} of ${status.total_vehicles} ${itemLabel} were processed before cancellation`}
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        {status.status === 'running' && (
          <div className="border-t p-4">
            <button
              onClick={onCancel}
              className="w-full rounded-md border px-4 py-2 text-sm font-medium hover:bg-muted"
            >
              Cancel {isRebuild ? 'Rebuild' : 'Reprocessing'}
            </button>
          </div>
        )}

        {(status.status === 'completed' || status.status === 'failed' || status.status === 'cancelled') && (
          <div className="border-t p-4">
            <button
              onClick={onClose}
              className="w-full rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
            >
              Close
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
