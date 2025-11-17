import { DashboardShell } from "@/components/dashboard-shell"
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Heading } from "@/components/ui/heading"
import { Text } from "@/components/ui/text"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Textarea } from "@/components/ui/textarea"
import { Switch } from "@/components/ui/switch"
import { FileText, BarChart2, Settings, Plus, Edit, Trash2, Save, Calendar } from "lucide-react"
import Link from "next/link"
import { CandidateAnalysisTable } from "@/components/candidate-analysis-table"
import { AssessmentResultsUploader } from "@/components/assessment-results-uploader"
import { CVBatchUploader } from "@/components/cv-batch-uploader"

// Sample assessment data
const assessments = [
  {
    id: 1,
    name: "Annual Leadership Assessment 2023",
    type: "Leadership",
    date: "2023-12-10",
    status: "Completed",
    teamMembers: 8,
  },
  {
    id: 2,
    name: "Mintzberg Management Roles Evaluation",
    type: "Management",
    date: "2023-11-15",
    status: "Completed",
    teamMembers: 8,
  },
  {
    id: 3,
    name: "X-Factor Assessment Q4 2023",
    type: "Performance",
    date: "2023-12-05",
    status: "In Progress",
    teamMembers: 5,
  },
  {
    id: 4,
    name: "Quantum Leadership Workshop Evaluation",
    type: "Leadership",
    date: "2023-10-20",
    status: "Completed",
    teamMembers: 8,
  },
  {
    id: 5,
    name: "Strategic Thinking Assessment",
    type: "Performance",
    date: "2024-01-15",
    status: "Scheduled",
    teamMembers: 8,
  },
]

export default function AdminPage() {
  return (
    <DashboardShell>
      <div className="flex flex-col space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <Heading level="h1">Assessment Administration</Heading>
            <Text color="muted">Manage assessment data and update MT profile information</Text>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" className="h-9">
              <Calendar className="mr-2 h-4 w-4" />
              Schedule Assessment
            </Button>
            <Button size="sm" className="h-9">
              <Plus className="mr-2 h-4 w-4" />
              New Assessment
            </Button>
          </div>
        </div>

        {/* Submodule Navigation */}
        <div className="flex flex-wrap items-center gap-4">
          <Link href="/dashboard/talent/profiles">
            <Button variant="outline" className="h-9">
              <BarChart2 className="mr-2 h-4 w-4" />
              Team Overview
            </Button>
          </Link>
          <Link href="/dashboard/talent/profiles/documents">
            <Button variant="outline" className="h-9">
              <FileText className="mr-2 h-4 w-4" />
              Document Management
            </Button>
          </Link>
          <Link href="/dashboard/talent/profiles/performance">
            <Button variant="outline" className="h-9">
              <BarChart2 className="mr-2 h-4 w-4" />
              Performance Matrix
            </Button>
          </Link>
          <Link href="/dashboard/talent/profiles/admin">
            <Button variant="secondary" className="h-9">
              <Settings className="mr-2 h-4 w-4" />
              Admin
            </Button>
          </Link>
        </div>

        <Tabs defaultValue="results" className="space-y-6">
          <TabsList>
            <TabsTrigger value="results">Assessment Results</TabsTrigger>
            <TabsTrigger value="cv-analysis">CV Analysis</TabsTrigger>
            <TabsTrigger value="settings">Settings</TabsTrigger>
          </TabsList>

          <TabsContent value="results" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Assessment Center Data</CardTitle>
                <CardDescription>Manage and update assessment data for MT profiles</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Assessment Name</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Team Members</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {assessments.map((assessment) => (
                      <TableRow key={assessment.id}>
                        <TableCell className="font-medium">{assessment.name}</TableCell>
                        <TableCell>{assessment.type}</TableCell>
                        <TableCell>{assessment.date}</TableCell>
                        <TableCell>
                          <div
                            className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                              assessment.status === "Completed"
                                ? "bg-green-100 text-green-800"
                                : assessment.status === "In Progress"
                                  ? "bg-blue-100 text-blue-800"
                                  : "bg-amber-100 text-amber-800"
                            }`}
                          >
                            {assessment.status}
                          </div>
                        </TableCell>
                        <TableCell>{assessment.teamMembers}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                              <Edit className="h-4 w-4" />
                              <span className="sr-only">Edit</span>
                            </Button>
                            <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                              <Save className="h-4 w-4" />
                              <span className="sr-only">Download</span>
                            </Button>
                            <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                              <Trash2 className="h-4 w-4" />
                              <span className="sr-only">Delete</span>
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Upload Assessment Results</CardTitle>
                <CardDescription>Upload and process assessment center results</CardDescription>
              </CardHeader>
              <CardContent>
                <AssessmentResultsUploader />
              </CardContent>
            </Card>
          </TabsContent>

          {/* New Tab: CV Analysis */}
          <TabsContent value="cv-analysis" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>CV Analysis & X-Factor Matching</CardTitle>
                <CardDescription>Upload candidate CVs for analysis against MT X-Factors</CardDescription>
              </CardHeader>
              <CardContent>
                <CVBatchUploader />
              </CardContent>
            </Card>

            <CandidateAnalysisTable />
          </TabsContent>

          <TabsContent value="settings" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Assessment Settings</CardTitle>
                <CardDescription>Configure assessment parameters and display options</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="default-assessment">Default Assessment Type</Label>
                      <Select defaultValue="leadership">
                        <SelectTrigger id="default-assessment">
                          <SelectValue placeholder="Select default assessment" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="leadership">Leadership Assessment</SelectItem>
                          <SelectItem value="mintzberg">Mintzberg Roles</SelectItem>
                          <SelectItem value="xfactor">X-Factor Scoring</SelectItem>
                          <SelectItem value="performance">Performance Matrix</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="assessment-period">Default Assessment Period</Label>
                      <Select defaultValue="annual">
                        <SelectTrigger id="assessment-period">
                          <SelectValue placeholder="Select assessment period" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="quarterly">Quarterly</SelectItem>
                          <SelectItem value="biannual">Bi-Annual</SelectItem>
                          <SelectItem value="annual">Annual</SelectItem>
                          <SelectItem value="custom">Custom</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="scoring-scale">Scoring Scale</Label>
                    <Select defaultValue="percentage">
                      <SelectTrigger id="scoring-scale">
                        <SelectValue placeholder="Select scoring scale" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="percentage">Percentage (0-100%)</SelectItem>
                        <SelectItem value="scale5">5-Point Scale</SelectItem>
                        <SelectItem value="scale10">10-Point Scale</SelectItem>
                        <SelectItem value="custom">Custom Scale</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="custom-attributes">Custom Leadership Attributes</Label>
                    <Textarea
                      id="custom-attributes"
                      placeholder="Enter custom attributes, one per line"
                      className="min-h-[100px]"
                    />
                    <p className="text-xs text-muted-foreground">
                      These attributes will be available in addition to the standard TPC leadership attributes.
                    </p>
                  </div>

                  <div className="space-y-4">
                    <div className="flex items-center space-x-2">
                      <Switch id="auto-update" defaultChecked />
                      <Label htmlFor="auto-update">Automatically update profiles when assessments are completed</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Switch id="historical-data" defaultChecked />
                      <Label htmlFor="historical-data">Maintain historical assessment data for trend analysis</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Switch id="peer-review" />
                      <Label htmlFor="peer-review">Enable peer review component in assessments</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Switch id="ai-analysis" defaultChecked />
                      <Label htmlFor="ai-analysis">Enable AI-powered CV analysis and X-Factor matching</Label>
                    </div>
                  </div>
                </div>
              </CardContent>
              <CardFooter className="flex justify-end gap-2">
                <Button variant="outline">Reset to Defaults</Button>
                <Button>Save Settings</Button>
              </CardFooter>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardShell>
  )
}
