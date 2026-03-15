import { useEffect, useState } from 'react'
import type { MQTTStatus } from '@/api/types'

const POLL_INTERVAL = 5000 // 5 seconds

export function useMQTTStatus() {
  const [status, setStatus] = useState<MQTTStatus | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchStatus = async () => {
    try {
      const response = await fetch('/api/status/mqtt')
      if (!response.ok) {
        throw new Error('Failed to fetch MQTT status')
      }
      const data = await response.json()
      setStatus(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchStatus()

    // Poll for updates
    const interval = setInterval(fetchStatus, POLL_INTERVAL)

    return () => clearInterval(interval)
  }, [])

  return { status, isLoading, error, refetch: fetchStatus }
}
