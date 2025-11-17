// Job Evaluation System Types
export interface RoleProfile {
  id: string
  title: string
  department: string
  description: string
  responsibilities: string[]
  requirements: string[]
  reportingTo: string
  directReports: number
}

export interface JobEvaluation {
  id: string
  roleProfileId: string
  impact: {
    degree: number
    points: number
  }
  communication: {
    degree: number
    points: number
  }
  innovation: {
    degree: number
    points: number
  }
  knowledge: {
    degree: number
    points: number
  }
  risk: {
    degree: number
    points: number
  }
  totalPoints: number
  positionClass: number
  jobGrade: string
  evaluatedBy: string
  evaluatedDate: string
  status: "draft" | "pending" | "approved"
}

// Job Mapping System Types
export interface MarketData {
  id: string
  source: "internal" | "external" | "market"
  jobTitle: string
  company?: string
  location: string
  industry?: string
  minSalary: number
  maxSalary: number
  medianSalary: number
  currency: string
  jobGrade?: string
  positionClass?: number
  lastUpdated: string
}

export interface ComparableJob {
  id: string
  jobTitle: string
  source: "internal" | "external" | "market"
  company?: string
  location: string
  similarity: number // 0-100%
  salary: {
    min: number
    median: number
    max: number
  }
  currency: string
}

// Pay for Performance System Types
export interface PerformanceMatrix {
  id: string
  name: string
  description: string
  rows: PerformanceLevel[]
  columns: PayPositionLevel[]
  cells: PerformanceMatrixCell[]
}

export interface PerformanceLevel {
  id: string
  name: string
  description: string
  minScore: number
  maxScore: number
}

export interface PayPositionLevel {
  id: string
  name: string
  description: string
  minPercentile: number
  maxPercentile: number
}

export interface PerformanceMatrixCell {
  rowId: string
  columnId: string
  bonusPercentage: number
}

export interface EmployeeCompensation {
  employeeId: string
  employeeName: string
  jobTitle: string
  jobGrade: string
  baseSalary: number
  payPositionPercentile: number
  performanceScore: number
  bonusPercentage: number
  bonusAmount: number
  totalCompensation: number
  currency: string
  effectiveDate: string
}
