import { Settings, Info } from 'lucide-react'
import type { PatternDetectionConfig as PatternDetectionConfigType } from '@/api/types'
import { Tooltip } from '@/components/ui/Tooltip'

interface PatternDetectionConfigProps {
  config: PatternDetectionConfigType
  onChange: (config: PatternDetectionConfigType) => void
}

export function PatternDetectionConfig({ config, onChange }: PatternDetectionConfigProps) {
  const updateConfig = (field: keyof PatternDetectionConfigType, value: number) => {
    onChange({ ...config, [field]: value })
  }

  return (
    <div className="rounded-lg border bg-card p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="rounded-full p-2 bg-primary/10">
          <Settings className="h-5 w-5 text-primary" />
        </div>
        <div>
          <h2 className="text-xl font-semibold">Pattern Detection Settings</h2>
          <p className="text-sm text-muted-foreground">
            Configure how license plate readings are analyzed and grouped into patterns
          </p>
        </div>
      </div>

      <div className="space-y-6">
        {/* Bucket Tolerance */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <label className="text-sm font-medium">Bucket Tolerance (minutes)</label>
              <Tooltip content="How close in time (±minutes) readings must be to group into the same pattern" />
            </div>
            <span className="text-sm text-muted-foreground">{config.bucket_tolerance_minutes} min</span>
          </div>
          <input
            type="range"
            min="15"
            max="180"
            step="5"
            value={config.bucket_tolerance_minutes}
            onChange={(e) => updateConfig('bucket_tolerance_minutes', parseInt(e.target.value))}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>15 min (precise)</span>
            <span>45 min (default)</span>
            <span>180 min (broad)</span>
          </div>
          <p className="text-xs text-muted-foreground">
            Higher values create broader patterns but may reduce precision
          </p>
        </div>

        {/* Min Pattern Samples */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <label className="text-sm font-medium">Min Pattern Samples</label>
              <Tooltip content="Minimum number of sightings needed to create a time pattern" />
            </div>
            <span className="text-sm text-muted-foreground">{config.min_pattern_samples} readings</span>
          </div>
          <input
            type="range"
            min="2"
            max="10"
            step="1"
            value={config.min_pattern_samples}
            onChange={(e) => updateConfig('min_pattern_samples', parseInt(e.target.value))}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>2 (sensitive)</span>
            <span>3 (default)</span>
            <span>10 (strict)</span>
          </div>
          <p className="text-xs text-muted-foreground">
            Minimum sightings required to form a pattern
          </p>
        </div>

        {/* Confidence Threshold */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <label className="text-sm font-medium">Confidence Threshold</label>
              <Tooltip content="Minimum OCR confidence (0-100%) to accept a plate reading" />
            </div>
            <span className="text-sm text-muted-foreground">{(config.confidence_threshold * 100).toFixed(0)}%</span>
          </div>
          <input
            type="range"
            min="0.0"
            max="1.0"
            step="0.05"
            value={config.confidence_threshold}
            onChange={(e) => updateConfig('confidence_threshold', parseFloat(e.target.value))}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>50% (permissive)</span>
            <span>65% (default)</span>
            <span>95% (strict)</span>
          </div>
          <p className="text-xs text-muted-foreground">
            Minimum confidence score to accept a reading
          </p>
        </div>

        {/* OCR Similarity Threshold */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <label className="text-sm font-medium">OCR Similarity Threshold</label>
              <Tooltip content="Similarity threshold for fuzzy plate matching and typo correction (0-100%)" />
            </div>
            <span className="text-sm text-muted-foreground">{(config.ocr_similarity_threshold * 100).toFixed(0)}%</span>
          </div>
          <input
            type="range"
            min="0.5"
            max="1.0"
            step="0.05"
            value={config.ocr_similarity_threshold}
            onChange={(e) => updateConfig('ocr_similarity_threshold', parseFloat(e.target.value))}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>50% (loose)</span>
            <span>85% (default)</span>
            <span>100% (exact)</span>
          </div>
          <p className="text-xs text-muted-foreground">
            Similarity score for fuzzy matching and OCR correction
          </p>
        </div>
      </div>
    </div>
  )
}
