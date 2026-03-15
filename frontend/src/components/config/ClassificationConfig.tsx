import { Shield } from 'lucide-react'
import type { ClassificationConfig as ClassificationConfigType } from '@/api/types'
import { Tooltip } from '@/components/ui/Tooltip'

interface ClassificationConfigProps {
  config: ClassificationConfigType
  onChange: (config: ClassificationConfigType) => void
}

export function ClassificationConfig({ config, onChange }: ClassificationConfigProps) {
  const updateConfig = (field: keyof ClassificationConfigType, value: number) => {
    onChange({ ...config, [field]: value })
  }

  // Calculate weight sum for display
  const weightSum = config.pattern_adherence_weight + config.confidence_stability_weight + config.pattern_concentration_weight

  return (
    <div className="rounded-lg border bg-card p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="rounded-full p-2 bg-blue-500/10">
          <Shield className="h-5 w-5 text-blue-500" />
        </div>
        <div>
          <h2 className="text-xl font-semibold">Classification Settings</h2>
          <p className="text-sm text-muted-foreground">
            Configure vehicle classification thresholds and RDS calculation weights
          </p>
        </div>
      </div>

      <div className="space-y-6">
        {/* Classification Thresholds */}
        <div className="space-y-4">
          <div className="flex items-center gap-1.5">
            <h3 className="text-sm font-medium">Classification Thresholds (RDS Score)</h3>
            <Tooltip content="RDS = Routine Deviation Score. Determines classification based on pattern predictability" />
          </div>

          {/* Commuter Threshold */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <label className="text-sm">Commuter Threshold</label>
                <Tooltip content="Minimum RDS score (0-100) to classify as Commuter (predictable patterns)" />
              </div>
              <span className="text-sm font-medium">{config.commuter_threshold}%+</span>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              step="5"
              value={config.commuter_threshold}
              onChange={(e) => updateConfig('commuter_threshold', parseInt(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>60%</span>
              <span>80% (default)</span>
              <span>100%</span>
            </div>
          </div>

          {/* Unknown Threshold */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <label className="text-sm">Unknown Threshold</label>
                <Tooltip content="Minimum RDS score (0-100) to classify as Unknown instead of Suspicious" />
              </div>
              <span className="text-sm font-medium">{config.unknown_threshold}%+</span>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              step="5"
              value={config.unknown_threshold}
              onChange={(e) => updateConfig('unknown_threshold', parseInt(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>0%</span>
              <span>60% (default)</span>
              <span>100%</span>
            </div>
          </div>

          {/* Visual representation of threshold zones */}
          <div className="flex items-center gap-1 rounded-md bg-muted p-2" title="Visual representation of classification zones based on RDS score">
            <div className="flex-1 h-4 rounded bg-red-500" style={{ width: `${config.unknown_threshold}%` }} />
            <div className="flex-1 h-4 rounded bg-yellow-500" style={{ width: `${config.commuter_threshold - config.unknown_threshold}%` }} />
            <div className="flex-1 h-4 rounded bg-green-500" style={{ width: `${100 - config.commuter_threshold}%` }} />
          </div>
          <div className="flex justify-between text-xs text-muted-foreground px-2">
            <span>Suspicious</span>
            <span>Unknown</span>
            <span>Commuter</span>
          </div>
        </div>

        {/* RDS Weights */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <h3 className="text-sm font-medium">RDS Calculation Weights</h3>
              <Tooltip content="How different factors contribute to the Routine Deviation Score (must sum to 100%)" />
            </div>
            <span className={`text-sm font-medium ${Math.abs(weightSum - 1.0) < 0.01 ? 'text-green-600' : 'text-red-600'}`}>
              {weightSum === 1.0 ? '✓ Sums to 100%' : `⚠ Sums to ${(weightSum * 100).toFixed(0)}%`}
            </span>
          </div>

          {/* Pattern Adherence Weight */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <label className="text-sm">Pattern Adherence Weight</label>
                <Tooltip content="Measures how well sightings match established time patterns" />
              </div>
              <span className="text-sm font-medium">{(config.pattern_adherence_weight * 100).toFixed(0)}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={config.pattern_adherence_weight}
              onChange={(e) => updateConfig('pattern_adherence_weight', parseFloat(e.target.value))}
              className="w-full"
            />
            <p className="text-xs text-muted-foreground">
              How well sightings match identified patterns
            </p>
          </div>

          {/* Confidence Stability Weight */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <label className="text-sm">Confidence Stability Weight</label>
                <Tooltip content="Measures consistency of OCR confidence scores across readings" />
              </div>
              <span className="text-sm font-medium">{(config.confidence_stability_weight * 100).toFixed(0)}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={config.confidence_stability_weight}
              onChange={(e) => updateConfig('confidence_stability_weight', parseFloat(e.target.value))}
              className="w-full"
            />
            <p className="text-xs text-muted-foreground">
              Consistency of detection confidence scores
            </p>
          </div>

          {/* Pattern Concentration Weight */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <label className="text-sm">Pattern Concentration Weight</label>
                <Tooltip content="Measures if sightings are clustered in few patterns or spread across many" />
              </div>
              <span className="text-sm font-medium">{(config.pattern_concentration_weight * 100).toFixed(0)}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={config.pattern_concentration_weight}
              onChange={(e) => updateConfig('pattern_concentration_weight', parseFloat(e.target.value))}
              className="w-full"
            />
            <p className="text-xs text-muted-foreground">
              How concentrated sightings are in few patterns vs spread out
            </p>
          </div>

          {/* Weight visualization */}
          <div className="rounded-md bg-muted p-3">
            <div className="mb-2 text-xs text-muted-foreground text-center">Weight Distribution</div>
            <div className="flex h-4 rounded overflow-hidden">
              <div
                className="bg-blue-500"
                style={{ width: `${config.pattern_adherence_weight * 100}%` }}
                title={`Pattern Adherence: ${(config.pattern_adherence_weight * 100).toFixed(0)}%`}
              />
              <div
                className="bg-green-500"
                style={{ width: `${config.confidence_stability_weight * 100}%` }}
                title={`Confidence Stability: ${(config.confidence_stability_weight * 100).toFixed(0)}%`}
              />
              <div
                className="bg-purple-500"
                style={{ width: `${config.pattern_concentration_weight * 100}%` }}
                title={`Pattern Concentration: ${(config.pattern_concentration_weight * 100).toFixed(0)}%`}
              />
            </div>
            <div className="flex justify-between text-xs text-muted-foreground mt-1">
              <span>Adherence</span>
              <span>Stability</span>
              <span>Concentration</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
