import { useState, useEffect } from 'react'
import { Save, RotateCcw, AlertCircle, RefreshCw } from 'lucide-react'
import { Header } from '../components/layout/Header'
import { Footer } from '../components/layout/Footer'
import { useConfiguration, useReprocess } from '../hooks/useConfiguration'
import { useImport } from '../hooks/useImport'
import { PatternDetectionConfig } from '../components/config/PatternDetectionConfig'
import { ClassificationConfig } from '../components/config/ClassificationConfig'
import { DisplayConfig } from '../components/config/DisplayConfig'
import { MQTTConfig } from '../components/config/MQTTConfig'
import { ImportConfig } from '../components/config/ImportConfig'
import { ConfigValidationPanel } from '../components/config/ConfigValidationPanel'
import { ReprocessStatusModal } from '../components/config/ReprocessStatusModal'
import { ImportStatusModal } from '../components/config/ImportStatusModal'
import type { ReprocessStatus, SystemConfig, ImportStatus } from '@/api/types'

type TabKey = 'pattern' | 'classification' | 'display' | 'mqtt' | 'import'

export function ConfigurationPage() {
  const [activeTab, setActiveTab] = useState<TabKey>('pattern')
  const [workingConfig, setWorkingConfig] = useState<SystemConfig | null>(null)
  const [hasChanges, setHasChanges] = useState(false)
  const [validationResult, setValidationResult] = useState<{
    errors: string[]
    warnings: string[]
  } | null>(null)
  const [showRebuildConfirm, setShowRebuildConfirm] = useState(false)

  const {
    config,
    isLoading,
    saveConfig,
    isSaving,
    validateConfig,
    isValidating,
    resetConfig,
  } = useConfiguration()

  const { status, startReprocess, isStarting, cancelReprocess, clearReprocessStatus } = useReprocess()

  const reprocessStatus = status as ReprocessStatus | undefined

  const importHook = useImport()
  const importStatus = importHook.status as ImportStatus | undefined

  // Sync working config when config loads or after reset (when no unsaved changes)
  useEffect(() => {
    if (config && !hasChanges) {
      setWorkingConfig(config)
    }
  }, [config, hasChanges])

  // Listen for manual import trigger
  useEffect(() => {
    const handleManualImport = () => {
      if (workingConfig?.import_config.auto_import_on_startup) {
        importHook.startImport()
      }
    }

    const handleRebuildAfterImport = () => {
      startReprocess()
    }

    window.addEventListener('import-manual-trigger', handleManualImport)
    window.addEventListener('rebuild-after-import', handleRebuildAfterImport)

    return () => {
      window.removeEventListener('import-manual-trigger', handleManualImport)
      window.removeEventListener('rebuild-after-import', handleRebuildAfterImport)
    }
  }, [workingConfig, importHook, startReprocess])

  // Auto-clear completed import status on mount (prevents modal from showing after refresh)
  useEffect(() => {
    if (importStatus?.status === 'completed' || importStatus?.status === 'failed' || importStatus?.status === 'cancelled') {
      // Clear stale import status from previous session
      importHook.clearImportStatus()
    }
    // Same for reprocess status
    if (reprocessStatus?.status === 'completed' || reprocessStatus?.status === 'failed' || reprocessStatus?.status === 'cancelled') {
      clearReprocessStatus()
    }
  }, [importStatus, importHook, reprocessStatus, clearReprocessStatus])

  const handleSave = async (reprocess = false) => {
    if (!workingConfig) return

    try {
      await saveConfig({ newConfig: workingConfig, reprocess })
      setHasChanges(false)
      setValidationResult(null)

      if (reprocess) {
        startReprocess()
      }
    } catch (error) {
      console.error('Failed to save config:', error)
    }
  }

  const handleReset = async () => {
    try {
      await resetConfig()
      setHasChanges(false)
      setValidationResult(null)
    } catch (error) {
      console.error('Failed to reset config:', error)
    }
  }

  const handleValidate = async () => {
    if (!workingConfig) return

    try {
      const result = await validateConfig(workingConfig)
      setValidationResult(result)
    } catch (error) {
      console.error('Validation failed:', error)
    }
  }

  const updateConfig = (updates: Partial<SystemConfig>) => {
    if (!workingConfig) return
    setWorkingConfig({ ...workingConfig, ...updates })
    setHasChanges(true)
  }

  if (isLoading || !workingConfig) {
    return (
      <div className="flex min-h-screen flex-col">
        <Header />
        <main className="flex-1">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-12">
            <div className="flex items-center justify-center">
              <div className="text-center">
                <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary border-r-transparent" />
                <p className="mt-4 text-muted-foreground">Loading configuration...</p>
              </div>
            </div>
          </div>
        </main>
        <Footer />
      </div>
    )
  }

  return (
    <div className="flex min-h-screen flex-col">
      <Header />

      <main className="flex-1">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-6">
          <div className="mb-8">
            <h1 className="text-3xl font-bold tracking-tight">System Configuration</h1>
            <p className="text-muted-foreground">
              Configure pattern detection, classification, display, and MQTT settings
            </p>
          </div>

          {/* Tabs */}
          <div className="mb-6 border-b">
            <nav className="flex gap-4 -mb-px">
              <button
                onClick={() => setActiveTab('pattern')}
                className={`border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
                  activeTab === 'pattern'
                    ? 'border-primary text-primary'
                    : 'border-transparent text-muted-foreground hover:text-foreground'
                }`}
              >
                Pattern Detection
              </button>
              <button
                onClick={() => setActiveTab('classification')}
                className={`border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
                  activeTab === 'classification'
                    ? 'border-primary text-primary'
                    : 'border-transparent text-muted-foreground hover:text-foreground'
                }`}
              >
                Classification
              </button>
              <button
                onClick={() => setActiveTab('display')}
                className={`border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
                  activeTab === 'display'
                    ? 'border-primary text-primary'
                    : 'border-transparent text-muted-foreground hover:text-foreground'
                }`}
              >
                Display & UI
              </button>
              <button
                onClick={() => setActiveTab('mqtt')}
                className={`border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
                  activeTab === 'mqtt'
                    ? 'border-primary text-primary'
                    : 'border-transparent text-muted-foreground hover:text-foreground'
                }`}
              >
                MQTT
              </button>
              <button
                onClick={() => setActiveTab('import')}
                className={`border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
                  activeTab === 'import'
                    ? 'border-primary text-primary'
                    : 'border-transparent text-muted-foreground hover:text-foreground'
                }`}
              >
                Data Import
              </button>
            </nav>
          </div>

          {/* Tab content */}
          <div className="mb-6">
            {activeTab === 'pattern' && (
              <PatternDetectionConfig
                config={workingConfig.pattern_detection}
                onChange={(newConfig) => updateConfig({ pattern_detection: newConfig })}
              />
            )}

            {activeTab === 'classification' && (
              <ClassificationConfig
                config={workingConfig.classification}
                onChange={(newConfig) => updateConfig({ classification: newConfig })}
              />
            )}

            {activeTab === 'display' && (
              <DisplayConfig
                config={workingConfig.display}
                onChange={(newConfig) => updateConfig({ display: newConfig })}
              />
            )}

            {activeTab === 'mqtt' && (
              <MQTTConfig
                config={workingConfig.mqtt}
                onChange={(newConfig) => updateConfig({ mqtt: newConfig })}
              />
            )}

            {activeTab === 'import' && (
              <ImportConfig
                config={workingConfig.import_config}
                onChange={(newConfig) => updateConfig({ import_config: newConfig })}
              />
            )}
          </div>

          {/* Validation panel */}
          {(validationResult || isValidating) && (
            <ConfigValidationPanel
              validationResult={validationResult}
              isValidating={isValidating}
            />
          )}

          {/* Action bar */}
          <div className="sticky bottom-0 rounded-lg border bg-background p-4 shadow">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <button
                  onClick={() => handleValidate()}
                  disabled={isValidating}
                  className="rounded-md border px-4 py-2 text-sm font-medium hover:bg-muted disabled:opacity-50"
                >
                  {isValidating ? 'Validating...' : 'Validate Changes'}
                </button>
                {hasChanges && (
                  <div className="flex items-center gap-1 text-sm text-muted-foreground">
                    <AlertCircle className="h-4 w-4" />
                    <span>Unsaved changes</span>
                  </div>
                )}
              </div>

              <div className="flex items-center gap-3">
                <button
                  onClick={() => setShowRebuildConfirm(true)}
                  disabled={reprocessStatus?.status === 'running'}
                  className="inline-flex items-center gap-2 rounded-md border border-orange-500/50 px-4 py-2 text-sm font-medium text-orange-600 hover:bg-orange-500/10 disabled:opacity-50 dark:text-orange-400 dark:border-orange-400/50"
                >
                  <RefreshCw className="h-4 w-4" />
                  Rebuild Profiles
                </button>
                <button
                  onClick={() => handleReset()}
                  disabled={isSaving}
                  className="inline-flex items-center gap-2 rounded-md border px-4 py-2 text-sm font-medium hover:bg-muted disabled:opacity-50"
                >
                  <RotateCcw className="h-4 w-4" />
                  Reset to Defaults
                </button>
                <button
                  onClick={() => handleSave(false)}
                  disabled={isSaving || !hasChanges}
                  className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                >
                  <Save className="h-4 w-4" />
                  {isSaving ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </div>

            {hasChanges && (
              <p className="mt-3 text-xs text-muted-foreground">
                ⚠️ Some settings require reprocessing all vehicle profiles to take effect.
              </p>
            )}
          </div>
        </div>
      </main>

      <Footer />

      {/* Rebuild confirmation dialog */}
      {showRebuildConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-md rounded-lg bg-background p-6 shadow-lg">
            <h2 className="text-xl font-semibold mb-2">Rebuild All Profiles?</h2>
            <p className="text-muted-foreground mb-4">
              This will rebuild all vehicle profiles from scratch using the data in <code className="bg-muted px-1 py-0.5 rounded text-sm">frigate_events.jsonl</code>.
              This may take several minutes depending on the amount of data.
            </p>
            <div className="bg-muted p-3 rounded-md mb-4 text-sm">
              <p className="font-medium mb-1">This will:</p>
              <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                <li>Clear all existing pattern buckets</li>
                <li>Reprocess all events with current configuration</li>
                <li>Reset plate names to values from events</li>
              </ul>
            </div>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowRebuildConfirm(false)}
                className="rounded-md border px-4 py-2 text-sm font-medium hover:bg-muted"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  setShowRebuildConfirm(false)
                  startReprocess()
                }}
                className="rounded-md bg-orange-600 px-4 py-2 text-sm font-medium text-white hover:bg-orange-700 dark:bg-orange-500 dark:hover:bg-orange-600"
              >
                Rebuild Now
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Reprocess status modal - shown first when rebuild is active */}
      {reprocessStatus && reprocessStatus.status !== 'none' && (
        <ReprocessStatusModal
          status={reprocessStatus}
          onCancel={cancelReprocess}
          onClose={clearReprocessStatus}
          mode="rebuild"
        />
      )}

      {/* Import status modal - only show if rebuild modal is not visible */}
      {importStatus && importStatus.status !== 'none' && (!reprocessStatus || reprocessStatus.status === 'none') && (
        <ImportStatusModal
          status={importStatus}
          onCancel={importHook.cancelImport}
          onClose={importHook.clearImportStatus}
        />
      )}
    </div>
  )
}
