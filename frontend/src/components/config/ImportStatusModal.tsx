import { X, Loader2, CheckCircle, XCircle, AlertCircle, Database } from 'lucide-react'
import type { ImportStatus } from '@/api/types'

interface ImportStatusModalProps {
  status: ImportStatus
  onCancel: () => void
  onClose: () => void
}

export function ImportStatusModal({ status, onCancel, onClose }: ImportStatusModalProps) {
  const getStatusIcon = () => {
    switch (status.status) {
      case 'running':
        return <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
      case 'completed':
        return <CheckCircle className="h-6 w-6 text-green-600" />
      case 'failed':
        return <XCircle className="h-6 w-6 text-red-600" />
      case 'cancelled':
        return <AlertCircle className="h-6 w-6 text-yellow-600" />
      default:
        return <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
    }
  }

  const getStatusText = () => {
    switch (status.status) {
      case 'running':
        return 'Importing...'
      case 'completed':
        return 'Completed'
      case 'failed':
        return 'Failed'
      case 'cancelled':
        return 'Cancelled'
      default:
        return 'Importing...'
    }
  }

  const formatDuration = () => {
    if (!status.started_at) return '-'

    const start = new Date(status.started_at).getTime()
    const end = status.completed_at ? new Date(status.completed_at).getTime() : Date.now()
    const seconds = Math.round((end - start) / 1000)

    if (seconds < 60) return `${seconds}s`
    return `${Math.floor(seconds / 60)}m ${seconds % 60}s`
  }

  const progressPercent = Math.round(status.progress * 100)

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-md rounded-lg border bg-background shadow-lg">
        {/* Header */}
        <div className="flex items-center justify-between border-b p-4">
          <div className="flex items-center gap-3">
            <div className="rounded-full p-2 bg-blue-500/10">
              <Database className="h-5 w-5 text-blue-500" />
            </div>
            <div>
              <h3 className="font-semibold">Frigate Database Import</h3>
              <p className="text-sm font-medium text-blue-600">{getStatusText()}</p>
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
              {/* Database info */}
              <div className="mb-4 rounded-lg bg-muted/50 p-3 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Database:</span>
                  <span className="font-medium">{status.db_path.split('/').pop()}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Size:</span>
                  <span className="font-medium">{status.db_size_mb.toFixed(2)} MB</span>
                </div>
              </div>

              {/* Progress bar */}
              <div className="mb-6">
                <div className="mb-2 flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Processing events</span>
                  <span className="font-medium">{progressPercent}%</span>
                </div>
                <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
                  <div
                    className="h-full bg-blue-600 transition-all duration-300"
                    style={{ width: `${progressPercent}%` }}
                  />
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-2 gap-4 text-center">
                <div className="rounded-lg bg-muted/50 p-4">
                  <div className="text-2xl font-bold">{status.processed_events}</div>
                  <div className="text-xs text-muted-foreground">
                    of {status.total_events} events
                  </div>
                </div>
                <div className="rounded-lg bg-muted/50 p-4">
                  <div className="text-2xl font-bold">{status.plates_created}</div>
                  <div className="text-xs text-muted-foreground">unique plates</div>
                </div>
              </div>

              {status.filtered_events > 0 && (
                <div className="mt-4 text-center text-xs text-muted-foreground">
                  {status.filtered_events} events filtered (low confidence)
                </div>
              )}
            </>
          )}

          {status.status === 'completed' && (
            <div className="text-center">
              <CheckCircle className="mx-auto mb-4 h-12 w-12 text-green-600" />
              <h3 className="text-lg font-semibold mb-2">Import Complete!</h3>
              <p className="text-muted-foreground mb-4">
                Successfully imported {status.processed_events} events from Frigate database.
                {status.filtered_events > 0 && ` ${status.filtered_events} events were filtered due to low confidence.`}
              </p>
              <div className="rounded-lg bg-muted/50 p-4 text-left">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Events processed:</span>
                    <span className="ml-auto font-medium">{status.processed_events}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Unique plates:</span>
                    <span className="ml-auto font-medium">{status.plates_created}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Filtered:</span>
                    <span className="ml-auto font-medium">{status.filtered_events}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Duration:</span>
                    <span className="ml-auto font-medium">{formatDuration()}</span>
                  </div>
                </div>
              </div>

              {status.rebuild_triggered && (
                <div className="mt-4 rounded-md bg-green-500/10 border border-green-500/20 p-3">
                  <p className="text-sm text-green-600 dark:text-green-400">
                    ✓ Profile rebuild triggered automatically
                  </p>
                </div>
              )}

              <p className="text-xs text-muted-foreground mt-4">
                Events have been written to <code className="bg-muted px-1 py-0.5 rounded">frigate_events.jsonl</code>.
                {status.rebuild_triggered
                  ? ' Vehicle profiles are being rebuilt in the background.'
                  : ' Use "Rebuild Profiles" to generate vehicle patterns from the imported events.'}
              </p>
            </div>
          )}

          {status.status === 'failed' && (
            <div className="text-center">
              <XCircle className="mx-auto mb-4 h-12 w-12 text-red-600" />
              <h3 className="text-lg font-semibold mb-2">Import Failed</h3>
              <p className="text-muted-foreground">
                {status.error_message || 'An error occurred during import. Please check the database path and try again.'}
              </p>
            </div>
          )}

          {status.status === 'cancelled' && (
            <div className="text-center">
              <AlertCircle className="mx-auto mb-4 h-12 w-12 text-yellow-600" />
              <h3 className="text-lg font-semibold mb-2">Import Cancelled</h3>
              <p className="text-muted-foreground">
                {status.processed_events} events were processed before cancellation.
                {status.processed_events > 0 && ' These events are preserved in the events file.'}
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
              Cancel Import
            </button>
          </div>
        )}

        {(status.status === 'completed' || status.status === 'failed' || status.status === 'cancelled') && (
          <div className="border-t p-4 flex gap-3">
            <button
              onClick={onClose}
              className="flex-1 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
            >
              Close
            </button>
            {status.status === 'completed' && (
              <button
                onClick={() => {
                  // Trigger rebuild after successful import
                  window.dispatchEvent(new CustomEvent('rebuild-after-import'))
                }}
                className="flex-1 rounded-md border border-orange-500/50 px-4 py-2 text-sm font-medium text-orange-600 hover:bg-orange-500/10"
              >
                Rebuild Profiles
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
