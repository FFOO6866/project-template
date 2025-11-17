"use client"

import { TooltipContent } from "@/components/ui/tooltip"

import type React from "react"

import { useState } from "react"
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
    jobTitle: "Assistant Director, Total Rewards",
    location: "singapore",
    portfolio: "TPC Group Corporate Office",
    department: "People & Organisation",
    employmentType: "permanent",
    internalGrade: "10",
    jobFamily: "Total Rewards",
    skillsRequired: [
      "Stakeholder Engagement and Management",
      "Human Resource Digitalisation",
      "Compensation Management",
      "Employee Mobility Management",
      "Total Rewards Philosophy Development",
      "Human Resource Analytics and Insights",
      "Diversity and Inclusion Management",
      "Technology Integration",
      "Strategic Workforce Planning",
    ],
    jobSummary:
      "The Assistant Director, Total Rewards designs organisation-wide performance management strategies and total rewards philosophy for TPC Group to attract and retain talent. He/She establishes performance review cycles and key performance indicators (KPIs) for the business units across TPC's diverse portfolio including property development, hospitality, and investment holdings.",
    alternativeTitles: [
      "Head of Total Rewards",
      "Head of Compensation and Benefits",
      "Head of Performance and Rewards",
    ],
    mercerJobCode: "HRM.04.005.M50",
    mercerJobDescription:
      "Total Rewards work is a specialized area of Rewards focused on the design of a holistic framework of financial and non-financial rewards that reflects the organization's strategy to attract, motivate, and retain employees including:\n\n• Researching and analyzing key perspectives (employee, external labor market, cost, and workforce requirements)\n• Incorporating traditional compensation and benefits elements as well as learning and development opportunities, career frameworks, and work/life benefits\n• Exploring opportunities for segmentation to allow certain performance driving areas of the business to offer fundamentally different total rewards packages\n• Ongoing management, communication, and monitoring of plan results\n\nLevel: A Director (M5) is responsible for strategy execution and operational direction of a business function or a part of a function within local entity/business unit. Supports strategy development for their functional area. Interacts with executive leadership concerning matters of significance to the organization. Typically manages multiple teams led by senior managers and managers.\n\nSpecialization Match Note: Incumbents responsible for the strategy and design of financial and non-financial rewards to attract, motivate and retain employees should be matched to the Total Rewards specialization.\n\nTypical Title: Total Rewards Sr. Manager, Total Rewards Manager, Total Rewards Supervisor",
    uploadedFiles: [],
  })
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [isGeneratingJobScope, setIsGeneratingJobScope] = useState(false)
  const [isGeneratingSkills, setIsGeneratingSkills] = useState(false)
  const [isMappingMercer, setIsMappingMercer] = useState(false)
  const [isProcessingFiles, setIsProcessingFiles] = useState(false)
  const [isGeneratingAlternatives, setIsGeneratingAlternatives] = useState(false)
  const [recommendation, setRecommendation] = useState<CompensationRecommendation | null>(null)
  const [activeTab, setActiveTab] = useState("input")
  const [hoveredDataSource, setHoveredDataSource] = useState<string | null>(null)
  const [editingAlternatives, setEditingAlternatives] = useState(false)
  const [newAlternativeTitle, setNewAlternativeTitle] = useState("")

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

  // Function to get data from JSON files based on job function
  const getJobListingData = (jobTitle: string, jobFamily: string) => {
    // This would normally fetch from JSON files based on the job function
    // For now, returning structured data that would come from JSON files

    // Filter based on job title and skills match
    const relevantListings = myCareersFutureData.filter((job) => {
      const titleMatch =
        job.jobTitle.toLowerCase().includes("total rewards") ||
        job.jobTitle.toLowerCase().includes("compensation") ||
        job.jobTitle.toLowerCase().includes("rewards")
      const skillsMatch = Number.parseInt(job.skillsMatch.replace("%", "")) >= 70
      return titleMatch && skillsMatch
    })

    return relevantListings
  }

  const getGlassdoorData = (jobTitle: string, jobFamily: string) => {
    // This would normally fetch from JSON files based on job function
    return glassdoorData.filter((job) => {
      return (
        job.jobTitle.toLowerCase().includes("total rewards") ||
        job.jobTitle.toLowerCase().includes("compensation") ||
        job.jobTitle.toLowerCase().includes("rewards")
      )
    })
  }

  const getMercerData = (mercerJobCode: string, jobFamily: string) => {
    // This would look up actual Mercer data based on job code and family
    return mercerBenchmarkData.filter((benchmark) => {
      return (
        benchmark.description.toLowerCase().includes("total rewards") ||
        benchmark.description.toLowerCase().includes("human resources") ||
        benchmark.category.includes("Job Family")
      )
    })
  }

  // Enhanced Mercer benchmark data from JSON lookup
  const mercerBenchmarkData: MercerBenchmarkData[] = [
    {
      category: "By Job",
      description: "HRM.04.005.M50 - Total Rewards - Director (M5)",
      p25: 135600,
      p50: 148200,
      p75: 158400,
      sampleSize: 87,
    },
    {
      category: "By Job Family and Career Level",
      description: "Human Resources - Director Level",
      p25: 142800,
      p50: 156000,
      p75: 168000,
      sampleSize: 156,
    },
    {
      category: "By Job Family and Position Class",
      description: "Human Resources - Management Class",
      p25: 138000,
      p50: 151200,
      p75: 162000,
      sampleSize: 203,
    },
    {
      category: "By Sub Job Family and Career Level",
      description: "Total Rewards - Director Level",
      p25: 144000,
      p50: 158400,
      p75: 171600,
      sampleSize: 64,
    },
    {
      category: "By Sub Job Family and Position Class",
      description: "Total Rewards - Management Class",
      p25: 140400,
      p50: 153600,
      p75: 165600,
      sampleSize: 89,
    },
  ]

  // Data from JSON files - My Careers Future listings
  const myCareersFutureData = [
    {
      company: "CapitaLand Group",
      jobTitle: "Head of Total Rewards",
      experienceRequired: "8-10 years",
      salaryRange: "SGD 13,000 - 15,000",
      datePosted: "2024-12-10",
      location: "Singapore",
      jobType: "Permanent",
      skillsMatch: "92%",
    },
    {
      company: "City Developments Limited",
      jobTitle: "Total Rewards Director",
      experienceRequired: "10-12 years",
      salaryRange: "SGD 12,500 - 14,500",
      datePosted: "2024-12-08",
      location: "Singapore",
      jobType: "Permanent",
      skillsMatch: "88%",
    },
    {
      company: "Shangri-La Group",
      jobTitle: "Head of Rewards & Recognition",
      experienceRequired: "8-10 years",
      salaryRange: "SGD 15,000 - 18,000",
      datePosted: "2024-12-05",
      location: "Singapore",
      jobType: "Permanent",
      skillsMatch: "85%",
    },
    {
      company: "Frasers Property",
      jobTitle: "Performance and Rewards Lead",
      experienceRequired: "7-9 years",
      salaryRange: "SGD 14,000 - 16,000",
      datePosted: "2024-12-03",
      location: "Singapore",
      jobType: "Permanent",
      skillsMatch: "90%",
    },
    {
      company: "Keppel Corporation",
      jobTitle: "Assistant Director, Compensation & Benefits",
      experienceRequired: "6-8 years",
      salaryRange: "SGD 11,500 - 13,500",
      datePosted: "2024-12-01",
      location: "Singapore",
      jobType: "Permanent",
      skillsMatch: "94%",
    },
    {
      company: "Marina Bay Sands",
      jobTitle: "Head of Performance & Rewards",
      experienceRequired: "8-10 years",
      salaryRange: "SGD 15,500 - 18,000",
      datePosted: "2024-11-15",
      location: "Singapore",
      jobType: "Permanent",
      skillsMatch: "89%",
    },
  ]

  // Data from JSON files - Glassdoor salary data
  const glassdoorData = [
    {
      company: "CapitaLand Group",
      jobTitle: "Head of Total Rewards",
      experienceRequired: "8-10 years",
      salaryRange: "SGD 12,000 - 15,000",
      datePosted: "2024-12-12",
      reliability: "High",
      reviewCount: 45,
      companyRating: 4.2,
    },
    {
      company: "City Developments Limited",
      jobTitle: "Total Rewards Director",
      experienceRequired: "10-12 years",
      salaryRange: "SGD 13,000 - 16,000",
      datePosted: "2024-12-09",
      reliability: "High",
      reviewCount: 38,
      companyRating: 4.1,
    },
    {
      company: "Shangri-La Group",
      jobTitle: "Head of Rewards & Recognition",
      experienceRequired: "8-10 years",
      salaryRange: "SGD 14,000 - 17,000",
      datePosted: "2024-12-07",
      reliability: "Medium",
      reviewCount: 22,
      companyRating: 4.3,
    },
    {
      company: "Marina Bay Sands",
      jobTitle: "Head of Performance & Rewards",
      experienceRequired: "8-10 years",
      salaryRange: "SGD 15,000 - 18,500",
      datePosted: "2024-11-16",
      reliability: "High",
      reviewCount: 67,
      companyRating: 4.4,
    },
    {
      company: "DBS Bank",
      jobTitle: "Vice President, Total Rewards",
      experienceRequired: "10-12 years",
      salaryRange: "SGD 16,000 - 19,000",
      datePosted: "2024-11-04",
      reliability: "High",
      reviewCount: 89,
      companyRating: 4.3,
    },
  ]

  // Internal data with Asian names
  const internalData = [
    {
      name: "Wong Mei Ling",
      entity: "TPC Group Corporate Office",
      dept: "P&O",
      location: "Singapore",
      title: "Chief People Officer",
      grade: "AA",
      tenure: "8 Years",
      status: "Current",
      monthlySalary: 22500,
      annualCash: 324000,
      performance: "A+ (2024)",
    },
    {
      name: "Lim Wei Han",
      entity: "TPC Group Corporate Office",
      dept: "P&O",
      location: "Singapore",
      title: "Director, Talent Management",
      grade: "BB",
      tenure: "5 Years",
      status: "Current",
      monthlySalary: 15200,
      annualCash: 218880,
      performance: "A (2024)",
    },
    {
      name: "Chen Kai Ming",
      entity: "TPC Group Corporate Office",
      dept: "P&O",
      location: "Singapore",
      title: "Assistant Director, Total Rewards",
      grade: "BB",
      tenure: "3 Years",
      status: "Current",
      monthlySalary: 13800,
      annualCash: 198720,
      performance: "A (2024)",
    },
    {
      name: "Tan Shu Hui",
      entity: "TPC Group Corporate Office",
      dept: "P&O",
      location: "Singapore",
      title: "Manager, Total Rewards & Technology",
      grade: "CC",
      tenure: "2 Years",
      status: "Current",
      monthlySalary: 11200,
      annualCash: 161280,
      performance: "B+ (2024)",
    },
    {
      name: "Lee Xin Yi",
      entity: "TPC Group Corporate Office",
      dept: "P&O",
      location: "Singapore",
      title: "Assistant Director, Total Rewards",
      grade: "BB",
      tenure: "4 Years",
      status: "R - Sep 2022",
      monthlySalary: 13500,
      annualCash: 194400,
      performance: "A (2022)",
    },
  ]

  // Other departments with same grade (Asian names)
  const otherDepartmentData = [
    {
      name: "Zhang Wei Jie",
      entity: "TPC Group Corporate Office",
      dept: "Finance",
      location: "Singapore",
      title: "Assistant Director, Financial Planning",
      grade: "10",
      tenure: "6 Years",
      monthlySalary: 14200,
      annualCash: 204480,
      performance: "A+ (2024)",
    },
    {
      name: "Ng Hui Min",
      entity: "TPC Properties",
      dept: "Operations",
      location: "Singapore",
      title: "Head, Operations Excellence",
      grade: "10",
      tenure: "7 Years",
      monthlySalary: 13600,
      annualCash: 195840,
      performance: "A (2024)",
    },
  ]

  // External applicants data with Asian names
  const externalApplicants = [
    {
      year: "2024",
      name: "Lim Jia Wei",
      organisation: "CapitaLand Group",
      title: "Global Rewards Director",
      experience: "15",
      currentSalary: "12500",
      expectedSalary: "15000",
      orgSummary: "Leading property development and investment company in Asia",
      roleScope: "Strategic rewards design across global property development portfolio",
      status: "Interview Stage 2",
    },
    {
      year: "2024",
      name: "Chan Mei Fang",
      organisation: "City Developments Ltd",
      title: "Head Performance and Rewards",
      experience: "12",
      currentSalary: "11800",
      expectedSalary: "14500",
      orgSummary: "Diversified real estate company with hospitality and residential focus",
      roleScope: "End-to-end performance management and rewards strategy",
      status: "Offer Extended",
    },
    {
      year: "2024",
      name: "Tan Keng Hua",
      organisation: "Shangri-La Group",
      title: "Head of Rewards",
      experience: "10",
      currentSalary: "14200",
      expectedSalary: "16000",
      orgSummary: "Luxury hospitality group with global presence",
      roleScope: "Global rewards strategy for hospitality operations",
      status: "Declined Offer",
    },
    {
      year: "2023",
      name: "Wong Siew Ling",
      organisation: "Frasers Property",
      title: "Total Rewards Manager",
      experience: "8",
      currentSalary: "10500",
      expectedSalary: "13000",
      orgSummary: "Integrated real estate company with diversified portfolio",
      roleScope: "Total rewards optimization and market benchmarking",
      status: "Hired",
    },
  ]

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
    if (!files) return

    setIsProcessingFiles(true)

    // Simulate file processing
    await new Promise((resolve) => setTimeout(resolve, 2000))

    const uploadedFiles = Array.from(files)
    setJobData({ ...jobData, uploadedFiles: [...(jobData.uploadedFiles || []), ...uploadedFiles] })

    // Simulate AI extraction from uploaded files
    if (uploadedFiles.length > 0) {
      const extractedJobSummary = `Based on uploaded documents: The Assistant Director, Total Rewards leads strategic compensation design across TPC Group's diversified portfolio. Key responsibilities include developing market-competitive salary structures, managing performance-based incentive programs, and ensuring regulatory compliance across property development, hospitality, and investment sectors. The role requires deep expertise in job evaluation methodologies, market benchmarking, and stakeholder management to support TPC's 2,800+ employees across multiple business units.

Key Accountabilities:
• Design and implement total rewards frameworks aligned with business strategy
• Conduct comprehensive market analysis using Mercer, Willis Towers Watson methodologies
• Lead annual compensation review processes and budget planning
• Ensure internal equity and external competitiveness across all business units
• Partner with senior leadership on strategic workforce planning initiatives`

      setJobData({ ...jobData, jobSummary: extractedJobSummary, uploadedFiles: uploadedFiles })
    }

    setIsProcessingFiles(false)
  }

  const removeFile = (index: number) => {
    const updatedFiles = jobData.uploadedFiles?.filter((_, i) => i !== index) || []
    setJobData({ ...jobData, uploadedFiles: updatedFiles })
  }

  const handleAnalyze = async () => {
    setIsAnalyzing(true)
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 3000))

    // Calculate employment type impact
    const employmentTypeMultiplier =
      jobData.employmentType === "permanent" ? 1.0 : jobData.employmentType === "contract" ? 1.15 : 0.95

    const baseMin = 11800 * employmentTypeMultiplier
    const baseMax = 14200 * employmentTypeMultiplier

    setRecommendation({
      baseSalaryRange: { min: Math.round(baseMin), max: Math.round(baseMax) },
      internalRange: { min: 10500, q1: Math.round(baseMin), mid: 12800, q3: Math.round(baseMax), max: 15500 },
      targetBonus: 20,
      totalCash: { min: Math.round(baseMin * 12 * 1.2), max: Math.round(baseMax * 12 * 1.2) },
      confidenceLevel: "High",
      riskLevel: "Medium",
      summary:
        "Based on comprehensive market analysis from 3 data sources, recommend positioning at P65-P75 to attract qualified candidates in Singapore's competitive Total Rewards market.",
      employmentTypeImpact:
        jobData.employmentType === "permanent"
          ? "Standard market rates applied for permanent positions"
          : jobData.employmentType === "contract"
            ? "15% premium applied for contract positions due to lack of benefits and job security"
            : "5% discount applied for fixed-term positions with potential for conversion",
    })
    setIsAnalyzing(false)

    // Redirect to benchmarking tab instead of analysis for initial version
    if (ENABLE_BENCHMARKING && !ENABLE_ANALYSIS_RESULTS) {
      setActiveTab("benchmarking")
    } else if (ENABLE_ANALYSIS_RESULTS) {
      setActiveTab("analysis")
    }
  }

  const handleGenerateJobScope = async () => {
    setIsGeneratingJobScope(true)
    await new Promise((resolve) => setTimeout(resolve, 2000))

    const aiGeneratedScope = `The Assistant Director, Total Rewards designs organisation-wide performance management strategies and total rewards philosophy for TPC Group to attract and retain talent. He/She establishes performance review cycles and key performance indicators (KPIs) for the business units across TPC Group's diverse portfolio including property development, hospitality, and investment holdings.

Key Responsibilities:
• Develop and maintain competitive compensation structures across property development, hospitality, and investment portfolios
• Design performance management frameworks and KPI systems for business units
• Conduct regular market analysis and salary benchmarking studies using Mercer, Willis Towers Watson methodologies
• Partner with business leaders to align rewards strategies with organizational objectives
• Oversee annual compensation review processes and budget planning
• Ensure compliance with local employment regulations across TPC Group entities
• Lead total rewards communication and change management initiatives
• Manage job evaluation processes and internal equity assessments

Required Qualifications:
• Bachelor's degree in Human Resources, Business Administration, or related field
• 8-12 years of experience in compensation and benefits, preferably in property/hospitality sectors
• Professional certification (CCP, CECP, or equivalent) preferred
• Strong analytical skills with proficiency in HRIS and compensation software
• Experience with Mercer, Willis Towers Watson, or similar consulting methodologies
• Excellent stakeholder management and communication skills

This role offers significant impact across TPC Group's 2,800+ employees and provides exposure to diverse business environments including luxury hospitality, commercial property development, and investment management.`

    setJobData({ ...jobData, jobSummary: aiGeneratedScope })
    setIsGeneratingJobScope(false)
  }

  const handleGenerateSkills = async () => {
    setIsGeneratingSkills(true)
    await new Promise((resolve) => setTimeout(resolve, 1500))

    // Simulate AI mapping based on job title, grade, and family
    const aiGeneratedSkills = [
      "Stakeholder Engagement and Management",
      "Human Resource Digitalisation",
      "Compensation Management",
      "Employee Mobility Management",
      "Total Rewards Philosophy Development",
      "Human Resource Analytics and Insights",
      "Diversity and Inclusion Management",
      "Technology Integration",
      "Strategic Workforce Planning",
      "Performance Management Systems",
      "Market Research and Analysis",
      "Data Analytics and Reporting",
      "Change Management",
      "Project Management",
      "Communication and Presentation",
    ]

    setJobData({ ...jobData, skillsRequired: aiGeneratedSkills })
    setIsGeneratingSkills(false)
  }

  const handleMapMercer = async () => {
    setIsMappingMercer(true)
    await new Promise((resolve) => setTimeout(resolve, 2000))

    const mercerMapping = {
      mercerJobCode: "HRM.04.005.M50 - Total Rewards - Director (M5)",
      mercerJobDescription: `Total Rewards work is a specialized area of Rewards focused on the design of a holistic framework of financial and non-financial rewards that reflects the organization's strategy to attract, motivate, and retain employees including:

• Researching and analyzing key perspectives (employee, external labor market, cost, and workforce requirements)
• Incorporating traditional compensation and benefits elements as well as learning and development opportunities, career frameworks, and work/life benefits
• Exploring opportunities for segmentation to allow certain performance driving areas of the business to offer fundamentally different total rewards packages
• Ongoing management, communication, and monitoring of plan results

Level: A Director (M5) is responsible for strategy execution and operational direction of a business function or a part of a function within local entity/business unit. Supports strategy development for their functional area. Interacts with executive leadership concerning matters of significance to the organization. Typically manages multiple teams led by senior managers and managers.

Specialization Match Note: Incumbents responsible for the strategy and design of financial and non-financial rewards to attract, motivate and retain employees should be matched to the Total Rewards specialization.

Typical Title: Total Rewards Sr. Manager, Total Rewards Manager, Total Rewards Supervisor`,
    }

    setJobData({ ...jobData, ...mercerMapping })
    setIsMappingMercer(false)
  }

  const handleGenerateAlternatives = async () => {
    setIsGeneratingAlternatives(true)
    await new Promise((resolve) => setTimeout(resolve, 1500))

    // AI generates alternatives based on job title, industry, and market data
    const aiGeneratedAlternatives = [
      "Head of Total Rewards",
      "Head of Compensation and Benefits",
      "Head of Performance and Rewards",
      "Director, Rewards and Recognition",
      "Senior Manager, Total Rewards",
      "Compensation and Benefits Director",
    ]

    setJobData({ ...jobData, alternativeTitles: aiGeneratedAlternatives })
    setIsGeneratingAlternatives(false)
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
                    Upload DOCX or PDF documents containing job descriptions or role summaries for AI analysis and
                    mapping
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

                    <div className="flex flex-wrap gap-2 p-3 border rounded-md min-h-[60px] bg-gray-50">
                      {jobData.alternativeTitles?.map((title, index) => (
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

                  {jobData.mercerJobCode && (
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
                  )}
                </CardContent>
              </Card>

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
                          {internalData.map((emp, index) => (
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
                            {otherDepartmentData.map((emp, index) => (
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
                        <div>
                          • <strong>Total Rewards Team:</strong> Current Assistant Directors earn SGD{" "}
                          {internalData[2].monthlySalary.toLocaleString()} -{" "}
                          {internalData[4].monthlySalary.toLocaleString()}
                          monthly, aligning with market P50-P60.
                        </div>
                        <div>
                          • <strong>Grade 10 Comparison:</strong> Roles in Finance and Operations at Grade 10 earn SGD{" "}
                          {otherDepartmentData[0].monthlySalary.toLocaleString()} -{" "}
                          {otherDepartmentData[1].monthlySalary.toLocaleString()}
                          monthly, indicating potential for higher compensation in specialized roles like Total Rewards.
                        </div>
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
                          {internalData.map((emp, index) => (
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
                            {otherDepartmentData.map((emp, index) => (
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
                        <div>
                          • <strong>Total Rewards Team:</strong> Current Assistant Directors earn SGD{" "}
                          {internalData[2].monthlySalary.toLocaleString()} -{" "}
                          {internalData[4].monthlySalary.toLocaleString()}
                          monthly, aligning with market P50-P60.
                        </div>
                        <div>
                          • <strong>Grade 10 Comparison:</strong> Roles in Finance and Operations at Grade 10 earn SGD{" "}
                          {otherDepartmentData[0].monthlySalary.toLocaleString()} -{" "}
                          {otherDepartmentData[1].monthlySalary.toLocaleString()}
                          monthly, indicating potential for higher compensation in specialized roles like Total Rewards.
                        </div>
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
