import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import type { TrendData } from '../../api/types'

interface TrendChartProps {
  trend: TrendData
}

export function TrendChart({ trend }: TrendChartProps) {
  const { weekly_data, trend: trendInfo } = trend

  const getTrendColor = () => {
    switch (trendInfo.direction.toLowerCase()) {
      case 'increasing':
        return '#10B981' // green
      case 'decreasing':
        return '#EF4444' // red
      default:
        return '#3B82F6' // blue
    }
  }

  const getTrendIcon = () => {
    switch (trendInfo.direction.toLowerCase()) {
      case 'increasing':
        return '↑'
      case 'decreasing':
        return '↓'
      default:
        return '→'
    }
  }

  return (
    <div className="rounded-lg border bg-card p-6">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h3 className="font-semibold">Historical Trends</h3>
          <p className="text-sm text-muted-foreground">
            Activity over the past {trend.weeks_analyzed} weeks
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span
            className="text-lg font-semibold"
            style={{ color: getTrendColor() }}
          >
            {getTrendIcon()}
          </span>
          <span className="text-sm text-muted-foreground">
            {trendInfo.direction} ({Math.abs(trendInfo.percent_change).toFixed(1)}%)
          </span>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={weekly_data}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
          <XAxis
            dataKey="week_start"
            tickFormatter={(value) => {
              const date = new Date(value)
              return `${date.getMonth() + 1}/${date.getDate()}`
            }}
            className="text-xs"
          />
          <YAxis className="text-xs" />
          <Tooltip
            contentStyle={{
              backgroundColor: 'hsl(var(--card))',
              border: '1px solid hsl(var(--border))',
              borderRadius: '0.5rem',
            }}
            labelFormatter={(value) => {
              const date = new Date(value)
              return date.toLocaleDateString()
            }}
          />
          <Line
            type="monotone"
            dataKey="sightings"
            stroke={getTrendColor()}
            strokeWidth={2}
            dot={{ fill: getTrendColor(), strokeWidth: 2, r: 4 }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>

      {/* Weekly statistics */}
      <div className="mt-4 grid grid-cols-3 gap-4">
        <div className="rounded-md border bg-muted/50 p-3 text-center">
          <p className="text-xs text-muted-foreground">Total Sightings</p>
          <p className="text-xl font-bold">
            {weekly_data.reduce((sum, week) => sum + week.sightings, 0)}
          </p>
        </div>
        <div className="rounded-md border bg-muted/50 p-3 text-center">
          <p className="text-xs text-muted-foreground">Avg per Week</p>
          <p className="text-xl font-bold">
            {Math.round(
              weekly_data.reduce((sum, week) => sum + week.sightings, 0) / weekly_data.length
            )}
          </p>
        </div>
        <div className="rounded-md border bg-muted/50 p-3 text-center">
          <p className="text-xs text-muted-foreground">Avg Confidence</p>
          <p className="text-xl font-bold">
            {Math.round(
              (weekly_data.reduce((sum, week) => sum + week.avg_confidence, 0) / weekly_data.length) *
                100
            )}
            %
          </p>
        </div>
      </div>
    </div>
  )
}
