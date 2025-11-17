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
import { Filter, Download, Search, Plus, Eye, MessageSquare, Calendar } from "lucide-react"
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, PieChart, Pie, Cell } from "recharts"

export default function TalentPipelinePage() {
  const [selectedSource, setSelectedSource] = useState("all")
  const [selectedRole, setSelectedRole] = useState("all")

  const pipelineMetrics = [
    {
      title: "Active Candidates",
      value: "1,247",
      change: "+18%",
      trend: "up" as const,
      category: "people" as const,
      description: "In pipeline across all roles",
    },
    {
      title: "Pipeline Conversion",
      value: "23%",
      change: "+5%",
      trend: "up" as const,
      category: "performance" as const,
      description: "Application to hire rate",
    },
    {
      title: "Time to Fill",
      value: "28 days",
      change: "-6 days",
      trend: "up" as const,
      category: "process" as const,
      description: "Average across all roles",
    },
    {
      title: "Quality of Hire",
      value: "4.2/5",
      change: "+0.3",
      trend: "up" as const,
      category: "performance" as const,
      description: "90-day performance rating",
    },
  ]

  const candidatesBySource = [
    { source: "Internal Referrals", count: 342, percentage: 27, quality: 4.5 },
    { source: "LinkedIn", count: 298, percentage: 24, quality: 4.1 },
    { source: "Job Portals", count: 234, percentage: 19, quality: 3.8 },
    { source: "Executive Search", count: 187, percentage: 15, quality: 4.7 },
    { source: "University Partnerships", count: 123, percentage: 10, quality: 4.0 },
    { source: "Direct Applications", count: 63, percentage: 5, quality: 3.6 },
  ]

  const pipelineByStage = [
    { stage: "Sourced", count: 1247, conversion: 100 },
    { stage: "Screened", count: 892, conversion: 72 },
    { stage: "Interviewed", count: 456, conversion: 51 },
    { stage: "Assessment", count: 234, conversion: 51 },
    { stage: "Final Round", count: 123, conversion: 53 },
    { stage: "Offer", count: 67, conversion: 54 },
    { stage: "Hired", count: 43, conversion: 64 },
  ]

  const diversityMetrics = [
    { category: "Gender", target: 50, current: 48, trend: "+2%" },
    { category: "Age Diversity", target: 30, current: 32, trend: "+5%" },
    { category: "Educational Background", target: 40, current: 38, trend: "+3%" },
    { category: "Geographic Diversity", target: 25, current: 28, trend: "+8%" },
  ]

  const topRoles = [
    {
      role: "Software Engineer",
      openings: 12,
      candidates: 234,
      timeToFill: 32,
      priority: "High",
    },
    {
      role: "Property Manager",
      openings: 8,
      candidates: 156,
      timeToFill: 28,
      priority: "High",
    },
    {
      role: "Data Analyst",
      openings: 6,
      candidates: 189,
      timeToFill: 25,
      priority: "Medium",
    },
    {
      role: "Hotel Operations Manager",
      openings: 4,
      candidates: 87,
      timeToFill: 35,
      priority: "High",
    },
    {
      role: "Investment Analyst",
      openings: 3,
      candidates: 145,
      timeToFill: 42,
      priority: "Medium",
    },
  ]

  const recentCandidates = [
    {
      name: "Sarah Chen",
      role: "Senior Data Analyst",
      source: "LinkedIn",
      stage: "Final Round",
      score: 4.5,
      experience: "8 years",
      lastActivity: "2 hours ago",
    },
    {
      name: "Michael Rodriguez",
      role: "Property Development Manager",
      source: "Executive Search",
      stage: "Assessment",
      score: 4.7,
      experience: "12 years",
      lastActivity: "1 day ago",
    },
    {
      name: "Jennifer Kim",
      role: "Hotel Operations Supervisor",
      source: "Internal Referral",
      stage: "Interviewed",
      score: 4.2,
      experience: "6 years",
      lastActivity: "3 hours ago",
    },
    {
      name: "David Tan",
      role: "Investment Associate",
      source: "University Partnership",
      stage: "Screened",
      score: 4.0,
      experience: "2 years",
      lastActivity: "5 hours ago",
    },
  ]

  const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"]

  return (
    <DashboardShell>
      <div className="space-y-6">
        <div className="flex justify-between items-start">
          <div>
            <Heading level="h1" className="mb-2">
              Talent Pipeline Engine
            </Heading>
            <Text size="lg" color="muted">
              AI-powered candidate sourcing and pipeline management across TPC Group
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
              Add Candidate
            </Button>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {pipelineMetrics.map((metric, index) => (
            <MetricCard key={index} {...metric} />
          ))}
        </div>

        <Tabs defaultValue="pipeline-overview" className="space-y-6">
          <TabsList>
            <TabsTrigger value="pipeline-overview">Pipeline Overview</TabsTrigger>
            <TabsTrigger value="sourcing-analytics">Sourcing Analytics</TabsTrigger>
            <TabsTrigger value="diversity-insights">Diversity & Inclusion</TabsTrigger>
            <TabsTrigger value="candidate-management">Candidate Management</TabsTrigger>
          </TabsList>

          <TabsContent value="pipeline-overview" className="space-y-6">
            <div className="grid gap-6 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>Pipeline Funnel Analysis</CardTitle>
                  <CardDescription>Conversion rates at each stage</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={pipelineByStage}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="stage" angle={-45} textAnchor="end" height={80} />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="count" fill="#3b82f6" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>High-Priority Roles</CardTitle>
                  <CardDescription>Current openings requiring immediate attention</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {topRoles.slice(0, 4).map((role, index) => (
                      <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                        <div>
                          <Text size="sm" weight="medium">
                            {role.role}
                          </Text>
                          <Text size="xs" color="muted">
                            {role.openings} openings • {role.candidates} candidates
                          </Text>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge variant={role.priority === "High" ? "destructive" : "secondary"} className="text-xs">
                            {role.priority}
                          </Badge>
                          <Text size="xs" color="muted">
                            {role.timeToFill}d
                          </Text>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="sourcing-analytics" className="space-y-6">
            <div className="grid gap-6 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>Candidate Sources Performance</CardTitle>
                  <CardDescription>Volume and quality by source channel</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {candidatesBySource.map((source, index) => (
                      <div key={index} className="space-y-2">
                        <div className="flex justify-between items-center">
                          <Text size="sm">{source.source}</Text>
                          <div className="flex items-center gap-2">
                            <Text size="sm" weight="medium">
                              {source.count}
                            </Text>
                            <Badge variant="outline" className="text-xs">
                              {source.quality}/5
                            </Badge>
                          </div>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${source.percentage}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Source Distribution</CardTitle>
                  <CardDescription>Candidate volume by channel</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={candidatesBySource}
                        cx="50%"
                        cy="50%"
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="count"
                        label={({ source, percentage }) => `${source}: ${percentage}%`}
                      >
                        {candidatesBySource.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="diversity-insights" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Diversity & Inclusion Metrics</CardTitle>
                <CardDescription>Progress towards diversity targets in candidate pipeline</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid gap-6 md:grid-cols-2">
                  {diversityMetrics.map((metric, index) => (
                    <div key={index} className="space-y-3">
                      <div className="flex justify-between items-center">
                        <Text size="sm" weight="medium">
                          {metric.category}
                        </Text>
                        <div className="flex items-center gap-2">
                          <Text size="sm">{metric.current}%</Text>
                          <Badge variant="default" className="text-xs">
                            {metric.trend}
                          </Badge>
                        </div>
                      </div>
                      <div className="space-y-1">
                        <div className="flex justify-between text-xs text-gray-500">
                          <span>Current</span>
                          <span>Target: {metric.target}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${
                              metric.current >= metric.target ? "bg-green-500" : "bg-blue-500"
                            }`}
                            style={{ width: `${Math.min((metric.current / metric.target) * 100, 100)}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="candidate-management" className="space-y-6">
            <Card>
              <CardHeader>
                <div className="flex justify-between items-center">
                  <div>
                    <CardTitle>Recent Candidate Activity</CardTitle>
                    <CardDescription>Latest updates and candidate interactions</CardDescription>
                  </div>
                  <Button variant="outline" size="sm">
                    <Search className="h-4 w-4 mr-2" />
                    Search Candidates
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {recentCandidates.map((candidate, index) => (
                    <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                          <Text size="sm" weight="medium" className="text-blue-600">
                            {candidate.name
                              .split(" ")
                              .map((n) => n[0])
                              .join("")}
                          </Text>
                        </div>
                        <div>
                          <Text size="sm" weight="medium">
                            {candidate.name}
                          </Text>
                          <Text size="xs" color="muted">
                            {candidate.role} • {candidate.experience} • via {candidate.source}
                          </Text>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <Badge variant="outline" className="text-xs">
                          {candidate.stage}
                        </Badge>
                        <Badge variant="secondary" className="text-xs">
                          {candidate.score}/5
                        </Badge>
                        <Text size="xs" color="muted">
                          {candidate.lastActivity}
                        </Text>
                        <div className="flex gap-1">
                          <Button variant="ghost" size="sm">
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="sm">
                            <MessageSquare className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="sm">
                            <Calendar className="h-4 w-4" />
                          </Button>
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
