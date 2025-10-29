"use client"

import type React from "react"

import { useState, useCallback, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Upload, FileText, Loader2, AlertCircle, CheckCircle2, XCircle } from "lucide-react"
import { apiClient } from "@/lib/api-client"
import { AuthenticationError, ValidationError } from "@/lib/api-errors"

interface DocumentUploadProps {
  onDocumentUploaded: (documentId: number, fileName: string) => void
}

type UploadStage = 'idle' | 'validating' | 'uploading' | 'processing' | 'success' | 'error'

export function DocumentUpload({ onDocumentUploaded }: DocumentUploadProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [uploadStage, setUploadStage] = useState<UploadStage>('idle')
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      handleFileUpload(files[0])
    }
  }, [])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    console.log('[DocumentUpload] File selected:', e.target.files)
    const files = e.target.files
    if (files && files.length > 0) {
      console.log('[DocumentUpload] Starting upload for:', files[0].name)
      handleFileUpload(files[0])
    }
  }, [])

  const validateFile = (file: File): string | null => {
    const maxSize = 50 * 1024 * 1024 // 50MB
    const allowedTypes = ['.pdf', '.doc', '.docx', '.txt']
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase()

    if (file.size > maxSize) {
      return `File size exceeds 50MB limit (${(file.size / 1024 / 1024).toFixed(2)}MB)`
    }

    if (!allowedTypes.includes(fileExtension)) {
      return `File type ${fileExtension} not supported. Please upload PDF, DOC, DOCX, or TXT files.`
    }

    return null
  }

  const handleFileUpload = async (file: File) => {
    console.log('[DocumentUpload] handleFileUpload called with file:', file.name, file.type, file.size)
    setUploadedFile(file)
    setError(null)
    setUploadProgress(0)

    // Validate file
    setUploadStage('validating')
    const validationError = validateFile(file)
    if (validationError) {
      setUploadStage('error')
      setError(validationError)
      return
    }

    try {
      // Start upload
      setUploadStage('uploading')
      setUploadProgress(30)

      console.log('[DocumentUpload] Calling apiClient.uploadFile...')
      const response = await apiClient.uploadFile({
        file,
        document_type: "rfp",
        metadata: {
          original_name: file.name,
          upload_timestamp: new Date().toISOString()
        }
      })

      console.log("[DocumentUpload] Upload successful:", response)

      // Show processing state
      setUploadProgress(70)
      setUploadStage('processing')

      // Brief delay to show success state before transitioning
      setTimeout(() => {
        setUploadProgress(100)
        setUploadStage('success')

        // Navigate to chat after showing success
        setTimeout(() => {
          console.log('[DocumentUpload] Creating new tab for document:', response.document_id, response.filename)
          onDocumentUploaded(response.document_id, response.filename)

          // Reset for next upload
          setTimeout(() => {
            setUploadStage('idle')
            setUploadProgress(0)
            setUploadedFile(null)
          }, 500)
        }, 1000)
      }, 800)

    } catch (err) {
      console.error("[DocumentUpload] Upload error:", err)
      setUploadStage('error')

      if (err instanceof ValidationError) {
        console.error('[DocumentUpload] Validation error:', err.message)
        setError(err.message)
      } else if (err instanceof Error) {
        // Provide more specific error messages
        if (err.message.includes('Network') || err.message.includes('fetch')) {
          setError("Connection error. Please check that the backend server is running on port 8002.")
        } else if (err.message.includes('timeout')) {
          setError("Upload timed out. Please try again with a smaller file.")
        } else {
          setError(err.message || "Upload failed. Please try again.")
        }
      } else {
        setError("Upload failed. Please try again.")
      }
    }
  }

  return (
    <Card className="border-slate-200 hover:shadow-md transition-shadow">
      <CardHeader className="pb-3 px-4 py-3">
        <CardTitle className="flex items-center text-slate-900 text-base">
          <Upload className="w-4 h-4 mr-2 text-amber-600" />
          Upload Document
        </CardTitle>
      </CardHeader>
      <CardContent className="px-4 pb-4">
        {/* Error Message */}
        {error && (
          <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded-lg flex items-start">
            <AlertCircle className="w-4 h-4 text-red-600 mr-2 flex-shrink-0 mt-0.5" />
            <p className="text-red-700 text-xs">{error}</p>
          </div>
        )}

        <div
          className={`border-2 border-dashed rounded-lg p-4 text-center transition-colors ${
            isDragging ? "border-amber-400 bg-amber-50" :
            uploadStage === 'error' ? "border-red-300 bg-red-50/30" :
            uploadStage === 'success' ? "border-green-300 bg-green-50/30" :
            "border-slate-300 hover:border-amber-400 hover:bg-amber-50/50"
          }`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          {uploadStage === 'idle' ? (
            <div className="space-y-3">
              <FileText className="w-8 h-8 text-slate-400 mx-auto" />
              <div>
                <p className="text-slate-900 font-medium mb-1 text-sm">Drop your RFP, quote request, or document here</p>
                <p className="text-slate-600 text-xs mb-3">Supports PDF, DOC, DOCX, TXT files up to 50MB</p>
                <input
                  type="file"
                  id="file-upload"
                  className="hidden"
                  accept=".pdf,.doc,.docx,.txt"
                  onChange={handleFileSelect}
                />
                <label htmlFor="file-upload">
                  <Button
                    variant="outline"
                    size="sm"
                    className="border-amber-200 text-amber-700 hover:bg-amber-50 cursor-pointer bg-transparent text-xs"
                    asChild
                  >
                    <span>Choose File</span>
                  </Button>
                </label>
              </div>
            </div>
          ) : uploadStage === 'validating' ? (
            <div className="space-y-3">
              <Loader2 className="w-8 h-8 text-amber-600 mx-auto animate-spin" />
              <div>
                <p className="text-slate-900 font-medium text-sm">Validating {uploadedFile?.name}</p>
                <p className="text-slate-600 text-xs">Checking file size and type...</p>
              </div>
            </div>
          ) : uploadStage === 'uploading' || uploadStage === 'processing' ? (
            <div className="space-y-3">
              <Loader2 className="w-8 h-8 text-amber-600 mx-auto animate-spin" />
              <div className="space-y-2">
                <div>
                  <p className="text-slate-900 font-medium text-sm">{uploadedFile?.name}</p>
                  <p className="text-slate-600 text-xs">
                    {uploadStage === 'uploading' ? 'Uploading to server...' : 'Processing document...'}
                  </p>
                </div>
                <div className="w-full max-w-xs mx-auto">
                  <Progress value={uploadProgress} className="h-1.5" />
                  <p className="text-xs text-slate-500 mt-0.5">{uploadProgress}%</p>
                </div>
              </div>
            </div>
          ) : uploadStage === 'success' ? (
            <div className="space-y-3">
              <CheckCircle2 className="w-8 h-8 text-green-600 mx-auto" />
              <div>
                <p className="text-slate-900 font-medium text-sm">Upload successful!</p>
                <p className="text-slate-600 text-xs">Opening chat interface...</p>
              </div>
            </div>
          ) : uploadStage === 'error' ? (
            <div className="space-y-3">
              <XCircle className="w-8 h-8 text-red-500 mx-auto" />
              <div>
                <p className="text-slate-900 font-medium text-sm">Upload failed</p>
                <p className="text-slate-600 text-xs">Please try again</p>
                <Button
                  variant="outline"
                  size="sm"
                  className="border-amber-200 text-amber-700 hover:bg-amber-50 mt-2 text-xs"
                  onClick={() => {
                    setUploadStage('idle')
                    setError(null)
                    setUploadedFile(null)
                  }}
                >
                  Try Again
                </Button>
              </div>
            </div>
          ) : null}
        </div>
      </CardContent>
    </Card>
  )
}
