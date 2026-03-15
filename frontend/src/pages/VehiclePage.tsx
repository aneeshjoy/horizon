import { useParams, useNavigate, Link } from 'react-router-dom'
import { ArrowLeft, Calendar, Clock, Activity } from 'lucide-react'
import { Header } from '../components/layout/Header'
import { Footer } from '../components/layout/Footer'
import { useVehicleSummary, useVehicleGrid } from '../hooks/useVehicleData'
import { formatDate, getDaysBetween, getClassificationBadgeColor } from '../lib/utils'
import { PatternGridVisualization } from '../components/grid/PatternGridVisualization'
import { ClassificationPanel } from '../components/analytics/ClassificationPanel'
import { StatsPanel } from '../components/analytics/StatsPanel'

export function VehiclePage() {
  const { plate } = useParams<{ plate: string }>()
  const navigate = useNavigate()

  const { data: summary, isLoading: summaryLoading, error: summaryError } = useVehicleSummary(
    plate || '',
    true
  )
  const { data: grid } = useVehicleGrid(plate || '', true)

  if (summaryLoading) {
    return (
      <div className="flex min-h-screen flex-col">
        <Header />
        <main className="flex-1 container py-12">
          <div className="flex items-center justify-center">
            <div className="text-center">
              <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary border-r-transparent" />
              <p className="mt-4 text-muted-foreground">Loading vehicle data...</p>
            </div>
          </div>
        </main>
        <Footer />
      </div>
    )
  }

  if (summaryError || !summary) {
    return (
      <div className="flex min-h-screen flex-col">
        <Header />
        <main className="flex-1 container py-12">
          <div className="mx-auto max-w-md text-center">
            <h1 className="text-2xl font-bold mb-4">Vehicle Not Found</h1>
            <p className="text-muted-foreground mb-8">
              The license plate "{plate}" was not found in the database.
            </p>
            <Link
              to="/"
              className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-primary-foreground hover:bg-primary/90"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Search
            </Link>
          </div>
        </main>
        <Footer />
      </div>
    )
  }

  const daysActive = getDaysBetween(summary.first_seen, summary.last_seen)

  return (
    <div className="flex min-h-screen flex-col">
      <Header />

      <main className="flex-1">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-6">
          {/* Back button and title */}
          <div className="mb-6">
            <button
              onClick={() => navigate(-1)}
              className="mb-3 inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
            >
              <ArrowLeft className="h-4 w-4" />
              Back
            </button>

            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h1 className="text-2xl md:text-3xl font-bold tracking-tight">{summary.plate}</h1>
                <div className="mt-1 flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <Calendar className="h-3.5 w-3.5" />
                    {formatDate(summary.first_seen)} - {formatDate(summary.last_seen)}
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock className="h-3.5 w-3.5" />
                    {daysActive} days active
                  </span>
                  <span className="flex items-center gap-1">
                    <Activity className="h-3.5 w-3.5" />
                    {summary.total_readings} sightings
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <span
                  className={`rounded-full px-3 py-1.5 text-sm font-medium ${getClassificationBadgeColor(
                    summary.classification
                  )}`}
                >
                  {summary.classification}
                </span>
              </div>
            </div>
          </div>

          {/* Statistics - moved to top */}
          <StatsPanel summary={summary} />

          {/* Main content grid */}
          <div className="mt-6 grid gap-6 lg:grid-cols-3">
            {/* Left column: Pattern grid (takes 2/3) */}
            <div className="lg:col-span-2">
              {/* Pattern Grid */}
              {grid ? (
                <PatternGridVisualization
                  grid={grid}
                  plate={summary.plate}
                  patterns={summary.patterns}
                />
              ) : (
                <div className="rounded-lg border bg-card p-8 text-center">
                  <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary border-r-transparent" />
                  <p className="mt-4 text-muted-foreground">Loading pattern grid...</p>
                </div>
              )}
            </div>

            {/* Right column: Analytics (takes 1/3) */}
            <div className="space-y-6">
              {/* Classification Panel */}
              <ClassificationPanel
                classification={summary.classification}
                score={summary.routine_deviation_score}
              />
            </div>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  )
}
