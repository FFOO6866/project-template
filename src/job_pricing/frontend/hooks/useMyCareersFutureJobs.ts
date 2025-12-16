/**
 * MyCareersFuture Integration Hook
 *
 * Production-ready hook with debouncing, request cancellation, and error handling.
 * Fetches real job listings from the MyCareersFuture API backend.
 */

import { useState, useEffect } from 'react'
import { useDebounce } from 'use-debounce'
import { config } from '@/lib/config'

export interface MyCareersFutureJob {
  id: string
  title: string
  company: string
  location: string
  salary_min?: number
  salary_max?: number
  posted_date?: string
  employment_type?: string
  description?: string
}

export interface UseMyCareersFutureJobsOptions {
  jobTitle: string
  location?: string
  enabled?: boolean
}

export interface UseMyCareersFutureJobsResult {
  data: MyCareersFutureJob[]
  loading: boolean
  error: Error | null
  disabled: boolean
  cached: boolean
}

/**
 * Hook to fetch MyCareersFuture job listings
 *
 * Features:
 * - Debouncing (500ms) to reduce API calls while typing
 * - Request cancellation to prevent race conditions
 * - Feature flag integration
 * - Loading and error states
 *
 * @example
 * ```typescript
 * const { data, loading, disabled, cached } = useMyCareersFutureJobs({
 *   jobTitle: 'HR Director',
 *   location: 'Singapore'
 * })
 *
 * if (disabled) return null
 * if (loading) return <Skeleton />
 * if (error) return <ErrorMessage error={error} />
 * return <JobsList jobs={data} cached={cached} />
 * ```
 */
export function useMyCareersFutureJobs(
  options: UseMyCareersFutureJobsOptions
): UseMyCareersFutureJobsResult {
  const { jobTitle, location, enabled = true } = options
  const featureEnabled = config.features.myCareersFuture

  // Debounce job title to avoid excessive API calls
  const [debouncedJobTitle] = useDebounce(jobTitle, 500)

  const [data, setData] = useState<MyCareersFutureJob[]>([])
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

    // Fetch jobs from backend API
    const fetchJobs = async () => {
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
          `${config.api.baseUrl}/api/v1/external/mycareersfuture?${params}`,
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
        setData(result.jobs || [])
        setCached(result.cached || false)

        // Log cache status for monitoring
        if (result.cached) {
          console.log('MyCareersFuture: Served from cache')
        }
      } catch (err) {
        // Ignore abort errors (expected when component unmounts)
        if (err instanceof Error && err.name === 'AbortError') {
          return
        }

        const error = err instanceof Error ? err : new Error('Failed to fetch jobs')
        setError(error)
        console.error('MyCareersFuture API error:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchJobs()

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
