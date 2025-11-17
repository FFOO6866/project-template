"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Heading } from "@/components/ui/heading"
import { Text } from "@/components/ui/text"
import { DashboardShell } from "@/components/dashboard-shell"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Sparkles, FileText, Download, Copy, RefreshCw, CheckCircle, AlertCircle, Target, BookOpen } from "lucide-react"

export default function JobDescriptionWriterPage() {
  const [jobTitle, setJobTitle] = useState("")
  const [department, setDepartment] = useState("")
  const [level, setLevel] = useState("")
  const [isGenerating, setIsGenerating] = useState(false)
  const [generatedJD, setGeneratedJD] = useState("")
  const [selectedSkills, setSelectedSkills] = useState<string[]>([])

  const ssgSkills = [
    "Strategic Planning",
    "Data Analysis",
    "Project Management",
    "Stakeholder Management",
    "Digital Transformation",
    "Change Management",
    "Team Leadership",
    "Financial Analysis",
    "Risk Management",
    "Communication",
    "Problem Solving",
    "Innovation",
    "Customer Service",
    "Quality Management",
    "Process Improvement",
  ]

  const aiSuggestedSkills = [
    "Artificial Intelligence",
    "Machine Learning",
    "Automation",
    "Cloud Computing",
    "Cybersecurity",
    "ESG Reporting",
    "Sustainability",
    "Agile Methodology",
    "Design Thinking",
    "Emotional Intelligence",
  ]

  const handleGenerateJD = async () => {
    setIsGenerating(true)
    // Simulate AI generation
    await new Promise((resolve) => setTimeout(resolve, 3000))

    const sampleJD = `**Position: ${jobTitle || "Senior Manager, Digital Transformation"}**

**Department:** ${department || "Technology & Innovation"}
**Reports To:** Director, Digital Strategy
**Location:** Singapore
**Employment Type:** Full-time

**Position Overview:**
We are seeking a dynamic ${jobTitle || "Senior Manager, Digital Transformation"} to lead our organization's digital evolution across TPC Group's diverse portfolio. This role will drive strategic initiatives to modernize our operations, enhance customer experiences, and position TPC as a leader in digital innovation within the property and hospitality sectors.

**Key Responsibilities:**

**Strategic Leadership:**
• Develop and execute comprehensive digital transformation strategies aligned with TPC Group's business objectives
• Lead cross-functional teams to implement digital solutions across property development, hospitality, and investment portfolios
• Collaborate with senior leadership to identify and prioritize digital opportunities

**Technology Implementation:**
• Oversee the deployment of emerging technologies including AI, IoT, and automation solutions
• Manage digital project portfolios with budgets exceeding SGD 5M annually
• Ensure seamless integration of new technologies with existing systems

**Stakeholder Management:**
• Partner with business unit leaders to understand digital needs and requirements
• Present digital transformation progress to executive committee and board members
• Build relationships with technology vendors and strategic partners

**Team Development:**
• Lead a team of 8-12 digital specialists and project managers
• Foster a culture of innovation and continuous learning
• Develop digital capabilities across the organization through training and mentorship

**Required Qualifications:**
• Bachelor's degree in Technology, Business, or related field; MBA preferred
• 8-12 years of experience in digital transformation, technology consulting, or related roles
• Proven track record of leading large-scale digital initiatives in real estate or hospitality
• Strong understanding of emerging technologies and their business applications
• Excellent communication and presentation skills
• PMP or equivalent project management certification preferred

**Key Skills & Competencies:**
${selectedSkills.map((skill) => `• ${skill}`).join("\n")}

**What We Offer:**
• Competitive salary package with performance bonuses
• Comprehensive medical and dental coverage
• Professional development opportunities and conference attendance
• Flexible working arrangements
• Career advancement within TPC Group's expanding portfolio

**About TPC Group:**
TPC Group is a leading conglomerate with interests in property development, hospitality, and investment management across Southeast Asia. We are committed to innovation, sustainability, and creating value for all stakeholders.

*TPC Group is an equal opportunity employer committed to diversity and inclusion.*`

    setGeneratedJD(sampleJD)
    setIsGenerating(false)
  }

  const toggleSkill = (skill: string) => {
    setSelectedSkills((prev) => (prev.includes(skill) ? prev.filter((s) => s !== skill) : [...prev, skill]))
  }

  const qualityChecks = [
    { check: "Inclusive Language", status: "pass", description: "No biased language detected" },
    { check: "Skills Alignment", status: "pass", description: "Skills match SSG taxonomy" },
    { check: "Compliance Check", status: "warning", description: "Consider adding diversity statement" },
    { check: "Market Competitiveness", status: "pass", description: "Salary range competitive" },
    { check: "Readability Score", status: "pass", description: "Grade 12 reading level" },
  ]

  return (
    <DashboardShell>
      <div className="space-y-6">
        <div className="flex justify-between items-start">
          <div>
            <Heading level="h1" className="mb-2">
              AI Job Description Writer
            </Heading>
            <Text size="lg" color="muted">
              Generate compelling, inclusive job descriptions using SSG Skills taxonomy and AI insights
            </Text>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm">
              <FileText className="h-4 w-4 mr-2" />
              Templates
            </Button>
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          {/* Input Panel */}
          <div className="lg:col-span-1 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="h-5 w-5" />
                  Job Requirements
                </CardTitle>
                <CardDescription>Define the role parameters for AI generation</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="jobTitle">Job Title *</Label>
                  <Input
                    id="jobTitle"
                    placeholder="e.g., Senior Manager, Digital Transformation"
                    value={jobTitle}
                    onChange={(e) => setJobTitle(e.target.value)}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="department">Department *</Label>
                  <select
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                  >
                    <option value="">Select Department</option>
                    <option value="Technology & Innovation">Technology & Innovation</option>
                    <option value="People & Organisation">People & Organisation</option>
                    <option value="Finance">Finance</option>
                    <option value="Operations">Operations</option>
                    <option value="Business Development">Business Development</option>
                    <option value="Marketing">Marketing</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="level">Seniority Level *</Label>
                  <select
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                    value={level}
                    onChange={(e) => setLevel(e.target.value)}
                  >
                    <option value="">Select Level</option>
                    <option value="Executive">Executive</option>
                    <option value="Senior Manager">Senior Manager</option>
                    <option value="Manager">Manager</option>
                    <option value="Assistant Manager">Assistant Manager</option>
                    <option value="Senior Executive">Senior Executive</option>
                    <option value="Executive">Executive</option>
                  </select>
                </div>

                <Button onClick={handleGenerateJD} disabled={isGenerating || !jobTitle} className="w-full">
                  {isGenerating ? (
                    <>
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-4 w-4 mr-2" />
                      Generate Job Description
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BookOpen className="h-5 w-5" />
                  Skills Selection
                </CardTitle>
                <CardDescription>Choose from SSG Skills taxonomy and AI suggestions</CardDescription>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="ssg-skills">
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="ssg-skills">SSG Skills</TabsTrigger>
                    <TabsTrigger value="ai-skills">AI Suggested</TabsTrigger>
                  </TabsList>
                  <TabsContent value="ssg-skills" className="space-y-3">
                    <div className="flex flex-wrap gap-2">
                      {ssgSkills.map((skill) => (
                        <Badge
                          key={skill}
                          variant={selectedSkills.includes(skill) ? "default" : "outline"}
                          className="cursor-pointer"
                          onClick={() => toggleSkill(skill)}
                        >
                          {skill}
                        </Badge>
                      ))}
                    </div>
                  </TabsContent>
                  <TabsContent value="ai-skills" className="space-y-3">
                    <div className="flex flex-wrap gap-2">
                      {aiSuggestedSkills.map((skill) => (
                        <Badge
                          key={skill}
                          variant={selectedSkills.includes(skill) ? "default" : "outline"}
                          className="cursor-pointer"
                          onClick={() => toggleSkill(skill)}
                        >
                          {skill}
                        </Badge>
                      ))}
                    </div>
                  </TabsContent>
                </Tabs>
                <div className="mt-4">
                  <Text size="sm" color="muted">
                    Selected: {selectedSkills.length} skills
                  </Text>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Output Panel */}
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <FileText className="h-5 w-5" />
                      Generated Job Description
                    </CardTitle>
                    <CardDescription>AI-powered, inclusive, and market-competitive</CardDescription>
                  </div>
                  {generatedJD && (
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm">
                        <Copy className="h-4 w-4 mr-2" />
                        Copy
                      </Button>
                      <Button variant="outline" size="sm">
                        <Download className="h-4 w-4 mr-2" />
                        Download
                      </Button>
                    </div>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                {generatedJD ? (
                  <div className="space-y-4">
                    <div className="p-4 bg-gray-50 rounded-lg max-h-96 overflow-y-auto">
                      <pre className="whitespace-pre-wrap text-sm">{generatedJD}</pre>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-64 text-gray-500">
                    <div className="text-center">
                      <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <Text>Generated job description will appear here</Text>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {generatedJD && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <CheckCircle className="h-5 w-5" />
                    Quality & Compliance Checks
                  </CardTitle>
                  <CardDescription>AI-powered analysis for best practices</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {qualityChecks.map((check, index) => (
                      <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                        <div className="flex items-center gap-3">
                          {check.status === "pass" ? (
                            <CheckCircle className="h-4 w-4 text-green-500" />
                          ) : (
                            <AlertCircle className="h-4 w-4 text-yellow-500" />
                          )}
                          <div>
                            <Text size="sm" weight="medium">
                              {check.check}
                            </Text>
                            <Text size="xs" color="muted">
                              {check.description}
                            </Text>
                          </div>
                        </div>
                        <Badge variant={check.status === "pass" ? "default" : "secondary"}>
                          {check.status === "pass" ? "Pass" : "Review"}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </DashboardShell>
  )
}
