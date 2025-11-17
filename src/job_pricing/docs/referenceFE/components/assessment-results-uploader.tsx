"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Upload, FileUp, CheckCircle, AlertCircle, FileText, Download } from "lucide-react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

// Sample assessment results data
const sampleResults = [
  {
    id: 1,
    candidateName: "Alex Johnson",
    assessmentDate: "2023-12-15",
    leadershipScore: 85,
    strategicThinkingScore: 78,
    communicationScore: 92,
    problemSolvingScore: 88,
    teamworkScore: 90,
    overallScore: 86.6,
    status: "Processed",
  },
  {
    id: 2,
    candidateName: "Maria Garcia",
    assessmentDate: "2023-12-15",
    leadershipScore: 92,
    strategicThinkingScore: 95,
    communicationScore: 88,
    problemSolvingScore: 91,
    teamworkScore: 84,
    overallScore: 90.0,
    status: "Processed",
  },
  {
    id: 3,
    candidateName: "Raj Patel",
    assessmentDate: "2023-12-15",
    leadershipScore: 79,
    strategicThinkingScore: 82,
    communicationScore: 75,
    problemSolvingScore: 80,
    teamworkScore: 88,
    overallScore: 80.8,
    status: "Processed",
  },
  {
    id: 4,
    candidateName: "Sophie Chen",
    assessmentDate: "2023-12-15",
    leadershipScore: 94,
    strategicThinkingScore: 89,
    communicationScore: 91,
    problemSolvingScore: 87,
    teamworkScore: 93,
    overallScore: 90.8,
    status: "Processed",
  },
  {
    id: 5,
    candidateName: "Omar Hassan",
    assessmentDate: "2023-12-15",
    leadershipScore: 81,
    strategicThinkingScore: 76,
    communicationScore: 85,
    problemSolvingScore: 79,
    teamworkScore: 82,
    overallScore: 80.6,
    status: "Processed",
  },
]

export function AssessmentResultsUploader() {
  const [uploadState, setUploadState] = useState<"idle" | "uploading" | "processing" | "success" | "error">("idle")
  const [progress, setProgress] = useState(0)
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([])
  const [processedResults, setProcessedResults] = useState<typeof sampleResults>([])

  const handleUpload = () => {
    setUploadState("uploading")
    setProgress(0)

    // Simulate upload progress
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval)
          setUploadState("processing")
          simulateProcessing()
          return 100
        }
        return prev + 10
      })
    }, 300)

    // Simulate uploaded files
    setUploadedFiles(["Assessment_Results_Q4_2023.xlsx"])
  }

  const simulateProcessing = () => {
    // Simulate processing delay
    setTimeout(() => {
      setUploadState("success")
      setProcessedResults(sampleResults)
    }, 2000)
  }

  return (
    <div className="space-y-6">
      {uploadState === "idle" && (
        <div className="border-2 border-dashed rounded-lg p-10 text-center">
          <div className="flex flex-col items-center gap-2">
            <Upload className="h-10 w-10 text-muted-foreground" />
            <p className="font-medium">Upload Assessment Center Results</p>
            <p className="text-sm text-muted-foreground">
              Upload Excel or CSV files containing assessment center results
            </p>
            <div className="flex gap-2 mt-4">
              <Button variant="outline" size="sm" onClick={handleUpload}>
                <FileUp className="mr-2 h-4 w-4" />
                Browse Files
              </Button>
              <Button variant="outline" size="sm">
                <FileText className="mr-2 h-4 w-4" />
                Use Template
              </Button>
            </div>
          </div>
        </div>
      )}

      {uploadState === "uploading" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FileUp className="h-5 w-5 text-blue-600" />
              <span className="font-medium">Uploading files...</span>
            </div>
            <span className="text-sm text-muted-foreground">{progress}%</span>
          </div>
          <Progress value={progress} className="h-2" />
          <div className="text-sm text-muted-foreground">Uploading {uploadedFiles.length} file(s)</div>
        </div>
      )}

      {uploadState === "processing" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-amber-600 animate-pulse" />
              <span className="font-medium">Processing assessment results...</span>
            </div>
          </div>
          <Progress value={100} className="h-2" />
          <div className="text-sm text-muted-foreground">Extracting data and analyzing assessment results...</div>
        </div>
      )}

      {uploadState === "success" && (
        <div className="space-y-6">
          <Alert variant="default" className="bg-green-50 border-green-200">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <AlertTitle>Upload Successful</AlertTitle>
            <AlertDescription>
              Assessment results have been successfully processed and are ready for review.
            </AlertDescription>
          </Alert>

          <div className="flex items-center justify-between">
            <div className="text-sm text-muted-foreground">Showing {processedResults.length} processed results</div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm">
                <Download className="mr-2 h-4 w-4" />
                Export Results
              </Button>
              <Button size="sm" onClick={() => setUploadState("idle")}>
                <Upload className="mr-2 h-4 w-4" />
                Upload More
              </Button>
            </div>
          </div>

          <Tabs defaultValue="table" className="w-full">
            <TabsList className="mb-4">
              <TabsTrigger value="table">Table View</TabsTrigger>
              <TabsTrigger value="summary">Summary</TabsTrigger>
            </TabsList>

            <TabsContent value="table">
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Candidate Name</TableHead>
                      <TableHead>Assessment Date</TableHead>
                      <TableHead>Leadership</TableHead>
                      <TableHead>Strategic Thinking</TableHead>
                      <TableHead>Communication</TableHead>
                      <TableHead>Problem Solving</TableHead>
                      <TableHead>Teamwork</TableHead>
                      <TableHead>Overall Score</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {processedResults.map((result) => (
                      <TableRow key={result.id}>
                        <TableCell className="font-medium">{result.candidateName}</TableCell>
                        <TableCell>{result.assessmentDate}</TableCell>
                        <TableCell>{result.leadershipScore}%</TableCell>
                        <TableCell>{result.strategicThinkingScore}%</TableCell>
                        <TableCell>{result.communicationScore}%</TableCell>
                        <TableCell>{result.problemSolvingScore}%</TableCell>
                        <TableCell>{result.teamworkScore}%</TableCell>
                        <TableCell className="font-medium">{result.overallScore}%</TableCell>
                        <TableCell>
                          <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                            {result.status}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </TabsContent>

            <TabsContent value="summary">
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                <div className="rounded-lg border bg-card p-4">
                  <div className="text-sm font-medium text-muted-foreground mb-2">Average Overall Score</div>
                  <div className="text-2xl font-bold">85.8%</div>
                </div>
                <div className="rounded-lg border bg-card p-4">
                  <div className="text-sm font-medium text-muted-foreground mb-2">Top Performer</div>
                  <div className="text-2xl font-bold">Sophie Chen</div>
                  <div className="text-sm text-muted-foreground">90.8% Overall Score</div>
                </div>
                <div className="rounded-lg border bg-card p-4">
                  <div className="text-sm font-medium text-muted-foreground mb-2">Highest Scoring Area</div>
                  <div className="text-2xl font-bold">Communication</div>
                  <div className="text-sm text-muted-foreground">86.2% Average</div>
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </div>
      )}

      {uploadState === "error" && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Upload Failed</AlertTitle>
          <AlertDescription>
            There was an error processing your assessment results. Please check the file format and try again.
          </AlertDescription>
        </Alert>
      )}
    </div>
  )
}
