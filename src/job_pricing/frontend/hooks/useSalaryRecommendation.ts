/**
 * Salary Recommendation Hook
 *
 * Fetches real salary recommendation data from backend API.
 * Replaces hardcoded mercerBenchmarkData array with real database-driven data.
 */

import { useState, useEffect, useCallback } from 'react'
import { salaryRecommendationApi, type SalaryRecommendationResponse } from '@/lib/api'

/**
 * Job Family Mapping: Convert full names to Mercer short codes
 *
 * This mapping ensures compatibility between document extraction (which returns full names)
 * and the salary recommendation API (which expects 3-letter codes, max 10 chars).
 */
const JOB_FAMILY_MAPPING: Record<string, string> = {
  // Human Resources
  'Human Resources Management': 'HRM',
  'Human Resources': 'HRM',
  'HR': 'HRM',
  'Total Rewards': 'HRM',  // Total Rewards is part of HRM
  'Compensation & Benefits': 'HRM',
  'C&B': 'HRM',

  // IT & Technology
  'Information Technology': 'ICT',
  'Information & Communications Technology': 'ICT',
  'IT': 'ICT',
  'Technology': 'ICT',

  // Finance
  'Finance': 'FIN',
  'Accounting': 'FIN',
  'Finance & Accounting': 'FIN',

  // Marketing
  'Marketing': 'MKT',
  'Sales & Marketing': 'MKT',

  // Operations
  'Operations': 'OPS',
  'Operations Management': 'OPS',

  // Engineering
  'Engineering': 'ENG',

  // Legal
  'Legal': 'LEG',

  // Add more mappings as needed
}

/**
 * Convert full job family name to short Mercer code (max 10 chars)
 *
 * @param jobFamily - Full job family name or short code
 * @returns Short Mercer code (max 10 chars) or undefined if not mappable
 *
 * @example
 * normalizeJobFamily('Human Resources Management') // 'HRM'
 * normalizeJobFamily('IT') // 'ICT'
 * normalizeJobFamily('HRM') // 'HRM' (already short)
 * normalizeJobFamily('') // undefined
 */
export function normalizeJobFamily(jobFamily?: string): string | undefined {
  if (!jobFamily || jobFamily.trim() === '') return undefined

  const trimmed = jobFamily.trim()

  // If already 10 chars or less, return as-is
  if (trimmed.length <= 10) {
    return trimmed
  }

  // Try to find mapping
  const mapped = JOB_FAMILY_MAPPING[trimmed]
  if (mapped) {
    return mapped
  }

  // If no mapping found, log warning and return undefined (skip filtering)
  console.warn(`[Job Family] No mapping found for "${trimmed}" - skipping job_family filter`)
  return undefined
}

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

    // Check if user is authenticated (has token)
    const token = typeof window !== 'undefined' ? localStorage.getItem('job_pricing_access_token') : null
    if (!token) {
      console.warn('[SalaryRecommendation] No authentication token found, skipping fetch')
      setData(null)
      setLoading(false)
      setError(null)
      return
    }

    setLoading(true)
    setError(null)

    try {
      // Normalize job_family to short code (max 10 chars) before sending to API
      const normalizedJobFamily = normalizeJobFamily(jobFamily)

      // Normalize career_level (remove empty strings, convert to undefined)
      const normalizedCareerLevel = careerLevel && careerLevel.trim() !== '' ? careerLevel : undefined

      const result = await salaryRecommendationApi.recommendSalary({
        job_title: jobTitle,
        job_description: jobDescription,
        location: location || 'Central Business District',
        job_family: normalizedJobFamily,
        career_level: normalizedCareerLevel,
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

  // Safely get sample size from confidence factors (preferred) or data sources (fallback)
  const getSampleSize = () => {
    // PREFERRED: Get from confidence.factors.sample_size (correct field name per TypeScript interface)
    if (data.confidence?.factors) {
      const factors = data.confidence.factors as any
      if (factors.sample_size !== undefined && factors.sample_size !== null) {
        return Math.round(factors.sample_size)
      }
    }

    // FALLBACK: Try to get sample size from any available data source
    if (data.data_sources) {
      const sources = Object.values(data.data_sources)
      if (sources.length > 0 && sources[0]?.total_sample_size) {
        return sources[0].total_sample_size
      }
    }

    // Log warning if sample size is unavailable - NO FALLBACK DATA
    console.warn('[SalaryRecommendation] Sample size unavailable from API response:', data)
    throw new Error('Sample size data unavailable from API response')
  }

  const sampleSize = getSampleSize()

  // Create benchmarks from matched jobs
  return data.matched_jobs.map((job, index) => ({
    category: index === 0 ? 'Best Match' : 'Similar Job',
    description: `${job.job_code} - ${job.job_title}`,
    p25: data.percentiles.p25,
    p50: data.percentiles.p50,
    p75: data.percentiles.p75,
    sampleSize,
  }))
}
