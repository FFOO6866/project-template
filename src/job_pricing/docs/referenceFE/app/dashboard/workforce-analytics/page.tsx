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
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  LineChart,
  Line,
} from "recharts"

export default function WorkforceAnalyticsPage() {
  const [selectedTimeframe, setSelectedTimeframe] = useState("12months")
  const [selectedEntity, setSelectedEntity] = useState("all")

  const metrics = [
    {
      title: "Total Workforce",
      value: "2,847",
      change: "+12%",
      trend: "up" as const,
      category: "people" as const,
      description: "Across all TPC entities",
    },
    {
      title: "Employee Engagement",
      value: "87%",
      change: "+5%",
      trend: "up" as const,
      category: "performance" as const,
      description: "Latest pulse survey",
    },
    {
      title: "Voluntary Turnover",
      value: "8.2%",
      change: "-2.1%",
      trend: "up" as const,
      category: "people" as const,
      description: "Below industry average",
    },
    {
      title: "Internal Mobility",
      value: "23%",
      change: "+8%",
      trend: "up" as const,
      category: "process" as const,
      description: "Roles filled internally",
    },
  ]

  const workforceByEntity = [
    { entity: "TPC Properties", count: 1245, percentage: 44 },
    { entity: "TPC Hospitality", count: 892, percentage: 31 },
    { entity: "TPC Investments", count: 234, percentage: 8 },
    { entity: "TPC Asset Mgmt", count: 187, percentage: 7 },
    { entity: "TPC Corporate", count: 289, percentage: 10 },
  ]

  const diversityData = [
    { category: "Gender", male: 52, female: 48 },
    { category: "Age Groups", "20-30": 28, "31-40": 35, "41-50": 25, "51+": 12 },
    { category: "Tenure", "0-2y": 32, "3-5y": 28, "6-10y": 25, "10y+": 15 },
  ]

  const performanceDistribution = [
    { rating: "Exceeds", count: 427, color: "#10b981" },
    { rating: "Meets", count: 1892, color: "#3b82f6" },
    { rating: "Developing", count: 456, color: "#f59e0b" },
    { rating: "Below", count: 72, color: "#ef4444" },
  ]

  const skillsGapData = [
    { skill: "Digital Transformation", gap: 35, priority: "High" },
    { skill: "Data Analytics", gap: 28, priority: "High" },
    { skill: "ESG & Sustainability", gap: 42, priority: "Medium" },
    { skill: "AI & Machine Learning", gap: 67, priority: "High" },
    { skill: "Project Management", gap: 18, priority: "Low" },
  ]

  const monthlyTrends = [
    { month: "Jan", headcount: 2756, engagement: 84, turnover: 9.1 },
    { month: "Feb", headcount: 2768, engagement: 85, turnover: 8.8 },
    { month: "Mar", headcount: 2781, engagement: 86, turnover: 8.5 },
    { month: "Apr", headcount: 2795, engagement: 87, turnover: 8.3 },
    { month: "May", headcount: 2812, engagement: 87, turnover: 8.1 },
    { month: "Jun", headcount: 2847, engagement: 87, turnover: 8.2 },
  ]

  return (
    <DashboardShell>
      <div className="space-y-6">
        <div className="flex justify-between items-start">
          <div>
            <Heading level="h1" className="mb-2">
              Workforce Analytics
            </Heading>
            <Text size="lg" color="muted">
              Comprehensive workforce insights across TPC Group's diverse portfolio
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

        {/* Key Metrics */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {metrics.map((metric, index) => (
            <MetricCard key={index} {...metric} />
          ))}
        </div>

        {/* Filters */}
        <div className="flex gap-4">
          <select
            className="px-3 py-2 border border-gray-300 rounded-md text-sm"
            value={selectedTimeframe}
            onChange={(e) => setSelectedTimeframe(e.target.value)}
          >
            <option value="3months">Last 3 Months</option>
            <option value="6months">Last 6 Months</option>
            <option value="12months">Last 12 Months</option>
            <option value="24months">Last 24 Months</option>
          </select>
          <select
            className="px-3 py-2 border border-gray-300 rounded-md text-sm"
            value={selectedEntity}
            onChange={(e) => setSelectedEntity(e.target.value)}
          >
            <option value="all">All Entities</option>
            <option value="properties">TPC Properties</option>
            <option value="hospitality">TPC Hospitality</option>
            <option value="investments">TPC Investments</option>
            <option value="corporate">TPC Corporate</option>
          </select>
        </div>

        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="diversity">Diversity & Inclusion</TabsTrigger>
            <TabsTrigger value="performance">Performance</TabsTrigger>
            <TabsTrigger value="skills">Skills & Capabilities</TabsTrigger>
            <TabsTrigger value="trends">Trends & Forecasting</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <div className="grid gap-6 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>Workforce Distribution by Entity</CardTitle>
                  <CardDescription>Employee count across TPC Group companies</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {workforceByEntity.map((entity, index) => (
                      <div key={index} className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-3 h-3 rounded-full bg-blue-500" />
                          <Text size="sm">{entity.entity}</Text>
                        </div>
                        <div className="flex items-center gap-3">
                          <Text size="sm" weight="medium">
                            {entity.count}
                          </Text>
                          <Badge variant="secondary">{entity.percentage}%</Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Monthly Workforce Trends</CardTitle>
                  <CardDescription>Headcount growth over time</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={monthlyTrends}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="month" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Line type="monotone" dataKey="headcount" stroke="#3b82f6" strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="diversity" className="space-y-6">
            <div className="grid gap-6 md:grid-cols-3">
              {diversityData.map((data, index) => (
                <Card key={index}>
                  <CardHeader>
                    <CardTitle>{data.category} Distribution</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {Object.entries(data)
                        .filter(([key]) => key !== "category")
                        .map(([key, value]) => (
                          <div key={key} className="flex justify-between items-center">
                            <Text size="sm">{key}</Text>
                            <Badge variant="outline">{value}%</Badge>
                          </div>
                        ))}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="performance" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Performance Rating Distribution</CardTitle>
                <CardDescription>Latest performance review cycle results</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={performanceDistribution}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="rating" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" fill="#3b82f6" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="skills" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Critical Skills Gap Analysis</CardTitle>
                <CardDescription>Priority skills requiring development investment</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {skillsGapData.map((skill, index) => (
                    <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                      <div>
                        <Text size="sm" weight="medium">
                          {skill.skill}
                        </Text>
                        <Text size="xs" color="muted">
                          Gap: {skill.gap}% of workforce
                        </Text>
                      </div>
                      <Badge
                        variant={
                          skill.priority === "High"
                            ? "destructive"
                            : skill.priority === "Medium"
                              ? "default"
                              : "secondary"
                        }
                      >
                        {skill.priority}
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="trends" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Key Workforce Trends</CardTitle>
                <CardDescription>Engagement and turnover trends over time</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={monthlyTrends}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="engagement" stroke="#10b981" strokeWidth={2} />
                    <Line type="monotone" dataKey="turnover" stroke="#ef4444" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardShell>
  )
}
