/**
 * Salary Recommendation Hook
 *
 * Fetches real salary recommendation data from backend API.
 * Replaces hardcoded mercerBenchmarkData array with real database-driven data.
 */

import { useState, useEffect, useCallback } from 'react'
import { salaryRecommendationApi, type SalaryRecommendationResponse } from '@/lib/api'

export interface UseSalaryRecommendationOptions {
  jobTitle: string
  jobDescription?: string
  location?: string
  jobFamily?: string
  careerLevel?: string
  enabled?: boolean  // Allow disabling the hook
}

export interface UseSalaryRecommendationResult {
  data: SalaryRecommendationResponse | null
  loading: boolean
  error: Error | null
  refetch: () => Promise<void>
}

/**
 * Hook to fetch salary recommendation from backend
 *
 * @example
 * ```typescript
 * const { data, loading, error } = useSalaryRecommendation({
 *   jobTitle: 'HR Director',
 *   location: 'Central Business District'
 * })
 *
 * if (loading) return <Skeleton />
 * if (error) return <Error message={error.message} />
 * if (data) return <SalaryChart data={data} />
 * ```
 */
export function useSalaryRecommendation(
  options: UseSalaryRecommendationOptions
): UseSalaryRecommendationResult {
  const { jobTitle, jobDescription, location, jobFamily, careerLevel, enabled = true } = options

  const [data, setData] = useState<SalaryRecommendationResponse | null>(null)
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<Error | null>(null)

  const fetchData = useCallback(async () => {
    // Don't fetch if disabled or no job title
    if (!enabled || !jobTitle || jobTitle.trim() === '') {
      setData(null)
      setLoading(false)
      setError(null)
      return
    }

    setLoading(true)
    setError(null)

    try {
      const result = await salaryRecommendationApi.recommendSalary({
        job_title: jobTitle,
        job_description: jobDescription,
        location: location || 'Central Business District',
        job_family: jobFamily,
        career_level: careerLevel,
      })

      setData(result)
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to fetch salary recommendation')
      setError(error)
      setData(null)
      console.error('Salary recommendation error:', error)
    } finally {
      setLoading(false)
    }
  }, [jobTitle, jobDescription, location, jobFamily, careerLevel, enabled])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  return {
    data,
    loading,
    error,
    refetch: fetchData,
  }
}

/**
 * Transform salary recommendation data to Mercer benchmark format
 *
 * This helper converts the backend API response to the format expected
 * by the frontend Mercer benchmark tables.
 */
export function transformToMercerBenchmarks(
  data: SalaryRecommendationResponse | null
): Array<{
  category: string
  description: string
  p25: number
  p50: number
  p75: number
  sampleSize: number
}> {
  if (!data || !data.success) {
    return []
  }

  // Create benchmarks from matched jobs
  return data.matched_jobs.map((job, index) => ({
    category: index === 0 ? 'Best Match' : 'Similar Job',
    description: `${job.job_code} - ${job.job_title}`,
    p25: data.percentiles.p25,
    p50: data.percentiles.p50,
    p75: data.percentiles.p75,
    sampleSize: data.data_sources.mercer_market_data.total_sample_size,
  }))
}
