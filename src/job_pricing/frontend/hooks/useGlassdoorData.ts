/**
 * Glassdoor Salary Data Hook
 *
 * Production-ready hook with debouncing, request cancellation, and error handling.
 * Fetches real salary insights from the Glassdoor API backend.
 */

import { useState, useEffect } from 'react'
import { useDebounce } from 'use-debounce'
import { config } from '@/lib/config'

export interface GlassdoorSalaryData {
  id: string
  job_title: string
  company?: string
  location: string
  salary_estimate?: {
    min: number
    max: number
    currency: string
  }
  rating?: number
  reviews_count?: number
  data_source: string
}

export interface UseGlassdoorDataOptions {
  jobTitle: string
  location?: string
  enabled?: boolean
}

export interface UseGlassdoorDataResult {
  data: GlassdoorSalaryData[]
  loading: boolean
  error: Error | null
  disabled: boolean
  cached: boolean
}

/**
 * Hook to fetch Glassdoor salary insights
 *
 * Features:
 * - Debouncing (500ms) to reduce API calls while typing
 * - Request cancellation to prevent race conditions
 * - Feature flag integration
 * - Loading and error states
 * - Cache status tracking
 *
 * @example
 * ```typescript
 * const { data, loading, disabled, cached } = useGlassdoorData({
 *   jobTitle: 'HR Director',
 *   location: 'Singapore'
 * })
 *
 * if (disabled) return null
 * if (loading) return <Skeleton />
 * if (error) return <ErrorMessage error={error} />
 * return <GlassdoorInsights data={data} cached={cached} />
 * ```
 */
export function useGlassdoorData(
  options: UseGlassdoorDataOptions
): UseGlassdoorDataResult {
  const { jobTitle, location, enabled = true } = options
  const featureEnabled = config.features.glassdoor

  // Debounce job title to avoid excessive API calls
  const [debouncedJobTitle] = useDebounce(jobTitle, 500)

  const [data, setData] = useState<GlassdoorSalaryData[]>([])
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<Error | null>(null)
  const [cached, setCached] = useState<boolean>(false)

  useEffect(() => {
    // Feature is disabled - return empty data
    if (!featureEnabled || !enabled || !debouncedJobTitle) {
      setData([])
      setLoading(false)
      setError(null)
      setCached(false)
      return
    }

    // Create abort controller for request cancellation
    const abortController = new AbortController()

    // Fetch salary data from backend API
    const fetchGlassdoorData = async () => {
      setLoading(true)
      setError(null)

      try {
        const params = new URLSearchParams({
          job_title: debouncedJobTitle,
          ...(location && { location })
        })

        // Get JWT token from localStorage
        const token = typeof window !== 'undefined' ? localStorage.getItem('job_pricing_access_token') : null

        const response = await fetch(
          `${config.api.baseUrl}/api/v1/external/glassdoor?${params}`,
          {
            signal: abortController.signal,
            headers: {
              'Content-Type': 'application/json',
              ...(token && { 'Authorization': `Bearer ${token}` }),
            },
          }
        )

        if (!response.ok) {
          throw new Error(`API error: ${response.status} ${response.statusText}`)
        }

        const result = await response.json()
        setData(result.salary_data || [])
        setCached(result.cached || false)

        // Log cache status for monitoring
        if (result.cached) {
          console.log('Glassdoor: Served from cache')
        }
      } catch (err) {
        // Ignore abort errors (expected when component unmounts)
        if (err instanceof Error && err.name === 'AbortError') {
          return
        }

        const error = err instanceof Error ? err : new Error('Failed to fetch Glassdoor data')
        setError(error)
        console.error('Glassdoor API error:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchGlassdoorData()

    // Cleanup: cancel ongoing request when jobTitle, location, or component unmounts
    return () => {
      abortController.abort()
    }
  }, [debouncedJobTitle, location, enabled, featureEnabled])

  return {
    data,
    loading,
    error,
    disabled: !featureEnabled,
    cached,
  }
}
