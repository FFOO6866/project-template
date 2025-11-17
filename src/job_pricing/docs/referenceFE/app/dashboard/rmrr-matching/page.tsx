"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Heading } from "@/components/ui/heading"
import { Text } from "@/components/ui/text"
import { MetricCard } from "@/components/ui/metric-card"
import { DashboardShell } from "@/components/dashboard-shell"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Brain, Filter, Download, Plus, Eye, CheckCircle, AlertTriangle } from "lucide-react"
import { ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from "recharts"

export default function RMRRMatchingPage() {
  const [selectedCandidate, setSelectedCandidate] = useState<string | null>(null)

  const rmrrMetrics = [
    {
      title: "Active Assessments",
      value: "47",
      change: "+12",
      trend: "up" as const,
      category: "process" as const,
      description: "In progress this month",
    },
    {
      title: "Average Match Score",
      value: "78%",
      change: "+5%",
      trend: "up" as const,
      category: "performance" as const,
      description: "Role-fit accuracy",
    },
    {
      title: "Successful Placements",
      value: "23",
      change: "+8",
      trend: "up" as const,
      category: "people" as const,
      description: "High-match hires",
    },
    {
      title: "Assessment Completion",
      value: "92%",
      change: "+3%",
      trend: "up" as const,
      category: "process" as const,
      description: "Candidate completion rate",
    },
  ]

  const candidateAssessments = [
    {
      name: "Sarah Chen",
      role: "Senior Data Analyst",
      status: "Completed",
      matchScore: 87,
      rmrrScore: {
        responsibility: 85,
        mindset: 89,
        relationships: 82,
        results: 91,
      },
      psychometrics: {
        mbti: "INTJ",
        enneagram: "Type 5",
        timeWaver: "Reason (400)",
      },
      recommendation: "Strong Fit",
      submittedDate: "2024-01-15",
      reviewStatus: "Pending Review",
    },
    {
      name: "Michael Rodriguez",
      role: "Property Development Manager",
      status: "Completed",
      matchScore: 92,
      rmrrScore: {
        responsibility: 94,
        mindset: 88,
        relationships: 95,
        results: 91,
      },
      psychometrics: {
        mbti: "ENTJ",
        enneagram: "Type 8",
        timeWaver: "Willingness (310)",
      },
      recommendation: "Excellent Fit",
      submittedDate: "2024-01-14",
      reviewStatus: "Approved",
    },
    {
      name: "Jennifer Kim",
      role: "Hotel Operations Supervisor",
      status: "In Progress",
      matchScore: 0,
      rmrrScore: {
        responsibility: 0,
        mindset: 0,
        relationships: 0,
        results: 0,
      },
      psychometrics: {
        mbti: "Pending",
        enneagram: "Pending",
        timeWaver: "Pending",
      },
      recommendation: "Assessment Incomplete",
      submittedDate: "2024-01-16",
      reviewStatus: "In Progress",
    },
    {
      name: "David Tan",
      role: "Investment Associate",
      status: "Completed",
      matchScore: 74,
      rmrrScore: {
        responsibility: 78,
        mindset: 72,
        relationships: 69,
        results: 77,
      },
      psychometrics: {
        mbti: "ISFJ",
        enneagram: "Type 6",
        timeWaver: "Neutrality (250)",
      },
      recommendation: "Moderate Fit",
      submittedDate: "2024-01-13",
      reviewStatus: "Under Review",
    },
  ]

  const rmrrFramework = [
    {
      dimension: "Responsibility",
      description: "Ownership and accountability for outcomes",
      weight: 25,
      criteria: ["Takes ownership", "Accountable for results", "Proactive problem-solving"],
    },
    {
      dimension: "Mindset",
      description: "Growth orientation and learning agility",
      weight: 25,
      criteria: ["Growth mindset", "Adaptability", "Continuous learning"],
    },
    {
      dimension: "Relationships",
      description: "Collaboration and stakeholder management",
      weight: 25,
      criteria: ["Team collaboration", "Stakeholder engagement", "Communication skills"],
    },
    {
      dimension: "Results",
      description: "Performance delivery and impact creation",
      weight: 25,
      criteria: ["Performance delivery", "Impact focus", "Goal achievement"],
    },
  ]

  const aiInsights = [
    {
      type: "Pattern",
      title: "High Performers Show Strong R&R Correlation",
      description: "Candidates scoring 85+ in Responsibility and Results show 94% success rate in first 90 days",
      impact: "High",
    },
    {
      type: "Recommendation",
      title: "Adjust Mindset Weighting for Tech Roles",
      description: "Technical positions benefit from 35% mindset weighting vs standard 25%",
      impact: "Medium",
    },
    {
      type: "Alert",
      title: "Assessment Completion Drop",
      description: "15% decrease in completion rates for assessments >45 minutes",
      impact: "Medium",
    },
  ]

  const getRecommendationColor = (recommendation: string) => {
    switch (recommendation) {
      case "Excellent Fit":
        return "bg-green-100 text-green-800 border-green-200"
      case "Strong Fit":
        return "bg-blue-100 text-blue-800 border-blue-200"
      case "Moderate Fit":
        return "bg-yellow-100 text-yellow-800 border-yellow-200"
      default:
        return "bg-gray-100 text-gray-800 border-gray-200"
    }
  }

  return (
    <DashboardShell>
      <div className="space-y-6">
        <div className="flex justify-between items-start">
          <div>
            <Heading level="h1" className="mb-2">
              RMRR Matching Engine
            </Heading>
            <Text size="lg" color="muted">
              AI-powered role-fit assessment using Responsibility, Mindset, Relationships & Results framework
            </Text>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm">
              <Filter className="h-4 w-4 mr-2" />
              Filters
            </Button>
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
            <Button size="sm">
              <Plus className="h-4 w-4 mr-2" />
              New Assessment
            </Button>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {rmrrMetrics.map((metric, index) => (
            <MetricCard key={index} {...metric} />
          ))}
        </div>

        <Tabs defaultValue="assessments" className="space-y-6">
          <TabsList>
            <TabsTrigger value="assessments">Active Assessments</TabsTrigger>
            <TabsTrigger value="rmrr-framework">RMRR Framework</TabsTrigger>
            <TabsTrigger value="ai-insights">AI Insights</TabsTrigger>
            <TabsTrigger value="reviewer-dashboard">Reviewer Dashboard</TabsTrigger>
          </TabsList>

          <TabsContent value="assessments" className="space-y-6">
            <div className="space-y-4">
              {candidateAssessments.map((candidate, index) => (
                <Card key={index} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-6">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <div className="flex items-center gap-3 mb-2">
                          <Text size="lg" weight="semibold">
                            {candidate.name}
                          </Text>
                          <Badge
                            variant={candidate.status === "Completed" ? "default" : "secondary"}
                            className="text-xs"
                          >
                            {candidate.status}
                          </Badge>
                        </div>
                        <Text size="sm" color="muted">
                          {candidate.role} • Submitted {candidate.submittedDate}
                        </Text>
                      </div>
                      <div className="text-right">
                        {candidate.matchScore > 0 && (
                          <div className="mb-2">
                            <Text size="2xl" weight="bold" className="text-blue-600">
                              {candidate.matchScore}%
                            </Text>
                            <Text size="xs" color="muted">
                              Match Score
                            </Text>
                          </div>
                        )}
                        <Badge className={getRecommendationColor(candidate.recommendation)}>
                          {candidate.recommendation}
                        </Badge>
                      </div>
                    </div>

                    {candidate.status === "Completed" && (
                      <div className="grid gap-6 md:grid-cols-2">
                        <div>
                          <Text size="sm" weight="medium" className="mb-3">
                            RMRR Scores
                          </Text>
                          <ResponsiveContainer width="100%" height={200}>
                            <RadarChart
                              data={Object.entries(candidate.rmrrScore).map(([key, value]) => ({
                                dimension: key,
                                score: value,
                              }))}
                            >
                              <PolarGrid />
                              <PolarAngleAxis dataKey="dimension" />
                              <PolarRadiusAxis angle={90} domain={[0, 100]} />
                              <Radar name="Score" dataKey="score" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} />
                            </RadarChart>
                          </ResponsiveContainer>
                        </div>

                        <div className="space-y-4">
                          <div>
                            <Text size="sm" weight="medium" className="mb-2">
                              Psychometric Profile
                            </Text>
                            <div className="space-y-2">
                              <div className="flex justify-between">
                                <Text size="sm" color="muted">
                                  MBTI Type:
                                </Text>
                                <Badge variant="outline">{candidate.psychometrics.mbti}</Badge>
                              </div>
                              <div className="flex justify-between">
                                <Text size="sm" color="muted">
                                  Enneagram:
                                </Text>
                                <Badge variant="outline">{candidate.psychometrics.enneagram}</Badge>
                              </div>
                              <div className="flex justify-between">
                                <Text size="sm" color="muted">
                                  Consciousness:
                                </Text>
                                <Badge variant="outline">{candidate.psychometrics.timeWaver}</Badge>
                              </div>
                            </div>
                          </div>

                          <div>
                            <Text size="sm" weight="medium" className="mb-2">
                              Review Status
                            </Text>
                            <div className="flex items-center gap-2">
                              {candidate.reviewStatus === "Approved" ? (
                                <CheckCircle className="h-4 w-4 text-green-500" />
                              ) : candidate.reviewStatus === "Under Review" ? (
                                <AlertTriangle className="h-4 w-4 text-yellow-500" />
                              ) : (
                                <Eye className="h-4 w-4 text-blue-500" />
                              )}
                              <Text size="sm">{candidate.reviewStatus}</Text>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    <div className="flex gap-2 mt-4 pt-4 border-t">
                      <Button variant="outline" size="sm">
                        <Eye className="h-4 w-4 mr-2" />
                        View Details
                      </Button>
                      {candidate.status === "Completed" && candidate.reviewStatus === "Pending Review" && (
                        <Button size="sm">
                          <CheckCircle className="h-4 w-4 mr-2" />
                          Review Assessment
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="rmrr-framework" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>RMRR Assessment Framework</CardTitle>
                <CardDescription>
                  Comprehensive evaluation framework for role-fit assessment across four key dimensions
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid gap-6 md:grid-cols-2">
                  {rmrrFramework.map((dimension, index) => (
                    <Card key={index} className="border-l-4 border-l-blue-500">
                      <CardHeader className="pb-3">
                        <div className="flex justify-between items-start">
                          <CardTitle className="text-lg">{dimension.dimension}</CardTitle>
                          <Badge variant="outline">{dimension.weight}%</Badge>
                        </div>
                        <CardDescription>{dimension.description}</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <Text size="sm" weight="medium" className="mb-2">
                          Key Criteria:
                        </Text>
                        <ul className="space-y-1">
                          {dimension.criteria.map((criterion, idx) => (
                            <li key={idx} className="text-sm text-gray-600 flex items-center gap-2">
                              <div className="w-1.5 h-1.5 bg-blue-500 rounded-full" />
                              {criterion}
                            </li>
                          ))}
                        </ul>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="ai-insights" className="space-y-6">
            <div className="space-y-4">
              {aiInsights.map((insight, index) => (
                <Card key={index}>
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge
                            variant={
                              insight.type === "Pattern"
                                ? "default"
                                : insight.type === "Alert"
                                  ? "destructive"
                                  : "secondary"
                            }
                          >
                            {insight.type}
                          </Badge>
                          <Text size="lg" weight="semibold">
                            {insight.title}
                          </Text>
                        </div>
                        <Text size="sm" color="muted" className="mb-3">
                          {insight.description}
                        </Text>
                        <Badge variant={insight.impact === "High" ? "destructive" : "secondary"} className="text-xs">
                          {insight.impact} Impact
                        </Badge>
                      </div>
                      <Button variant="outline" size="sm">
                        <Brain className="h-4 w-4 mr-2" />
                        Apply Insight
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="reviewer-dashboard" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Reviewer Dashboard</CardTitle>
                <CardDescription>Pending assessments requiring review and approval</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {candidateAssessments
                    .filter((candidate) => candidate.reviewStatus === "Pending Review")
                    .map((candidate, index) => (
                      <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                        <div>
                          <Text size="sm" weight="medium">
                            {candidate.name}
                          </Text>
                          <Text size="xs" color="muted">
                            {candidate.role} • Match Score: {candidate.matchScore}%
                          </Text>
                        </div>
                        <div className="flex gap-2">
                          <Button variant="outline" size="sm">
                            <Eye className="h-4 w-4 mr-2" />
                            Review
                          </Button>
                          <Button size="sm">
                            <CheckCircle className="h-4 w-4 mr-2" />
                            Approve
                          </Button>
                        </div>
                      </div>
                    ))}
                  {candidateAssessments.filter((candidate) => candidate.reviewStatus === "Pending Review").length ===
                    0 && (
                    <div className="text-center py-8 text-gray-500">
                      <CheckCircle className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <Text>No assessments pending review</Text>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardShell>
  )
}
