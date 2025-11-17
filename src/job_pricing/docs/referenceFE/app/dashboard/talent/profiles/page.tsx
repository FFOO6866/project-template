"use client"

import { AvatarFallback } from "@/components/ui/avatar"
import { AvatarImage } from "@/components/ui/avatar"
import { Avatar } from "@/components/ui/avatar"
import { DashboardShell } from "@/components/dashboard-shell"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { Filter, Search, Download, FileText, BarChart2, Settings, List, LayoutGrid } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Heading } from "@/components/ui/heading"
import { Text } from "@/components/ui/text"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { TeamMemberCard } from "@/components/team-member-card"
import { TeamComparisonChart } from "@/components/team-comparison-chart"
import { TeamNetworkGraph } from "@/components/team-network-graph"
import { ConsciousnessLineIndicator } from "@/components/consciousness-line-indicator"
import Link from "next/link"
import { useState } from "react"
import { Badge } from "@/components/ui/badge"

export default function MTProfilesPage() {
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid")

  // Team member data - updated with silhouette images
  const teamMembers = [
    {
      name: "Camille Wong Yuk",
      role: "Management Trainee",
      department: "Executive",
      imageUrl: "/silhouette-female.png",
      strengths: ["Strategic Thinking", "Communication", "Adaptability"],
      rmrrScore: 85,
      leadershipScore: 82,
      influenceScore: 78,
      consciousnessLevel: "Willingness",
      consciousnessValue: 310,
    },
    {
      name: "Marcel Melhado",
      role: "Management Trainee",
      department: "Executive",
      imageUrl: "/silhouette-male.png",
      strengths: ["Problem Solving", "Team Collaboration", "Innovation"],
      rmrrScore: 83,
      leadershipScore: 80,
      influenceScore: 85,
      consciousnessLevel: "Acceptance",
      consciousnessValue: 350,
    },
    {
      name: "Vivian Ho",
      role: "Management Trainee",
      department: "Executive",
      imageUrl: "/silhouette-female.png",
      strengths: ["Data Analysis", "Project Management", "Critical Thinking"],
      rmrrScore: 88,
      leadershipScore: 79,
      influenceScore: 81,
      consciousnessLevel: "Reason",
      consciousnessValue: 400,
    },
    {
      name: "Massie Shen",
      role: "Management Trainee",
      department: "Executive",
      imageUrl: "/silhouette-female.png",
      strengths: ["Financial Acumen", "Strategic Planning", "Negotiation"],
      rmrrScore: 86,
      leadershipScore: 83,
      influenceScore: 80,
      consciousnessLevel: "Acceptance",
      consciousnessValue: 350,
    },
    {
      name: "Gloria Cai Xinyi",
      role: "Management Trainee",
      department: "Executive",
      imageUrl: "/silhouette-female.png",
      strengths: ["Market Research", "Customer Insights", "Strategic Vision"],
      rmrrScore: 84,
      leadershipScore: 81,
      influenceScore: 87,
      consciousnessLevel: "Neutrality",
      consciousnessValue: 250,
    },
    {
      name: "Egan Valentino",
      role: "Management Trainee",
      department: "Executive",
      imageUrl: "/silhouette-male.png",
      strengths: ["Digital Marketing", "Content Strategy", "Analytics"],
      rmrrScore: 82,
      leadershipScore: 78,
      influenceScore: 89,
      consciousnessLevel: "Willingness",
      consciousnessValue: 310,
    },
    {
      name: "Madhav Kapoor",
      role: "Management Trainee",
      department: "Executive",
      imageUrl: "/silhouette-male.png",
      strengths: ["Technical Knowledge", "Problem Solving", "Innovation"],
      rmrrScore: 87,
      leadershipScore: 80,
      influenceScore: 82,
      consciousnessLevel: "Reason",
      consciousnessValue: 400,
    },
    {
      name: "Shauryaa Ladha",
      role: "Management Trainee",
      department: "Executive",
      imageUrl: "/silhouette-female.png",
      strengths: ["Process Optimization", "Team Building", "Change Management"],
      rmrrScore: 85,
      leadershipScore: 84,
      influenceScore: 79,
      consciousnessLevel: "Acceptance",
      consciousnessValue: 350,
    },
    {
      name: "Jane Putri",
      role: "Management Trainee",
      department: "Executive",
      imageUrl: "/silhouette-female.png",
      strengths: ["Financial Analysis", "Risk Management", "Strategic Planning"],
      rmrrScore: 89,
      leadershipScore: 81,
      influenceScore: 78,
      consciousnessLevel: "Neutrality",
      consciousnessValue: 250,
    },
    {
      name: "Mathew Ling",
      role: "Management Trainee",
      department: "Executive",
      imageUrl: "/silhouette-male.png",
      strengths: ["Product Development", "User Experience", "Market Analysis"],
      rmrrScore: 84,
      leadershipScore: 82,
      influenceScore: 85,
      consciousnessLevel: "Willingness",
      consciousnessValue: 310,
    },
    {
      name: "Wu Hong Rui",
      role: "Management Trainee",
      department: "Executive",
      imageUrl: "/silhouette-male.png",
      strengths: ["Brand Strategy", "Digital Marketing", "Communication"],
      rmrrScore: 83,
      leadershipScore: 79,
      influenceScore: 88,
      consciousnessLevel: "Acceptance",
      consciousnessValue: 350,
    },
    {
      name: "Ra Won Park",
      role: "Management Trainee",
      department: "Executive",
      imageUrl: "/silhouette-female.png",
      strengths: ["Talent Development", "Organizational Design", "Culture Building"],
      rmrrScore: 86,
      leadershipScore: 85,
      influenceScore: 80,
      consciousnessLevel: "Reason",
      consciousnessValue: 400,
    },
  ]

  // Generate profile URL - updated to link to Performance Matrix with member parameter
  const getProfileUrl = (name: string) => {
    return `/dashboard/talent/profiles/performance?member=${name.toLowerCase().replace(/\s+/g, "-")}`
  }

  return (
    <DashboardShell>
      <div className="flex flex-col space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <Heading level="h1">MT Profiles</Heading>
            <Text color="muted">Management Team profiles, assessments, and team dynamics</Text>
          </div>
          <div className="flex items-center gap-2">
            <div className="relative w-64">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input type="search" placeholder="Search team members..." className="w-full pl-8" />
            </div>
            <Button variant="outline" size="icon">
              <Filter className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="sm" className="h-9">
              <Download className="mr-2 h-4 w-4" />
              Export
            </Button>
          </div>
        </div>

        {/* Submodule Navigation */}
        <div className="flex flex-wrap items-center gap-4">
          <Link href="/dashboard/talent/profiles">
            <Button variant="secondary" className="h-9">
              <BarChart2 className="mr-2 h-4 w-4" />
              Team Overview
            </Button>
          </Link>
          <Link href="/dashboard/talent/profiles/performance">
            <Button variant="outline" className="h-9">
              <BarChart2 className="mr-2 h-4 w-4" />
              Performance Matrix
            </Button>
          </Link>
          <Link href="/dashboard/talent/profiles/documents">
            <Button variant="outline" className="h-9">
              <FileText className="mr-2 h-4 w-4" />
              Document Management
            </Button>
          </Link>
          <Link href="/dashboard/talent/profiles/admin">
            <Button variant="outline" className="h-9">
              <Settings className="mr-2 h-4 w-4" />
              Admin
            </Button>
          </Link>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <Text size="sm" weight="medium">
                Department:
              </Text>
              <Select defaultValue="all">
                <SelectTrigger className="w-[180px] h-9">
                  <SelectValue placeholder="All Departments" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Departments</SelectItem>
                  <SelectItem value="executive">Executive</SelectItem>
                  <SelectItem value="product">Product & Development</SelectItem>
                  <SelectItem value="marketing">Marketing & Sales</SelectItem>
                  <SelectItem value="operations">Operations</SelectItem>
                  <SelectItem value="finance">Finance</SelectItem>
                  <SelectItem value="hr">Human Resources</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-2">
              <Text size="sm" weight="medium">
                Level:
              </Text>
              <Select defaultValue="all">
                <SelectTrigger className="w-[180px] h-9">
                  <SelectValue placeholder="All Levels" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Levels</SelectItem>
                  <SelectItem value="c-suite">C-Suite</SelectItem>
                  <SelectItem value="vp">VP Level</SelectItem>
                  <SelectItem value="director">Director Level</SelectItem>
                  <SelectItem value="senior">Senior Management</SelectItem>
                  <SelectItem value="middle">Middle Management</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Text size="sm" weight="medium">
              View:
            </Text>
            <div className="flex items-center border rounded-md overflow-hidden">
              <Button
                variant={viewMode === "grid" ? "default" : "ghost"}
                size="sm"
                className="rounded-none h-9 px-3"
                onClick={() => setViewMode("grid")}
              >
                <LayoutGrid className="h-4 w-4 mr-2" />
                Grid
              </Button>
              <Button
                variant={viewMode === "list" ? "default" : "ghost"}
                size="sm"
                className="rounded-none h-9 px-3"
                onClick={() => setViewMode("list")}
              >
                <List className="h-4 w-4 mr-2" />
                List
              </Button>
            </div>
          </div>
        </div>

        {viewMode === "grid" && (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {teamMembers.map((member) => (
              <TeamMemberCard
                key={member.name}
                name={member.name}
                role={member.role}
                department={member.department}
                imageUrl={member.imageUrl}
                strengths={member.strengths}
                rmrrScore={member.rmrrScore}
                leadershipScore={member.leadershipScore}
                influenceScore={member.influenceScore}
                consciousnessLevel={member.consciousnessLevel}
                consciousnessValue={member.consciousnessValue}
              />
            ))}
          </div>
        )}

        {viewMode === "list" && (
          <Card className="overflow-hidden">
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="text-left p-4 font-medium">Name</th>
                      <th className="text-left p-4 font-medium">Role</th>
                      <th className="text-left p-4 font-medium">Department</th>
                      <th className="text-left p-4 font-medium">X Factor 1</th>
                      <th className="text-left p-4 font-medium">X Factor 2</th>
                      <th className="text-left p-4 font-medium">X Factor 3</th>
                      <th className="text-left p-4 font-medium">Consciousness</th>
                      <th className="text-left p-4 font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {teamMembers.map((member) => (
                      <tr key={member.name} className="border-b hover:bg-muted/50 transition-colors">
                        <td className="p-4">
                          <div className="flex items-center gap-3">
                            <Avatar className="h-8 w-8">
                              <AvatarImage src={member.imageUrl || "/placeholder.svg"} alt={member.name} />
                              <AvatarFallback>
                                {member.name
                                  .split(" ")
                                  .map((n) => n[0])
                                  .join("")}
                              </AvatarFallback>
                            </Avatar>
                            <span className="font-medium">{member.name}</span>
                          </div>
                        </td>
                        <td className="p-4">{member.role}</td>
                        <td className="p-4">{member.department}</td>
                        <td className="p-4">
                          <Badge variant={member.rmrrScore >= 90 ? "success" : "default"}>{member.rmrrScore}%</Badge>
                        </td>
                        <td className="p-4">
                          <Badge variant={member.leadershipScore >= 90 ? "success" : "default"}>
                            {member.leadershipScore}%
                          </Badge>
                        </td>
                        <td className="p-4">
                          <Badge variant={member.influenceScore >= 90 ? "success" : "default"}>
                            {member.influenceScore}%
                          </Badge>
                        </td>
                        <td className="p-4 w-48">
                          <ConsciousnessLineIndicator
                            level={member.consciousnessLevel}
                            value={member.consciousnessValue}
                            className="h-6"
                          />
                        </td>
                        <td className="p-4">
                          <Link href={getProfileUrl(member.name)}>
                            <Button variant="ghost" size="sm">
                              View
                            </Button>
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        )}

        <Tabs defaultValue="team-dynamics" className="space-y-6 mt-6">
          <TabsList>
            <TabsTrigger value="team-dynamics">Team Dynamics</TabsTrigger>
            <TabsTrigger value="competency-comparison">Competency Comparison</TabsTrigger>
            <TabsTrigger value="succession-planning">Succession Planning</TabsTrigger>
          </TabsList>

          <TabsContent value="team-dynamics" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Management Team Network</CardTitle>
                <CardDescription>
                  Visualization of relationships and collaboration patterns within the management team
                </CardDescription>
              </CardHeader>
              <CardContent className="h-[500px] p-0">
                <TeamNetworkGraph />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="competency-comparison" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Competency Comparison</CardTitle>
                <CardDescription>Comparative analysis of key competencies across the management team</CardDescription>
              </CardHeader>
              <CardContent className="h-[500px]">
                <TeamComparisonChart />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="succession-planning" className="space-y-6">
            <div className="grid gap-6 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>Succession Readiness</CardTitle>
                  <CardDescription>Assessment of succession readiness for key positions</CardDescription>
                </CardHeader>
                <CardContent className="h-[300px] flex items-center justify-center text-muted-foreground">
                  Succession readiness visualization placeholder
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Development Needs</CardTitle>
                  <CardDescription>Identified development areas for potential successors</CardDescription>
                </CardHeader>
                <CardContent className="h-[300px] flex items-center justify-center text-muted-foreground">
                  Development needs visualization placeholder
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardShell>
  )
}
