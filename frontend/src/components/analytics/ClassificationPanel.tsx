import { Shield, AlertTriangle, CheckCircle, Info } from 'lucide-react'
import { Tooltip } from '@/components/ui/Tooltip'

interface ClassificationPanelProps {
  classification: 'Commuter' | 'Unknown' | 'Suspicious'
  score: number
}

export function ClassificationPanel({ classification, score }: ClassificationPanelProps) {
  const getIcon = () => {
    switch (classification) {
      case 'Commuter':
        return <CheckCircle className="h-6 w-6" />
      case 'Suspicious':
        return <AlertTriangle className="h-6 w-6" />
      default:
        return <Shield className="h-6 w-6" />
    }
  }

  const getColorClass = () => {
    switch (classification) {
      case 'Commuter':
        return 'text-commuter-600 bg-commuter-50 border-commuter-200'
      case 'Suspicious':
        return 'text-suspicious-600 bg-suspicious-50 border-suspicious-200'
      default:
        return 'text-unknown-600 bg-unknown-50 border-unknown-200'
    }
  }

  const getScoreColor = () => {
    if (score >= 80) return 'text-score-high'
    if (score >= 60) return 'text-score-medium'
    return 'text-score-low'
  }

  const getScoreLabel = () => {
    if (score >= 80) return 'High'
    if (score >= 60) return 'Medium'
    return 'Low'
  }

  const getClassificationTooltip = () => {
    switch (classification) {
      case 'Commuter':
        return 'Regular patterns suggest predictable commuting behavior'
      case 'Suspicious':
        return 'Irregular patterns may indicate unusual activity'
      default:
        return 'Insufficient data to determine behavior pattern'
    }
  }

  return (
    <div className="rounded-lg border bg-card p-6">
      <div className="flex items-center gap-3 mb-4">
        <div className={`rounded-full p-2 ${getColorClass()}`}>
          {getIcon()}
        </div>
        <div>
          <h3 className="font-semibold">Classification</h3>
          <p className="text-sm text-muted-foreground">Based on pattern analysis</p>
        </div>
      </div>

      <div className="space-y-4">
        {/* Classification badge */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
            <span>Category</span>
            <Tooltip content={getClassificationTooltip()} />
          </div>
          <span
            className={`rounded-full px-3 py-1 text-sm font-medium ${getClassificationBadgeColor(
              classification
            )}`}
          >
            {classification}
          </span>
        </div>

        {/* RDS Score */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
            <span>RDS Score</span>
            <Tooltip content="Routine Deviation Score: measures how predictable the patterns are (100 = very predictable)" />
          </div>
          <div className="flex items-center gap-2">
            <span className={`text-2xl font-bold ${getScoreColor()}`}>{score}</span>
            <span className="text-xs text-muted-foreground">/100</span>
            <span
              className={`rounded px-2 py-0.5 text-xs font-medium ${getScoreColor()} ${getScoreColor() ===
                'text-score-high'
                ? 'bg-score-high/10'
                : getScoreColor() === 'text-score-medium'
                ? 'bg-score-medium/10'
                : 'bg-score-low/10'
              }`}
            >
              {getScoreLabel()}
            </span>
          </div>
        </div>

        {/* Classification explanation */}
        <div className="rounded-md bg-muted/50 p-3 text-xs text-muted-foreground">
          <div className="flex items-start gap-2">
            <Info className="h-3.5 w-3.5 mt-0.5 flex-shrink-0" />
            <p>{getClassificationTooltip()}</p>
          </div>
        </div>
      </div>
    </div>
  )
}

function getClassificationBadgeColor(classification: string): string {
  switch (classification) {
    case 'Commuter':
      return 'bg-commuter-500 text-white hover:bg-commuter-600'
    case 'Suspicious':
      return 'bg-suspicious-500 text-white hover:bg-suspicious-600'
    default:
      return 'bg-unknown-500 text-white hover:bg-unknown-600'
  }
}
