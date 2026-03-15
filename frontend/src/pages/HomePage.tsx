import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, X } from 'lucide-react'
import { Header } from '../components/layout/Header'
import { Footer } from '../components/layout/Footer'
import { searchApi } from '../api/search'
import type { VehicleListItem } from '../api/types'
import { getClassificationBadgeColor } from '../lib/utils'

const SEARCH_STORAGE_KEY = 'horizon_search_state'

export function HomePage() {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<VehicleListItem[]>([])
  const [isSearching, setIsSearching] = useState(false)

  // Load previous search state on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem(SEARCH_STORAGE_KEY)
      if (saved) {
        const { query: savedQuery, results: savedResults } = JSON.parse(saved)
        if (savedQuery) {
          setQuery(savedQuery)
          setResults(savedResults)
        }
      }
    } catch (error) {
      console.error('Failed to load search state:', error)
    }
  }, [])

  // Save search state when it changes
  useEffect(() => {
    try {
      if (query || results.length > 0) {
        localStorage.setItem(SEARCH_STORAGE_KEY, JSON.stringify({ query, results }))
      }
    } catch (error) {
      console.error('Failed to save search state:', error)
    }
  }, [query, results])

  // Debounced search function
  const performSearch = useCallback(async (searchQuery: string) => {
    if (!searchQuery.trim()) {
      setResults([])
      return
    }

    setIsSearching(true)
    try {
      const searchResults = await searchApi.search(searchQuery, 10)
      setResults(searchResults)
    } catch (error) {
      console.error('Search failed:', error)
      setResults([])
    } finally {
      setIsSearching(false)
    }
  }, [])

  // Debounce effect
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      performSearch(query)
    }, 300) // 300ms debounce

    return () => clearTimeout(timeoutId)
  }, [query, performSearch])

  const handlePlateClick = (plate: string) => {
    navigate(`/vehicle/${plate}`)
  }

  const handleClear = () => {
    setQuery('')
    setResults([])
    try {
      localStorage.removeItem(SEARCH_STORAGE_KEY)
    } catch (error) {
      console.error('Failed to clear search state:', error)
    }
  }

  return (
    <div className="flex min-h-screen flex-col">
      <Header />

      <main className="flex-1">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-12">
          <div className="mx-auto max-w-2xl text-center">
            <h1 className="text-4xl font-bold tracking-tight sm:text-5xl mb-4">
              License Plate Analysis
            </h1>
            <p className="text-muted-foreground text-lg mb-12">
              Search for a vehicle to view pattern analysis, classification, and predictive intelligence
            </p>

            <div className="relative mb-8">
              <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter license plate (e.g., ABC-123)"
                className="h-14 w-full rounded-lg border bg-background pl-12 pr-24 text-lg focus:outline-none focus:ring-2 focus:ring-primary"
                autoFocus
              />
              {query && (
                <button
                  onClick={handleClear}
                  className="absolute right-20 top-1/2 -translate-y-1/2 rounded-md p-2 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                  type="button"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
              {isSearching && (
                <div className="absolute right-3 top-1/2 -translate-y-1/2">
                  <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                </div>
              )}
            </div>

            {results.length > 0 && (
              <div className="text-left">
                <h2 className="text-xl font-semibold mb-4">Search Results</h2>
                <div className="space-y-2">
                  {results.map((vehicle) => (
                    <button
                      key={vehicle.plate}
                      onClick={() => handlePlateClick(vehicle.plate)}
                      className="w-full rounded-lg border bg-card p-4 text-left transition-colors hover:bg-muted/50"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-semibold text-lg">{vehicle.plate}</p>
                          <p className="text-sm text-muted-foreground">
                            {vehicle.total_readings} sightings • {vehicle.pattern_count} patterns
                          </p>
                        </div>
                        <span
                          className={`rounded-full px-3 py-1 text-sm font-medium ${getClassificationBadgeColor(
                            vehicle.classification
                          )}`}
                        >
                          {vehicle.classification}
                        </span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {query && results.length === 0 && !isSearching && (
              <div className="text-center text-muted-foreground">
                <p>No vehicles found matching "{query}"</p>
                <p className="text-sm mt-2">Try checking the plate number or use fuzzy matching</p>
              </div>
            )}
          </div>
        </div>
      </main>

      <Footer />
    </div>
  )
}
