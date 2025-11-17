"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Upload, FileUp, CheckCircle, AlertCircle, FileText, Trash2 } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"

type FileStatus = "queued" | "analyzing" | "complete" | "error"

interface UploadedFile {
  id: string
  name: string
  size: string
  status: FileStatus
  progress: number
}

export function CVBatchUploader() {
  const [uploadState, setUploadState] = useState<"idle" | "uploading" | "analyzing" | "complete" | "error">("idle")
  const [progress, setProgress] = useState(0)
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([])
  const [analysisInProgress, setAnalysisInProgress] = useState(false)

  const handleUpload = () => {
    setUploadState("uploading")
    setProgress(0)

    // Simulate upload progress
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval)
          setUploadState("analyzing")
          simulateFileUploads()
          return 100
        }
        return prev + 5
      })
    }, 150)
  }

  const simulateFileUploads = () => {
    // Simulate uploaded files
    const files: UploadedFile[] = [
      { id: "1", name: "John_Smith_CV.pdf", size: "1.2 MB", status: "queued", progress: 0 },
      { id: "2", name: "Emily_Johnson_Resume.pdf", size: "890 KB", status: "queued", progress: 0 },
      { id: "3", name: "Michael_Chen_CV.pdf", size: "1.5 MB", status: "queued", progress: 0 },
      { id: "4", name: "Sarah_Williams_Resume.pdf", size: "1.1 MB", status: "queued", progress: 0 },
      { id: "5", name: "David_Rodriguez_CV.pdf", size: "950 KB", status: "queued", progress: 0 },
    ]

    setUploadedFiles(files)

    // Simulate file analysis
    setAnalysisInProgress(true)

    files.forEach((file, index) => {
      setTimeout(() => {
        setUploadedFiles((prev) => prev.map((f) => (f.id === file.id ? { ...f, status: "analyzing", progress: 0 } : f)))

        // Simulate progress for each file
        const progressInterval = setInterval(() => {
          setUploadedFiles((prev) => {
            const updatedFiles = prev.map((f) => {
              if (f.id === file.id) {
                const newProgress = f.progress + 10
                if (newProgress >= 100) {
                  clearInterval(progressInterval)
                  return { ...f, progress: 100, status: "complete" }
                }
                return { ...f, progress: newProgress }
              }
              return f
            })

            // Check if all files are complete
            if (updatedFiles.every((f) => f.status === "complete")) {
              setUploadState("complete")
              setAnalysisInProgress(false)
            }

            return updatedFiles
          })
        }, 300)
      }, index * 1000) // Stagger the start of each file analysis
    })
  }

  const removeFile = (id: string) => {
    setUploadedFiles((prev) => prev.filter((file) => file.id !== id))
    if (uploadedFiles.length <= 1) {
      setUploadState("idle")
    }
  }

  return (
    <div className="space-y-6">
      {uploadState === "idle" && (
        <>
          <div className="border-2 border-dashed rounded-lg p-10 text-center">
            <div className="flex flex-col items-center gap-2">
              <Upload className="h-10 w-10 text-muted-foreground" />
              <p className="font-medium">Upload Candidate CVs for Analysis</p>
              <p className="text-sm text-muted-foreground">
                Upload PDF or DOCX files containing candidate CVs for X-Factor analysis
              </p>
              <Button variant="outline" size="sm" className="mt-4" onClick={handleUpload}>
                <FileUp className="mr-2 h-4 w-4" />
                Browse Files
              </Button>
            </div>
          </div>

          <Card>
            <CardContent className="pt-6">
              <div className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="job-position">Target Job Position</Label>
                    <Select defaultValue="executive">
                      <SelectTrigger id="job-position">
                        <SelectValue placeholder="Select job position" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="executive">Executive Leadership</SelectItem>
                        <SelectItem value="director">Director Level</SelectItem>
                        <SelectItem value="manager">Senior Manager</SelectItem>
                        <SelectItem value="specialist">Specialist</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="x-factor-profile">X-Factor Profile</Label>
                    <Select defaultValue="leadership">
                      <SelectTrigger id="x-factor-profile">
                        <SelectValue placeholder="Select X-Factor profile" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="leadership">Leadership Excellence</SelectItem>
                        <SelectItem value="innovation">Innovation & Strategy</SelectItem>
                        <SelectItem value="execution">Execution & Results</SelectItem>
                        <SelectItem value="custom">Custom Profile</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <Switch id="deep-learning" defaultChecked />
                    <Label htmlFor="deep-learning">Use deep learning from existing MT profiles</Label>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <Switch id="comprehensive" defaultChecked />
                    <Label htmlFor="comprehensive">Perform comprehensive analysis (takes longer)</Label>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
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
          <div className="text-sm text-muted-foreground">Please wait while we upload your files</div>
        </div>
      )}

      {(uploadState === "analyzing" || uploadState === "complete") && (
        <div className="space-y-6">
          {analysisInProgress && (
            <Alert variant="default" className="bg-blue-50 border-blue-200">
              <FileText className="h-4 w-4 text-blue-600" />
              <AlertTitle>Analysis in Progress</AlertTitle>
              <AlertDescription>
                Our AI is analyzing CVs against X-Factors derived from your MT profiles. This may take a few minutes.
              </AlertDescription>
            </Alert>
          )}

          {uploadState === "complete" && (
            <Alert variant="default" className="bg-green-50 border-green-200">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <AlertTitle>Analysis Complete</AlertTitle>
              <AlertDescription>
                All CVs have been analyzed. View the results in the Candidate Analysis table below.
              </AlertDescription>
            </Alert>
          )}

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium">Uploaded Files</h3>
              <Button variant="outline" size="sm" onClick={handleUpload}>
                <FileUp className="mr-2 h-4 w-4" />
                Upload More
              </Button>
            </div>

            <div className="space-y-2">
              {uploadedFiles.map((file) => (
                <div key={file.id} className="flex items-center justify-between p-3 border rounded-md">
                  <div className="flex items-center gap-3">
                    <FileText className="h-5 w-5 text-blue-600" />
                    <div>
                      <p className="font-medium">{file.name}</p>
                      <p className="text-xs text-muted-foreground">{file.size}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {file.status === "analyzing" && (
                      <div className="w-24">
                        <Progress value={file.progress} className="h-2" />
                      </div>
                    )}
                    <Badge
                      variant="outline"
                      className={`
                        ${file.status === "queued" ? "bg-gray-50 text-gray-700 border-gray-200" : ""}
                        ${file.status === "analyzing" ? "bg-blue-50 text-blue-700 border-blue-200" : ""}
                        ${file.status === "complete" ? "bg-green-50 text-green-700 border-green-200" : ""}
                        ${file.status === "error" ? "bg-red-50 text-red-700 border-red-200" : ""}
                      `}
                    >
                      {file.status === "queued" && "Queued"}
                      {file.status === "analyzing" && "Analyzing"}
                      {file.status === "complete" && "Complete"}
                      {file.status === "error" && "Error"}
                    </Badge>
                    <Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={() => removeFile(file.id)}>
                      <Trash2 className="h-4 w-4" />
                      <span className="sr-only">Remove</span>
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {uploadState === "error" && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Upload Failed</AlertTitle>
          <AlertDescription>
            There was an error uploading your files. Please check the file format and try again.
          </AlertDescription>
        </Alert>
      )}
    </div>
  )
}
