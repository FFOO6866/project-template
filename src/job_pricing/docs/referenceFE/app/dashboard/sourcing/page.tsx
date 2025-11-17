"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Heading } from "@/components/ui/heading"
import { Text } from "@/components/ui/text"
import { DashboardShell } from "@/components/dashboard-shell"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Search,
  Filter,
  Download,
  Plus,
  Globe,
  Linkedin,
  Mail,
  Phone,
  MapPin,
  Briefcase,
  GraduationCap,
  Star,
} from "lucide-react"

export default function SourcingDashboardPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedFilters, setSelectedFilters] = useState<string[]>([])

  const sourcingMetrics = [
    { title: "Active Sources", value: "12", description: "Platforms & channels" },
    { title: "Candidates Sourced", value: "1,847", description: "This month" },
    { title: "Response Rate", value: "34%", description: "Outreach success" },
    { title: "Quality Score", value: "4.2/5", description: "Average candidate rating" },
  ]

  const sourcingChannels = [
    {
      name: "LinkedIn Recruiter",
      status: "Active",
      candidates: 542,
      responseRate: 28,
      cost: "SGD 2,400/month",
      quality: 4.3,
    },
    {
      name: "Indeed Prime",
      status: "Active",
      candidates: 234,
      responseRate: 22,
      cost: "SGD 1,800/month",
      quality: 3.9,
    },
    {
      name: "Executive Search Firms",
      status: "Active",
      candidates: 87,
      responseRate: 65,
      cost: "SGD 15,000/placement",
      quality: 4.8,
    },
    {
      name: "University Partnerships",
      status: "Active",
      candidates: 156,
      responseRate: 45,
      cost: "SGD 500/month",
      quality: 4.1,
    },
    {
      name: "Employee Referrals",
      status: "Active",
      candidates: 298,
      responseRate: 78,
      cost: "SGD 2,000/hire",
      quality: 4.6,
    },
    {
      name: "GitHub Talent",
      status: "Pilot",
      candidates: 45,
      responseRate: 31,
      cost: "SGD 1,200/month",
      quality: 4.2,
    },
  ]

  const candidateProfiles = [
    {
      name: "Alex Chen",
      title: "Senior Software Engineer",
      company: "Tech Startup",
      location: "Singapore",
      experience: "8 years",
      skills: ["React", "Node.js", "AWS", "Python"],
      education: "NUS Computer Science",
      salary: "SGD 120K",
      availability: "2 weeks notice",
      source: "LinkedIn",
      matchScore: 92,
      contacted: false,
    },
    {
      name: "Maria Rodriguez",
      title: "Property Development Manager",
      company: "Global Real Estate",
      location: "Singapore",
      experience: "12 years",
      skills: ["Project Management", "Real Estate", "Finance", "Negotiation"],
      education: "NTU Business",
      salary: "SGD 95K",
      availability: "1 month notice",
      source: "Executive Search",
      matchScore: 88,
      contacted: true,
    },
    {
      name: "David Kim",
      title: "Data Scientist",
      company: "Fintech Company",
      location: "Singapore",
      experience: "6 years",
      skills: ["Python", "Machine Learning", "SQL", "Tableau"],
      education: "SMU Analytics",
      salary: "SGD 110K",
      availability: "Immediate",
      source: "Indeed",
      matchScore: 85,
      contacted: false,
    },
    {
      name: "Sarah Tan",
      title: "Hotel Operations Manager",
      company: "Luxury Hotel Chain",
      location: "Singapore",
      experience: "10 years",
      skills: ["Operations", "Customer Service", "Team Leadership", "Revenue Management"],
      education: "SIT Hospitality",
      salary: "SGD 85K",
      availability: "3 weeks notice",
      source: "Referral",
      matchScore: 90,
      contacted: true,
    },
  ]

  const aiInsights = [
    {
      type: "Opportunity",
      title: "High-Quality Candidates Available",
      description: "15% increase in senior-level candidates in the market this month",
      action: "Increase outreach to senior profiles",
    },
    {
      type: "Trend",
      title: "Skills Demand Shift",
      description: "AI/ML skills showing 40% higher response rates",
      action: "Adjust search criteria to include emerging tech skills",
    },
    {
      type: "Alert",
      title: "Competitor Activity",
      description: "CapitaLand increased hiring activity by 25% this quarter",
      action: "Review compensation packages for competitiveness",
    },
  ]

  const handleContactCandidate = (candidateName: string) => {
    console.log(`Contacting ${candidateName}`)
  }

  return (
    <DashboardShell>
      <div className="space-y-6">
        <div className="flex justify-between items-start">
          <div>
            <Heading level="h1" className="mb-2">
              Sourcing Dashboard
            </Heading>
            <Text size="lg" color="muted">
              AI-powered candidate discovery and outreach management
            </Text>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm">
              <Filter className="h-4 w-4 mr-2" />
              Advanced Filters
            </Button>
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
            <Button size="sm">
              <Plus className="h-4 w-4 mr-2" />
              New Search
            </Button>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid gap-4 md:grid-cols-4">
          {sourcingMetrics.map((metric, index) => (
            <Card key={index}>
              <CardContent className="p-4">
                <div className="text-2xl font-bold">{metric.value}</div>
                <div className="text-sm font-medium">{metric.title}</div>
                <div className="text-xs text-muted-foreground">{metric.description}</div>
              </CardContent>
            </Card>
          ))}
        </div>

        <Tabs defaultValue="candidate-search" className="space-y-6">
          <TabsList>
            <TabsTrigger value="candidate-search">Candidate Search</TabsTrigger>
            <TabsTrigger value="sourcing-channels">Sourcing Channels</TabsTrigger>
            <TabsTrigger value="ai-insights">AI Insights</TabsTrigger>
            <TabsTrigger value="outreach-campaigns">Outreach Campaigns</TabsTrigger>
          </TabsList>

          <TabsContent value="candidate-search" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>AI-Powered Candidate Search</CardTitle>
                <CardDescription>Find the best candidates using intelligent matching algorithms</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-4">
                  <div className="flex-1">
                    <Input
                      placeholder="Search by role, skills, company, or keywords..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full"
                    />
                  </div>
                  <Button>
                    <Search className="h-4 w-4 mr-2" />
                    Search
                  </Button>
                </div>

                <div className="flex gap-2 flex-wrap">
                  {["Software Engineer", "Property Manager", "Data Scientist", "Hotel Manager"].map((filter) => (
                    <Badge
                      key={filter}
                      variant={selectedFilters.includes(filter) ? "default" : "outline"}
                      className="cursor-pointer"
                      onClick={() =>
                        setSelectedFilters((prev) =>
                          prev.includes(filter) ? prev.filter((f) => f !== filter) : [...prev, filter],
                        )
                      }
                    >
                      {filter}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>

            <div className="grid gap-6">
              {candidateProfiles.map((candidate, index) => (
                <Card key={index} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-6">
                    <div className="flex justify-between items-start mb-4">
                      <div className="flex items-start gap-4">
                        <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                          <Text size="sm" weight="medium" className="text-blue-600">
                            {candidate.name
                              .split(" ")
                              .map((n) => n[0])
                              .join("")}
                          </Text>
                        </div>
                        <div>
                          <Text size="lg" weight="semibold">
                            {candidate.name}
                          </Text>
                          <Text size="sm" color="muted">
                            {candidate.title} at {candidate.company}
                          </Text>
                          <div className="flex items-center gap-4 mt-2 text-sm text-gray-600">
                            <div className="flex items-center gap-1">
                              <MapPin className="h-3 w-3" />
                              {candidate.location}
                            </div>
                            <div className="flex items-center gap-1">
                              <Briefcase className="h-3 w-3" />
                              {candidate.experience}
                            </div>
                            <div className="flex items-center gap-1">
                              <GraduationCap className="h-3 w-3" />
                              {candidate.education}
                            </div>
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="flex items-center gap-1 mb-2">
                          <Star className="h-4 w-4 text-yellow-500" />
                          <Text size="sm" weight="medium">
                            {candidate.matchScore}% match
                          </Text>
                        </div>
                        <Badge variant="outline" className="text-xs">
                          via {candidate.source}
                        </Badge>
                      </div>
                    </div>

                    <div className="space-y-3">
                      <div>
                        <Text size="sm" weight="medium" className="mb-2">
                          Key Skills
                        </Text>
                        <div className="flex gap-2 flex-wrap">
                          {candidate.skills.map((skill) => (
                            <Badge key={skill} variant="secondary" className="text-xs">
                              {skill}
                            </Badge>
                          ))}
                        </div>
                      </div>

                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div>
                          <Text size="xs" color="muted">
                            Current Salary
                          </Text>
                          <Text size="sm" weight="medium">
                            {candidate.salary}
                          </Text>
                        </div>
                        <div>
                          <Text size="xs" color="muted">
                            Availability
                          </Text>
                          <Text size="sm" weight="medium">
                            {candidate.availability}
                          </Text>
                        </div>
                        <div>
                          <Text size="xs" color="muted">
                            Status
                          </Text>
                          <Badge variant={candidate.contacted ? "default" : "outline"} className="text-xs">
                            {candidate.contacted ? "Contacted" : "Not Contacted"}
                          </Badge>
                        </div>
                      </div>

                      <div className="flex gap-2 pt-2">
                        <Button
                          size="sm"
                          onClick={() => handleContactCandidate(candidate.name)}
                          disabled={candidate.contacted}
                        >
                          <Mail className="h-4 w-4 mr-2" />
                          {candidate.contacted ? "Contacted" : "Send Message"}
                        </Button>
                        <Button variant="outline" size="sm">
                          <Linkedin className="h-4 w-4 mr-2" />
                          LinkedIn
                        </Button>
                        <Button variant="outline" size="sm">
                          <Phone className="h-4 w-4 mr-2" />
                          Call
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="sourcing-channels" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Sourcing Channel Performance</CardTitle>
                <CardDescription>Monitor and optimize your talent acquisition channels</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {sourcingChannels.map((channel, index) => (
                    <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                          <Globe className="h-5 w-5 text-blue-600" />
                        </div>
                        <div>
                          <Text size="sm" weight="medium">
                            {channel.name}
                          </Text>
                          <Text size="xs" color="muted">
                            {channel.candidates} candidates • {channel.responseRate}% response rate
                          </Text>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <Text size="sm" weight="medium">
                            {channel.cost}
                          </Text>
                          <div className="flex items-center gap-1">
                            <Star className="h-3 w-3 text-yellow-500" />
                            <Text size="xs">{channel.quality}/5</Text>
                          </div>
                        </div>
                        <Badge variant={channel.status === "Active" ? "default" : "secondary"}>{channel.status}</Badge>
                      </div>
                    </div>
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
                              insight.type === "Opportunity"
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
                        <Text size="sm" weight="medium" className="text-blue-600">
                          Recommended Action: {insight.action}
                        </Text>
                      </div>
                      <Button variant="outline" size="sm">
                        Take Action
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="outreach-campaigns" className="space-y-6">
            <Card>
              <CardHeader>
                <div className="flex justify-between items-center">
                  <div>
                    <CardTitle>Outreach Campaigns</CardTitle>
                    <CardDescription>Manage and track your candidate outreach efforts</CardDescription>
                  </div>
                  <Button size="sm">
                    <Plus className="h-4 w-4 mr-2" />
                    New Campaign
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-center py-12 text-gray-500">
                  <Mail className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <Text>No active campaigns. Create your first outreach campaign to get started.</Text>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardShell>
  )
}
