import { CheckCircle2, AlertTriangle, XCircle } from 'lucide-react'

interface ConfigValidationPanelProps {
  validationResult: {
    errors: string[]
    warnings: string[]
  } | null
  isValidating: boolean
}

export function ConfigValidationPanel({ validationResult, isValidating }: ConfigValidationPanelProps) {
  if (isValidating) {
    return (
      <div className="mb-6 rounded-lg border bg-blue-50 dark:bg-blue-950/20 p-4">
        <div className="flex items-center gap-3">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
          <div>
            <p className="font-medium text-blue-700 dark:text-blue-300">Validating configuration...</p>
            <p className="text-sm text-blue-600 dark:text-blue-400">Please wait</p>
          </div>
        </div>
      </div>
    )
  }

  if (!validationResult) {
    return null
  }

  const { errors, warnings } = validationResult

  if (errors.length === 0 && warnings.length === 0) {
    return (
      <div className="mb-6 rounded-lg border bg-green-50 dark:bg-green-950/20 p-4">
        <div className="flex items-center gap-3">
          <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400" />
          <div>
            <p className="font-medium text-green-700 dark:text-green-300">Configuration is valid</p>
            <p className="text-sm text-green-600 dark:text-green-400">You can save your changes</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="mb-6 space-y-3">
      {/* Errors */}
      {errors.length > 0 && (
        <div className="rounded-lg border bg-red-50 dark:bg-red-950/20 p-4">
          <div className="flex items-start gap-3">
            <XCircle className="h-5 w-5 text-red-600 dark:text-red-400 mt-0.5" />
            <div className="flex-1">
              <p className="font-medium text-red-700 dark:text-red-300">Configuration errors:</p>
              <ul className="mt-2 space-y-1">
                {errors.map((error, idx) => (
                  <li key={idx} className="text-sm text-red-600 dark:text-red-400">
                    • {error}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Warnings */}
      {warnings.length > 0 && (
        <div className="rounded-lg border bg-yellow-50 dark:bg-yellow-950/20 p-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-yellow-600 dark:text-yellow-400 mt-0.5" />
            <div className="flex-1">
              <p className="font-medium text-yellow-700 dark:text-yellow-300">
                {errors.length === 0 ? 'Configuration warnings:' : 'Warnings (can be ignored):'}
              </p>
              <ul className="mt-2 space-y-1">
                {warnings.map((warning, idx) => (
                  <li key={idx} className="text-sm text-yellow-600 dark:text-yellow-400">
                    • {warning}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
