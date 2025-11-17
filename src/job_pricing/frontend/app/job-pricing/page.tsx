"use client"

import { TooltipContent } from "@/components/ui/tooltip"

import type React from "react"

import { useState } from "react"
import { jobPricingApi, aiApi, salaryRecommendationApi, documentsApi, type JobPricingResultResponse, ApiError } from "@/lib/api"
import { config } from "@/lib/config"
import {
  useSalaryRecommendation,
  transformToMercerBenchmarks,
} from "@/hooks/useSalaryRecommendation"
import { useMyCareersFutureJobs } from "@/hooks/useMyCareersFutureJobs"
import { useGlassdoorData } from "@/hooks/useGlassdoorData"
import { useInternalHRIS } from "@/hooks/useInternalHRIS"
import { useExternalApplicants } from "@/hooks/useExternalApplicants"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Heading } from "@/components/ui/heading"
import { Text } from "@/components/ui/text"
import {
  TrendingUp,
  DollarSign,
  Building2,
  Sparkles,
  BarChart3,
  Download,
  Search,
  Upload,
  FileText,
  AlertCircle,
  Info,
  Edit3,
  X,
  Plus,
} from "lucide-react"
import { DashboardShell } from "@/components/dashboard-shell"
import { Textarea } from "@/components/ui/textarea"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Tooltip, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"

interface JobPricingData {
  jobTitle: string
  location: string
  portfolio: string
  department: string
  employmentType: string
  internalGrade: string
  jobFamily: string
  skillsRequired: string[]
  jobSummary: string
  alternativeTitles: string[]
  mercerJobCode: string
  mercerJobDescription: string
  uploadedFiles: File[]
}

interface CompensationRecommendation {
  baseSalaryRange: { min: number; max: number }
  internalRange: { min: number; q1: number; mid: number; q3: number; max: number }
  targetBonus: number
  totalCash: { min: number; max: number }
  confidenceLevel: "High" | "Medium" | "Low"
  riskLevel: "High" | "Medium" | "Low"
  summary: string
  employmentTypeImpact: string
}

interface MarketDataSource {
  source: string
  p10?: number
  p25?: number
  p50?: number
  p75?: number
  p90?: number
  sampleSize: string
  industry: string
  location: string
  notes: string
  detailedData?: {
    organisation: string
    title: string
    tenure: string
    salaryRange: string
    orgSummary: string
    roleScope: string
  }[]
}

interface MercerBenchmarkData {
  category: string
  description: string
  p25: number
  p50: number
  p75: number
  sampleSize: number
}

export default function DynamicJobPricingPage() {
  const [jobData, setJobData] = useState<Partial<JobPricingData>>({
    jobTitle: "",
    location: "singapore",
    portfolio: "",
    department: "",
    employmentType: "",
    internalGrade: "",
    jobFamily: "",
    skillsRequired: [],
    jobSummary: "",
    alternativeTitles: [],
    mercerJobCode: "",
    mercerJobDescription: "",
    uploadedFiles: [],
  })
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [isGeneratingJobScope, setIsGeneratingJobScope] = useState(false)
  const [isGeneratingSkills, setIsGeneratingSkills] = useState(false)
  const [isMappingMercer, setIsMappingMercer] = useState(false)
  const [isProcessingFiles, setIsProcessingFiles] = useState(false)
  const [uploadProgress, setUploadProgress] = useState<{
    status: 'uploading' | 'extracting' | 'analyzing' | 'generating_alternatives' | 'mapping_mercer' | 'complete' | null
    fileName: string
    message: string
  }>({ status: null, fileName: '', message: '' })
  const [isGeneratingAlternatives, setIsGeneratingAlternatives] = useState(false)
  const [recommendation, setRecommendation] = useState<CompensationRecommendation | null>(null)
  const [apiRequestId, setApiRequestId] = useState<string | null>(null)
  const [apiResponse, setApiResponse] = useState<JobPricingResultResponse | null>(null)
  const [apiError, setApiError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState("input")
  const [hoveredDataSource, setHoveredDataSource] = useState<string | null>(null)
  const [editingAlternatives, setEditingAlternatives] = useState(false)
  const [newAlternativeTitle, setNewAlternativeTitle] = useState("")

  // API hooks for fetching real data (replaces hardcoded mock data)
  const {
    data: salaryRecommendationData,
    loading: salaryLoading,
    error: salaryError,
  } = useSalaryRecommendation({
    jobTitle: jobData.jobTitle || "",
    jobDescription: jobData.jobSummary,
    location: jobData.location,
    jobFamily: jobData.jobFamily,
    careerLevel: jobData.internalGrade,
    enabled: !!jobData.jobTitle,
  })

  const {
    data: mcfJobs,
    loading: mcfLoading,
    error: mcfError,
    disabled: mcfDisabled,
  } = useMyCareersFutureJobs({
    jobTitle: jobData.jobTitle || "",
    location: jobData.location,
    enabled: !!jobData.jobTitle,
  })

  const {
    data: glassdoorData,
    loading: glassdoorLoading,
    error: glassdoorError,
    disabled: glassdoorDisabled,
  } = useGlassdoorData({
    jobTitle: jobData.jobTitle || "",
    location: jobData.location,
    enabled: !!jobData.jobTitle,
  })

  const {
    data: internalHRISData,
    loading: internalHRISLoading,
    error: internalHRISError,
    disabled: internalHRISDisabled,
  } = useInternalHRIS({
    department: jobData.department,
    jobTitle: jobData.jobTitle,
    enabled: !!jobData.jobTitle,
  })

  const {
    data: externalApplicantsData,
    loading: applicantsLoading,
    error: applicantsError,
    disabled: applicantsDisabled,
  } = useExternalApplicants({
    jobTitle: jobData.jobTitle,
    jobFamily: jobData.jobFamily,
    enabled: !!jobData.jobTitle,
  })

  // Transform salary recommendation data to Mercer benchmark format
  const mercerBenchmarkData = transformToMercerBenchmarks(salaryRecommendationData)

  // Feature flags for phased rollout
  const ENABLE_ANALYSIS_RESULTS = false // Hidden for initial version
  const ENABLE_BENCHMARKING = true // Keep benchmarking active

  const [activeFilters, setActiveFilters] = useState({
    dataSources: ["Market Data", "Internal Data", "External Data", "Competitor Data"],
    timePeriod: ["2020-2024", "Current", "YTD 2024"],
    roleLevel: ["Assistant Director", "Grade 10"],
    geography: ["Singapore", "APAC Region"],
    industryFocus: ["Real Estate", "Hospitality", "Conglomerate"],
  })
  const [showAddFilter, setShowAddFilter] = useState(false)
  const [selectedFilterCategory, setSelectedFilterCategory] = useState("")

  const removeFilter = (category: string, filter: string) => {
    setActiveFilters((prev) => ({
      ...prev,
      [category]: prev[category as keyof typeof prev].filter((f) => f !== filter),
    }))
  }

  const addFilter = (category: string, filter: string) => {
    if (!activeFilters[category as keyof typeof activeFilters].includes(filter)) {
      setActiveFilters((prev) => ({
        ...prev,
        [category]: [...prev[category as keyof typeof prev], filter],
      }))
    }
  }

  const filterOptions = {
    dataSources: ["Market Data", "Internal Data", "External Data", "Competitor Data", "Historical Data", "Survey Data"],
    timePeriod: ["2020-2024", "Current", "YTD 2024", "Last 12 Months", "2023", "2022", "Q4 2024"],
    roleLevel: ["Assistant Director", "Grade 10", "Director", "Manager", "Senior Manager", "Grade 9", "Grade 11"],
    geography: ["Singapore", "APAC Region", "Malaysia", "Thailand", "Indonesia", "Global", "Southeast Asia"],
    industryFocus: [
      "Real Estate",
      "Hospitality",
      "Conglomerate",
      "Property Development",
      "Asset Management",
      "Investment",
    ],
  }

  // Function to get MyCareersFuture job listings from API hook
  const getJobListingData = (jobTitle: string, jobFamily: string) => {
    // Return real data from API hook
    // Feature is disabled by default (NEXT_PUBLIC_FEATURE_MYCAREERSFUTURE=false)
    if (mcfDisabled) {
      return []
    }

    // Return all data from hook (filtering happens on backend)
    return mcfJobs
  }

  // Function to get Glassdoor salary data from API hook
  const getGlassdoorData = (jobTitle: string, jobFamily: string) => {
    // Return real data from API hook
    // Feature is disabled by default (NEXT_PUBLIC_FEATURE_GLASSDOOR=false)
    if (glassdoorDisabled) {
      return []
    }

    // Return all data from hook (filtering happens on backend)
    return glassdoorData
  }

  // Function to get Mercer benchmark data from salary recommendation API
  const getMercerData = (mercerJobCode: string, jobFamily: string) => {
    // Return real Mercer data from salary recommendation API
    // mercerBenchmarkData is transformed from salaryRecommendationData
    return mercerBenchmarkData
  }


  // External applicants data from API
  const externalApplicants = externalApplicantsData || []

  // Get filtered data based on job function
  const myCareersFutureJobListings = getJobListingData(jobData.jobTitle || "", jobData.jobFamily || "")
  const glassdoorJobListings = getGlassdoorData(jobData.jobTitle || "", jobData.jobFamily || "")
  const relevantMercerData = getMercerData(jobData.mercerJobCode || "", jobData.jobFamily || "")

  // Calculate insights based on actual data
  const calculateMarketInsights = () => {
    const salaryRanges = myCareersFutureJobListings.map((job) => {
      const range = job.salaryRange.replace("SGD ", "").split(" - ")
      return {
        min: Number.parseInt(range[0].replace(",", "")),
        max: Number.parseInt(range[1].replace(",", "")),
      }
    })

    const avgMin = salaryRanges.reduce((sum, range) => sum + range.min, 0) / salaryRanges.length
    const avgMax = salaryRanges.reduce((sum, range) => sum + range.max, 0) / salaryRanges.length
    const avgSkillsMatch =
      myCareersFutureJobListings.reduce((sum, job) => sum + Number.parseInt(job.skillsMatch.replace("%", "")), 0) /
      myCareersFutureJobListings.length

    return { avgMin, avgMax, avgSkillsMatch, totalListings: myCareersFutureJobListings.length }
  }

  const marketInsights = calculateMarketInsights()

  // File upload handler
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files
    if (!files || files.length === 0) return

    setIsProcessingFiles(true)

    try {
      const uploadedFiles = Array.from(files)

      // Process each file with real API
      for (const file of uploadedFiles) {
        try {
          // Step 1: Uploading
          setUploadProgress({
            status: 'uploading',
            fileName: file.name,
            message: `Uploading ${file.name}...`
          })

          // Step 2: Extracting
          setUploadProgress({
            status: 'extracting',
            fileName: file.name,
            message: 'Extracting text from document...'
          })

          // Step 3: AI Analysis
          setUploadProgress({
            status: 'analyzing',
            fileName: file.name,
            message: 'AI analyzing job details and skills...'
          })

          const extractedData = await documentsApi.extractDocument(file)

          // REPLACE all job data with newly extracted information (clear previous upload data)
          const newJobData = {
            jobTitle: extractedData.job_title || "",
            jobSummary: extractedData.job_summary || "",
            department: extractedData.department || "",
            skillsRequired: extractedData.skills_required || [],
            keyResponsibilities: extractedData.key_responsibilities || [],
            qualifications: extractedData.qualifications || [],
            yearsOfExperienceMin: extractedData.experience_required ? parseInt(extractedData.experience_required) : undefined,
            employmentType: extractedData.employment_type || "",
            jobFamily: extractedData.job_family || "",
            portfolio: extractedData.portfolio || "",
            uploadedFiles: [file],  // Replace with new file only
            // Clear other fields that aren't extracted from document
            location: "",
            internalGrade: "",
            alternativeTitles: [],
            mercerJobCode: "",
            mercerJobDescription: "",
          }

          setJobData(newJobData)

          // Auto-generate Alternative Titles and Mercer Mapping if job title exists
          if (newJobData.jobTitle) {
            console.log(`[AUTO-AI] Starting automatic AI generation for job: ${newJobData.jobTitle}`)

            try {
              // Step 4: Generate Alternative Titles
              console.log('[AUTO-AI] Step 4: Generating alternative titles...')
              setUploadProgress({
                status: 'generating_alternatives',
                fileName: file.name,
                message: 'AI generating alternative job titles...'
              })

              const alternativeTitlesResponse = await aiApi.generateAlternativeTitles({
                job_title: newJobData.jobTitle,
                job_family: newJobData.jobFamily || undefined,
                industry: newJobData.industry || undefined,
              })

              console.log('[AUTO-AI] Alternative titles generated:', alternativeTitlesResponse.alternative_titles)

              // Update with alternative titles
              const dataWithAlternatives = {
                ...newJobData,
                alternativeTitles: alternativeTitlesResponse.alternative_titles
              }
              setJobData(dataWithAlternatives)

              // Step 5: Map to Mercer Code
              console.log('[AUTO-AI] Step 5: Mapping to Mercer...')
              setUploadProgress({
                status: 'mapping_mercer',
                fileName: file.name,
                message: 'AI mapping to Mercer job library...'
              })

              const mercerResponse = await aiApi.mapMercerCode({
                job_title: newJobData.jobTitle,
                job_description: newJobData.jobSummary || undefined,
                job_family: newJobData.jobFamily || undefined,
              })

              console.log('[AUTO-AI] Mercer mapping complete:', mercerResponse.mercer_job_code)

              // Update with Mercer mapping
              setJobData({
                ...dataWithAlternatives,
                mercerJobCode: mercerResponse.mercer_job_code,
                mercerJobDescription: mercerResponse.mercer_job_description,
              })

              console.log('[AUTO-AI] ✅ All automatic AI generation complete!')

            } catch (aiError: any) {
              console.error("❌ [AUTO-AI] AI generation error (non-blocking):", aiError)
              console.error("Error details:", aiError.message, aiError.stack)
              // Show user-visible warning
              setApiError(`⚠️ Auto-generation warning: ${aiError.message || 'AI features failed but document was uploaded successfully'}`)
            }
          } else {
            console.warn('[AUTO-AI] Skipping automatic AI generation - no job title found')
          }

          // Step 6: Complete
          setUploadProgress({
            status: 'complete',
            fileName: file.name,
            message: 'Processing complete!'
          })

          // Clear progress after a short delay
          setTimeout(() => {
            setUploadProgress({ status: null, fileName: '', message: '' })
          }, 2000)
        } catch (error) {
          console.error(`Error extracting document ${file.name}:`, error)
          setUploadProgress({ status: null, fileName: '', message: '' })
          setApiError(error instanceof ApiError ? error.message : "Failed to extract document data")
          // Continue with next file even if one fails
        }
      }
    } catch (error) {
      console.error("Error processing files:", error)
      setUploadProgress({ status: null, fileName: '', message: '' })
      setApiError(error instanceof ApiError ? error.message : "Failed to extract document data")
    } finally {
      setIsProcessingFiles(false)
    }
  }

  const removeFile = (index: number) => {
    const updatedFiles = jobData.uploadedFiles?.filter((_, i) => i !== index) || []
    setJobData({ ...jobData, uploadedFiles: updatedFiles })
  }

  const handleAnalyze = async () => {
    setIsAnalyzing(true)
    setApiError(null)

    try {
      // Call new salary recommendation API
      const response = await salaryRecommendationApi.recommendSalary({
        job_title: jobData.jobTitle || "",
        job_description: jobData.jobSummary || "",
        location: jobData.location || "",
        job_family: jobData.jobFamily || undefined,
        career_level: jobData.internalGrade || undefined,
      })

      // Map API response to UI's expected format
      if (response.success) {
        // Calculate employment type impact (preserve existing logic)
        const employmentTypeMultiplier =
          jobData.employmentType === "permanent" ? 1.0 : jobData.employmentType === "contract" ? 1.15 : 0.95

        const baseMin = response.recommended_range.min
        const baseMax = response.recommended_range.max
        const adjustedMin = baseMin * employmentTypeMultiplier
        const adjustedMax = baseMax * employmentTypeMultiplier

        // Estimate p10 and p90 from the percentiles we have
        const p10 = response.percentiles.p25 * 0.92 // Approximate p10 as ~92% of p25
        const p90 = response.percentiles.p75 * 1.08 // Approximate p90 as ~108% of p75

        setRecommendation({
          baseSalaryRange: { min: Math.round(adjustedMin), max: Math.round(adjustedMax) },
          internalRange: {
            min: Math.round(p10),
            q1: Math.round(response.percentiles.p25),
            mid: Math.round(response.percentiles.p50),
            q3: Math.round(response.percentiles.p75),
            max: Math.round(p90),
          },
          targetBonus: 20,
          totalCash: {
            min: Math.round(adjustedMin * 12 * 1.2),
            max: Math.round(adjustedMax * 12 * 1.2)
          },
          confidenceLevel: response.confidence.level as "High" | "Medium" | "Low",
          riskLevel: response.confidence.level === "High" ? "Low" : response.confidence.level === "Low" ? "High" : "Medium",
          summary: response.summary || "Salary recommendation completed successfully.",
          employmentTypeImpact:
            jobData.employmentType === "permanent"
              ? "Standard market rates applied for permanent positions"
              : jobData.employmentType === "contract"
                ? "15% premium applied for contract positions due to lack of benefits and job security"
                : "5% discount applied for fixed-term positions with potential for conversion",
        })
      } else {
        throw new Error("Salary recommendation failed")
      }

      // Redirect to benchmarking tab (preserve existing behavior)
      if (ENABLE_BENCHMARKING && !ENABLE_ANALYSIS_RESULTS) {
        setActiveTab("benchmarking")
      } else if (ENABLE_ANALYSIS_RESULTS) {
        setActiveTab("analysis")
      }
    } catch (error) {
      console.error("Job pricing analysis error:", error)

      if (error instanceof ApiError) {
        setApiError(`API Error: ${error.message}`)
      } else if (error instanceof Error) {
        setApiError(error.message)
      } else {
        setApiError("An unexpected error occurred during analysis")
      }
    } finally {
      setIsAnalyzing(false)
    }
  }

  const handleGenerateJobScope = async () => {
    if (!jobData.jobTitle) {
      setApiError("Job title is required to generate job description")
      return
    }

    setIsGeneratingJobScope(true)
    setApiError("")

    try {
      const response = await aiApi.generateJobDescription({
        job_title: jobData.jobTitle,
        department: jobData.department || undefined,
        job_family: jobData.jobFamily || undefined,
        key_responsibilities: jobData.keyResponsibilities || undefined,
      })

      setJobData({ ...jobData, jobSummary: response.job_description })
    } catch (error: any) {
      console.error("Failed to generate job description:", error)
      setApiError(error.message || "Failed to generate job description. Please try again.")
    } finally {
      setIsGeneratingJobScope(false)
    }
  }

  const handleGenerateSkills = async () => {
    if (!jobData.jobTitle) {
      setApiError("Job title is required to generate skills")
      return
    }

    setIsGeneratingSkills(true)
    setApiError("")

    try {
      const response = await aiApi.extractSkills({
        job_title: jobData.jobTitle,
        job_description: jobData.jobSummary || undefined,
      })

      setJobData({ ...jobData, skillsRequired: response.skills.map(s => s.skill_name) })
    } catch (error: any) {
      console.error("Failed to generate skills:", error)
      setApiError(error.message || "Failed to generate skills. Please try again.")
    } finally {
      setIsGeneratingSkills(false)
    }
  }

  const handleMapMercer = async () => {
    if (!jobData.jobTitle) {
      setApiError("Job title is required to map to Mercer code")
      return
    }

    setIsMappingMercer(true)
    setApiError("")

    try {
      const response = await aiApi.mapMercerCode({
        job_title: jobData.jobTitle,
        job_description: jobData.jobSummary || undefined,
        job_family: jobData.jobFamily || undefined,
      })

      setJobData({
        ...jobData,
        mercerJobCode: response.mercer_job_code,
        mercerJobDescription: response.mercer_job_description,
      })
    } catch (error: any) {
      console.error("Failed to map Mercer code:", error)
      setApiError(error.message || "Failed to map to Mercer code. Please try again.")
    } finally {
      setIsMappingMercer(false)
    }
  }

  const handleGenerateAlternatives = async () => {
    if (!jobData.jobTitle) {
      setApiError("Job title is required to generate alternative titles")
      return
    }

    setIsGeneratingAlternatives(true)
    setApiError("")

    try {
      const response = await aiApi.generateAlternativeTitles({
        job_title: jobData.jobTitle,
        job_family: jobData.jobFamily || undefined,
        industry: jobData.industry || undefined,
      })

      setJobData({ ...jobData, alternativeTitles: response.alternative_titles })
    } catch (error: any) {
      console.error("Failed to generate alternative titles:", error)
      setApiError(error.message || "Failed to generate alternative titles. Please try again.")
    } finally {
      setIsGeneratingAlternatives(false)
    }
  }

  const addAlternativeTitle = () => {
    if (newAlternativeTitle.trim() && !jobData.alternativeTitles?.includes(newAlternativeTitle.trim())) {
      setJobData({
        ...jobData,
        alternativeTitles: [...(jobData.alternativeTitles || []), newAlternativeTitle.trim()],
      })
      setNewAlternativeTitle("")
    }
  }

  const removeAlternativeTitle = (index: number) => {
    setJobData({
      ...jobData,
      alternativeTitles: jobData.alternativeTitles?.filter((_, i) => i !== index) || [],
    })
  }

  return (
    <DashboardShell>
      <div className="space-y-6">
        <div className="flex justify-between items-start">
          <div>
            <Heading level="h1" className="mb-2">
              Dynamic Job Pricing Engine
            </Heading>
            <Text size="lg" color="muted">
              AI-powered salary recommendations with transparent market data and internal benchmarking for TPC Group
            </Text>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Export PDF
            </Button>
            <Button variant="outline" size="sm">
              <Search className="h-4 w-4 mr-2" />
              Search History
            </Button>
          </div>
        </div>

        {/* Custom Tab Implementation */}
        <div className="space-y-6">
          <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
            <button
              onClick={() => setActiveTab("input")}
              className={`flex-1 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                activeTab === "input" ? "bg-white text-gray-900 shadow-sm" : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Job Input
            </button>

            {/* Analysis Results Tab - Hidden for initial version */}
            {ENABLE_ANALYSIS_RESULTS && (
              <button
                onClick={() => setActiveTab("analysis")}
                disabled={!recommendation}
                className={`flex-1 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                  activeTab === "analysis" && recommendation
                    ? "bg-white text-gray-900 shadow-sm"
                    : "text-gray-400 cursor-not-allowed"
                }`}
              >
                Analysis Results
              </button>
            )}

            {/* Market Benchmarking Tab */}
            <button
              onClick={() => setActiveTab("benchmarking")}
              disabled={!recommendation}
              className={`flex-1 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                activeTab === "benchmarking" && recommendation
                  ? "bg-white text-gray-900 shadow-sm"
                  : "text-gray-400 cursor-not-allowed"
              }`}
            >
              Market Benchmarking
            </button>
          </div>

          {/* Phase Rollout Notice */}
          {!ENABLE_ANALYSIS_RESULTS && (
            <Alert>
              <Info className="h-4 w-4" />
              <AlertDescription>
                <strong>Initial Version:</strong> Advanced analysis features are being fine-tuned and will be available
                in a future release. Current version focuses on core job pricing and market benchmarking functionality.
              </AlertDescription>
            </Alert>
          )}

          {/* Job Input Tab */}
          {activeTab === "input" && (
            <div className="space-y-6">
              {/* File Upload Section */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Upload className="h-5 w-5" />
                    Upload Role Profiles
                  </CardTitle>
                  <CardDescription>
                    Upload DOCX or PDF documents containing job descriptions. AI will extract job summaries, skills, and requirements to auto-populate the form below.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-gray-400 transition-colors">
                    <input
                      type="file"
                      id="file-upload"
                      multiple
                      accept=".pdf,.docx,.doc"
                      onChange={handleFileUpload}
                      className="hidden"
                      disabled={isProcessingFiles}
                    />
                    <label htmlFor="file-upload" className="cursor-pointer">
                      <Upload className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                      <Text size="sm" className="text-gray-600 mb-1">
                        {isProcessingFiles ? "Processing files..." : "Click to upload or drag and drop"}
                      </Text>
                      <Text size="xs" color="muted">
                        PDF, DOCX files up to 10MB each
                      </Text>
                    </label>
                  </div>

                  {/* Progress Indicator */}
                  {uploadProgress.status && (
                    <div className="border border-blue-200 bg-blue-50 rounded-lg p-4 space-y-3">
                      <div className="flex items-center gap-2">
                        <div className="animate-spin rounded-full h-4 w-4 border-2 border-blue-500 border-t-transparent"></div>
                        <Text size="sm" weight="medium" className="text-blue-900">
                          {uploadProgress.fileName}
                        </Text>
                      </div>
                      <div className="space-y-2">
                        {/* Step 1: Uploading */}
                        <div className="flex items-center gap-2">
                          {uploadProgress.status === 'uploading' ? (
                            <div className="h-4 w-4 rounded-full border-2 border-blue-500 border-t-transparent animate-spin"></div>
                          ) : (
                            <div className="h-4 w-4 rounded-full bg-green-500 flex items-center justify-center">
                              <svg className="h-3 w-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                              </svg>
                            </div>
                          )}
                          <Text size="xs" className={uploadProgress.status === 'uploading' ? 'text-blue-700 font-medium' : 'text-gray-600'}>
                            Uploading document
                          </Text>
                        </div>

                        {/* Step 2: Extracting */}
                        <div className="flex items-center gap-2">
                          {uploadProgress.status === 'extracting' ? (
                            <div className="h-4 w-4 rounded-full border-2 border-blue-500 border-t-transparent animate-spin"></div>
                          ) : ['analyzing', 'generating_alternatives', 'mapping_mercer', 'complete'].includes(uploadProgress.status || '') ? (
                            <div className="h-4 w-4 rounded-full bg-green-500 flex items-center justify-center">
                              <svg className="h-3 w-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                              </svg>
                            </div>
                          ) : (
                            <div className="h-4 w-4 rounded-full border-2 border-gray-300"></div>
                          )}
                          <Text size="xs" className={uploadProgress.status === 'extracting' ? 'text-blue-700 font-medium' : 'text-gray-600'}>
                            Extracting text from document
                          </Text>
                        </div>

                        {/* Step 3: AI Analysis */}
                        <div className="flex items-center gap-2">
                          {uploadProgress.status === 'analyzing' ? (
                            <div className="h-4 w-4 rounded-full border-2 border-blue-500 border-t-transparent animate-spin"></div>
                          ) : ['generating_alternatives', 'mapping_mercer', 'complete'].includes(uploadProgress.status || '') ? (
                            <div className="h-4 w-4 rounded-full bg-green-500 flex items-center justify-center">
                              <svg className="h-3 w-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                              </svg>
                            </div>
                          ) : (
                            <div className="h-4 w-4 rounded-full border-2 border-gray-300"></div>
                          )}
                          <Text size="xs" className={uploadProgress.status === 'analyzing' ? 'text-blue-700 font-medium' : 'text-gray-600'}>
                            AI analyzing job details and skills
                          </Text>
                        </div>

                        {/* Step 4: Generate Alternative Titles */}
                        <div className="flex items-center gap-2">
                          {uploadProgress.status === 'generating_alternatives' ? (
                            <div className="h-4 w-4 rounded-full border-2 border-blue-500 border-t-transparent animate-spin"></div>
                          ) : ['mapping_mercer', 'complete'].includes(uploadProgress.status || '') ? (
                            <div className="h-4 w-4 rounded-full bg-green-500 flex items-center justify-center">
                              <svg className="h-3 w-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                              </svg>
                            </div>
                          ) : (
                            <div className="h-4 w-4 rounded-full border-2 border-gray-300"></div>
                          )}
                          <Text size="xs" className={uploadProgress.status === 'generating_alternatives' ? 'text-blue-700 font-medium' : 'text-gray-600'}>
                            AI generating alternative job titles
                          </Text>
                        </div>

                        {/* Step 5: Map to Mercer */}
                        <div className="flex items-center gap-2">
                          {uploadProgress.status === 'mapping_mercer' ? (
                            <div className="h-4 w-4 rounded-full border-2 border-blue-500 border-t-transparent animate-spin"></div>
                          ) : uploadProgress.status === 'complete' ? (
                            <div className="h-4 w-4 rounded-full bg-green-500 flex items-center justify-center">
                              <svg className="h-3 w-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                              </svg>
                            </div>
                          ) : (
                            <div className="h-4 w-4 rounded-full border-2 border-gray-300"></div>
                          )}
                          <Text size="xs" className={uploadProgress.status === 'mapping_mercer' ? 'text-blue-700 font-medium' : 'text-gray-600'}>
                            AI mapping to Mercer job library
                          </Text>
                        </div>

                        {/* Completion Message */}
                        {uploadProgress.status === 'complete' && (
                          <div className="mt-2 flex items-center gap-2 text-green-700">
                            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <Text size="sm" weight="medium">Processing complete!</Text>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {jobData.uploadedFiles && jobData.uploadedFiles.length > 0 && (
                    <div className="space-y-2">
                      <Text size="sm" weight="medium">
                        Uploaded Files:
                      </Text>
                      {jobData.uploadedFiles.map((file, index) => (
                        <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded-md">
                          <div className="flex items-center gap-2">
                            <FileText className="h-4 w-4 text-gray-500" />
                            <Text size="sm">{file.name}</Text>
                            <Badge variant="outline" className="text-xs">
                              {(file.size / 1024 / 1024).toFixed(1)} MB
                            </Badge>
                          </div>
                          <Button variant="ghost" size="sm" onClick={() => removeFile(index)} className="h-6 w-6 p-0">
                            <X className="h-3 w-3" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}

                  <Alert>
                    <Info className="h-4 w-4" />
                    <AlertDescription>
                      AI will extract job summaries, skills, and requirements from uploaded documents to auto-populate
                      the form below.
                    </AlertDescription>
                  </Alert>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Building2 className="h-5 w-5" />
                    Job Details Input
                  </CardTitle>
                  <CardDescription>
                    Enter job details for AI-powered salary analysis across TPC's business portfolio
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="jobTitle">Job Title *</Label>
                      <Input
                        id="jobTitle"
                        placeholder="e.g., Assistant Director, Total Rewards"
                        value={jobData.jobTitle || ""}
                        onChange={(e) => setJobData({ ...jobData, jobTitle: e.target.value })}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="location">Location/Country *</Label>
                      <select
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                        value={jobData.location || ""}
                        onChange={(e) => setJobData({ ...jobData, location: e.target.value })}
                      >
                        <option value="">Select location</option>
                        <option value="singapore">Singapore</option>
                        <option value="malaysia">Malaysia</option>
                        <option value="thailand">Thailand</option>
                        <option value="indonesia">Indonesia</option>
                        <option value="vietnam">Vietnam</option>
                        <option value="china">China</option>
                      </select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="portfolio">Portfolio/Entity *</Label>
                      <select
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                        value={jobData.portfolio || ""}
                        onChange={(e) => setJobData({ ...jobData, portfolio: e.target.value })}
                      >
                        <option value="">Select TPC Entity</option>
                        <option value="TPC Group Corporate Office">TPC Group Corporate Office</option>
                        <option value="TPC Properties">TPC Properties</option>
                        <option value="TPC Hospitality">TPC Hospitality</option>
                        <option value="TPC Investments">TPC Investments</option>
                        <option value="TPC Development">TPC Development</option>
                        <option value="TPC Asset Management">TPC Asset Management</option>
                      </select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="department">Department *</Label>
                      <select
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                        value={jobData.department || ""}
                        onChange={(e) => setJobData({ ...jobData, department: e.target.value })}
                      >
                        <option value="">Select Department</option>
                        <option value="People & Organisation">People & Organisation</option>
                        <option value="Finance">Finance</option>
                        <option value="Operations">Operations</option>
                        <option value="Business Development">Business Development</option>
                        <option value="Asset Management">Asset Management</option>
                        <option value="Project Management">Project Management</option>
                        <option value="Marketing">Marketing</option>
                        <option value="Legal & Compliance">Legal & Compliance</option>
                      </select>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <Label htmlFor="employmentType">Employment Type *</Label>
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger>
                              <Info className="h-4 w-4 text-gray-400" />
                            </TooltipTrigger>
                            <TooltipContent>
                              <p className="max-w-xs">
                                Employment type affects salary benchmarking:
                                <br />• Permanent: Standard market rates
                                <br />• Contract: +15% premium (no benefits)
                                <br />• Fixed-term: -5% (conversion potential)
                              </p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      </div>
                      <select
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                        value={jobData.employmentType || ""}
                        onChange={(e) => setJobData({ ...jobData, employmentType: e.target.value })}
                      >
                        <option value="">Select type</option>
                        <option value="permanent">Permanent</option>
                        <option value="contract">Contract</option>
                        <option value="fixed-term">Fixed-term</option>
                        <option value="secondment">Secondment</option>
                      </select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="internalGrade">Internal Job Grade *</Label>
                      <select
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                        value={jobData.internalGrade || ""}
                        onChange={(e) => setJobData({ ...jobData, internalGrade: e.target.value })}
                      >
                        <option value="">Select Grade</option>
                        <option value="AA">AA - C-Suite</option>
                        <option value="BB">BB - Director Level</option>
                        <option value="CC">CC - Manager Level</option>
                        <option value="DD">DD - Senior Executive</option>
                        <option value="EE">EE - Executive</option>
                        <option value="FF">FF - Associate</option>
                        <option value="10">10 - Assistant Director</option>
                      </select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="jobFamily">Job Family</Label>
                      <Input
                        id="jobFamily"
                        placeholder="e.g., Total Rewards"
                        value={jobData.jobFamily || ""}
                        onChange={(e) => setJobData({ ...jobData, jobFamily: e.target.value })}
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Label>Skills Required (SSG Skills Library)</Label>
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger>
                              <Info className="h-4 w-4 text-gray-400" />
                            </TooltipTrigger>
                            <TooltipContent>
                              <p className="max-w-xs">
                                AI maps skills based on:
                                <br />• Job title and industry context
                                <br />• Internal grade level requirements
                                <br />• Job family specialization
                                <br />• SSG Skills Framework alignment
                                <br />
                                Used for My Careers Future matching (70%+ skill overlap required)
                              </p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleGenerateSkills}
                        disabled={isGeneratingSkills || !jobData.jobTitle}
                      >
                        {isGeneratingSkills ? (
                          <>
                            <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-gray-600 mr-2"></div>
                            Generating...
                          </>
                        ) : (
                          <>
                            <Sparkles className="h-3 w-3 mr-2" />
                            AI Generate Skills
                          </>
                        )}
                      </Button>
                    </div>
                    <div className="flex flex-wrap gap-2 p-3 border rounded-md min-h-[100px] bg-gray-50">
                      {jobData.skillsRequired?.map((skill, index) => (
                        <Badge key={index} variant="secondary" className="text-xs">
                          {skill}
                          <button
                            onClick={() =>
                              setJobData({
                                ...jobData,
                                skillsRequired: jobData.skillsRequired?.filter((_, i) => i !== index),
                              })
                            }
                            className="ml-1 text-gray-500 hover:text-gray-700"
                          >
                            ×
                          </button>
                        </Badge>
                      ))}
                    </div>
                    <Alert>
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>
                        Skills mapping considers job grade (complexity level) and job family (specialization). SSG
                        Skills Library enables precise My Careers Future matching for salary benchmarking.
                      </AlertDescription>
                    </Alert>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label htmlFor="jobSummary">Job Summary</Label>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleGenerateJobScope}
                        disabled={isGeneratingJobScope || !jobData.jobTitle}
                      >
                        {isGeneratingJobScope ? (
                          <>
                            <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-gray-600 mr-2"></div>
                            Generating...
                          </>
                        ) : (
                          <>
                            <Sparkles className="h-3 w-3 mr-2" />
                            AI Generate
                          </>
                        )}
                      </Button>
                    </div>
                    <Textarea
                      id="jobSummary"
                      placeholder="Provide a concise summary of the role responsibilities and key requirements... or use AI Generate to create a comprehensive job summary"
                      className="min-h-[150px]"
                      value={jobData.jobSummary || ""}
                      onChange={(e) => setJobData({ ...jobData, jobSummary: e.target.value })}
                    />
                    <Text size="xs" color="muted">
                      Job Summary provides focused role overview for better market matching compared to lengthy job
                      descriptions.
                    </Text>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Label>Alternative Market Titles</Label>
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger>
                              <Info className="h-4 w-4 text-gray-400" />
                            </TooltipTrigger>
                            <TooltipContent>
                              <p className="max-w-xs">
                                AI generates alternatives from:
                                <br />• Market survey databases
                                <br />• Industry-specific title variations
                                <br />• Regional naming conventions
                                <br />• Competitor job postings
                                <br />
                                Used to expand salary benchmarking coverage
                              </p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      </div>
                      <div className="flex gap-2">
                        <Button variant="ghost" size="sm" onClick={() => setEditingAlternatives(!editingAlternatives)}>
                          <Edit3 className="h-3 w-3 mr-1" />
                          Edit
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={handleGenerateAlternatives}
                          disabled={isGeneratingAlternatives || !jobData.jobTitle}
                        >
                          {isGeneratingAlternatives ? (
                            <>
                              <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-gray-600 mr-2"></div>
                              Generating...
                            </>
                          ) : (
                            <>
                              <Sparkles className="h-3 w-3 mr-2" />
                              AI Generate
                            </>
                          )}
                        </Button>
                      </div>
                    </div>

                    {jobData.alternativeTitles && jobData.alternativeTitles.length > 0 ? (
                      <div className="flex flex-wrap gap-2 p-3 border rounded-md min-h-[60px] bg-gray-50">
                        {jobData.alternativeTitles.map((title, index) => (
                          <Badge key={index} variant="outline" className="text-xs">
                            {title}
                            {editingAlternatives && (
                              <button
                                onClick={() => removeAlternativeTitle(index)}
                                className="ml-1 text-gray-500 hover:text-gray-700"
                              >
                                ×
                              </button>
                            )}
                          </Badge>
                        ))}
                      </div>
                    ) : (
                      <div className="p-6 border-2 border-dashed rounded-lg bg-gray-50 text-center">
                        <Text size="sm" color="muted">
                          Click "AI Generate" to create alternative job titles for better market matching
                        </Text>
                      </div>
                    )}

                    {editingAlternatives && (
                      <div className="flex gap-2">
                        <Input
                          placeholder="Add alternative title..."
                          value={newAlternativeTitle}
                          onChange={(e) => setNewAlternativeTitle(e.target.value)}
                          onKeyPress={(e) => e.key === "Enter" && addAlternativeTitle()}
                        />
                        <Button size="sm" onClick={addAlternativeTitle}>
                          <Plus className="h-3 w-3" />
                        </Button>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Mercer Job Mapping */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Search className="h-5 w-5" />
                    Mercer Job Library Mapping
                  </CardTitle>
                  <CardDescription>
                    AI-powered mapping to Mercer Job Catalogue for accurate benchmarking
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex justify-between items-center">
                    <Text size="sm" weight="medium">
                      Mercer Job Code & Description
                    </Text>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleMapMercer}
                      disabled={isMappingMercer || !jobData.jobTitle}
                    >
                      {isMappingMercer ? (
                        <>
                          <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-gray-600 mr-2"></div>
                          Mapping...
                        </>
                      ) : (
                        <>
                          <Sparkles className="h-3 w-3 mr-2" />
                          AI Map to Mercer
                        </>
                      )}
                    </Button>
                  </div>

                  {jobData.mercerJobCode ? (
                    <div className="space-y-3">
                      <div className="p-3 bg-blue-50 rounded-lg">
                        <Text size="sm" weight="semibold" className="text-blue-800">
                          {jobData.mercerJobCode}
                        </Text>
                      </div>
                      <div className="p-3 border rounded-lg">
                        <Text size="sm" className="whitespace-pre-line">
                          {jobData.mercerJobDescription}
                        </Text>
                      </div>
                    </div>
                  ) : (
                    <div className="p-6 border-2 border-dashed rounded-lg bg-gray-50 text-center">
                      <Text size="sm" color="muted">
                        Click "AI Map to Mercer" to find the best matching Mercer job code
                      </Text>
                    </div>
                  )}
                </CardContent>
              </Card>

              {apiError && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{apiError}</AlertDescription>
                </Alert>
              )}

              <Button onClick={handleAnalyze} disabled={isAnalyzing || !jobData.jobTitle} className="w-full">
                {isAnalyzing ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Analyzing Market Data...
                  </>
                ) : (
                  <>
                    <TrendingUp className="h-4 w-4 mr-2" />
                    Analyze Job Pricing
                  </>
                )}
              </Button>
            </div>
          )}

          {/* Market Benchmarking Tab */}
          {activeTab === "benchmarking" && recommendation && (
            <div className="space-y-6">
              {/* Simple Salary Recommendation Card */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <DollarSign className="h-5 w-5" />
                    Salary Recommendation Summary
                  </CardTitle>
                  <CardDescription>Market-based compensation recommendation for {jobData.jobTitle}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="text-center p-6 bg-blue-50 rounded-lg border border-blue-200">
                      <Text size="sm" weight="semibold" className="text-blue-800 mb-2">
                        Recommended Range
                      </Text>
                      <Text size="2xl" weight="bold" className="text-blue-900 mb-1">
                        SGD {recommendation.baseSalaryRange.min.toLocaleString()} -{" "}
                        {recommendation.baseSalaryRange.max.toLocaleString()}
                      </Text>
                      <Text size="xs" className="text-blue-700">
                        Monthly base salary
                      </Text>
                    </div>

                    <div className="text-center p-6 bg-green-50 rounded-lg border border-green-200">
                      <Text size="sm" weight="semibold" className="text-green-800 mb-2">
                        Market Position
                      </Text>
                      <Text size="2xl" weight="bold" className="text-green-900 mb-1">
                        P70
                      </Text>
                      <Text size="xs" className="text-green-700">
                        Above market median
                      </Text>
                    </div>

                    <div className="text-center p-6 bg-purple-50 rounded-lg border border-purple-200">
                      <Text size="sm" weight="semibold" className="text-purple-800 mb-2">
                        Annual Package
                      </Text>
                      <Text size="2xl" weight="bold" className="text-purple-900 mb-1">
                        SGD {Math.round(recommendation.totalCash.min / 1000)}K
                      </Text>
                      <Text size="xs" className="text-purple-700">
                        With {recommendation.targetBonus}% bonus target
                      </Text>
                    </div>
                  </div>

                  {/* Employment Type Impact */}
                  {jobData.employmentType !== "permanent" && (
                    <Alert className="mt-4">
                      <Info className="h-4 w-4" />
                      <AlertDescription>
                        <strong>Employment Type Impact:</strong> {recommendation.employmentTypeImpact}
                      </AlertDescription>
                    </Alert>
                  )}

                  <div className="mt-6 p-4 bg-slate-50 rounded-lg">
                    <Text size="sm" weight="semibold" className="text-slate-900 mb-2">
                      Key Insights
                    </Text>
                    <Text size="sm" className="text-slate-700">
                      {recommendation.summary}
                    </Text>
                  </div>
                </CardContent>
              </Card>

              {/* Enhanced Mercer Benchmarking Data */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="h-5 w-5" />
                    Mercer Benchmarking Data
                  </CardTitle>
                  <CardDescription>
                    Annual Total Cash (ATC) benchmarks from Mercer database for {jobData.jobTitle} roles
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {salaryLoading && (
                      <div className="animate-pulse space-y-3">
                        <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                        <div className="h-4 bg-gray-200 rounded w-full"></div>
                        <div className="h-4 bg-gray-200 rounded w-5/6"></div>
                        <div className="h-4 bg-gray-200 rounded w-4/5"></div>
                        <div className="text-sm text-gray-500 mt-2">Loading salary benchmarks from backend API...</div>
                      </div>
                    )}

                    {salaryError && (
                      <Alert className="border-red-200 bg-red-50">
                        <AlertCircle className="h-4 w-4 text-red-600" />
                        <AlertDescription className="text-red-800">
                          <strong>Error loading salary data:</strong> {salaryError.message}
                          <br />
                          <span className="text-sm text-red-600">
                            Please check backend API connectivity at {config.api.baseUrl}/api/v1/salary/recommend
                          </span>
                        </AlertDescription>
                      </Alert>
                    )}

                    {!salaryLoading && !salaryError && (
                      <>
                      <Alert>
                        <Info className="h-4 w-4" />
                        <AlertDescription>
                          <strong>Data Source:</strong> Mercer Total Remuneration Survey - Singapore Market, filtered by
                          job code {jobData.mercerJobCode} and related categories. All figures represent Annual Total Cash
                          (ATC) including base salary and target bonus.
                        </AlertDescription>
                      </Alert>

                      <div className="overflow-x-auto">
                        <table className="w-full text-sm border-collapse border border-gray-200">
                          <thead>
                            <tr className="bg-gray-50">
                              <th className="border border-gray-200 px-4 py-3 text-left font-semibold text-gray-700">
                                Benchmark Category
                              </th>
                              <th className="border border-gray-200 px-4 py-3 text-left font-semibold text-gray-700">
                                Description
                              </th>
                              <th className="border border-gray-200 px-4 py-3 text-center font-semibold text-gray-700">
                                P25 (SGD)
                              </th>
                              <th className="border border-gray-200 px-4 py-3 text-center font-semibold text-gray-700">
                                P50 (SGD)
                              </th>
                              <th className="border border-gray-200 px-4 py-3 text-center font-semibold text-gray-700">
                                P75 (SGD)
                              </th>
                              <th className="border border-gray-200 px-4 py-3 text-center font-semibold text-gray-700">
                                Sample Size
                              </th>
                            </tr>
                          </thead>
                          <tbody>
                            {relevantMercerData.map((benchmark, index) => (
                            <tr key={index} className="hover:bg-gray-50">
                              <td className="border border-gray-200 px-4 py-3 font-medium text-gray-900">
                                {benchmark.category}
                              </td>
                              <td className="border border-gray-200 px-4 py-3 text-gray-700">
                                {benchmark.description}
                              </td>
                              <td className="border border-gray-200 px-4 py-3 text-center font-semibold">
                                {benchmark.p25.toLocaleString()}
                              </td>
                              <td className="border border-gray-200 px-4 py-3 text-center font-semibold text-blue-700">
                                {benchmark.p50.toLocaleString()}
                              </td>
                              <td className="border border-gray-200 px-4 py-3 text-center font-semibold">
                                {benchmark.p75.toLocaleString()}
                              </td>
                              <td className="border border-gray-200 px-4 py-3 text-center text-gray-600">
                                {benchmark.sampleSize}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                      <Text size="sm" weight="semibold" className="text-blue-800 mb-2">
                        Key Observations
                      </Text>
                      <div className="space-y-2 text-sm text-blue-700">
                        <div>
                          • <strong>Specific Job Match:</strong> Most targeted data with{" "}
                          {relevantMercerData[0]?.sampleSize} companies
                        </div>
                        <div>
                          • <strong>Total Rewards Specialization:</strong> Shows premium of ~7% over general HR roles
                        </div>
                        <div>
                          • <strong>Career Level vs Position Class:</strong> Director level commands higher compensation
                          than Management class
                        </div>
                        <div>
                          • <strong>Sample Size Impact:</strong> Larger samples provide more reliable benchmarks for
                          decision making
                        </div>
                      </div>
                    </div>
                    </>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* My Careers Future - Job Listings from JSON Data */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Search className="h-5 w-5" />
                    My Careers Future - Job Listings Analysis
                  </CardTitle>
                  <CardDescription>
                    Job postings from Singapore's national jobs portal filtered by {jobData.jobTitle} and related skills
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {/* Summary Statistics based on actual data */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                      <div className="text-center p-3 bg-blue-50 rounded-lg border border-blue-200">
                        <Text size="xs" color="muted" className="mb-1">
                          P50 (Median)
                        </Text>
                        <Text size="sm" weight="semibold" className="text-blue-700">
                          SGD{" "}
                          {Math.round(
                            marketInsights.avgMin + (marketInsights.avgMax - marketInsights.avgMin) / 2,
                          ).toLocaleString()}
                        </Text>
                      </div>
                      <div className="text-center p-3 bg-slate-50 rounded-lg">
                        <Text size="xs" color="muted" className="mb-1">
                          Total Listings
                        </Text>
                        <Text size="sm" weight="semibold">
                          {marketInsights.totalListings} jobs
                        </Text>
                      </div>
                      <div className="text-center p-3 bg-slate-50 rounded-lg">
                        <Text size="xs" color="muted" className="mb-1">
                          Avg Skills Match
                        </Text>
                        <Text size="sm" weight="semibold">
                          {Math.round(marketInsights.avgSkillsMatch)}%
                        </Text>
                      </div>
                      <div className="text-center p-3 bg-slate-50 rounded-lg">
                        <Text size="xs" color="muted" className="mb-1">
                          Last Updated
                        </Text>
                        <Text size="sm" weight="semibold">
                          Dec 15, 2024
                        </Text>
                      </div>
                    </div>

                    <Alert>
                      <Info className="h-4 w-4" />
                      <AlertDescription>
                        <strong>Data Filtering:</strong> Results filtered from comprehensive job listings database to
                        show {jobData.jobTitle} and related Total Rewards positions with{" "}
                        {Math.round(marketInsights.avgSkillsMatch)}%+ SSG Skills Library match.
                      </AlertDescription>
                    </Alert>

                    {/* Job Listings Table from filtered data */}
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm border-collapse border border-gray-200">
                        <thead>
                          <tr className="bg-gray-50">
                            <th className="border border-gray-200 px-4 py-3 text-left font-semibold text-gray-700">
                              Company Name
                            </th>
                            <th className="border border-gray-200 px-4 py-3 text-left font-semibold text-gray-700">
                              Job Title
                            </th>
                            <th className="border border-gray-200 px-4 py-3 text-center font-semibold text-gray-700">
                              Experience Required
                            </th>
                            <th className="border border-gray-200 px-4 py-3 text-center font-semibold text-gray-700">
                              Salary Range
                            </th>
                            <th className="border border-gray-200 px-4 py-3 text-center font-semibold text-gray-700">
                              Date Posted
                            </th>
                            <th className="border border-gray-200 px-4 py-3 text-center font-semibold text-gray-700">
                              Skills Match
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {myCareersFutureJobListings.map((job, index) => (
                            <tr key={index} className="hover:bg-gray-50">
                              <td className="border border-gray-200 px-4 py-3 font-medium text-gray-900">
                                {job.company}
                              </td>
                              <td className="border border-gray-200 px-4 py-3 text-gray-700">{job.jobTitle}</td>
                              <td className="border border-gray-200 px-4 py-3 text-center text-gray-700">
                                {job.experienceRequired}
                              </td>
                              <td className="border border-gray-200 px-4 py-3 text-center font-semibold text-blue-700">
                                {job.salaryRange}
                              </td>
                              <td className="border border-gray-200 px-4 py-3 text-center text-gray-600">
                                {new Date(job.datePosted).toLocaleDateString("en-SG", {
                                  year: "numeric",
                                  month: "short",
                                  day: "numeric",
                                })}
                              </td>
                              <td className="border border-gray-200 px-4 py-3 text-center">
                                <Badge
                                  variant={
                                    Number.parseInt(job.skillsMatch) >= 90
                                      ? "default"
                                      : Number.parseInt(job.skillsMatch) >= 85
                                        ? "secondary"
                                        : "outline"
                                  }
                                  className="text-xs"
                                >
                                  {job.skillsMatch}
                                </Badge>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    <div className="mt-4 p-4 bg-green-50 rounded-lg border border-green-200">
                      <Text size="sm" weight="semibold" className="text-green-800 mb-2">
                        Market Intelligence from Data Analysis
                      </Text>
                      <div className="space-y-2 text-sm text-green-700">
                        <div>
                          • <strong>Salary Range:</strong> SGD {Math.round(marketInsights.avgMin).toLocaleString()} -{" "}
                          {Math.round(marketInsights.avgMax).toLocaleString()} based on {marketInsights.totalListings}{" "}
                          relevant positions
                        </div>
                        <div>
                          • <strong>Premium Employers:</strong>{" "}
                          {myCareersFutureJobListings
                            .filter(
                              (job) =>
                                Number.parseInt(job.salaryRange.split(" - ")[1].replace("SGD ", "").replace(",", "")) >
                                marketInsights.avgMax,
                            )
                            .map((job) => job.company)
                            .slice(0, 2)
                            .join(" and ")}{" "}
                          offer highest compensation
                        </div>
                        <div>
                          • <strong>Skills Alignment:</strong> Average {Math.round(marketInsights.avgSkillsMatch)}%
                          match with SSG Skills Library requirements
                        </div>
                        <div>
                          • <strong>Market Focus:</strong>{" "}
                          {Math.round(
                            (myCareersFutureJobListings.filter(
                              (job) => job.company.includes("Property") || job.company.includes("Land"),
                            ).length /
                              myCareersFutureJobListings.length) *
                              100,
                          )}
                          % of listings from real estate sector
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Glassdoor - Employee Salary Data from JSON */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5" />
                    Glassdoor - Employee-Reported Salary Data
                  </CardTitle>
                  <CardDescription>
                    Employee salary reports filtered for {jobData.jobTitle} and Total Rewards roles with reliability
                    indicators
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {/* Summary Statistics from filtered Glassdoor data */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                      <div className="text-center p-3 bg-blue-50 rounded-lg border border-blue-200">
                        <Text size="xs" color="muted" className="mb-1">
                          P50 (Median)
                        </Text>
                        <Text size="sm" weight="semibold" className="text-blue-700">
                          SGD{" "}
                          {Math.round(
                            glassdoorJobListings.reduce((sum, job) => {
                              const range = job.salaryRange.replace("SGD ", "").split(" - ")
                              return (
                                sum +
                                (Number.parseInt(range[0].replace(",", "")) +
                                  Number.parseInt(range[1].replace(",", ""))) /
                                  2
                              )
                            }, 0) / glassdoorJobListings.length,
                          ).toLocaleString()}
                        </Text>
                      </div>
                      <div className="text-center p-3 bg-slate-50 rounded-lg">
                        <Text size="xs" color="muted" className="mb-1">
                          Total Reviews
                        </Text>
                        <Text size="sm" weight="semibold">
                          {glassdoorJobListings.reduce((sum, job) => sum + job.reviewCount, 0)} reviews
                        </Text>
                      </div>
                      <div className="text-center p-3 bg-slate-50 rounded-lg">
                        <Text size="xs" color="muted" className="mb-1">
                          High Reliability
                        </Text>
                        <Text size="sm" weight="semibold">
                          {Math.round(
                            (glassdoorJobListings.filter((job) => job.reliability === "High").length /
                              glassdoorJobListings.length) *
                              100,
                          )}
                          %
                        </Text>
                      </div>
                      <div className="text-center p-3 bg-slate-50 rounded-lg">
                        <Text size="xs" color="muted" className="mb-1">
                          Last Updated
                        </Text>
                        <Text size="sm" weight="semibold">
                          Dec 15, 2024
                        </Text>
                      </div>
                    </div>

                    <Alert>
                      <Info className="h-4 w-4" />
                      <AlertDescription>
                        <strong>Data Filtering:</strong> Filtered from comprehensive Glassdoor database to show{" "}
                        {glassdoorJobListings.length} relevant Total Rewards salary reports. Reliability scores based on
                        review count and data consistency.
                      </AlertDescription>
                    </Alert>

                    {/* Glassdoor Table from filtered data */}
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm border-collapse border border-gray-200">
                        <thead>
                          <tr className="bg-gray-50">
                            <th className="border border-gray-200 px-4 py-3 text-left font-semibold text-gray-700">
                              Company
                            </th>
                            <th className="border border-gray-200 px-4 py-3 text-left font-semibold text-gray-700">
                              Job Title
                            </th>
                            <th className="border border-gray-200 px-4 py-3 text-center font-semibold text-gray-700">
                              Experience Required
                            </th>
                            <th className="border border-gray-200 px-4 py-3 text-center font-semibold text-gray-700">
                              Reported Salary Range
                            </th>
                            <th className="border border-gray-200 px-4 py-3 text-center font-semibold text-gray-700">
                              Date Posted
                            </th>
                            <th className="border border-gray-200 px-4 py-3 text-center font-semibold text-gray-700">
                              Reliability
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {glassdoorJobListings.map((job, index) => (
                            <tr key={index} className="hover:bg-gray-50">
                              <td className="border border-gray-200 px-4 py-3 font-medium text-gray-900">
                                <div className="flex flex-col">
                                  <span>{job.company}</span>
                                  <div className="flex items-center gap-1 mt-1">
                                    <span className="text-xs text-gray-500">★ {job.companyRating}</span>
                                    <span className="text-xs text-gray-400">({job.reviewCount} reviews)</span>
                                  </div>
                                </div>
                              </td>
                              <td className="border border-gray-200 px-4 py-3 text-gray-700">{job.jobTitle}</td>
                              <td className="border border-gray-200 px-4 py-3 text-center text-gray-700">
                                {job.experienceRequired}
                              </td>
                              <td className="border border-gray-200 px-4 py-3 text-center font-semibold text-blue-700">
                                {job.salaryRange}
                              </td>
                              <td className="border border-gray-200 px-4 py-3 text-center text-gray-600">
                                {new Date(job.datePosted).toLocaleDateString("en-SG", {
                                  year: "numeric",
                                  month: "short",
                                  day: "numeric",
                                })}
                              </td>
                              <td className="border border-gray-200 px-4 py-3 text-center">
                                <Badge
                                  variant={
                                    job.reliability === "High"
                                      ? "default"
                                      : job.reliability === "Medium"
                                        ? "secondary"
                                        : "outline"
                                  }
                                  className="text-xs"
                                >
                                  {job.reliability}
                                </Badge>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    <div className="mt-4 p-4 bg-orange-50 rounded-lg border border-orange-200">
                      <Text size="sm" weight="semibold" className="text-orange-800 mb-2">
                        Employee Salary Intelligence
                      </Text>
                      <div className="space-y-2 text-sm text-orange-700">
                        <div>
                          •{" "}
                          <strong>
                            High Reliability Sources (
                            {Math.round(
                              (glassdoorJobListings.filter((job) => job.reliability === "High").length /
                                glassdoorJobListings.length) *
                                100,
                            )}
                            %):
                          </strong>{" "}
                          Based on companies with 30+ reviews and consistent data
                        </div>
                        <div>
                          • <strong>Premium Sectors:</strong> Banking and Government-linked companies show 15-20% higher
                          compensation
                        </div>
                        <div>
                          • <strong>Average Company Rating:</strong>{" "}
                          {(
                            glassdoorJobListings.reduce((sum, job) => sum + job.companyRating, 0) /
                            glassdoorJobListings.length
                          ).toFixed(1)}
                          /5.0 across Total Rewards employers
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Internal TPC Group Benchmarking with Asian Names */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Building2 className="h-5 w-5" />
                    Internal TPC Group Benchmarking
                  </CardTitle>
                  <CardDescription>
                    Internal compensation data across TPC Group entities with performance correlation
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <Alert>
                      <Info className="h-4 w-4" />
                      <AlertDescription>
                        <strong>Data Source:</strong> Internal HRIS data for TPC Group employees, filtered by job family
                        and grade.
                      </AlertDescription>
                    </Alert>

                    {/* Internal Data Table */}
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm border-collapse border border-gray-200">
                        <thead>
                          <tr className="bg-gray-50">
                            <th className="border border-gray-200 px-4 py-3 text-left font-semibold text-gray-700">
                              Name
                            </th>
                            <th className="border border-gray-200 px-4 py-3 text-left font-semibold text-gray-700">
                              Department
                            </th>
                            <th className="border border-gray-200 px-4 py-3 text-center font-semibold text-gray-700">
                              Title
                            </th>
                            <th className="border border-gray-200 px-4 py-3 text-center font-semibold text-gray-700">
                              Grade
                            </th>
                            <th className="border border-gray-200 px-4 py-3 text-center font-semibold text-gray-700">
                              Monthly Salary
                            </th>
                            <th className="border border-gray-200 px-4 py-3 text-center font-semibold text-gray-700">
                              Annual Cash
                            </th>
                            <th className="border border-gray-200 px-4 py-3 text-center font-semibold text-gray-700">
                              Performance (2024)
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {internalHRISData.map((emp, index) => (
                            <tr key={index} className="hover:bg-gray-50">
                              <td className="border border-gray-200 px-4 py-3 font-medium text-gray-900">{emp.name}</td>
                              <td className="border border-gray-200 px-4 py-3 text-gray-700">{emp.dept}</td>
                              <td className="border border-gray-200 px-4 py-3 text-center text-gray-700">
                                {emp.title}
                              </td>
                              <td className="border border-gray-200 px-4 py-3 text-center font-semibold">
                                {emp.grade}
                              </td>
                              <td className="border border-gray-200 px-4 py-3 text-center font-semibold text-blue-700">
                                SGD {emp.monthlySalary.toLocaleString()}
                              </td>
                              <td className="border border-gray-200 px-4 py-3 text-center font-semibold text-green-700">
                                SGD {emp.annualCash.toLocaleString()}
                              </td>
                              <td className="border border-gray-200 px-4 py-3 text-center">
                                <Badge variant="outline" className="text-xs">
                                  {emp.performance}
                                </Badge>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    {/* Other Departments Data */}
                    <div className="mt-6">
                      <Text size="lg" weight="semibold" className="mb-3">
                        Benchmarking with Other Departments (Same Grade)
                      </Text>
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm border-collapse border border-gray-200">
                          <thead>
                            <tr className="bg-gray-50">
                              <th className="border border-gray-200 px-4 py-3 text-left font-semibold text-gray-700">
                                Name
                              </th>
                              <th className="border border-gray-200 px-4 py-3 text-left font-semibold text-gray-700">
                                Department
                              </th>
                              <th className="border border-gray-200 px-4 py-3 text-center font-semibold text-gray-700">
                                Title
                              </th>
                              <th className="border border-gray-200 px-4 py-3 text-center font-semibold text-gray-700">
                                Grade
                              </th>
                              <th className="border border-gray-200 px-4 py-3 text-center font-semibold text-gray-700">
                                Monthly Salary
                              </th>
                              <th className="border border-gray-200 px-4 py-3 text-center font-semibold text-gray-700">
                                Annual Cash
                              </th>
                            </tr>
                          </thead>
                          <tbody>
                            {internalHRISData.map((emp, index) => (
                              <tr key={index} className="hover:bg-gray-50">
                                <td className="border border-gray-200 px-4 py-3 font-medium text-gray-900">
                                  {emp.name}
                                </td>
                                <td className="border border-gray-200 px-4 py-3 text-gray-700">{emp.dept}</td>
                                <td className="border border-gray-200 px-4 py-3 text-center text-gray-700">
                                  {emp.title}
                                </td>
                                <td className="border border-gray-200 px-4 py-3 text-center font-semibold">
                                  {emp.grade}
                                </td>
                                <td className="border border-gray-200 px-4 py-3 text-center font-semibold text-blue-700">
                                  SGD {emp.monthlySalary.toLocaleString()}
                                </td>
                                <td className="border border-gray-200 px-4 py-3 text-center font-semibold text-green-700">
                                  SGD {emp.annualCash.toLocaleString()}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>

                    <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                      <Text size="sm" weight="semibold" className="text-blue-800 mb-2">
                        Internal Benchmarking Insights
                      </Text>
                      <div className="space-y-2 text-sm text-blue-700">
                        {internalHRISDisabled ? (
                          <div className="text-gray-500 italic">
                            • Internal salary data unavailable (HRIS integration disabled)
                          </div>
                        ) : internalHRISData.length > 0 ? (
                          <>
                            <div>
                              • <strong>Internal Team:</strong> Current employees earn SGD{" "}
                              {Math.min(...internalHRISData.map(e => e.current_salary)).toLocaleString()} -{" "}
                              {Math.max(...internalHRISData.map(e => e.current_salary)).toLocaleString()}
                              monthly, aligning with market benchmarks.
                            </div>
                            <div>
                              • <strong>Department Comparison:</strong> Similar roles across departments show comparable salary ranges.
                            </div>
                          </>
                        ) : (
                          <div className="text-gray-500 italic">
                            • No internal salary data available for this role
                          </div>
                        )}
                        <div>
                          • <strong>Performance Correlation:</strong> High performers (A+, A) generally receive higher
                          compensation within their grade bands.
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* External Applicant Intelligence with Asian Names */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5" />
                    External Applicant Intelligence
                  </CardTitle>
                  <CardDescription>
                    Analysis of recent applicants for Total Rewards roles with salary expectations
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    {/* Summary Statistics from actual applicant data */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                      <div className="text-center p-3 bg-blue-50 rounded-lg border border-blue-200">
                        <Text size="xs" color="muted" className="mb-1">
                          Avg Expected Salary
                        </Text>
                        <Text size="sm" weight="semibold" className="text-blue-700">
                          SGD{" "}
                          {Math.round(
                            externalApplicants.reduce((sum, app) => sum + Number.parseInt(app.expectedSalary) * 12, 0) /
                              externalApplicants.length,
                          ).toLocaleString()}
                        </Text>
                      </div>
                      <div className="text-center p-3 bg-slate-50 rounded-lg">
                        <Text size="xs" color="muted" className="mb-1">
                          Total Applicants
                        </Text>
                        <Text size="sm" weight="semibold">
                          {externalApplicants.length} candidates
                        </Text>
                      </div>
                      <div className="text-center p-3 bg-slate-50 rounded-lg">
                        <Text size="xs" color="muted" className="mb-1">
                          Avg Experience
                        </Text>
                        <Text size="sm" weight="semibold">
                          {Math.round(
                            externalApplicants.reduce((sum, app) => sum + Number.parseInt(app.experience), 0) /
                              externalApplicants.length,
                          )}{" "}
                          years
                        </Text>
                      </div>
                      <div className="text-center p-3 bg-slate-50 rounded-lg">
                        <Text size="xs" color="muted" className="mb-1">
                          Salary Premium
                        </Text>
                        <Text size="sm" weight="semibold">
                          +
                          {Math.round(
                            externalApplicants.reduce(
                              (sum, app) =>
                                sum +
                                ((Number.parseInt(app.expectedSalary) - Number.parseInt(app.currentSalary)) /
                                  Number.parseInt(app.currentSalary)) *
                                  100,
                              0,
                            ) / externalApplicants.length,
                          )}
                          %
                        </Text>
                      </div>
                    </div>

                    {/* Applicant Details */}
                    <div className="space-y-4">
                      {externalApplicants.map((applicant, index) => (
                        <div key={index} className="p-4 border rounded-lg hover:shadow-sm transition-shadow">
                          <div className="flex items-start justify-between mb-3">
                            <div className="flex-1">
                              <div className="flex items-center gap-3 mb-2">
                                <Text size="sm" weight="semibold" className="text-slate-900">
                                  {applicant.name}
                                </Text>
                                <Badge
                                  variant={
                                    applicant.status === "Hired"
                                      ? "default"
                                      : applicant.status === "Offer Extended"
                                        ? "secondary"
                                        : applicant.status === "Declined Offer"
                                          ? "destructive"
                                          : "outline"
                                  }
                                  className="text-xs"
                                >
                                  {applicant.status}
                                </Badge>
                              </div>
                              <Text size="xs" color="muted" className="mb-3">
                                {applicant.title} at {applicant.organisation} • {applicant.experience} years experience
                              </Text>
                            </div>
                            <Badge variant="outline" className="text-xs">
                              {applicant.year}
                            </Badge>
                          </div>

                          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                            <div className="p-3 bg-slate-50 rounded-lg">
                              <Text size="xs" color="muted" className="mb-1">
                                Current Annual Salary
                              </Text>
                              <Text size="sm" weight="semibold">
                                SGD {(Number.parseInt(applicant.currentSalary) * 12).toLocaleString()}
                              </Text>
                            </div>
                            <div className="p-3 bg-green-50 rounded-lg border border-green-200">
                              <Text size="xs" color="muted" className="mb-1">
                                Expected Annual Salary
                              </Text>
                              <Text size="sm" weight="semibold" className="text-green-700">
                                SGD {(Number.parseInt(applicant.expectedSalary) * 12).toLocaleString()}
                              </Text>
                            </div>
                            <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                              <Text size="xs" color="muted" className="mb-1">
                                Salary Increase
                              </Text>
                              <Text size="sm" weight="semibold" className="text-blue-700">
                                +
                                {Math.round(
                                  ((Number.parseInt(applicant.expectedSalary) -
                                    Number.parseInt(applicant.currentSalary)) /
                                    Number.parseInt(applicant.currentSalary)) *
                                    100,
                                )}
                                %
                              </Text>
                            </div>
                          </div>

                          <div className="space-y-2">
                            <Text size="xs" className="text-slate-600">
                              <span className="font-medium">Organization:</span> {applicant.orgSummary}
                            </Text>
                            <Text size="xs" className="text-slate-700">
                              <span className="font-medium">Role Scope:</span> {applicant.roleScope}
                            </Text>
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Data-Driven Insights */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="p-4 bg-orange-50 rounded-lg border border-orange-200">
                        <Text size="sm" weight="semibold" className="text-orange-800 mb-3">
                          Recruitment Intelligence
                        </Text>
                        <div className="space-y-2 text-sm text-orange-700">
                          <div>
                            • <strong>Success Rate:</strong>{" "}
                            {Math.round(
                              (externalApplicants.filter((app) => app.status === "Hired").length /
                                externalApplicants.length) *
                                100,
                            )}
                            % of candidates hired
                          </div>
                          <div>
                            • <strong>Average Expectation:</strong>{" "}
                            {Math.round(
                              externalApplicants.reduce(
                                (sum, app) =>
                                  sum +
                                  ((Number.parseInt(app.expectedSalary) - Number.parseInt(app.currentSalary)) /
                                    Number.parseInt(app.currentSalary)) *
                                    100,
                                0,
                              ) / externalApplicants.length,
                            )}
                            % increase over current salary
                          </div>
                          <div>
                            • <strong>Top Source:</strong>{" "}
                            {externalApplicants.reduce((acc, app) => {
                              const sector =
                                app.organisation.includes("Property") || app.organisation.includes("Land")
                                  ? "Property"
                                  : app.organisation.includes("Shangri-La") || app.organisation.includes("Marina")
                                    ? "Hospitality"
                                    : "Other"
                              acc[sector] = (acc[sector] || 0) + 1
                              return acc
                            }, {} as any).Property > 1
                              ? "Property sector"
                              : "Hospitality sector"}{" "}
                            provides most candidates
                          </div>
                        </div>
                      </div>

                      <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
                        <Text size="sm" weight="semibold" className="text-purple-800 mb-3">
                          Strategic Recommendations
                        </Text>
                        <div className="space-y-2 text-sm text-purple-700">
                          <div>
                            • <strong>Offer Strategy:</strong> Position at P
                            {Math.round(
                              70 +
                                externalApplicants.reduce(
                                  (sum, app) =>
                                    sum +
                                    ((Number.parseInt(app.expectedSalary) - Number.parseInt(app.currentSalary)) /
                                      Number.parseInt(app.currentSalary)) *
                                      100,
                                  0,
                                ) /
                                  externalApplicants.length /
                                  10,
                            )}{" "}
                            based on expectations
                          </div>
                          <div>
                            • <strong>Competition:</strong>{" "}
                            {externalApplicants.filter((app) => app.status === "Declined Offer").length > 0
                              ? "High competition"
                              : "Moderate competition"}{" "}
                            from market
                          </div>
                          <div>
                            • <strong>Speed Factor:</strong> Fast decision process critical for{" "}
                            {Math.round(
                              (externalApplicants.filter((app) => app.status.includes("Interview")).length /
                                externalApplicants.length) *
                                100,
                            )}
                            % in interview process
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Market Benchmarking Tab */}
          {activeTab === "benchmarking" && recommendation && (
            <div className="space-y-6">
              {/* Simple Salary Recommendation Card */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <DollarSign className="h-5 w-5" />
                    Salary Recommendation Summary
                  </CardTitle>
                  <CardDescription>Market-based compensation recommendation for {jobData.jobTitle}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="text-center p-6 bg-blue-50 rounded-lg border border-blue-200">
                      <Text size="sm" weight="semibold" className="text-blue-800 mb-2">
                        Recommended Range
                      </Text>
                      <Text size="2xl" weight="bold" className="text-blue-900 mb-1">
                        SGD {recommendation.baseSalaryRange.min.toLocaleString()} -{" "}
                        {recommendation.baseSalaryRange.max.toLocaleString()}
                      </Text>
                      <Text size="xs" className="text-blue-700">
                        Monthly base salary
                      </Text>
                    </div>

                    <div className="text-center p-6 bg-green-50 rounded-lg border border-green-200">
                      <Text size="sm" weight="semibold" className="text-green-800 mb-2">
                        Market Position
                      </Text>
                      <Text size="2xl" weight="bold" className="text-green-900 mb-1">
                        P70
                      </Text>
                      <Text size="xs" className="text-green-700">
                        Above market median
                      </Text>
                    </div>

                    <div className="text-center p-6 bg-purple-50 rounded-lg border border-purple-200">
                      <Text size="sm" weight="semibold" className="text-purple-800 mb-2">
                        Annual Package
                      </Text>
                      <Text size="2xl" weight="bold" className="text-purple-900 mb-1">
                        SGD {Math.round(recommendation.totalCash.min / 1000)}K
                      </Text>
                      <Text size="xs" className="text-purple-700">
                        With {recommendation.targetBonus}% bonus target
                      </Text>
                    </div>
                  </div>

                  {/* Employment Type Impact */}
                  {jobData.employmentType !== "permanent" && (
                    <Alert className="mt-4">
                      <Info className="h-4 w-4" />
                      <AlertDescription>
                        <strong>Employment Type Impact:</strong> {recommendation.employmentTypeImpact}
                      </AlertDescription>
                    </Alert>
                  )}

                  <div className="mt-6 p-4 bg-slate-50 rounded-lg">
                    <Text size="sm" weight="semibold" className="text-slate-900 mb-2">
                      Key Insights
                    </Text>
                    <Text size="sm" className="text-slate-700">
                      {recommendation.summary}
                    </Text>
                  </div>
                </CardContent>
              </Card>

              {/* Enhanced Mercer Benchmarking Data */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="h-5 w-5" />
                    Mercer Benchmarking Data
                  </CardTitle>
                  <CardDescription>
                    Annual Total Cash (ATC) benchmarks from Mercer database for {jobData.jobTitle} roles
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {salaryLoading && (
                      <div className="animate-pulse space-y-3">
                        <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                        <div className="h-4 bg-gray-200 rounded w-full"></div>
                        <div className="h-4 bg-gray-200 rounded w-5/6"></div>
                        <div className="h-4 bg-gray-200 rounded w-4/5"></div>
                        <div className="text-sm text-gray-500 mt-2">Loading salary benchmarks from backend API...</div>
                      </div>
                    )}

                    {salaryError && (
                      <Alert className="border-red-200 bg-red-50">
                        <AlertCircle className="h-4 w-4 text-red-600" />
                        <AlertDescription className="text-red-800">
                          <strong>Error loading salary data:</strong> {salaryError.message}
                          <br />
                          <span className="text-sm text-red-600">
                            Please check backend API connectivity at {config.api.baseUrl}/api/v1/salary/recommend
                          </span>
                        </AlertDescription>
                      </Alert>
                    )}

                    {!salaryLoading && !salaryError && (
                      <>
                      <Alert>
                        <Info className="h-4 w-4" />
                        <AlertDescription>
                          <strong>Data Source:</strong> Mercer Total Remuneration Survey - Singapore Market, filtered by
                          job code {jobData.mercerJobCode} and related categories. All figures represent Annual Total Cash
                          (ATC) including base salary and target bonus.
                        </AlertDescription>
                      </Alert>

                      <div className="overflow-x-auto">
                        <table className="w-full text-sm border-collapse border border-gray-200">
                          <thead>
                            <tr className="bg-gray-50">
                              <th className="border border-gray-200 px-4 py-3 text-left font-semibold text-gray-700">
                                Benchmark Category
                              </th>
                              <th className="border border-gray-200 px-4 py-3 text-left font-semibold text-gray-700">
                                Description
                              </th>
                              <th className="border border-gray-200 px-4 py-3 text-center font-semibold text-gray-700">
                                P25 (SGD)
                              </th>
                              <th className="border border-gray-200 px-4 py-3 text-center font-semibold text-gray-700">
                                P50 (SGD)
                              </th>
                              <th className="border border-gray-200 px-4 py-3 text-center font-semibold text-gray-700">
                                P75 (SGD)
                              </th>
                              <th className="border border-gray-200 px-4 py-3 text-center font-semibold text-gray-700">
                                Sample Size
                              </th>
                            </tr>
                          </thead>
                          <tbody>
                            {relevantMercerData.map((benchmark, index) => (
                            <tr key={index} className="hover:bg-gray-50">
                              <td className="border border-gray-200 px-4 py-3 font-medium text-gray-900">
                                {benchmark.category}
                              </td>
                              <td className="border border-gray-200 px-4 py-3 text-gray-700">
                                {benchmark.description}
                              </td>
                              <td className="border border-gray-200 px-4 py-3 text-center font-semibold">
                                {benchmark.p25.toLocaleString()}
                              </td>
                              <td className="border border-gray-200 px-4 py-3 text-center font-semibold text-blue-700">
                                {benchmark.p50.toLocaleString()}
                              </td>
                              <td className="border border-gray-200 px-4 py-3 text-center font-semibold">
                                {benchmark.p75.toLocaleString()}
                              </td>
                              <td className="border border-gray-200 px-4 py-3 text-center text-gray-600">
                                {benchmark.sampleSize}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                      <Text size="sm" weight="semibold" className="text-blue-800 mb-2">
                        Key Observations
                      </Text>
                      <div className="space-y-2 text-sm text-blue-700">
                        <div>
                          • <strong>Specific Job Match:</strong> Most targeted data with{" "}
                          {relevantMercerData[0]?.sampleSize} companies
                        </div>
                        <div>
                          • <strong>Total Rewards Specialization:</strong> Shows premium of ~7% over general HR roles
                        </div>
                        <div>
                          • <strong>Career Level vs Position Class:</strong> Director level commands higher compensation
                          than Management class
                        </div>
                        <div>
                          • <strong>Sample Size Impact:</strong> Larger samples provide more reliable benchmarks for
                          decision making
                        </div>
                      </div>
                    </div>
                    </>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* My Careers Future - Job Listings from JSON Data */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Search className="h-5 w-5" />
                    My Careers Future - Job Listings Analysis
                  </CardTitle>
                  <CardDescription>
                    Job postings from Singapore's national jobs portal filtered by {jobData.jobTitle} and related skills
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {/* Summary Statistics based on actual data */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                      <div className="text-center p-3 bg-blue-50 rounded-lg border border-blue-200">
                        <Text size="xs" color="muted" className="mb-1">
                          P50 (Median)
                        </Text>
                        <Text size="sm" weight="semibold" className="text-blue-700">
                          SGD{" "}
                          {Math.round(
                            marketInsights.avgMin + (marketInsights.avgMax - marketInsights.avgMin) / 2,
                          ).toLocaleString()}
                        </Text>
                      </div>
                      <div className="text-center p-3 bg-slate-50 rounded-lg">
                        <Text size="xs" color="muted" className="mb-1">
                          Total Listings
                        </Text>
                        <Text size="sm" weight="semibold">
                          {marketInsights.totalListings} jobs
                        </Text>
                      </div>
                      <div className="text-center p-3 bg-slate-50 rounded-lg">
                        <Text size="xs" color="muted" className="mb-1">
                          Avg Skills Match
                        </Text>
                        <Text size="sm" weight="semibold">
                          {Math.round(marketInsights.avgSkillsMatch)}%
                        </Text>
                      </div>
                      <div className="text-center p-3 bg-slate-50 rounded-lg">
                        <Text size="xs" color="muted" className="mb-1">
                          Last Updated
                        </Text>
                        <Text size="sm" weight="semibold">
                          Dec 15, 2024
                        </Text>
                      </div>
                    </div>

                    <Alert>
                      <Info className="h-4 w-4" />
                      <AlertDescription>
                        <strong>Data Filtering:</strong> Results filtered from comprehensive job listings database to
                        show {jobData.jobTitle} and related Total Rewards positions with{" "}
                        {Math.round(marketInsights.avgSkillsMatch)}%+ SSG Skills Library match.
                      </AlertDescription>
                    </Alert>

                    {/* Job Listings Table from filtered data */}
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm border-collapse border border-gray-200">
                        <thead>
                          <tr className="bg-gray-50">
                            <th className="border border-gray-200 px-4 py-3 text-left font-semibold text-gray-700">
                              Company Name
                            </th>
                            <th className="border border-gray-200 px-4 py-3 text-left font-semibold text-gray-700">
                              Job Title
                            </th>
                            <th className="border border-gray-200 px-4 py-3 text-center font-semibold text-gray-700">
                              Experience Required
                            </th>
                            <th className="border border-gray-200 px-4 py-3 text-center font-semibold text-gray-700">
                              Salary Range
                            </th>
                            <th className="border border-gray-200 px-4 py-3 text-center font-semibold text-gray-700">
                              Date Posted
                            </th>
                            <th className="border border-gray-200 px-4 py-3 text-center font-semibold text-gray-700">
                              Skills Match
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {myCareersFutureJobListings.map((job, index) => (
                            <tr key={index} className="hover:bg-gray-50">
                              <td className="border border-gray-200 px-4 py-3 font-medium text-gray-900">
                                {job.company}
                              </td>
                              <td className="border border-gray-200 px-4 py-3 text-gray-700">{job.jobTitle}</td>
                              <td className="border border-gray-200 px-4 py-3 text-center text-gray-700">
                                {job.experienceRequired}
                              </td>
                              <td className="border border-gray-200 px-4 py-3 text-center font-semibold text-blue-700">
                                {job.salaryRange}
                              </td>
                              <td className="border border-gray-200 px-4 py-3 text-center text-gray-600">
                                {new Date(job.datePosted).toLocaleDateString("en-SG", {
                                  year: "numeric",
                                  month: "short",
                                  day: "numeric",
                                })}
                              </td>
                              <td className="border border-gray-200 px-4 py-3 text-center">
                                <Badge
                                  variant={
                                    Number.parseInt(job.skillsMatch) >= 90
                                      ? "default"
                                      : Number.parseInt(job.skillsMatch) >= 85
                                        ? "secondary"
                                        : "outline"
                                  }
                                  className="text-xs"
                                >
                                  {job.skillsMatch}
                                </Badge>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    <div className="mt-4 p-4 bg-green-50 rounded-lg border border-green-200">
                      <Text size="sm" weight="semibold" className="text-green-800 mb-2">
                        Market Intelligence from Data Analysis
                      </Text>
                      <div className="space-y-2 text-sm text-green-700">
                        <div>
                          • <strong>Salary Range:</strong> SGD {Math.round(marketInsights.avgMin).toLocaleString()} -{" "}
                          {Math.round(marketInsights.avgMax).toLocaleString()} based on {marketInsights.totalListings}{" "}
                          relevant positions
                        </div>
                        <div>
                          • <strong>Premium Employers:</strong>{" "}
                          {myCareersFutureJobListings
                            .filter(
                              (job) =>
                                Number.parseInt(job.salaryRange.split(" - ")[1].replace("SGD ", "").replace(",", "")) >
                                marketInsights.avgMax,
                            )
                            .map((job) => job.company)
                            .slice(0, 2)
                            .join(" and ")}{" "}
                          offer highest compensation
                        </div>
                        <div>
                          • <strong>Skills Alignment:</strong> Average {Math.round(marketInsights.avgSkillsMatch)}%
                          match with SSG Skills Library requirements
                        </div>
                        <div>
                          • <strong>Market Focus:</strong>{" "}
                          {Math.round(
                            (myCareersFutureJobListings.filter(
                              (job) => job.company.includes("Property") || job.company.includes("Land"),
                            ).length /
                              myCareersFutureJobListings.length) *
                              100,
                          )}
                          % of listings from real estate sector
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Glassdoor - Employee Salary Data from JSON */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5" />
                    Glassdoor - Employee-Reported Salary Data
                  </CardTitle>
                  <CardDescription>
                    Employee salary reports filtered for {jobData.jobTitle} and Total Rewards roles with reliability
                    indicators
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {/* Summary Statistics from filtered Glassdoor data */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                      <div className="text-center p-3 bg-blue-50 rounded-lg border border-blue-200">
                        <Text size="xs" color="muted" className="mb-1">
                          P50 (Median)
                        </Text>
                        <Text size="sm" weight="semibold" className="text-blue-700">
                          SGD{" "}
                          {Math.round(
                            glassdoorJobListings.reduce((sum, job) => {
                              const range = job.salaryRange.replace("SGD ", "").split(" - ")
                              return (
                                sum +
                                (Number.parseInt(range[0].replace(",", "")) +
                                  Number.parseInt(range[1].replace(",", ""))) /
                                  2
                              )
                            }, 0) / glassdoorJobListings.length,
                          ).toLocaleString()}
                        </Text>
                      </div>
                      <div className="text-center p-3 bg-slate-50 rounded-lg">
                        <Text size="xs" color="muted" className="mb-1">
                          Total Reviews
                        </Text>
                        <Text size="sm" weight="semibold">
                          {glassdoorJobListings.reduce((sum, job) => sum + job.reviewCount, 0)} reviews
                        </Text>
                      </div>
                      <div className="text-center p-3 bg-slate-50 rounded-lg">
                        <Text size="xs" color="muted" className="mb-1">
                          High Reliability
                        </Text>
                        <Text size="sm" weight="semibold">
                          {Math.round(
                            (glassdoorJobListings.filter((job) => job.reliability === "High").length /
                              glassdoorJobListings.length) *
                              100,
                          )}
                          %
                        </Text>
                      </div>
                      <div className="text-center p-3 bg-slate-50 rounded-lg">
                        <Text size="xs" color="muted" className="mb-1">
                          Last Updated
                        </Text>
                        <Text size="sm" weight="semibold">
                          Dec 15, 2024
                        </Text>
                      </div>
                    </div>

                    <Alert>
                      <Info className="h-4 w-4" />
                      <AlertDescription>
                        <strong>Data Filtering:</strong> Filtered from comprehensive Glassdoor database to show{" "}
                        {glassdoorJobListings.length} relevant Total Rewards salary reports. Reliability scores based on
                        review count and data consistency.
                      </AlertDescription>
                    </Alert>

                    {/* Glassdoor Table from filtered data */}
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm border-collapse border border-gray-200">
                        <thead>
                          <tr className="bg-gray-50">
                            <th className="border border-gray-200 px-4 py-3 text-left font-semibold text-gray-700">
                              Company
                            </th>
                            <th className="border border-gray-200 px-4 py-3 text-left font-semibold text-gray-700">
                              Job Title
                            </th>
                            <th className="border border-gray-200 px-4 py-3 text-center font-semibold text-gray-700">
                              Experience Required
                            </th>
                            <th className="border border-gray-200 px-4 py-3 text-center font-semibold text-gray-700">
                              Reported Salary Range
                            </th>
                            <th className="border border-gray-200 px-4 py-3 text-center font-semibold text-gray-700">
                              Date Posted
                            </th>
                            <th className="border border-gray-200 px-4 py-3 text-center font-semibold text-gray-700">
                              Reliability
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {glassdoorJobListings.map((job, index) => (
                            <tr key={index} className="hover:bg-gray-50">
                              <td className="border border-gray-200 px-4 py-3 font-medium text-gray-900">
                                <div className="flex flex-col">
                                  <span>{job.company}</span>
                                  <div className="flex items-center gap-1 mt-1">
                                    <span className="text-xs text-gray-500">★ {job.companyRating}</span>
                                    <span className="text-xs text-gray-400">({job.reviewCount} reviews)</span>
                                  </div>
                                </div>
                              </td>
                              <td className="border border-gray-200 px-4 py-3 text-gray-700">{job.jobTitle}</td>
                              <td className="border border-gray-200 px-4 py-3 text-center text-gray-700">
                                {job.experienceRequired}
                              </td>
                              <td className="border border-gray-200 px-4 py-3 text-center font-semibold text-blue-700">
                                {job.salaryRange}
                              </td>
                              <td className="border border-gray-200 px-4 py-3 text-center text-gray-600">
                                {new Date(job.datePosted).toLocaleDateString("en-SG", {
                                  year: "numeric",
                                  month: "short",
                                  day: "numeric",
                                })}
                              </td>
                              <td className="border border-gray-200 px-4 py-3 text-center">
                                <Badge
                                  variant={
                                    job.reliability === "High"
                                      ? "default"
                                      : job.reliability === "Medium"
                                        ? "secondary"
                                        : "outline"
                                  }
                                  className="text-xs"
                                >
                                  {job.reliability}
                                </Badge>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    <div className="mt-4 p-4 bg-orange-50 rounded-lg border border-orange-200">
                      <Text size="sm" weight="semibold" className="text-orange-800 mb-2">
                        Employee Salary Intelligence
                      </Text>
                      <div className="space-y-2 text-sm text-orange-700">
                        <div>
                          •{" "}
                          <strong>
                            High Reliability Sources (
                            {Math.round(
                              (glassdoorJobListings.filter((job) => job.reliability === "High").length /
                                glassdoorJobListings.length) *
                                100,
                            )}
                            %):
                          </strong>{" "}
                          Based on companies with 30+ reviews and consistent data
                        </div>
                        <div>
                          • <strong>Premium Sectors:</strong> Banking and Government-linked companies show 15-20% higher
                          compensation
                        </div>
                        <div>
                          • <strong>Average Company Rating:</strong>{" "}
                          {(
                            glassdoorJobListings.reduce((sum, job) => sum + job.companyRating, 0) /
                            glassdoorJobListings.length
                          ).toFixed(1)}
                          /5.0 across Total Rewards employers
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Internal TPC Group Benchmarking with Asian Names */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Building2 className="h-5 w-5" />
                    Internal TPC Group Benchmarking
                  </CardTitle>
                  <CardDescription>
                    Internal compensation data across TPC Group entities with performance correlation
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <Alert>
                      <Info className="h-4 w-4" />
                      <AlertDescription>
                        <strong>Data Source:</strong> Internal HRIS data for TPC Group employees, filtered by job family
                        and grade.
                      </AlertDescription>
                    </Alert>

                    {/* Internal Data Table */}
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm border-collapse border border-gray-200">
                        <thead>
                          <tr className="bg-gray-50">
                            <th className="border border-gray-200 px-4 py-3 text-left font-semibold text-gray-700">
                              Name
                            </th>
                            <th className="border border-gray-200 px-4 py-3 text-left font-semibold text-gray-700">
                              Department
                            </th>
                            <th className="border border-gray-200 px-4 py-3 text-center font-semibold text-gray-700">
                              Title
                            </th>
                            <th className="border border-gray-200 px-4 py-3 text-center font-semibold text-gray-700">
                              Grade
                            </th>
                            <th className="border border-gray-200 px-4 py-3 text-center font-semibold text-gray-700">
                              Monthly Salary
                            </th>
                            <th className="border border-gray-200 px-4 py-3 text-center font-semibold text-gray-700">
                              Annual Cash
                            </th>
                            <th className="border border-gray-200 px-4 py-3 text-center font-semibold text-gray-700">
                              Performance (2024)
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {internalHRISData.map((emp, index) => (
                            <tr key={index} className="hover:bg-gray-50">
                              <td className="border border-gray-200 px-4 py-3 font-medium text-gray-900">{emp.name}</td>
                              <td className="border border-gray-200 px-4 py-3 text-gray-700">{emp.dept}</td>
                              <td className="border border-gray-200 px-4 py-3 text-center text-gray-700">
                                {emp.title}
                              </td>
                              <td className="border border-gray-200 px-4 py-3 text-center font-semibold">
                                {emp.grade}
                              </td>
                              <td className="border border-gray-200 px-4 py-3 text-center font-semibold text-blue-700">
                                SGD {emp.monthlySalary.toLocaleString()}
                              </td>
                              <td className="border border-gray-200 px-4 py-3 text-center font-semibold text-green-700">
                                SGD {emp.annualCash.toLocaleString()}
                              </td>
                              <td className="border border-gray-200 px-4 py-3 text-center">
                                <Badge variant="outline" className="text-xs">
                                  {emp.performance}
                                </Badge>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    {/* Other Departments Data */}
                    <div className="mt-6">
                      <Text size="lg" weight="semibold" className="mb-3">
                        Benchmarking with Other Departments (Same Grade)
                      </Text>
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm border-collapse border border-gray-200">
                          <thead>
                            <tr className="bg-gray-50">
                              <th className="border border-gray-200 px-4 py-3 text-left font-semibold text-gray-700">
                                Name
                              </th>
                              <th className="border border-gray-200 px-4 py-3 text-left font-semibold text-gray-700">
                                Department
                              </th>
                              <th className="border border-gray-200 px-4 py-3 text-center font-semibold text-gray-700">
                                Title
                              </th>
                              <th className="border border-gray-200 px-4 py-3 text-center font-semibold text-gray-700">
                                Grade
                              </th>
                              <th className="border border-gray-200 px-4 py-3 text-center font-semibold text-gray-700">
                                Monthly Salary
                              </th>
                              <th className="border border-gray-200 px-4 py-3 text-center font-semibold text-gray-700">
                                Annual Cash
                              </th>
                            </tr>
                          </thead>
                          <tbody>
                            {internalHRISData.map((emp, index) => (
                              <tr key={index} className="hover:bg-gray-50">
                                <td className="border border-gray-200 px-4 py-3 font-medium text-gray-900">
                                  {emp.name}
                                </td>
                                <td className="border border-gray-200 px-4 py-3 text-gray-700">{emp.dept}</td>
                                <td className="border border-gray-200 px-4 py-3 text-center text-gray-700">
                                  {emp.title}
                                </td>
                                <td className="border border-gray-200 px-4 py-3 text-center font-semibold">
                                  {emp.grade}
                                </td>
                                <td className="border border-gray-200 px-4 py-3 text-center font-semibold text-blue-700">
                                  SGD {emp.monthlySalary.toLocaleString()}
                                </td>
                                <td className="border border-gray-200 px-4 py-3 text-center font-semibold text-green-700">
                                  SGD {emp.annualCash.toLocaleString()}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>

                    <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                      <Text size="sm" weight="semibold" className="text-blue-800 mb-2">
                        Internal Benchmarking Insights
                      </Text>
                      <div className="space-y-2 text-sm text-blue-700">
                        {internalHRISDisabled ? (
                          <div className="text-gray-500 italic">
                            • Internal salary data unavailable (HRIS integration disabled)
                          </div>
                        ) : internalHRISData.length > 0 ? (
                          <>
                            <div>
                              • <strong>Internal Team:</strong> Current employees earn SGD{" "}
                              {Math.min(...internalHRISData.map(e => e.current_salary)).toLocaleString()} -{" "}
                              {Math.max(...internalHRISData.map(e => e.current_salary)).toLocaleString()}
                              monthly, aligning with market benchmarks.
                            </div>
                            <div>
                              • <strong>Department Comparison:</strong> Similar roles across departments show comparable salary ranges.
                            </div>
                          </>
                        ) : (
                          <div className="text-gray-500 italic">
                            • No internal salary data available for this role
                          </div>
                        )}
                        <div>
                          • <strong>Performance Correlation:</strong> High performers (A+, A) generally receive higher
                          compensation within their grade bands.
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* External Applicant Intelligence with Asian Names */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5" />
                    External Applicant Intelligence
                  </CardTitle>
                  <CardDescription>
                    Analysis of recent applicants for Total Rewards roles with salary expectations
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    {/* Summary Statistics from actual applicant data */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                      <div className="text-center p-3 bg-blue-50 rounded-lg border border-blue-200">
                        <Text size="xs" color="muted" className="mb-1">
                          Avg Expected Salary
                        </Text>
                        <Text size="sm" weight="semibold" className="text-blue-700">
                          SGD{" "}
                          {Math.round(
                            externalApplicants.reduce((sum, app) => sum + Number.parseInt(app.expectedSalary) * 12, 0) /
                              externalApplicants.length,
                          ).toLocaleString()}
                        </Text>
                      </div>
                      <div className="text-center p-3 bg-slate-50 rounded-lg">
                        <Text size="xs" color="muted" className="mb-1">
                          Total Applicants
                        </Text>
                        <Text size="sm" weight="semibold">
                          {externalApplicants.length} candidates
                        </Text>
                      </div>
                      <div className="text-center p-3 bg-slate-50 rounded-lg">
                        <Text size="xs" color="muted" className="mb-1">
                          Avg Experience
                        </Text>
                        <Text size="sm" weight="semibold">
                          {Math.round(
                            externalApplicants.reduce((sum, app) => sum + Number.parseInt(app.experience), 0) /
                              externalApplicants.length,
                          )}{" "}
                          years
                        </Text>
                      </div>
                      <div className="text-center p-3 bg-slate-50 rounded-lg">
                        <Text size="xs" color="muted" className="mb-1">
                          Salary Premium
                        </Text>
                        <Text size="sm" weight="semibold">
                          +
                          {Math.round(
                            externalApplicants.reduce(
                              (sum, app) =>
                                sum +
                                ((Number.parseInt(app.expectedSalary) - Number.parseInt(app.currentSalary)) /
                                  Number.parseInt(app.currentSalary)) *
                                  100,
                              0,
                            ) / externalApplicants.length,
                          )}
                          %
                        </Text>
                      </div>
                    </div>

                    {/* Applicant Details */}
                    <div className="space-y-4">
                      {externalApplicants.map((applicant, index) => (
                        <div key={index} className="p-4 border rounded-lg hover:shadow-sm transition-shadow">
                          <div className="flex items-start justify-between mb-3">
                            <div className="flex-1">
                              <div className="flex items-center gap-3 mb-2">
                                <Text size="sm" weight="semibold" className="text-slate-900">
                                  {applicant.name}
                                </Text>
                                <Badge
                                  variant={
                                    applicant.status === "Hired"
                                      ? "default"
                                      : applicant.status === "Offer Extended"
                                        ? "secondary"
                                        : applicant.status === "Declined Offer"
                                          ? "destructive"
                                          : "outline"
                                  }
                                  className="text-xs"
                                >
                                  {applicant.status}
                                </Badge>
                              </div>
                              <Text size="xs" color="muted" className="mb-3">
                                {applicant.title} at {applicant.organisation} • {applicant.experience} years experience
                              </Text>
                            </div>
                            <Badge variant="outline" className="text-xs">
                              {applicant.year}
                            </Badge>
                          </div>

                          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                            <div className="p-3 bg-slate-50 rounded-lg">
                              <Text size="xs" color="muted" className="mb-1">
                                Current Annual Salary
                              </Text>
                              <Text size="sm" weight="semibold">
                                SGD {(Number.parseInt(applicant.currentSalary) * 12).toLocaleString()}
                              </Text>
                            </div>
                            <div className="p-3 bg-green-50 rounded-lg border border-green-200">
                              <Text size="xs" color="muted" className="mb-1">
                                Expected Annual Salary
                              </Text>
                              <Text size="sm" weight="semibold" className="text-green-700">
                                SGD {(Number.parseInt(applicant.expectedSalary) * 12).toLocaleString()}
                              </Text>
                            </div>
                            <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                              <Text size="xs" color="muted" className="mb-1">
                                Salary Increase
                              </Text>
                              <Text size="sm" weight="semibold" className="text-blue-700">
                                +
                                {Math.round(
                                  ((Number.parseInt(applicant.expectedSalary) -
                                    Number.parseInt(applicant.currentSalary)) /
                                    Number.parseInt(applicant.currentSalary)) *
                                    100,
                                )}
                                %
                              </Text>
                            </div>
                          </div>

                          <div className="space-y-2">
                            <Text size="xs" className="text-slate-600">
                              <span className="font-medium">Organization:</span> {applicant.orgSummary}
                            </Text>
                            <Text size="xs" className="text-slate-700">
                              <span className="font-medium">Role Scope:</span> {applicant.roleScope}
                            </Text>
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Data-Driven Insights */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="p-4 bg-orange-50 rounded-lg border border-orange-200">
                        <Text size="sm" weight="semibold" className="text-orange-800 mb-3">
                          Recruitment Intelligence
                        </Text>
                        <div className="space-y-2 text-sm text-orange-700">
                          <div>
                            • <strong>Success Rate:</strong>{" "}
                            {Math.round(
                              (externalApplicants.filter((app) => app.status === "Hired").length /
                                externalApplicants.length) *
                                100,
                            )}
                            % of candidates hired
                          </div>
                          <div>
                            • <strong>Average Expectation:</strong>{" "}
                            {Math.round(
                              externalApplicants.reduce(
                                (sum, app) =>
                                  sum +
                                  ((Number.parseInt(app.expectedSalary) - Number.parseInt(app.currentSalary)) /
                                    Number.parseInt(app.currentSalary)) *
                                    100,
                                0,
                              ) / externalApplicants.length,
                            )}
                            % increase over current salary
                          </div>
                          <div>
                            • <strong>Top Source:</strong>{" "}
                            {externalApplicants.reduce((acc, app) => {
                              const sector =
                                app.organisation.includes("Property") || app.organisation.includes("Land")
                                  ? "Property"
                                  : app.organisation.includes("Shangri-La") || app.organisation.includes("Marina")
                                    ? "Hospitality"
                                    : "Other"
                              acc[sector] = (acc[sector] || 0) + 1
                              return acc
                            }, {} as any).Property > 1
                              ? "Property sector"
                              : "Hospitality sector"}{" "}
                            provides most candidates
                          </div>
                        </div>
                      </div>

                      <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
                        <Text size="sm" weight="semibold" className="text-purple-800 mb-3">
                          Strategic Recommendations
                        </Text>
                        <div className="space-y-2 text-sm text-purple-700">
                          <div>
                            • <strong>Offer Strategy:</strong> Position at P
                            {Math.round(
                              70 +
                                externalApplicants.reduce(
                                  (sum, app) =>
                                    sum +
                                    ((Number.parseInt(app.expectedSalary) - Number.parseInt(app.currentSalary)) /
                                      Number.parseInt(app.currentSalary)) *
                                      100,
                                  0,
                                ) /
                                  externalApplicants.length /
                                  10,
                            )}{" "}
                            based on expectations
                          </div>
                          <div>
                            • <strong>Competition:</strong>{" "}
                            {externalApplicants.filter((app) => app.status === "Declined Offer").length > 0
                              ? "High competition"
                              : "Moderate competition"}{" "}
                            from market
                          </div>
                          <div>
                            • <strong>Speed Factor:</strong> Fast decision process critical for{" "}
                            {Math.round(
                              (externalApplicants.filter((app) => app.status.includes("Interview")).length /
                                externalApplicants.length) *
                                100,
                            )}
                            % in interview process
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </div>
    </DashboardShell>
  )
}
