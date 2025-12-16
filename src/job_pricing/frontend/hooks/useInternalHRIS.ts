/**
 * Internal HRIS Integration Hook (Placeholder)
 *
 * This hook is currently disabled by default (NEXT_PUBLIC_FEATURE_INTERNAL_HRIS=false).
 * When the feature flag is enabled, this hook should fetch real employee salary benchmarks
 * from the company's internal HRIS system API.
 *
 * Purpose: Replace hardcoded internalData and otherDepartmentData arrays with real HRIS integration
 */

import { useState, useEffect } from 'react'
import { config } from '@/lib/config'

export interface InternalEmployeeData {
  id: string
  employee_id?: string // Anonymized or hashed
  department: string
  job_title: string
  experience_years: number
  current_salary: number
  performance_rating?: string
  last_promotion_date?: string
}

export interface UseInternalHRISOptions {
  department?: string
  jobTitle?: string
  enabled?: boolean
}

export interface UseInternalHRISResult {
  data: InternalEmployeeData[]
  loading: boolean
  error: Error | null
  disabled: boolean
}

/**
 * Hook to fetch internal HRIS employee benchmarks
 *
 * Returns empty data by default since feature is disabled.
 * Enable by setting NEXT_PUBLIC_FEATURE_INTERNAL_HRIS=true
 * Requires HRIS system API integration and proper data anonymization.
 *
 * @example
 * ```typescript
 * const { data, loading, disabled } = useInternalHRIS({
 *   department: 'Human Resources',
 *   jobTitle: 'HR Director'
 * })
 *
 * if (disabled) return null
 * if (loading) return <Skeleton />
 * return <InternalBenchmarks data={data} />
 * ```
 */
export function useInternalHRIS(
  options: UseInternalHRISOptions = {}
): UseInternalHRISResult {
  const { department, jobTitle, enabled = true } = options
  const featureEnabled = config.features.internalHRIS

  const [data, setData] = useState<InternalEmployeeData[]>([])
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    // Feature is disabled - return empty data
    if (!featureEnabled || !enabled) {
      setData([])
      setLoading(false)
      setError(null)
      return
    }

    // Fetch internal HRIS data from API
    const fetchInternalData = async () => {
      setLoading(true)
      try {
        const params = new URLSearchParams()
        if (department) params.set('department', department)
        if (jobTitle) params.set('job_title', jobTitle)

        // Get JWT token from localStorage
        const token = typeof window !== 'undefined' ? localStorage.getItem('job_pricing_access_token') : null

        // Skip fetch if no authentication token
        if (!token) {
          console.warn('[useInternalHRIS] No authentication token found, skipping fetch')
          setData([])
          setLoading(false)
          return
        }

        const response = await fetch(
          `${config.api.baseUrl}/api/v1/internal/hris/benchmarks?${params}`,
          {
            headers: {
              'Content-Type': 'application/json',
              ...(token && { 'Authorization': `Bearer ${token}` }),
            },
          }
        )

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const result = await response.json()
        setData(result.employees || []) // Backend returns anonymized data
      } catch (err) {
        console.error('[useInternalHRIS] Error fetching data:', err)
        setError(err instanceof Error ? err : new Error('Failed to fetch HRIS data'))
      } finally {
        setLoading(false)
      }
    }

    fetchInternalData()
  }, [department, jobTitle, enabled, featureEnabled])

  return {
    data,
    loading,
    error,
    disabled: !featureEnabled, // Expose disabled state to components
  }
}
