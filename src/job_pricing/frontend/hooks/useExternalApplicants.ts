import { useState, useEffect, useCallback, useRef } from 'react'
import { externalApplicantsApi } from '@/lib/api/externalApplicantsApi'

export interface ExternalApplicant {
  year: string
  name?: string
  organisation?: string
  title?: string
  experience?: number
  currentSalary?: number
  expectedSalary?: number
  orgSummary?: string
  roleScope?: string
  status: string
}

export interface UseExternalApplicantsOptions {
  jobTitle?: string
  jobFamily?: string
  enabled?: boolean
}

export interface UseExternalApplicantsReturn {
  data: ExternalApplicant[]
  loading: boolean
  error: Error | null
  refetch: () => Promise<void>
  disabled: boolean
}

const DEBOUNCE_DELAY = 500

export function useExternalApplicants(
  options: UseExternalApplicantsOptions
): UseExternalApplicantsReturn {
  const { jobTitle, jobFamily, enabled = true } = options

  const [data, setData] = useState<ExternalApplicant[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const [disabled, setDisabled] = useState(false)

  const abortControllerRef = useRef<AbortController | null>(null)
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null)

  const fetchData = useCallback(async (signal: AbortSignal) => {
    try {
      setLoading(true)
      setError(null)

      const response = await externalApplicantsApi.getExternalApplicants({
        jobTitle,
        jobFamily,
        signal,
      })

      if (response.success && response.applicants) {
        setData(response.applicants)
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        console.error('[useExternalApplicants] Error:', err)
        setError(err)
        setDisabled(true)
      }
    } finally {
      setLoading(false)
    }
  }, [jobTitle, jobFamily])

  const refetch = useCallback(async () => {
    const controller = new AbortController()
    await fetchData(controller.signal)
  }, [fetchData])

  useEffect(() => {
    if (!enabled || (!jobTitle && !jobFamily)) {
      setData([])
      return
    }

    // Check if user is authenticated (has token)
    const token = typeof window !== 'undefined' ? localStorage.getItem('job_pricing_access_token') : null
    if (!token) {
      console.warn('[useExternalApplicants] No authentication token found, skipping fetch')
      setData([])
      setLoading(false)
      return
    }

    // Cancel previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }

    // Clear previous debounce timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
    }

    // Debounce API call
    debounceTimerRef.current = setTimeout(() => {
      const controller = new AbortController()
      abortControllerRef.current = controller
      fetchData(controller.signal)
    }, DEBOUNCE_DELAY)

    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current)
      }
    }
  }, [enabled, jobTitle, jobFamily, fetchData])

  return {
    data,
    loading,
    error,
    refetch,
    disabled,
  }
}
