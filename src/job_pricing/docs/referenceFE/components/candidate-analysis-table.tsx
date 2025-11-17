"use client"

import { useState } from "react"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Progress } from "@/components/ui/progress"
import { Download, Eye, FileText, Filter, SortAsc, SortDesc } from "lucide-react"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

// Sample candidate analysis data
const candidateData = [
  {
    id: 1,
    name: "John Smith",
    position: "Executive Leadership",
    xFactorMatch: 87,
    leadershipScore: 92,
    strategicThinkingScore: 85,
    executionScore: 82,
    innovationScore: 79,
    communicationScore: 90,
    culturalFitScore: 88,
    overallRank: 2,
    status: "Recommended",
  },
  {
    id: 2,
    name: "Emily Johnson",
    position: "Executive Leadership",
    xFactorMatch: 92,
    leadershipScore: 94,
    strategicThinkingScore: 91,
    executionScore: 88,
    innovationScore: 90,
    communicationScore: 93,
    culturalFitScore: 95,
    overallRank: 1,
    status: "Highly Recommended",
  },
  {
    id: 3,
    name: "Michael Chen",
    position: "Executive Leadership",
    xFactorMatch: 76,
    leadershipScore: 80,
    strategicThinkingScore: 85,
    executionScore: 78,
    innovationScore: 82,
    communicationScore: 75,
    culturalFitScore: 72,
    overallRank: 4,
    status: "Consider",
  },
  {
    id: 4,
    name: "Sarah Williams",
    position: "Executive Leadership",
    xFactorMatch: 81,
    leadershipScore: 85,
    strategicThinkingScore: 79,
    executionScore: 84,
    innovationScore: 76,
    communicationScore: 82,
    culturalFitScore: 80,
    overallRank: 3,
    status: "Recommended",
  },
  {
    id: 5,
    name: "David Rodriguez",
    position: "Executive Leadership",
    xFactorMatch: 68,
    leadershipScore: 72,
    strategicThinkingScore: 70,
    executionScore: 75,
    innovationScore: 65,
    communicationScore: 68,
    culturalFitScore: 62,
    overallRank: 5,
    status: "Consider with Reservations",
  },
]

export function CandidateAnalysisTable() {
  const [sortField, setSortField] = useState<string>("overallRank")
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc")
  const [filterStatus, setFilterStatus] = useState<string>("all")

  // Sort and filter candidates
  const sortedCandidates = [...candidateData]
    .sort((a, b) => {
      const fieldA = a[sortField as keyof typeof a]
      const fieldB = b[sortField as keyof typeof b]

      if (typeof fieldA === "number" && typeof fieldB === "number") {
        return sortDirection === "asc" ? fieldA - fieldB : fieldB - fieldA
      }

      if (typeof fieldA === "string" && typeof fieldB === "string") {
        return sortDirection === "asc" ? fieldA.localeCompare(fieldB) : fieldB.localeCompare(fieldA)
      }

      return 0
    })
    .filter(
      (candidate) => filterStatus === "all" || candidate.status.toLowerCase().includes(filterStatus.toLowerCase()),
    )

  const toggleSort = (field: string) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc")
    } else {
      setSortField(field)
      setSortDirection("asc")
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "Highly Recommended":
        return "bg-green-50 text-green-700 border-green-200"
      case "Recommended":
        return "bg-blue-50 text-blue-700 border-blue-200"
      case "Consider":
        return "bg-amber-50 text-amber-700 border-amber-200"
      case "Consider with Reservations":
        return "bg-red-50 text-red-700 border-red-200"
      default:
        return "bg-gray-50 text-gray-700 border-gray-200"
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Candidate X-Factor Analysis</CardTitle>
        <CardDescription>AI-powered analysis of candidate CVs against MT X-Factors</CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="table" className="w-full">
          <div className="flex items-center justify-between mb-4">
            <TabsList>
              <TabsTrigger value="table">Table View</TabsTrigger>
              <TabsTrigger value="summary">Summary</TabsTrigger>
            </TabsList>

            <div className="flex items-center gap-2">
              <Select value={filterStatus} onValueChange={setFilterStatus}>
                <SelectTrigger className="w-[180px]">
                  <Filter className="mr-2 h-4 w-4" />
                  <SelectValue placeholder="Filter by status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="highly">Highly Recommended</SelectItem>
                  <SelectItem value="recommended">Recommended</SelectItem>
                  <SelectItem value="consider">Consider</SelectItem>
                  <SelectItem value="reservations">With Reservations</SelectItem>
                </SelectContent>
              </Select>

              <Button variant="outline" size="sm">
                <Download className="mr-2 h-4 w-4" />
                Export
              </Button>
            </div>
          </div>

          <TabsContent value="table">
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[200px]">Candidate Name</TableHead>
                    <TableHead>
                      <div
                        className="flex items-center gap-1 cursor-pointer"
                        onClick={() => toggleSort("xFactorMatch")}
                      >
                        X-Factor Match
                        {sortField === "xFactorMatch" &&
                          (sortDirection === "asc" ? (
                            <SortAsc className="h-4 w-4" />
                          ) : (
                            <SortDesc className="h-4 w-4" />
                          ))}
                      </div>
                    </TableHead>
                    <TableHead>Leadership</TableHead>
                    <TableHead>Strategic</TableHead>
                    <TableHead>Execution</TableHead>
                    <TableHead>Innovation</TableHead>
                    <TableHead>
                      <div className="flex items-center gap-1 cursor-pointer" onClick={() => toggleSort("overallRank")}>
                        Rank
                        {sortField === "overallRank" &&
                          (sortDirection === "asc" ? (
                            <SortAsc className="h-4 w-4" />
                          ) : (
                            <SortDesc className="h-4 w-4" />
                          ))}
                      </div>
                    </TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sortedCandidates.map((candidate) => (
                    <TableRow key={candidate.id}>
                      <TableCell className="font-medium">{candidate.name}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Progress value={candidate.xFactorMatch} className="h-2 w-16" />
                          <span>{candidate.xFactorMatch}%</span>
                        </div>
                      </TableCell>
                      <TableCell>{candidate.leadershipScore}%</TableCell>
                      <TableCell>{candidate.strategicThinkingScore}%</TableCell>
                      <TableCell>{candidate.executionScore}%</TableCell>
                      <TableCell>{candidate.innovationScore}%</TableCell>
                      <TableCell className="text-center font-medium">{candidate.overallRank}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className={getStatusColor(candidate.status)}>
                          {candidate.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                            <Eye className="h-4 w-4" />
                            <span className="sr-only">View</span>
                          </Button>
                          <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                            <FileText className="h-4 w-4" />
                            <span className="sr-only">Report</span>
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </TabsContent>

          <TabsContent value="summary">
            <div className="space-y-6">
              <div className="grid gap-4 md:grid-cols-3">
                <div className="rounded-lg border bg-card p-4">
                  <div className="text-sm font-medium text-muted-foreground mb-2">Top Candidate</div>
                  <div className="text-2xl font-bold">Emily Johnson</div>
                  <div className="text-sm text-muted-foreground">92% X-Factor Match</div>
                </div>
                <div className="rounded-lg border bg-card p-4">
                  <div className="text-sm font-medium text-muted-foreground mb-2">Average X-Factor Match</div>
                  <div className="text-2xl font-bold">80.8%</div>
                </div>
                <div className="rounded-lg border bg-card p-4">
                  <div className="text-sm font-medium text-muted-foreground mb-2">Candidates Analyzed</div>
                  <div className="text-2xl font-bold">5</div>
                  <div className="text-sm text-muted-foreground">2 Highly Recommended</div>
                </div>
              </div>

              <div className="rounded-lg border bg-card p-4">
                <div className="text-sm font-medium mb-4">X-Factor Match Distribution</div>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span>90-100%</span>
                      <span>1 candidate</span>
                    </div>
                    <Progress value={20} className="h-2" />
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span>80-89%</span>
                      <span>2 candidates</span>
                    </div>
                    <Progress value={40} className="h-2" />
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span>70-79%</span>
                      <span>1 candidate</span>
                    </div>
                    <Progress value={20} className="h-2" />
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span>60-69%</span>
                      <span>1 candidate</span>
                    </div>
                    <Progress value={20} className="h-2" />
                  </div>
                </div>
              </div>

              <div className="flex justify-end">
                <Button>
                  <FileText className="mr-2 h-4 w-4" />
                  Generate Detailed Report
                </Button>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}
