"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Heading } from "@/components/ui/heading"
import { Text } from "@/components/ui/text"
import { DashboardShell } from "@/components/dashboard-shell"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Brain, Filter, Download, Plus, Eye, BarChart3 } from "lucide-react"

export default function PsychometricAssessmentsPage() {
  const [selectedAssessment, setSelectedAssessment] = useState("all")

  const assessmentTypes = [
    {
      name: "MBTI (Myers-Briggs)",
      description: "Personality type indicator",
      duration: "15-20 minutes",
      completions: 234,
      avgScore: "N/A",
      status: "Active",
    },
    {
      name: "Enneagram",
      description: "Nine personality types",
      duration: "10-15 minutes",
      completions: 198,
      avgScore: "N/A",
      status: "Active",
    },
    {
      name: "TimeWaver Consciousness",
      description: "Consciousness level assessment",
      duration: "25-30 minutes",
      completions: 156,
      avgScore: "325 avg",
      status: "Active",
    },
    {
      name: "SHL Cognitive",
      description: "Cognitive ability assessment",
      duration: "45 minutes",
      completions: 89,
      avgScore: "78%",
      status: "Pilot",
    },
  ]

  const recentAssessments = [
    {
      candidate: "Sarah Chen",
      role: "Senior Data Analyst",
      assessments: ["MBTI: INTJ", "Enneagram: Type 5", "TimeWaver: 400"],
      status: "Completed",
      date: "2024-01-15",
      insights: "Strong analytical mindset, independent worker, high consciousness level",
    },
    {
      candidate: "Michael Rodriguez",
      role: "Property Manager",
      assessments: ["MBTI: ENTJ", "Enneagram: Type 8", "TimeWaver: 310"],
      status: "Completed",
      date: "2024-01-14",
      insights: "Natural leader, results-oriented, strong willingness to take action",
    },
    {
      candidate: "Jennifer Kim",
      role: "Hotel Supervisor",
      assessments: ["MBTI: In Progress", "Enneagram: Pending", "TimeWaver: Pending"],
      status: "In Progress",
      date: "2024-01-16",
      insights: "Assessment incomplete",
    },
  ]

  const personalityDistribution = {
    mbti: [
      { type: "NT (Analysts)", count: 45, percentage: 32 },
      { type: "NF (Diplomats)", count: 28, percentage: 20 },
      { type: "SJ (Sentinels)", count: 38, percentage: 27 },
      { type: "SP (Explorers)", count: 29, percentage: 21 },
    ],
    enneagram: [
      { type: "Type 1 (Perfectionist)", count: 18, percentage: 13 },
      { type: "Type 2 (Helper)", count: 22, percentage: 16 },
      { type: "Type 3 (Achiever)", count: 31, percentage: 22 },
      { type: "Type 8 (Challenger)", count: 25, percentage: 18 },
      { type: "Others", count: 44, percentage: 31 },
    ],
  }

  return (
    <DashboardShell>
      <div className="space-y-6">
        <div className="flex justify-between items-start">
          <div>
            <Heading level="h1" className="mb-2">
              Psychometric Assessment Hub
            </Heading>
            <Text size="lg" color="muted">
              Comprehensive personality and cognitive assessments for role-fit evaluation
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

        <Tabs defaultValue="assessment-overview" className="space-y-6">
          <TabsList>
            <TabsTrigger value="assessment-overview">Assessment Overview</TabsTrigger>
            <TabsTrigger value="personality-insights">Personality Insights</TabsTrigger>
            <TabsTrigger value="cognitive-results">Cognitive Results</TabsTrigger>
            <TabsTrigger value="assessment-library">Assessment Library</TabsTrigger>
          </TabsList>

          <TabsContent value="assessment-overview" className="space-y-6">
            <div className="grid gap-4 md:grid-cols-4">
              {assessmentTypes.map((assessment, index) => (
                <Card key={index}>
                  <CardContent className="p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Brain className="h-4 w-4 text-blue-500" />
                      <Badge variant={assessment.status === "Active" ? "default" : "secondary"} className="text-xs">
                        {assessment.status}
                      </Badge>
                    </div>
                    <Text size="sm" weight="medium" className="mb-1">
                      {assessment.name}
                    </Text>
                    <Text size="xs" color="muted" className="mb-3">
                      {assessment.description}
                    </Text>
                    <div className="space-y-1">
                      <div className="flex justify-between text-xs">
                        <span>Completions:</span>
                        <span className="font-medium">{assessment.completions}</span>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span>Duration:</span>
                        <span className="font-medium">{assessment.duration}</span>
                      </div>
                      {assessment.avgScore !== "N/A" && (
                        <div className="flex justify-between text-xs">
                          <span>Avg Score:</span>
                          <span className="font-medium">{assessment.avgScore}</span>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Recent Assessment Results</CardTitle>
                <CardDescription>Latest completed and in-progress assessments</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {recentAssessments.map((assessment, index) => (
                    <div key={index} className="flex items-start justify-between p-4 border rounded-lg">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <Text size="sm" weight="medium">
                            {assessment.candidate}
                          </Text>
                          <Badge
                            variant={assessment.status === "Completed" ? "default" : "secondary"}
                            className="text-xs"
                          >
                            {assessment.status}
                          </Badge>
                        </div>
                        <Text size="xs" color="muted" className="mb-2">
                          {assessment.role} • {assessment.date}
                        </Text>
                        <div className="flex gap-2 mb-2">
                          {assessment.assessments.map((result, idx) => (
                            <Badge key={idx} variant="outline" className="text-xs">
                              {result}
                            </Badge>
                          ))}
                        </div>
                        <Text size="xs" className="text-gray-600">
                          {assessment.insights}
                        </Text>
                      </div>
                      <div className="flex gap-2">
                        <Button variant="outline" size="sm">
                          <Eye className="h-4 w-4 mr-2" />
                          View
                        </Button>
                        {assessment.status === "Completed" && (
                          <Button size="sm">
                            <BarChart3 className="h-4 w-4 mr-2" />
                            Analyze
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="personality-insights" className="space-y-6">
            <div className="grid gap-6 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>MBTI Distribution</CardTitle>
                  <CardDescription>Personality type distribution across candidates</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {personalityDistribution.mbti.map((type, index) => (
                      <div key={index} className="space-y-2">
                        <div className="flex justify-between items-center">
                          <Text size="sm">{type.type}</Text>
                          <div className="flex items-center gap-2">
                            <Text size="sm" weight="medium">
                              {type.count}
                            </Text>
                            <Badge variant="outline" className="text-xs">
                              {type.percentage}%
                            </Badge>
                          </div>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${type.percentage}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Enneagram Distribution</CardTitle>
                  <CardDescription>Enneagram type distribution across candidates</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {personalityDistribution.enneagram.map((type, index) => (
                      <div key={index} className="space-y-2">
                        <div className="flex justify-between items-center">
                          <Text size="sm">{type.type}</Text>
                          <div className="flex items-center gap-2">
                            <Text size="sm" weight="medium">
                              {type.count}
                            </Text>
                            <Badge variant="outline" className="text-xs">
                              {type.percentage}%
                            </Badge>
                          </div>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div className="bg-green-500 h-2 rounded-full" style={{ width: `${type.percentage}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="cognitive-results" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Cognitive Assessment Results</CardTitle>
                <CardDescription>SHL and other cognitive ability test outcomes</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center py-12 text-gray-500">
                  <Brain className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <Text>Cognitive assessment results will be displayed here</Text>
                  <Text size="sm" color="muted">
                    Complete cognitive assessments to view detailed analytics
                  </Text>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="assessment-library" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Assessment Library</CardTitle>
                <CardDescription>Available psychometric and cognitive assessments</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-2">
                  {assessmentTypes.map((assessment, index) => (
                    <Card key={index} className="border-l-4 border-l-blue-500">
                      <CardHeader className="pb-3">
                        <div className="flex justify-between items-start">
                          <CardTitle className="text-lg">{assessment.name}</CardTitle>
                          <Badge variant={assessment.status === "Active" ? "default" : "secondary"}>
                            {assessment.status}
                          </Badge>
                        </div>
                        <CardDescription>{assessment.description}</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2 mb-4">
                          <div className="flex justify-between text-sm">
                            <span>Duration:</span>
                            <span className="font-medium">{assessment.duration}</span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span>Completions:</span>
                            <span className="font-medium">{assessment.completions}</span>
                          </div>
                        </div>
                        <Button variant="outline" size="sm" className="w-full bg-transparent">
                          <Plus className="h-4 w-4 mr-2" />
                          Assign Assessment
                        </Button>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardShell>
  )
}
