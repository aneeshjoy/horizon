import { useMemo, useState, useCallback } from 'react'
import type { PatternGrid as PatternGridType, SightingPattern } from '../../api/types'

interface PatternGridVisualizationProps {
  grid: PatternGridType
  plate: string
  patterns?: SightingPattern[]
}

interface TooltipState {
  text: string
  x: number
  y: number
  visible: boolean
}

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

// Bright green color scheme (GitHub-style) with 5 intensity levels
const GREEN_COLORS = [
  'hsl(var(--muted) / 0.5)',   // 0 sightings - grey (like stats panel)
  'rgba(39, 174, 96, 0.16)',   // 1-2 sightings - very light
  'rgba(39, 174, 96, 0.32)',   // 3-4 sightings - light
  'rgba(39, 174, 96, 0.48)',   // 5-9 sightings - medium
  'rgba(39, 174, 96, 0.64)',   // 10-19 sightings - medium-high
  'rgba(39, 174, 96, 0.8)',    // 20+ sightings - high
]

export function PatternGridVisualization({ grid, plate, patterns = [] }: PatternGridVisualizationProps) {
  const [tooltip, setTooltip] = useState<TooltipState>({ text: '', x: 0, y: 0, visible: false })

  // Create a map of pattern_id to pattern for quick lookup
  const patternMap = useMemo(() => {
    const map = new Map<number, SightingPattern>()
    patterns.forEach(pattern => {
      map.set(pattern.pattern_id, pattern)
    })
    return map
  }, [patterns])

  // Handle cell interaction
  const handleCellInteraction = useCallback((
    day: string,
    patternIds: number[],
    count: number,
    slotStartMinutes: number,
    slotEndMinutes: number,
    event: React.MouseEvent<HTMLDivElement>
  ) => {
    const tooltipText = getCellTooltip(day, patternIds, count, slotStartMinutes, slotEndMinutes)
    const rect = (event.target as HTMLDivElement).getBoundingClientRect()

    setTooltip({
      text: tooltipText,
      x: rect.left + rect.width / 2,
      y: rect.top - 8,
      visible: true
    })
  }, [])

  const handleCellLeave = useCallback(() => {
    setTooltip(prev => ({ ...prev, visible: false }))
  }, [])

  // Get color intensity based on count
  const getCellColor = (count: number) => {
    if (count === 0) return GREEN_COLORS[0]
    if (count <= 2) return GREEN_COLORS[1]
    if (count <= 4) return GREEN_COLORS[2]
    if (count <= 9) return GREEN_COLORS[3]
    if (count <= 19) return GREEN_COLORS[4]
    return GREEN_COLORS[5]
  }

  // Helper to get tooltip text for a cell
  const getCellTooltip = useCallback((day: string, patternIds: number[], count: number, slotStartMinutes: number, slotEndMinutes: number) => {
    if (count === 0) return `${day}: No sightings`

    // Get actual pattern times if available
    const patternTimes = patternIds
      .map(id => patternMap.get(id)?.time)
      .filter((time): time is string => time !== undefined)
      .sort()

    const slotStartTime = `${Math.floor(slotStartMinutes / 60).toString().padStart(2, '0')}:${(slotStartMinutes % 60).toString().padStart(2, '0')}`
    const slotEndTime = `${Math.floor(slotEndMinutes / 60).toString().padStart(2, '0')}:${(slotEndMinutes % 60).toString().padStart(2, '0')}`

    if (patternTimes.length > 0) {
      // Show actual pattern times (e.g., "08:35, 09:20")
      const timesStr = patternTimes.join(', ')
      return `${day} ${timesStr}: ${count} sighting${count > 1 ? 's' : ''}`
    }

    // Fallback to time slot range
    return `${day} ${slotStartTime}-${slotEndTime}: ${count} sighting${count > 1 ? 's' : ''}`
  }, [patternMap])

  const maxCount = grid.max_count

  // Reorganize data: days as rows, time slots as columns
  const dayRows = useMemo(() => {
    const rows: Array<{ day: string; dayIndex: number; cells: Array<{ time: string; count: number; timeLabel: string }> }> = []

    DAYS.forEach((day, dayIndex) => {
      const cells: Array<{ time: string; count: number; timeLabel: string }> = []

      grid.rows.forEach((row) => {
        const cell = row.cells.find(c => c.day === dayIndex)
        if (cell) {
          cells.push({
            time: row.time_label,
            count: cell.count,
            timeLabel: row.time_label
          })
        }
      })

      rows.push({ day, dayIndex, cells })
    })

    return rows
  }, [grid])

  return (
    <div className="rounded-lg border bg-card p-4 md:p-5 relative">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-base md:text-lg font-semibold">Pattern Visualization</h2>
        <span className="text-xs text-muted-foreground">Color intensity = sightings</span>
      </div>

      {/* Custom Tooltip */}
      {tooltip.visible && (
        <div
          className="fixed z-50 px-2 py-1 text-xs bg-popover text-popover-foreground border rounded-md shadow-lg pointer-events-none transform -translate-x-1/2 -translate-y-full mb-1"
          style={{
            left: `${tooltip.x}px`,
            top: `${tooltip.y}px`,
          }}
        >
          {tooltip.text}
          {/* Arrow */}
          <div className="absolute left-1/2 transform -translate-x-1/2 top-full w-0 h-0 border-l-4 border-r-4 border-t-4 border-l-transparent border-r-transparent border-t-popper" />
        </div>
      )}

      <div className="w-full">
        {/* Header row with time labels */}
        <div className="mb-1.5">
          <div className="flex">
            <div className="w-12 flex-shrink-0"></div>
            <div className="flex gap-[2px] overflow-hidden">
              {grid.rows.map((row) => (
                <div
                  key={row.time_slot}
                  className="text-[10px] text-muted-foreground text-center flex-shrink-0"
                  style={{ width: '11px' }}
                  title={row.time_label}
                >
                  {row.time_slot % 4 === 0 ? row.time_label : ''}
                </div>
              ))}
            </div>
          </div>
        </div>

          {/* Grid rows - days on left, time across */}
          <div className="flex">
            {/* Day labels */}
            <div className="w-12 flex-shrink-0 pr-1.5 flex flex-col gap-[2px]">
              {DAYS.map((day) => (
                <div
                  key={day}
                  className="flex items-center justify-center text-xs font-medium text-muted-foreground"
                  style={{ height: '11px' }}
                >
                  {day}
                </div>
              ))}
            </div>

            {/* Grid cells */}
            <div className="flex gap-[2px] overflow-hidden">
              {grid.rows.map((row, rowIndex) => (
                <div key={row.time_slot} className="flex flex-col gap-[2px] flex-shrink-0">
                  {DAYS.map((day, dayIndex) => {
                    const cell = row.cells.find(c => c.day === dayIndex)
                    const count = cell?.count || 0
                    const patternIds = cell?.pattern_ids || []

                    // Calculate time slot for fallback tooltip
                    const slotStartMinutes = rowIndex * 45  // Assuming 45-min granularity
                    const slotEndMinutes = slotStartMinutes + 45

                    return (
                      <div
                        key={`${dayIndex}-${row.time_slot}`}
                        className="rounded-sm transition-all hover:ring-1 hover:ring-ring flex-shrink-0 cursor-pointer"
                        style={{
                          width: '11px',
                          height: '11px',
                          backgroundColor: getCellColor(count),
                        }}
                        onMouseEnter={(e) => handleCellInteraction(day, patternIds, count, slotStartMinutes, slotEndMinutes, e)}
                        onMouseLeave={handleCellLeave}
                        onClick={(e) => handleCellInteraction(day, patternIds, count, slotStartMinutes, slotEndMinutes, e)}
                      />
                    )
                  })}
                </div>
              ))}
            </div>
          </div>

        {/* Empty state message if no data */}
        {maxCount === 0 && (
          <div className="col-span-8 py-8 text-center text-sm text-muted-foreground">
            No pattern data available for this vehicle yet.
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="mt-4 flex flex-wrap items-center gap-3 border-t pt-3">
        <span className="text-xs text-muted-foreground">Sightings per cell:</span>
        <div className="flex items-center gap-1.5">
          <div className="flex items-center gap-1">
            <div
              className="rounded-sm bg-muted/50"
              style={{ width: '11px', height: '11px' }}
            />
            <span className="text-xs text-muted-foreground">0</span>
          </div>
          <div className="flex items-center gap-1">
            <div
              className="rounded-sm"
              style={{ width: '11px', height: '11px', backgroundColor: GREEN_COLORS[1] }}
            />
            <span className="text-xs text-muted-foreground">1-2</span>
          </div>
          <div className="flex items-center gap-1">
            <div
              className="rounded-sm"
              style={{ width: '11px', height: '11px', backgroundColor: GREEN_COLORS[2] }}
            />
            <span className="text-xs text-muted-foreground">3-4</span>
          </div>
          <div className="flex items-center gap-1">
            <div
              className="rounded-sm"
              style={{ width: '11px', height: '11px', backgroundColor: GREEN_COLORS[3] }}
            />
            <span className="text-xs text-muted-foreground">5-9</span>
          </div>
          <div className="flex items-center gap-1">
            <div
              className="rounded-sm"
              style={{ width: '11px', height: '11px', backgroundColor: GREEN_COLORS[4] }}
            />
            <span className="text-xs text-muted-foreground">10-19</span>
          </div>
          <div className="flex items-center gap-1">
            <div
              className="rounded-sm"
              style={{ width: '11px', height: '11px', backgroundColor: GREEN_COLORS[5] }}
            />
            <span className="text-xs text-muted-foreground">20+</span>
          </div>
        </div>
      </div>

      {/* Max count indicator */}
      {maxCount > 0 && (
        <div className="mt-2 text-xs text-muted-foreground">
          Maximum sightings in a cell: <span className="font-medium text-foreground">{maxCount}</span>
        </div>
      )}
    </div>
  )
}
