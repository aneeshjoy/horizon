import { Calendar, Clock, Activity, TrendingUp, Info } from 'lucide-react'
import type { VehicleSummary } from '@/api/types'
import { formatDate, formatTime } from '@/lib/utils'
import { Tooltip } from '@/components/ui/Tooltip'

interface StatsPanelProps {
  summary: VehicleSummary
}

export function StatsPanel({ summary }: StatsPanelProps) {
  // Calculate some statistics
  const avgConfidence = summary.patterns.length > 0
    ? summary.patterns.reduce((sum, p) => sum + p.avg_confidence, 0) / summary.patterns.length
    : 0

  const mostActivePattern = summary.patterns.length > 0
    ? summary.patterns.reduce((max, p) => (p.sightings > max.sightings ? p : max), summary.patterns[0])
    : null

  return (
    <div className="rounded-lg border bg-card p-6">
      <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
        Statistics
        <span className="text-xs text-muted-foreground font-normal">Key metrics about this vehicle</span>
      </h2>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Total sightings */}
        <div className="rounded-lg bg-muted/50 p-4">
          <div className="flex items-center gap-2 text-muted-foreground mb-2">
            <Activity className="h-4 w-4" />
            <span className="text-xs uppercase">Total</span>
            <Tooltip content="All detections of this plate" />
          </div>
          <div className="text-2xl font-bold">{summary.total_readings}</div>
          <p className="text-xs text-muted-foreground mt-1">Sightings</p>
        </div>

        {/* Patterns */}
        <div className="rounded-lg bg-muted/50 p-4">
          <div className="flex items-center gap-2 text-muted-foreground mb-2">
            <TrendingUp className="h-4 w-4" />
            <span className="text-xs uppercase">Patterns</span>
            <Tooltip content="Recurring time patterns (e.g., weekdays at 8am)" />
          </div>
          <div className="text-2xl font-bold">{summary.patterns.length}</div>
          <p className="text-xs text-muted-foreground mt-1">Identified</p>
        </div>

        {/* First seen */}
        <div className="rounded-lg bg-muted/50 p-4">
          <div className="flex items-center gap-2 text-muted-foreground mb-2">
            <Calendar className="h-4 w-4" />
            <span className="text-xs uppercase">First Seen</span>
            <Tooltip content="Earliest recorded sighting" />
          </div>
          <div className="text-sm font-semibold">{formatDate(summary.first_seen)}</div>
          <p className="text-xs text-muted-foreground mt-1">{formatTime(summary.first_seen)}</p>
        </div>

        {/* Last seen */}
        <div className="rounded-lg bg-muted/50 p-4">
          <div className="flex items-center gap-2 text-muted-foreground mb-2">
            <Clock className="h-4 w-4" />
            <span className="text-xs uppercase">Last Seen</span>
            <Tooltip content="Latest recorded sighting" />
          </div>
          <div className="text-sm font-semibold">{formatDate(summary.last_seen)}</div>
          <p className="text-xs text-muted-foreground mt-1">{formatTime(summary.last_seen)}</p>
        </div>
      </div>

      {/* Additional stats */}
      <div className="mt-4 pt-4 border-t">
        <div className="grid gap-4 sm:grid-cols-2">
          {/* Average confidence */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
              <span>Avg Confidence</span>
              <Tooltip content="How reliably the plate text was read (higher is better)" />
            </div>
            <span className="font-semibold">{(avgConfidence * 100).toFixed(1)}%</span>
          </div>

          {/* Pending readings */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
              <span>Pending Readings</span>
              <Tooltip content="Sightings waiting for more data to form a pattern (3+ similar times needed)" />
            </div>
            <span className="font-semibold">{summary.pending_readings}</span>
          </div>

          {/* Most active pattern */}
          {mostActivePattern && (
            <div className="col-span-2 flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                <span>Most Active Pattern</span>
                <Tooltip content="Day(s) and time with the highest frequency of sightings" />
              </div>
              <span className="font-semibold">
                {mostActivePattern.days
                  .sort((a, b) => {
                    const dayOrder = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                    return dayOrder.indexOf(a) - dayOrder.indexOf(b)
                  })
                  .join(', ')} @ {mostActivePattern.time}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
