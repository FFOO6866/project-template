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
import { Download, Filter } from "lucide-react"
import {
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts"

export default function StrategicImpactPage() {
  const [selectedPillar, setSelectedPillar] = useState("all")
  const [selectedTimeframe, setSelectedTimeframe] = useState("current")

  const impactPillars = [
    {
      title: "Business Excellence",
      value: "85%",
      change: "+8%",
      trend: "up" as const,
      category: "business" as const,
      description: "Operational efficiency & growth",
    },
    {
      title: "Investment Returns",
      value: "92%",
      change: "+12%",
      trend: "up" as const,
      category: "investment" as const,
      description: "Portfolio performance",
    },
    {
      title: "Advocacy & Influence",
      value: "78%",
      change: "+5%",
      trend: "up" as const,
      category: "advocacy" as const,
      description: "Industry leadership",
    },
    {
      title: "Philanthropy & ESG",
      value: "88%",
      change: "+15%",
      trend: "up" as const,
      category: "philanthropy" as const,
      description: "Social impact initiatives",
    },
  ]

  const strategicPillars = [
    {
      title: "People Development",
      value: "87%",
      change: "+6%",
      trend: "up" as const,
      category: "people" as const,
      description: "Talent growth & engagement",
    },
    {
      title: "Process Excellence",
      value: "82%",
      change: "+4%",
      trend: "up" as const,
      category: "process" as const,
      description: "Operational efficiency",
    },
    {
      title: "Performance Culture",
      value: "89%",
      change: "+7%",
      trend: "up" as const,
      category: "performance" as const,
      description: "Results-driven mindset",
    },
    {
      title: "Innovation & Growth",
      value: "76%",
      change: "+9%",
      trend: "up" as const,
      category: "business" as const,
      description: "Future-ready capabilities",
    },
    {
      title: "Sustainability Focus",
      value: "84%",
      change: "+11%",
      trend: "up" as const,
      category: "philanthropy" as const,
      description: "Environmental stewardship",
    },
    {
      title: "Stakeholder Value",
      value: "91%",
      change: "+8%",
      trend: "up" as const,
      category: "investment" as const,
      description: "Shareholder returns",
    },
  ]

  const radarData = [
    { pillar: "Business Excellence", current: 85, target: 90, industry: 75 },
    { pillar: "Investment Returns", current: 92, target: 95, industry: 80 },
    { pillar: "Advocacy", current: 78, target: 85, industry: 70 },
    { pillar: "Philanthropy", current: 88, target: 90, industry: 65 },
    { pillar: "People Dev", current: 87, target: 90, industry: 78 },
    { pillar: "Process Excellence", current: 82, target: 88, industry: 72 },
  ]

  const okrProgress = [
    {
      objective: "Achieve 90% Employee Engagement",
      keyResults: [
        { kr: "Pulse survey scores >4.5/5", progress: 87, target: 90 },
        { kr: "Manager effectiveness >85%", progress: 82, target: 85 },
        { kr: "Career development satisfaction >80%", progress: 78, target: 80 },
      ],
      owner: "CPO",
      status: "On Track",
    },
    {
      objective: "Digital Transformation Leadership",
      keyResults: [
        { kr: "AI adoption across 80% of processes", progress: 65, target: 80 },
        { kr: "Digital skills certification 100%", progress: 73, target: 100 },
        { kr: "Automation ROI >300%", progress: 285, target: 300 },
      ],
      owner: "CTO",
      status: "At Risk",
    },
    {
      objective: "ESG Excellence Recognition",
      keyResults: [
        { kr: "Carbon neutrality by 2025", progress: 78, target: 100 },
        { kr: "Diversity targets achieved", progress: 92, target: 100 },
        { kr: "Community impact programs", progress: 88, target: 90 },
      ],
      owner: "CEO",
      status: "Ahead",
    },
  ]

  const businessImpactMetrics = [
    { metric: "Revenue Growth", value: "12.5%", benchmark: "8.2%", status: "Exceeding" },
    { metric: "Profit Margin", value: "18.7%", benchmark: "15.3%", status: "Exceeding" },
    { metric: "Market Share", value: "23.4%", benchmark: "20.1%", status: "Exceeding" },
    { metric: "Customer Satisfaction", value: "4.6/5", benchmark: "4.2/5", status: "Exceeding" },
    { metric: "Employee Productivity", value: "127%", benchmark: "100%", status: "Exceeding" },
    { metric: "Innovation Index", value: "8.9/10", benchmark: "7.5/10", status: "Exceeding" },
  ]

  return (
    <DashboardShell>
      <div className="space-y-6">
        <div className="flex justify-between items-start">
          <div>
            <Heading level="h1" className="mb-2">
              Strategic Impact Dashboard
            </Heading>
            <Text size="lg" color="muted">
              Tracking progress against TPC Group's 4 Impact Pillars and 6 Strategic Pillars
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
          </div>
        </div>

        <Tabs defaultValue="impact-pillars" className="space-y-6">
          <TabsList>
            <TabsTrigger value="impact-pillars">4 Impact Pillars</TabsTrigger>
            <TabsTrigger value="strategic-pillars">6 Strategic Pillars</TabsTrigger>
            <TabsTrigger value="okr-tracking">OKR Tracking</TabsTrigger>
            <TabsTrigger value="business-impact">Business Impact</TabsTrigger>
          </TabsList>

          <TabsContent value="impact-pillars" className="space-y-6">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              {impactPillars.map((pillar, index) => (
                <MetricCard key={index} {...pillar} />
              ))}
            </div>

            <div className="grid gap-6 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>Impact Pillars Performance Radar</CardTitle>
                  <CardDescription>Current vs Target vs Industry Benchmark</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <RadarChart data={radarData}>
                      <PolarGrid />
                      <PolarAngleAxis dataKey="pillar" />
                      <PolarRadiusAxis angle={90} domain={[0, 100]} />
                      <Radar name="Current" dataKey="current" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} />
                      <Radar name="Target" dataKey="target" stroke="#10b981" fill="#10b981" fillOpacity={0.1} />
                      <Radar name="Industry" dataKey="industry" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.1} />
                      <Legend />
                    </RadarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Pillar Impact on Business Outcomes</CardTitle>
                  <CardDescription>Correlation with key business metrics</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg">
                      <div>
                        <Text size="sm" weight="medium">
                          Business Excellence → Revenue Growth
                        </Text>
                        <Text size="xs" color="muted">
                          Strong positive correlation (0.87)
                        </Text>
                      </div>
                      <Badge variant="default">High Impact</Badge>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
                      <div>
                        <Text size="sm" weight="medium">
                          Investment Returns → Profit Margin
                        </Text>
                        <Text size="xs" color="muted">
                          Direct correlation (0.94)
                        </Text>
                      </div>
                      <Badge variant="default">High Impact</Badge>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-purple-50 rounded-lg">
                      <div>
                        <Text size="sm" weight="medium">
                          Advocacy → Market Share
                        </Text>
                        <Text size="xs" color="muted">
                          Moderate correlation (0.72)
                        </Text>
                      </div>
                      <Badge variant="secondary">Medium Impact</Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="strategic-pillars" className="space-y-6">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {strategicPillars.map((pillar, index) => (
                <MetricCard key={index} {...pillar} />
              ))}
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Strategic Pillar Progress Tracking</CardTitle>
                <CardDescription>Year-over-year improvement across all pillars</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={strategicPillars}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="title" angle={-45} textAnchor="end" height={100} />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" fill="#3b82f6" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="okr-tracking" className="space-y-6">
            <div className="space-y-6">
              {okrProgress.map((okr, index) => (
                <Card key={index}>
                  <CardHeader>
                    <div className="flex justify-between items-start">
                      <div>
                        <CardTitle className="text-lg">{okr.objective}</CardTitle>
                        <Text size="sm" color="muted">
                          Owner: {okr.owner}
                        </Text>
                      </div>
                      <Badge
                        variant={
                          okr.status === "Ahead" ? "default" : okr.status === "On Track" ? "secondary" : "destructive"
                        }
                      >
                        {okr.status}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {okr.keyResults.map((kr, krIndex) => (
                        <div key={krIndex} className="space-y-2">
                          <div className="flex justify-between items-center">
                            <Text size="sm">{kr.kr}</Text>
                            <Text size="sm" weight="medium">
                              {kr.progress}% / {kr.target}%
                            </Text>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full ${
                                kr.progress >= kr.target
                                  ? "bg-green-500"
                                  : kr.progress >= kr.target * 0.8
                                    ? "bg-blue-500"
                                    : "bg-red-500"
                              }`}
                              style={{ width: `${Math.min((kr.progress / kr.target) * 100, 100)}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="business-impact" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Business Impact Metrics</CardTitle>
                <CardDescription>Key performance indicators vs industry benchmarks</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {businessImpactMetrics.map((metric, index) => (
                    <div key={index} className="p-4 border rounded-lg">
                      <div className="flex justify-between items-start mb-2">
                        <Text size="sm" weight="medium">
                          {metric.metric}
                        </Text>
                        <Badge variant="default">{metric.status}</Badge>
                      </div>
                      <div className="space-y-1">
                        <div className="flex justify-between">
                          <Text size="xs" color="muted">
                            TPC Group
                          </Text>
                          <Text size="sm" weight="semibold" className="text-green-600">
                            {metric.value}
                          </Text>
                        </div>
                        <div className="flex justify-between">
                          <Text size="xs" color="muted">
                            Industry Avg
                          </Text>
                          <Text size="sm">{metric.benchmark}</Text>
                        </div>
                      </div>
                    </div>
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
