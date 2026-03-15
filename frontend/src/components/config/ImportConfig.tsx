import { Database, Upload, Info } from 'lucide-react'
import type { ImportConfig as ImportConfigType } from '@/api/types'
import { Tooltip } from '@/components/ui/Tooltip'

interface ImportConfigProps {
  config: ImportConfigType
  onChange: (config: ImportConfigType) => void
}

export function ImportConfig({ config, onChange }: ImportConfigProps) {
  const updateConfig = (field: keyof ImportConfigType, value: any) => {
    onChange({ ...config, [field]: value })
  }

  return (
    <div className="rounded-lg border bg-card p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="rounded-full p-2 bg-blue-500/10">
          <Database className="h-5 w-5 text-blue-500" />
        </div>
        <div>
          <h2 className="text-xl font-semibold">Frigate Database Import</h2>
          <p className="text-sm text-muted-foreground">
            Import historical license plate data from Frigate
          </p>
        </div>
      </div>

      <div className="space-y-6">
        {/* Info Box */}
        <div className="rounded-md bg-blue-500/10 border border-blue-500/20 p-4">
          <div className="flex gap-3">
            <Info className="h-5 w-5 text-blue-500 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-blue-600 dark:text-blue-400">
              <p className="font-medium mb-1">Quick Start Guide</p>
              <ol className="list-decimal list-inside space-y-1 text-blue-600/80 dark:text-blue-400/80">
                <li>Copy your Frigate DB to <code className="bg-blue-500/10 px-1 py-0.5 rounded text-xs">./data/external/frigate.db</code></li>
                <li>Enable "Auto-import on startup" below</li>
                <li>Restart the container</li>
                <li>Events will be extracted and profiles built automatically</li>
              </ol>
            </div>
          </div>
        </div>

        {/* Auto Import on Startup */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <label className="text-sm font-medium">Auto-import on startup</label>
            <Tooltip content="Automatically import from Frigate database when container starts" />
          </div>
          <button
            onClick={() => updateConfig('auto_import_on_startup', !config.auto_import_on_startup)}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              config.auto_import_on_startup ? 'bg-primary' : 'bg-input'
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                config.auto_import_on_startup ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>
        <p className="text-xs text-muted-foreground">
          When enabled, automatically imports license plate events from the configured database file on container startup.
          Use this for initial setup or after updating your Frigate database.
        </p>

        {/* Auto Rebuild After Import */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <label className="text-sm font-medium">Auto-rebuild after import</label>
            <Tooltip content="Automatically rebuild profiles after import completes" />
          </div>
          <button
            onClick={() => updateConfig('auto_rebuild_after_import', !config.auto_rebuild_after_import)}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              config.auto_rebuild_after_import ? 'bg-primary' : 'bg-input'
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                config.auto_rebuild_after_import ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>
        <p className="text-xs text-muted-foreground">
          When enabled, automatically rebuilds vehicle profiles after a successful import.
          This generates pattern buckets from the imported events. Recommended for most users.
        </p>

        {/* Database Path */}
        <div className="space-y-2">
          <div className="flex items-center gap-1.5">
            <label className="text-sm font-medium">Database Path</label>
            <Tooltip content="Path to the Frigate SQLite database file (relative to container)" />
          </div>
          <input
            type="text"
            value={config.import_db_path}
            onChange={(e) => updateConfig('import_db_path', e.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            placeholder="/app/data/external/frigate.db"
          />
          <p className="text-xs text-muted-foreground">
            Default: <code className="bg-muted px-1 py-0.5 rounded">data/external/frigate.db</code>
            <br />
            For Docker mounts, use the container path (e.g., <code className="bg-muted px-1 py-0.5 rounded">/app/data/external/frigate.db</code>)
          </p>
        </div>

        {/* After Date Filter */}
        <div className="space-y-2">
          <div className="flex items-center gap-1.5">
            <label className="text-sm font-medium">Import After Date (Optional)</label>
            <Tooltip content="Only import events after this date (YYYY-MM-DD format)" />
          </div>
          <input
            type="date"
            value={config.import_after_date || ''}
            onChange={(e) => updateConfig('import_after_date', e.target.value || null)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          />
          <p className="text-xs text-muted-foreground">
            Leave empty to import all available events. Use this to skip old data or reimport recent events only.
          </p>
        </div>

        {/* Manual Import Button */}
        <div className="pt-4 border-t">
          <button
            onClick={() => {
              // This will be connected to a manual import function
              window.dispatchEvent(new CustomEvent('import-manual-trigger'))
            }}
            className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            <Upload className="h-4 w-4" />
            Import Now
          </button>
          <p className="text-xs text-muted-foreground mt-2">
            Manually trigger import without restarting. Requires database file to be in place.
          </p>
        </div>
      </div>
    </div>
  )
}
