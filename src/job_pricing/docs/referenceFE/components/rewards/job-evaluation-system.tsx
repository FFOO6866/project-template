"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { FileText, Search, Plus, Edit, CheckCircle, AlertCircle, Clock, ArrowUpDown } from "lucide-react"

// Mock data for role profiles
const mockRoleProfiles = [
  {
    id: "rp1",
    title: "Software Engineer",
    department: "Engineering",
    description: "Responsible for developing and maintaining software applications",
    responsibilities: [
      "Develop and maintain software applications",
      "Write clean, efficient, and well-documented code",
      "Collaborate with cross-functional teams",
      "Participate in code reviews",
    ],
    requirements: [
      "Bachelor's degree in Computer Science or related field",
      "3+ years of experience in software development",
      "Proficiency in JavaScript, TypeScript, and React",
      "Experience with Node.js and RESTful APIs",
    ],
    reportingTo: "Engineering Manager",
    directReports: 0,
  },
  {
    id: "rp2",
    title: "Product Manager",
    department: "Product",
    description: "Responsible for defining product vision, strategy, and roadmap",
    responsibilities: [
      "Define product vision, strategy, and roadmap",
      "Gather and prioritize product requirements",
      "Work closely with engineering, design, and marketing teams",
      "Analyze market trends and competition",
    ],
    requirements: [
      "Bachelor's degree in Business, Computer Science, or related field",
      "5+ years of experience in product management",
      "Strong analytical and problem-solving skills",
      "Excellent communication and leadership skills",
    ],
    reportingTo: "Head of Product",
    directReports: 0,
  },
  {
    id: "rp3",
    title: "Marketing Manager",
    department: "Marketing",
    description: "Responsible for developing and implementing marketing strategies",
    responsibilities: [
      "Develop and implement marketing strategies",
      "Manage marketing campaigns and initiatives",
      "Analyze marketing metrics and KPIs",
      "Collaborate with sales and product teams",
    ],
    requirements: [
      "Bachelor's degree in Marketing, Business, or related field",
      "5+ years of experience in marketing",
      "Strong understanding of digital marketing channels",
      "Excellent communication and project management skills",
    ],
    reportingTo: "Head of Marketing",
    directReports: 2,
  },
]

// Mock data for job evaluations
const mockJobEvaluations = [
  {
    id: "je1",
    roleProfileId: "rp1",
    impact: {
      degree: 6,
      points: 92,
    },
    communication: {
      degree: 3,
      points: 40,
    },
    innovation: {
      degree: 4,
      points: 75,
    },
    knowledge: {
      degree: 4,
      points: 90,
    },
    risk: {
      degree: 0,
      points: 0,
    },
    totalPoints: 297,
    positionClass: 50,
    jobGrade: "P3",
    evaluatedBy: "Sam Johnson",
    evaluatedDate: "2023-10-15",
    status: "approved",
  },
  {
    id: "je2",
    roleProfileId: "rp2",
    impact: {
      degree: 9,
      points: 175,
    },
    communication: {
      degree: 4,
      points: 75,
    },
    innovation: {
      degree: 5,
      points: 100,
    },
    knowledge: {
      degree: 5,
      points: 113,
    },
    risk: {
      degree: 0,
      points: 0,
    },
    totalPoints: 463,
    positionClass: 57,
    jobGrade: "P5",
    evaluatedBy: "Morgan Chen",
    evaluatedDate: "2023-09-20",
    status: "approved",
  },
  {
    id: "je3",
    roleProfileId: "rp3",
    impact: {
      degree: 8,
      points: 152,
    },
    communication: {
      degree: 4,
      points: 75,
    },
    innovation: {
      degree: 4,
      points: 75,
    },
    knowledge: {
      degree: 4,
      points: 90,
    },
    risk: {
      degree: 0,
      points: 0,
    },
    totalPoints: 392,
    positionClass: 54,
    jobGrade: "P4",
    evaluatedBy: "Jamie Rodriguez",
    evaluatedDate: "2023-11-05",
    status: "pending",
  },
]

export function JobEvaluationSystem() {
  const [selectedRoleProfile, setSelectedRoleProfile] = useState(null)
  const [selectedEvaluation, setSelectedEvaluation] = useState(null)
  const [evaluationMode, setEvaluationMode] = useState("view")

  const handleSelectRoleProfile = (roleProfile) => {
    setSelectedRoleProfile(roleProfile)
    const evaluation = mockJobEvaluations.find((je) => je.roleProfileId === roleProfile.id)
    setSelectedEvaluation(evaluation || null)
    setEvaluationMode(evaluation ? "view" : "new")
  }

  const getStatusBadge = (status) => {
    switch (status) {
      case "draft":
        return (
          <Badge variant="outline" className="flex items-center gap-1">
            <Clock className="h-3 w-3" /> Draft
          </Badge>
        )
      case "pending":
        return (
          <Badge variant="outline" className="flex items-center gap-1 text-amber-500 border-amber-500">
            <AlertCircle className="h-3 w-3" /> Pending
          </Badge>
        )
      case "approved":
        return (
          <Badge variant="outline" className="flex items-center gap-1 text-green-500 border-green-500">
            <CheckCircle className="h-3 w-3" /> Approved
          </Badge>
        )
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Job Evaluation System</h2>
          <p className="text-muted-foreground">Evaluate job positions using the Mercer Job Evaluation methodology</p>
        </div>
        <Button>
          <Plus className="mr-2 h-4 w-4" /> New Role Profile
        </Button>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card className="md:col-span-1">
          <CardHeader>
            <CardTitle>Role Profiles</CardTitle>
            <CardDescription>Select a role profile to evaluate</CardDescription>
            <div className="relative mt-2">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input placeholder="Search role profiles..." className="pl-8" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {mockRoleProfiles.map((profile) => (
                <div
                  key={profile.id}
                  className={`flex items-start p-3 rounded-md cursor-pointer hover:bg-muted transition-colors ${
                    selectedRoleProfile?.id === profile.id ? "bg-muted" : ""
                  }`}
                  onClick={() => handleSelectRoleProfile(profile)}
                >
                  <FileText className="h-5 w-5 mr-3 mt-0.5 text-muted-foreground" />
                  <div>
                    <h3 className="font-medium">{profile.title}</h3>
                    <p className="text-sm text-muted-foreground">{profile.department}</p>
                    <p className="text-xs text-muted-foreground mt-1">Reports to: {profile.reportingTo}</p>
                  </div>
                  {mockJobEvaluations.find((je) => je.roleProfileId === profile.id) && (
                    <div className="ml-auto">
                      {getStatusBadge(mockJobEvaluations.find((je) => je.roleProfileId === profile.id).status)}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="md:col-span-1">
          {selectedRoleProfile ? (
            <>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle>{selectedRoleProfile.title}</CardTitle>
                    <CardDescription>{selectedRoleProfile.department}</CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm">
                      <Edit className="h-4 w-4 mr-1" /> Edit Profile
                    </Button>
                    {selectedEvaluation && evaluationMode === "view" && (
                      <Button variant="default" size="sm" onClick={() => setEvaluationMode("edit")}>
                        <Edit className="h-4 w-4 mr-1" /> Edit Evaluation
                      </Button>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="profile" className="w-full">
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="profile">Role Profile</TabsTrigger>
                    <TabsTrigger value="evaluation" disabled={!selectedEvaluation && evaluationMode !== "new"}>
                      Job Evaluation
                    </TabsTrigger>
                  </TabsList>
                  <TabsContent value="profile" className="pt-4 space-y-4">
                    <div>
                      <h3 className="font-medium mb-2">Description</h3>
                      <p className="text-sm text-muted-foreground">{selectedRoleProfile.description}</p>
                    </div>
                    <div>
                      <h3 className="font-medium mb-2">Key Responsibilities</h3>
                      <ul className="list-disc pl-5 text-sm text-muted-foreground space-y-1">
                        {selectedRoleProfile.responsibilities.map((resp, index) => (
                          <li key={index}>{resp}</li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <h3 className="font-medium mb-2">Requirements</h3>
                      <ul className="list-disc pl-5 text-sm text-muted-foreground space-y-1">
                        {selectedRoleProfile.requirements.map((req, index) => (
                          <li key={index}>{req}</li>
                        ))}
                      </ul>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <h3 className="font-medium mb-2">Reporting To</h3>
                        <p className="text-sm text-muted-foreground">{selectedRoleProfile.reportingTo}</p>
                      </div>
                      <div>
                        <h3 className="font-medium mb-2">Direct Reports</h3>
                        <p className="text-sm text-muted-foreground">{selectedRoleProfile.directReports}</p>
                      </div>
                    </div>
                    {!selectedEvaluation && (
                      <div className="pt-4">
                        <Button onClick={() => setEvaluationMode("new")}>Start Evaluation</Button>
                      </div>
                    )}
                  </TabsContent>
                  <TabsContent value="evaluation" className="pt-4 space-y-6">
                    {(selectedEvaluation || evaluationMode === "new") && (
                      <>
                        <div className="space-y-4">
                          <div>
                            <h3 className="font-medium mb-3">Impact</h3>
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <Label htmlFor="impact-nature">Nature</Label>
                                <Select
                                  defaultValue={selectedEvaluation?.impact.degree.toString() || "3"}
                                  disabled={evaluationMode === "view"}
                                >
                                  <SelectTrigger id="impact-nature">
                                    <SelectValue placeholder="Select nature" />
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="1">Delivery</SelectItem>
                                    <SelectItem value="2">Operational</SelectItem>
                                    <SelectItem value="3">Tactical</SelectItem>
                                    <SelectItem value="4">Strategic</SelectItem>
                                    <SelectItem value="5">Visionary</SelectItem>
                                  </SelectContent>
                                </Select>
                              </div>
                              <div>
                                <Label htmlFor="impact-contribution">Contribution</Label>
                                <Select
                                  defaultValue={selectedEvaluation ? "3" : "3"}
                                  disabled={evaluationMode === "view"}
                                >
                                  <SelectTrigger id="impact-contribution">
                                    <SelectValue placeholder="Select contribution" />
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="1">Limited</SelectItem>
                                    <SelectItem value="2">Some</SelectItem>
                                    <SelectItem value="3">Direct</SelectItem>
                                    <SelectItem value="4">Significant</SelectItem>
                                    <SelectItem value="5">Major</SelectItem>
                                  </SelectContent>
                                </Select>
                              </div>
                            </div>
                          </div>

                          <div>
                            <h3 className="font-medium mb-3">Communication</h3>
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <Label htmlFor="communication-type">Type</Label>
                                <Select
                                  defaultValue={selectedEvaluation?.communication.degree.toString() || "3"}
                                  disabled={evaluationMode === "view"}
                                >
                                  <SelectTrigger id="communication-type">
                                    <SelectValue placeholder="Select type" />
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="1">Convey</SelectItem>
                                    <SelectItem value="2">Adapt and Exchange</SelectItem>
                                    <SelectItem value="3">Influence</SelectItem>
                                    <SelectItem value="4">Negotiate</SelectItem>
                                    <SelectItem value="5">Negotiate Long Term</SelectItem>
                                  </SelectContent>
                                </Select>
                              </div>
                              <div>
                                <Label htmlFor="communication-frame">Frame</Label>
                                <Select
                                  defaultValue={selectedEvaluation ? "1" : "1"}
                                  disabled={evaluationMode === "view"}
                                >
                                  <SelectTrigger id="communication-frame">
                                    <SelectValue placeholder="Select frame" />
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="1">Internal Shared Interests</SelectItem>
                                    <SelectItem value="2">External Shared Interests</SelectItem>
                                    <SelectItem value="3">Internal Divergent Interests</SelectItem>
                                    <SelectItem value="4">External Divergent Interests</SelectItem>
                                  </SelectContent>
                                </Select>
                              </div>
                            </div>
                          </div>

                          <div>
                            <h3 className="font-medium mb-3">Innovation</h3>
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <Label htmlFor="innovation-level">Level</Label>
                                <Select
                                  defaultValue={selectedEvaluation?.innovation.degree.toString() || "4"}
                                  disabled={evaluationMode === "view"}
                                >
                                  <SelectTrigger id="innovation-level">
                                    <SelectValue placeholder="Select level" />
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="1">Follow</SelectItem>
                                    <SelectItem value="2">Check</SelectItem>
                                    <SelectItem value="3">Modify</SelectItem>
                                    <SelectItem value="4">Improve</SelectItem>
                                    <SelectItem value="5">Create/Conceptualize</SelectItem>
                                    <SelectItem value="6">Scientific/Technical Breakthrough</SelectItem>
                                  </SelectContent>
                                </Select>
                              </div>
                              <div>
                                <Label htmlFor="innovation-complexity">Complexity</Label>
                                <Select
                                  defaultValue={selectedEvaluation ? "3" : "3"}
                                  disabled={evaluationMode === "view"}
                                >
                                  <SelectTrigger id="innovation-complexity">
                                    <SelectValue placeholder="Select complexity" />
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="1">Defined</SelectItem>
                                    <SelectItem value="2">Difficult</SelectItem>
                                    <SelectItem value="3">Complex</SelectItem>
                                    <SelectItem value="4">Multi-dimensional</SelectItem>
                                  </SelectContent>
                                </Select>
                              </div>
                            </div>
                          </div>

                          <div>
                            <h3 className="font-medium mb-3">Knowledge</h3>
                            <div className="grid grid-cols-3 gap-4">
                              <div>
                                <Label htmlFor="knowledge-level">Level</Label>
                                <Select
                                  defaultValue={selectedEvaluation?.knowledge.degree.toString() || "4"}
                                  disabled={evaluationMode === "view"}
                                >
                                  <SelectTrigger id="knowledge-level">
                                    <SelectValue placeholder="Select level" />
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="1">Limited Job Knowledge</SelectItem>
                                    <SelectItem value="2">Basic Job Knowledge</SelectItem>
                                    <SelectItem value="3">Broad Job Knowledge</SelectItem>
                                    <SelectItem value="4">Expertise</SelectItem>
                                    <SelectItem value="5">Professional Standard</SelectItem>
                                    <SelectItem value="6">Organizational Generalist</SelectItem>
                                    <SelectItem value="7">Broad Practical Experience</SelectItem>
                                    <SelectItem value="8">Broad and Deep Practical Experience</SelectItem>
                                  </SelectContent>
                                </Select>
                              </div>
                              <div>
                                <Label htmlFor="knowledge-teams">Teams</Label>
                                <Select
                                  defaultValue={selectedEvaluation ? "1" : "1"}
                                  disabled={evaluationMode === "view"}
                                >
                                  <SelectTrigger id="knowledge-teams">
                                    <SelectValue placeholder="Select teams" />
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="1">Team Member</SelectItem>
                                    <SelectItem value="2">Team Leader</SelectItem>
                                    <SelectItem value="3">Teams Manager</SelectItem>
                                  </SelectContent>
                                </Select>
                              </div>
                              <div>
                                <Label htmlFor="knowledge-breadth">Breadth</Label>
                                <Select
                                  defaultValue={selectedEvaluation ? "1" : "1"}
                                  disabled={evaluationMode === "view"}
                                >
                                  <SelectTrigger id="knowledge-breadth">
                                    <SelectValue placeholder="Select breadth" />
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="1">Domestic</SelectItem>
                                    <SelectItem value="2">Regional</SelectItem>
                                    <SelectItem value="3">Global</SelectItem>
                                  </SelectContent>
                                </Select>
                              </div>
                            </div>
                          </div>

                          <div>
                            <h3 className="font-medium mb-3">Risk (Optional)</h3>
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <Label htmlFor="risk-level">Level</Label>
                                <Select
                                  defaultValue={selectedEvaluation?.risk.degree.toString() || "0"}
                                  disabled={evaluationMode === "view"}
                                >
                                  <SelectTrigger id="risk-level">
                                    <SelectValue placeholder="Select level" />
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="0">Normal</SelectItem>
                                    <SelectItem value="1">Mental</SelectItem>
                                    <SelectItem value="2">Injury</SelectItem>
                                    <SelectItem value="3">Disability</SelectItem>
                                  </SelectContent>
                                </Select>
                              </div>
                              <div>
                                <Label htmlFor="risk-environment">Environment</Label>
                                <Select
                                  defaultValue={selectedEvaluation ? "1" : "1"}
                                  disabled={evaluationMode === "view"}
                                >
                                  <SelectTrigger id="risk-environment">
                                    <SelectValue placeholder="Select environment" />
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="1">Low Exposure</SelectItem>
                                    <SelectItem value="2">Medium Exposure</SelectItem>
                                    <SelectItem value="3">High Exposure</SelectItem>
                                  </SelectContent>
                                </Select>
                              </div>
                            </div>
                          </div>
                        </div>

                        <div className="pt-4 border-t">
                          <h3 className="font-medium mb-3">Evaluation Results</h3>
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <Label>Total Points</Label>
                              <div className="text-2xl font-bold">{selectedEvaluation?.totalPoints || "297"}</div>
                            </div>
                            <div>
                              <Label>Position Class</Label>
                              <div className="text-2xl font-bold">{selectedEvaluation?.positionClass || "50"}</div>
                            </div>
                          </div>
                          <div className="mt-4">
                            <Label>Job Grade</Label>
                            <div className="text-2xl font-bold">{selectedEvaluation?.jobGrade || "P3"}</div>
                          </div>
                        </div>
                      </>
                    )}
                  </TabsContent>
                </Tabs>
              </CardContent>
              <CardFooter className="flex justify-end gap-2">
                {evaluationMode !== "view" && (
                  <>
                    <Button variant="outline" onClick={() => setEvaluationMode("view")}>
                      Cancel
                    </Button>
                    <Button>{evaluationMode === "new" ? "Save Evaluation" : "Update Evaluation"}</Button>
                  </>
                )}
              </CardFooter>
            </>
          ) : (
            <CardContent className="flex flex-col items-center justify-center h-[400px] text-center">
              <FileText className="h-16 w-16 text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium">No Role Profile Selected</h3>
              <p className="text-sm text-muted-foreground mt-1 mb-4">
                Select a role profile from the list to view details and evaluation
              </p>
            </CardContent>
          )}
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Job Evaluations</CardTitle>
          <CardDescription>View all job evaluations and their status</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Job Title</TableHead>
                <TableHead>Department</TableHead>
                <TableHead>
                  <div className="flex items-center">
                    Total Points
                    <ArrowUpDown className="ml-1 h-4 w-4" />
                  </div>
                </TableHead>
                <TableHead>
                  <div className="flex items-center">
                    Position Class
                    <ArrowUpDown className="ml-1 h-4 w-4" />
                  </div>
                </TableHead>
                <TableHead>
                  <div className="flex items-center">
                    Job Grade
                    <ArrowUpDown className="ml-1 h-4 w-4" />
                  </div>
                </TableHead>
                <TableHead>Evaluated By</TableHead>
                <TableHead>Evaluated Date</TableHead>
                <TableHead>Status</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {mockJobEvaluations.map((evaluation) => {
                const roleProfile = mockRoleProfiles.find((rp) => rp.id === evaluation.roleProfileId)
                return (
                  <TableRow key={evaluation.id}>
                    <TableCell className="font-medium">{roleProfile?.title}</TableCell>
                    <TableCell>{roleProfile?.department}</TableCell>
                    <TableCell>{evaluation.totalPoints}</TableCell>
                    <TableCell>{evaluation.positionClass}</TableCell>
                    <TableCell>{evaluation.jobGrade}</TableCell>
                    <TableCell>{evaluation.evaluatedBy}</TableCell>
                    <TableCell>{evaluation.evaluatedDate}</TableCell>
                    <TableCell>{getStatusBadge(evaluation.status)}</TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setSelectedRoleProfile(roleProfile || null)
                          setSelectedEvaluation(evaluation)
                          setEvaluationMode("view")
                        }}
                      >
                        View
                      </Button>
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}
