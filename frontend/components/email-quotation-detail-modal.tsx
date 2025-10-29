"use client"

import { useState, useEffect } from "react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import {
  Mail,
  User,
  Calendar,
  FileText,
  CheckCircle,
  XCircle,
  RefreshCw,
  AlertCircle,
  Download,
} from "lucide-react"
import { apiClient } from "@/lib/api-client"
import type { EmailQuotationRequestDetail } from "@/lib/api-types"

interface EmailQuotationDetailModalProps {
  requestId: number | null
  isOpen: boolean
  onClose: () => void
  onProcessSuccess?: () => void
  onIgnoreSuccess?: () => void
}

export function EmailQuotationDetailModal({
  requestId,
  isOpen,
  onClose,
  onProcessSuccess,
  onIgnoreSuccess,
}: EmailQuotationDetailModalProps) {
  const [request, setRequest] = useState<EmailQuotationRequestDetail | null>(null)
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [processing, setProcessing] = useState<boolean>(false)
  const [ignoring, setIgnoring] = useState<boolean>(false)

  // Fetch request details when modal opens
  useEffect(() => {
    if (isOpen && requestId !== null) {
      fetchRequestDetails()
    }
  }, [isOpen, requestId])

  const fetchRequestDetails = async () => {
    if (requestId === null) return

    try {
      setLoading(true)
      setError(null)
      const data = await apiClient.getEmailQuotationRequest(requestId)
      setRequest(data)
    } catch (err: any) {
      console.error('Failed to fetch request details:', err)
      setError(err.message || 'Failed to load request details')
    } finally {
      setLoading(false)
    }
  }

  const handleProcess = async () => {
    if (!request) return

    try {
      setProcessing(true)
      setError(null)

      await apiClient.processEmailQuotationRequest(request.id)

      // Refresh details
      await fetchRequestDetails()

      // Notify parent
      onProcessSuccess?.()

      // Show success message
      alert('Quotation processing started successfully')
    } catch (err: any) {
      console.error('Failed to process request:', err)
      setError(err.message || 'Failed to process request')
    } finally {
      setProcessing(false)
    }
  }

  const handleIgnore = async () => {
    if (!request) return

    try {
      setIgnoring(true)
      setError(null)

      await apiClient.updateEmailQuotationRequestStatus(request.id, {
        status: 'ignored',
        notes: 'Ignored by user from detail modal'
      })

      // Notify parent
      onIgnoreSuccess?.()

      // Close modal
      onClose()
    } catch (err: any) {
      console.error('Failed to ignore request:', err)
      setError(err.message || 'Failed to ignore request')
    } finally {
      setIgnoring(false)
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-emerald-100 text-emerald-800"
      case "quotation_created":
        return "bg-blue-100 text-blue-800"
      case "processing":
      case "quotation_processing":
        return "bg-amber-100 text-amber-800"
      case "pending":
        return "bg-slate-100 text-slate-800"
      case "failed":
        return "bg-red-100 text-red-800"
      default:
        return "bg-slate-100 text-slate-800"
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center">
            <Mail className="w-5 h-5 mr-2 text-amber-600" />
            Email Quotation Request Details
          </DialogTitle>
          <DialogDescription>
            View complete email details and extracted AI requirements
          </DialogDescription>
        </DialogHeader>

        {loading && (
          <div className="flex items-center justify-center py-12">
            <RefreshCw className="w-6 h-6 mr-2 animate-spin text-slate-500" />
            <span className="text-slate-500">Loading details...</span>
          </div>
        )}

        {error && !loading && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center text-red-800">
              <AlertCircle className="w-5 h-5 mr-2" />
              <span className="font-medium">{error}</span>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={fetchRequestDetails}
              className="mt-3 border-red-200 text-red-700 hover:bg-red-50"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Retry
            </Button>
          </div>
        )}

        {request && !loading && (
          <div className="space-y-6">
            {/* Email Header */}
            <div className="bg-slate-50 rounded-lg p-4">
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <h3 className="font-semibold text-lg text-slate-900">
                    {request.subject}
                  </h3>
                </div>
                <Badge className={getStatusColor(request.status)}>
                  {request.status.replace('_', ' ')}
                </Badge>
              </div>

              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="flex items-center text-slate-700">
                  <User className="w-4 h-4 mr-2 text-slate-500" />
                  <div>
                    <div className="font-medium">{request.sender_name || 'Unknown'}</div>
                    <div className="text-slate-600">{request.sender_email}</div>
                  </div>
                </div>
                <div className="flex items-center text-slate-700">
                  <Calendar className="w-4 h-4 mr-2 text-slate-500" />
                  <span>{formatDate(request.received_date)}</span>
                </div>
              </div>

              {/* AI Confidence Score */}
              {request.ai_confidence_score !== undefined && request.ai_confidence_score !== null && (
                <div className="mt-4">
                  <div className="flex items-center justify-between text-sm mb-2">
                    <span className="text-slate-600 font-medium">AI Confidence</span>
                    <span className={`font-semibold ${
                      (request.ai_confidence_score || 0) >= 0.7
                        ? 'text-emerald-700'
                        : (request.ai_confidence_score || 0) >= 0.5
                          ? 'text-amber-700'
                          : 'text-red-700'
                    }`}>
                      {Math.round((request.ai_confidence_score || 0) * 100)}%
                    </span>
                  </div>
                  <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${
                        (request.ai_confidence_score || 0) >= 0.7
                          ? 'bg-emerald-500'
                          : (request.ai_confidence_score || 0) >= 0.5
                            ? 'bg-amber-500'
                            : 'bg-red-500'
                      }`}
                      style={{ width: `${(request.ai_confidence_score || 0) * 100}%` }}
                    />
                  </div>
                </div>
              )}
            </div>

            <Separator />

            {/* Email Body */}
            {request.body_text && (
              <div>
                <h4 className="font-semibold text-slate-900 mb-2 flex items-center">
                  <Mail className="w-4 h-4 mr-2" />
                  Email Content
                </h4>
                <div className="bg-slate-50 rounded-lg p-4 text-sm text-slate-700 whitespace-pre-wrap max-h-60 overflow-y-auto">
                  {request.body_text}
                </div>
              </div>
            )}

            {/* Attachments */}
            {request.attachments && request.attachments.length > 0 && (
              <div>
                <h4 className="font-semibold text-slate-900 mb-3 flex items-center">
                  <FileText className="w-4 h-4 mr-2" />
                  Attachments ({request.attachments.length})
                </h4>
                <div className="space-y-2">
                  {request.attachments.map((attachment) => (
                    <div
                      key={attachment.id}
                      className="flex items-center justify-between bg-slate-50 rounded-lg p-3 border border-slate-200"
                    >
                      <div className="flex items-center flex-1 min-w-0">
                        <FileText className="w-5 h-5 mr-3 text-slate-500 flex-shrink-0" />
                        <div className="min-w-0">
                          <div className="font-medium text-slate-900 truncate">
                            {attachment.filename}
                          </div>
                          <div className="text-xs text-slate-600">
                            {formatFileSize(attachment.file_size)}
                            {attachment.processed && (
                              <span className="ml-2 text-emerald-600">• Processed</span>
                            )}
                          </div>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="ml-3 flex-shrink-0"
                        onClick={() => {
                          // In a real implementation, this would download the file
                          console.log('Download attachment:', attachment.id)
                        }}
                      >
                        <Download className="w-4 h-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Extracted Requirements */}
            {request.extracted_requirements && (
              <div>
                <h4 className="font-semibold text-slate-900 mb-3 flex items-center">
                  <CheckCircle className="w-4 h-4 mr-2 text-emerald-600" />
                  AI Extracted Requirements
                </h4>
                <div className="bg-emerald-50 rounded-lg p-4 border border-emerald-200">
                  <pre className="text-sm text-slate-700 whitespace-pre-wrap max-h-60 overflow-y-auto">
                    {JSON.stringify(request.extracted_requirements, null, 2)}
                  </pre>
                </div>
              </div>
            )}

            {/* Quotation Link */}
            {request.quotation_id && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center text-blue-900">
                    <FileText className="w-5 h-5 mr-2" />
                    <span className="font-medium">Quotation Generated</span>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    className="border-blue-300 text-blue-700 hover:bg-blue-100"
                    onClick={() => {
                      window.location.href = `/quotations/${request.quotation_id}`
                    }}
                  >
                    View Quotation
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}

        <DialogFooter className="flex gap-2">
          {request && !loading && !request.quotation_id && (
            request.status === 'pending' || request.status === 'completed' ? (
              <>
                <Button
                  variant="outline"
                  onClick={handleIgnore}
                  disabled={ignoring}
                  className="border-red-200 text-red-700 hover:bg-red-50"
                >
                  {ignoring ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      Ignoring...
                    </>
                  ) : (
                    <>
                      <XCircle className="w-4 h-4 mr-2" />
                      Ignore Request
                    </>
                  )}
                </Button>
                <Button
                  onClick={handleProcess}
                  disabled={processing}
                  className="bg-gradient-to-r from-amber-600 to-red-600 hover:from-amber-700 hover:to-red-700"
                >
                  {processing ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <CheckCircle className="w-4 h-4 mr-2" />
                      Process Quotation
                    </>
                  )}
                </Button>
              </>
            ) : null
          )}
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
