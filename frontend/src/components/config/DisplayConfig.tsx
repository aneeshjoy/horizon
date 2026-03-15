import { Monitor } from 'lucide-react'
import type { DisplayConfig as DisplayConfigType } from '@/api/types'
import { Tooltip } from '@/components/ui/Tooltip'

interface DisplayConfigProps {
  config: DisplayConfigType
  onChange: (config: DisplayConfigType) => void
}

export function DisplayConfig({ config, onChange }: DisplayConfigProps) {
  const updateConfig = (field: keyof DisplayConfigType, value: any) => {
    onChange({ ...config, [field]: value })
  }

  return (
    <div className="rounded-lg border bg-card p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="rounded-full p-2 bg-purple-500/10">
          <Monitor className="h-5 w-5 text-purple-500" />
        </div>
        <div>
          <h2 className="text-xl font-semibold">Display & UI Settings</h2>
          <p className="text-sm text-muted-foreground">
            Configure visualization and refresh behavior
          </p>
        </div>
      </div>

      <div className="space-y-6">
        {/* Grid Time Granularity */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <label className="text-sm font-medium">Grid Time Granularity</label>
              <Tooltip content="Time duration per row in the pattern grid visualization" />
            </div>
            <span className="text-sm text-muted-foreground">{config.grid_time_granularity_minutes} min</span>
          </div>
          <input
            type="range"
            min="15"
            max="120"
            step="15"
            value={config.grid_time_granularity_minutes}
            onChange={(e) => updateConfig('grid_time_granularity_minutes', parseInt(e.target.value))}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>15 min (detailed)</span>
            <span>45 min (default)</span>
            <span>120 min (simple)</span>
          </div>
          <p className="text-xs text-muted-foreground">
            Minutes per grid row. Lower values show more detail but may clutter the interface.
          </p>
        </div>

        {/* Auto Refresh Interval */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <label className="text-sm font-medium">Auto Refresh Interval</label>
              <Tooltip content="How often to automatically reload vehicle data" />
            </div>
            <span className="text-sm text-muted-foreground">
              {config.auto_refresh_interval_seconds === 0 ? 'Off' : `${config.auto_refresh_interval_seconds}s`}
            </span>
          </div>
          <input
            type="range"
            min="0"
            max="600"
            step="30"
            value={config.auto_refresh_interval_seconds}
            onChange={(e) => updateConfig('auto_refresh_interval_seconds', parseInt(e.target.value))}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>Off</span>
            <span>30s</span>
            <span>2 min</span>
            <span>10 min</span>
          </div>
          <p className="text-xs text-muted-foreground">
            Automatically refresh dashboard data. Set to 0 to disable.
          </p>
        </div>
      </div>
    </div>
  )
}
