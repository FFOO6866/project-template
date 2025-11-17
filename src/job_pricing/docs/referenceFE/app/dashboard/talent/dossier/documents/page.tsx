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

// Employee document data
const documents = [
  {
    id: 1,
    name: "Alex Morgan",
    role: "Senior Project Manager",
    documentTypes: [
      { type: "CV", path: "/documents/alex-morgan/cv.pdf", lastUpdated: "2023-05-15" },
      { type: "Performance Review", path: "/documents/alex-morgan/review-2023.pdf", lastUpdated: "2023-12-10" },
      {
        type: "Leadership Assessment",
        path: "/documents/alex-morgan/leadership-assessment.pdf",
        lastUpdated: "2023-11-22",
      },
    ],
  },
  {
    id: 2,
    name: "Sarah Chen",
    role: "VP of Product",
    documentTypes: [
      { type: "CV", path: "/documents/sarah-chen/cv.pdf", lastUpdated: "2023-04-20" },
      { type: "Performance Review", path: "/documents/sarah-chen/review-2023.pdf", lastUpdated: "2023-12-05" },
      { type: "Strategic Plan", path: "/documents/sarah-chen/strategic-plan.pdf", lastUpdated: "2023-10-15" },
    ],
  },
  {
    id: 3,
    name: "James Wilson",
    role: "UX Designer",
    documentTypes: [
      { type: "CV", path: "/documents/james-wilson/cv.pdf", lastUpdated: "2023-06-10" },
      { type: "Performance Review", path: "/documents/james-wilson/review-2023.pdf", lastUpdated: "2023-12-08" },
      { type: "Portfolio", path: "/documents/james-wilson/portfolio.pdf", lastUpdated: "2023-10-15" },
    ],
  },
  {
    id: 4,
    name: "Olivia Martinez",
    role: "Marketing Director",
    documentTypes: [
      { type: "CV", path: "/documents/olivia-martinez/cv.pdf", lastUpdated: "2023-03-25" },
      { type: "Performance Review", path: "/documents/olivia-martinez/review-2023.pdf", lastUpdated: "2023-12-01" },
      { type: "Marketing Plan", path: "/documents/olivia-martinez/marketing-plan.pdf", lastUpdated: "2023-09-18" },
    ],
  },
  {
    id: 5,
    name: "Robert Chen",
    role: "Software Engineer",
    documentTypes: [
      { type: "CV", path: "/documents/robert-chen/cv.pdf", lastUpdated: "2023-07-12" },
      { type: "Performance Review", path: "/documents/robert-chen/review-2023.pdf", lastUpdated: "2023-11-28" },
      { type: "Technical Assessment", path: "/documents/robert-chen/tech-assessment.pdf", lastUpdated: "2023-10-05" },
    ],
  },
]

// Document types
const documentTypes = [
  { id: 1, name: "CV", description: "Curriculum Vitae", defaultDirectory: "/documents/{name}/cv", icon: "FilePdf" },
  {
    id: 2,
    name: "Performance Review",
    description: "Annual Performance Review",
    defaultDirectory: "/documents/{name}/reviews",
    icon: "FileSpreadsheet",
  },
  {
    id: 3,
    name: "Leadership Assessment",
    description: "Leadership Capabilities Assessment",
    defaultDirectory: "/documents/{name}/leadership",
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
    name: "Portfolio",
    description: "Work Portfolio",
    defaultDirectory: "/documents/{name}/portfolio",
    icon: "FileText",
  },
  {
    id: 6,
    name: "Strategic Plan",
    description: "Strategic Planning Documents",
    defaultDirectory: "/documents/{name}/strategic",
    icon: "FileText",
  },
  {
    id: 7,
    name: "Marketing Plan",
    description: "Marketing Strategy Documents",
    defaultDirectory: "/documents/{name}/marketing",
    icon: "FileText",
  },
  {
    id: 8,
    name: "Development Plan",
    description: "Career Development Plan",
    defaultDirectory: "/documents/{name}/development",
    icon: "FileText",
  },
  {
    id: 9,
    name: "Certification",
    description: "Professional Certifications",
    defaultDirectory: "/documents/{name}/certifications",
    icon: "FileText",
  },
]

export default function EDossierDocumentsPage() {
  return (
    <DashboardShell>
      <div className="flex flex-col space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <Heading level="h1">Document Management</Heading>
            <Text color="muted">Manage and access employee documents and records</Text>
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
          <Link href="/dashboard/talent/dossier">
            <Button variant="outline" className="h-9">
              <BarChart2 className="mr-2 h-4 w-4" />
              Employee Overview
            </Button>
          </Link>
          <Link href="/dashboard/talent/dossier/performance">
            <Button variant="outline" className="h-9">
              <BarChart2 className="mr-2 h-4 w-4" />
              Performance Matrix
            </Button>
          </Link>
          <Link href="/dashboard/talent/dossier/documents">
            <Button variant="secondary" className="h-9">
              <FileText className="mr-2 h-4 w-4" />
              Document Management
            </Button>
          </Link>
          <Link href="/dashboard/talent/dossier/admin">
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
                <CardTitle>Employee Documents</CardTitle>
                <CardDescription>Access and manage documents for each employee</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="mb-6 p-4 border rounded-lg bg-muted/20">
                  <h3 className="text-base font-medium mb-2">Upload New Document</h3>
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="upload-employee">Employee</Label>
                      <Select>
                        <SelectTrigger id="upload-employee">
                          <SelectValue placeholder="Select employee" />
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
                      <TableHead>Employee</TableHead>
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
                                  <AvatarImage
                                    src={`/team/${person.name.toLowerCase().replace(/\s+/g, "-")}.jpg`}
                                    alt={person.name}
                                  />
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
                              {doc.type === "Performance Review" && (
                                <FileSpreadsheet className="h-4 w-4 text-green-500" />
                              )}
                              {doc.type === "Portfolio" && <FileText className="h-4 w-4 text-blue-500" />}
                              {doc.type === "Technical Assessment" && <File className="h-4 w-4 text-purple-500" />}
                              {doc.type === "Leadership Assessment" && <FileText className="h-4 w-4 text-blue-500" />}
                              {doc.type === "Strategic Plan" && <FileText className="h-4 w-4 text-orange-500" />}
                              {doc.type === "Marketing Plan" && <FileText className="h-4 w-4 text-pink-500" />}
                              {doc.type === "Development Plan" && <FileText className="h-4 w-4 text-violet-500" />}
                              {doc.type === "Certification" && <FileText className="h-4 w-4 text-yellow-500" />}
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
                <CardDescription>Define and manage document types for employee profiles</CardDescription>
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
