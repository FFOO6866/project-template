import { DashboardShell } from "@/components/dashboard-shell"
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Heading } from "@/components/ui/heading"
import { Text } from "@/components/ui/text"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  Search,
  Filter,
  Download,
  FileText,
  BarChart2,
  Settings,
  File,
  FileIcon as FilePdf,
  FileSpreadsheet,
  Upload,
  User,
  Tag,
  Trash2,
} from "lucide-react"
import Link from "next/link"
import { DocumentTypeForm } from "@/components/document-type-form"

// Updated document data with management trainees
const documents = [
  {
    id: 1,
    name: "Camille Wong Yuk",
    role: "Management Trainee",
    documentTypes: [
      { type: "CV", path: "/documents/camille-wong-yuk/cv.pdf", lastUpdated: "2023-05-15" },
      { type: "Evaluation", path: "/documents/camille-wong-yuk/evaluation-2023.pdf", lastUpdated: "2023-12-10" },
      {
        type: "Leadership Assessment",
        path: "/documents/camille-wong-yuk/leadership-assessment.pdf",
        lastUpdated: "2023-11-22",
      },
    ],
  },
  {
    id: 2,
    name: "Marcel Melhado",
    role: "Management Trainee",
    documentTypes: [
      { type: "CV", path: "/documents/marcel-melhado/cv.pdf", lastUpdated: "2023-04-20" },
      { type: "Evaluation", path: "/documents/marcel-melhado/evaluation-2023.pdf", lastUpdated: "2023-12-05" },
    ],
  },
  {
    id: 3,
    name: "Vivian Ho",
    role: "Management Trainee",
    documentTypes: [
      { type: "CV", path: "/documents/vivian-ho/cv.pdf", lastUpdated: "2023-06-10" },
      { type: "Evaluation", path: "/documents/vivian-ho/evaluation-2023.pdf", lastUpdated: "2023-12-08" },
      { type: "Journal", path: "/documents/vivian-ho/journal.docx", lastUpdated: "2023-10-15" },
    ],
  },
  {
    id: 4,
    name: "Massie Shen",
    role: "Management Trainee",
    documentTypes: [
      { type: "CV", path: "/documents/massie-shen/cv.pdf", lastUpdated: "2023-03-25" },
      { type: "Evaluation", path: "/documents/massie-shen/evaluation-2023.pdf", lastUpdated: "2023-12-01" },
      { type: "Technical Assessment", path: "/documents/massie-shen/tech-assessment.pdf", lastUpdated: "2023-09-18" },
    ],
  },
  {
    id: 5,
    name: "Gloria Cai Xinyi",
    role: "Management Trainee",
    documentTypes: [
      { type: "CV", path: "/documents/gloria-cai-xinyi/cv.pdf", lastUpdated: "2023-07-12" },
      { type: "Evaluation", path: "/documents/gloria-cai-xinyi/evaluation-2023.pdf", lastUpdated: "2023-11-28" },
    ],
  },
  {
    id: 6,
    name: "Egan Valentino",
    role: "Management Trainee",
    documentTypes: [
      { type: "CV", path: "/documents/egan-valentino/cv.pdf", lastUpdated: "2023-08-05" },
      { type: "Evaluation", path: "/documents/egan-valentino/evaluation-2023.pdf", lastUpdated: "2023-12-12" },
    ],
  },
  {
    id: 7,
    name: "Madhav Kapoor",
    role: "Management Trainee",
    documentTypes: [
      { type: "CV", path: "/documents/madhav-kapoor/cv.pdf", lastUpdated: "2023-05-22" },
      { type: "Evaluation", path: "/documents/madhav-kapoor/evaluation-2023.pdf", lastUpdated: "2023-12-07" },
      {
        type: "Project Assessment",
        path: "/documents/madhav-kapoor/project-assessment.pdf",
        lastUpdated: "2023-10-30",
      },
    ],
  },
  {
    id: 8,
    name: "Shauryaa Ladha",
    role: "Management Trainee",
    documentTypes: [
      { type: "CV", path: "/documents/shauryaa-ladha/cv.pdf", lastUpdated: "2023-06-18" },
      { type: "Evaluation", path: "/documents/shauryaa-ladha/evaluation-2023.pdf", lastUpdated: "2023-12-03" },
    ],
  },
  {
    id: 9,
    name: "Jane Putri",
    role: "Management Trainee",
    documentTypes: [
      { type: "CV", path: "/documents/jane-putri/cv.pdf", lastUpdated: "2023-07-25" },
      { type: "Evaluation", path: "/documents/jane-putri/evaluation-2023.pdf", lastUpdated: "2023-12-09" },
      { type: "Financial Analysis", path: "/documents/jane-putri/financial-analysis.pdf", lastUpdated: "2023-11-05" },
    ],
  },
  {
    id: 10,
    name: "Mathew Ling",
    role: "Management Trainee",
    documentTypes: [
      { type: "CV", path: "/documents/mathew-ling/cv.pdf", lastUpdated: "2023-04-15" },
      { type: "Evaluation", path: "/documents/mathew-ling/evaluation-2023.pdf", lastUpdated: "2023-12-11" },
    ],
  },
  {
    id: 11,
    name: "Wu Hong Rui",
    role: "Management Trainee",
    documentTypes: [
      { type: "CV", path: "/documents/wu-hong-rui/cv.pdf", lastUpdated: "2023-05-30" },
      { type: "Evaluation", path: "/documents/wu-hong-rui/evaluation-2023.pdf", lastUpdated: "2023-12-02" },
      { type: "Marketing Strategy", path: "/documents/wu-hong-rui/marketing-strategy.pdf", lastUpdated: "2023-10-20" },
    ],
  },
  {
    id: 12,
    name: "Ra Won Park",
    role: "Management Trainee",
    documentTypes: [
      { type: "CV", path: "/documents/ra-won-park/cv.pdf", lastUpdated: "2023-06-05" },
      { type: "Evaluation", path: "/documents/ra-won-park/evaluation-2023.pdf", lastUpdated: "2023-12-15" },
      { type: "HR Assessment", path: "/documents/ra-won-park/hr-assessment.pdf", lastUpdated: "2023-11-10" },
    ],
  },
]

// Updated document types
const documentTypes = [
  { id: 1, name: "CV", description: "Curriculum Vitae", defaultDirectory: "/documents/{name}/cv", icon: "FilePdf" },
  {
    id: 2,
    name: "Evaluation",
    description: "Annual Performance Evaluation",
    defaultDirectory: "/documents/{name}/evaluations",
    icon: "FileSpreadsheet",
  },
  {
    id: 3,
    name: "Journal",
    description: "Leadership or Professional Journal",
    defaultDirectory: "/documents/{name}/journals",
    icon: "FileText",
  },
  {
    id: 4,
    name: "Technical Assessment",
    description: "Technical Skills Assessment",
    defaultDirectory: "/documents/{name}/assessments",
    icon: "File",
  },
  {
    id: 5,
    name: "Leadership Assessment",
    description: "Leadership Capabilities Assessment",
    defaultDirectory: "/documents/{name}/leadership",
    icon: "FileText",
  },
  {
    id: 6,
    name: "Project Assessment",
    description: "Project Management Assessment",
    defaultDirectory: "/documents/{name}/projects",
    icon: "FileText",
  },
  {
    id: 7,
    name: "Financial Analysis",
    description: "Financial Analysis Reports",
    defaultDirectory: "/documents/{name}/finance",
    icon: "FileSpreadsheet",
  },
  {
    id: 8,
    name: "Marketing Strategy",
    description: "Marketing Strategy Documents",
    defaultDirectory: "/documents/{name}/marketing",
    icon: "FileText",
  },
  {
    id: 9,
    name: "HR Assessment",
    description: "Human Resources Assessment",
    defaultDirectory: "/documents/{name}/hr",
    icon: "FileText",
  },
]

export default function DocumentManagementPage() {
  return (
    <DashboardShell>
      <div className="flex flex-col space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <Heading level="h1">Document Management</Heading>
            <Text color="muted">Manage and access MT profile documents and directories</Text>
          </div>
          <div className="flex items-center gap-2">
            <div className="relative w-64">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input type="search" placeholder="Search documents..." className="w-full pl-8" />
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
            <Button variant="outline" className="h-9">
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
            <Button variant="secondary" className="h-9">
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

        <Tabs defaultValue="documents" className="space-y-6">
          <TabsList>
            <TabsTrigger value="documents">Documents</TabsTrigger>
            <TabsTrigger value="document-types">Document Types</TabsTrigger>
          </TabsList>

          <TabsContent value="documents" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>MT Profile Documents</CardTitle>
                <CardDescription>Access and manage documents for each management team member</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="mb-6 p-4 border rounded-lg bg-muted/20">
                  <h3 className="text-base font-medium mb-2">Upload New Document</h3>
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="upload-team-member">Team Member</Label>
                      <Select>
                        <SelectTrigger id="upload-team-member">
                          <SelectValue placeholder="Select team member" />
                        </SelectTrigger>
                        <SelectContent>
                          {documents.map((person) => (
                            <SelectItem key={person.id} value={person.id.toString()}>
                              {person.name} - {person.role}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="upload-document-type">Document Type</Label>
                      <Select>
                        <SelectTrigger id="upload-document-type">
                          <SelectValue placeholder="Select document type" />
                        </SelectTrigger>
                        <SelectContent>
                          {documentTypes.map((type) => (
                            <SelectItem key={type.id} value={type.name}>
                              {type.name} - {type.description}
                            </SelectItem>
                          ))}
                          <SelectItem value="new">+ Add New Document Type</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div className="mt-4">
                    <Button className="w-full">
                      <Upload className="mr-2 h-4 w-4" />
                      Select Files to Upload
                    </Button>
                  </div>
                </div>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Team Member</TableHead>
                      <TableHead>Document Type</TableHead>
                      <TableHead>Last Updated</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {documents.flatMap((person) =>
                      person.documentTypes.map((doc, index) => (
                        <TableRow key={`${person.id}-${index}`}>
                          {index === 0 ? (
                            <TableCell rowSpan={person.documentTypes.length} className="align-top">
                              <div className="flex items-center gap-2">
                                <Avatar className="h-8 w-8">
                                  <AvatarImage src="/silhouette-male.png" alt={person.name} />
                                  <AvatarFallback>
                                    <User className="h-4 w-4" />
                                  </AvatarFallback>
                                </Avatar>
                                <div>
                                  <p className="font-medium">{person.name}</p>
                                  <p className="text-xs text-muted-foreground">{person.role}</p>
                                </div>
                              </div>
                            </TableCell>
                          ) : null}
                          <TableCell>
                            <div className="flex items-center gap-2">
                              {doc.type === "CV" && <FilePdf className="h-4 w-4 text-red-500" />}
                              {doc.type === "Evaluation" && <FileSpreadsheet className="h-4 w-4 text-green-500" />}
                              {doc.type === "Journal" && <FileText className="h-4 w-4 text-blue-500" />}
                              {doc.type === "Technical Assessment" && <File className="h-4 w-4 text-purple-500" />}
                              {doc.type === "Leadership Assessment" && <FileText className="h-4 w-4 text-blue-500" />}
                              {doc.type === "Project Assessment" && <FileText className="h-4 w-4 text-orange-500" />}
                              {doc.type === "Financial Analysis" && (
                                <FileSpreadsheet className="h-4 w-4 text-green-500" />
                              )}
                              {doc.type === "Marketing Strategy" && <FileText className="h-4 w-4 text-pink-500" />}
                              {doc.type === "HR Assessment" && <FileText className="h-4 w-4 text-violet-500" />}
                              {doc.type}
                            </div>
                          </TableCell>
                          <TableCell>{doc.lastUpdated}</TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                                <Search className="h-4 w-4" />
                                <span className="sr-only">View</span>
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-8 w-8 p-0 text-red-500 hover:text-red-600 hover:bg-red-50"
                              >
                                <Trash2 className="h-4 w-4" />
                                <span className="sr-only">Delete</span>
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-8 w-8 p-0 text-blue-500 hover:text-blue-600 hover:bg-blue-50"
                              >
                                <Upload className="h-4 w-4" />
                                <span className="sr-only">Upload Again</span>
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      )),
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="document-types" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Document Types</CardTitle>
                <CardDescription>Define and manage document types for team member profiles</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Type Name</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead>Default Directory</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {documentTypes.map((type) => (
                      <TableRow key={type.id}>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            {type.icon === "FilePdf" && <FilePdf className="h-4 w-4 text-red-500" />}
                            {type.icon === "FileSpreadsheet" && <FileSpreadsheet className="h-4 w-4 text-green-500" />}
                            {type.icon === "FileText" && <FileText className="h-4 w-4 text-blue-500" />}
                            {type.icon === "File" && <File className="h-4 w-4 text-purple-500" />}
                            {type.name}
                          </div>
                        </TableCell>
                        <TableCell>{type.description}</TableCell>
                        <TableCell>
                          <code className="rounded bg-muted px-1 py-0.5 text-sm">{type.defaultDirectory}</code>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Button variant="ghost" size="sm">
                              Edit
                            </Button>
                            <Button variant="ghost" size="sm" className="text-red-500 hover:text-red-600">
                              Delete
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
              <CardFooter>
                <Button>
                  <Tag className="mr-2 h-4 w-4" />
                  Add New Document Type
                </Button>
              </CardFooter>
            </Card>

            <DocumentTypeForm />
          </TabsContent>
        </Tabs>
      </div>
    </DashboardShell>
  )
}
