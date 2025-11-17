// Global type definitions for the Talent Verse dashboard

// People metrics
export interface PeopleMetrics {
  workforceEngagementPulse: number
  internalCulturalAdvocacyIndex: number
  roleProgressionMobility: number
  leadershipInfluenceScore: number
  consciousnessCalibrationDelta: number
  rmrrFitIndex: number
}

// Process metrics
export interface ProcessMetrics {
  strategicContributionRatio: number
  executionFlowQuality: number
  consciousDecisionCycleTime: number
  organisationRhythmIndex: number
}

// Performance metrics
export interface PerformanceMetrics {
  impactOnPillarsIndex: number
  valueRealisationRatio: number
  contributionToFlowQuotient: number
  roleValueAddScore: number
  performanceAndContributionIndex: number
}

// Strategic pillars
export enum StrategicPillar {
  Business = "Business",
  Investment = "Investment",
  Advocacy = "Advocacy",
  Philanthropy = "Philanthropy",
}

// Quadruple Organisation components
export enum QuadrupleOrg {
  Hierarchy = "Hierarchy",
  SMP = "Strategic Management Processes",
  CCC = "Communication, Community & Culture",
  Network = "Network & Advocacy",
}

// Psychometric assessment types
export enum PsychometricType {
  AACC = "Aware-Align-Collaborate-Co-create",
  IRTF = "In-search, Research, Think-through, Follow-through",
  TimeWaver = "TimeWaver",
  RMRR = "Role Mandate",
}
