"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Mail, Calendar, User, FileText, CheckCircle, XCircle, RefreshCw, AlertCircle } from "lucide-react"
import { apiClient } from "@/lib/api-client"
import type { EmailQuotationRequestResponse } from "@/lib/api-types"
import { EmailQuotationDetailModal } from "@/components/email-quotation-detail-modal"

interface NewQuotationRequestsProps {
  onRequestSelect?: (requestId: number) => void
  onDocumentUploaded?: (documentId: number, fileName: string) => void
}

export function NewQuotationRequests({ onRequestSelect, onDocumentUploaded }: NewQuotationRequestsProps) {
  const [requests, setRequests] = useState<EmailQuotationRequestResponse[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [processingId, setProcessingId] = useState<number | null>(null)
  const [ignoringId, setIgnoringId] = useState<number | null>(null)
  const [selectedRequestId, setSelectedRequestId] = useState<number | null>(null)
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false)

  // Fetch email quotation requests from API
  const fetchRequests = async () => {
    try {
      setError(null)
      const data = await apiClient.getEmailQuotationRequests(20)
      setRequests(data)
    } catch (err: any) {
      console.error('Failed to fetch email quotation requests:', err)
      setError(err.message || 'Failed to load quotation requests')
    } finally {
      setLoading(false)
    }
  }

  // Initial load
  useEffect(() => {
    fetchRequests()

    // Auto-refresh every 60 seconds
    const interval = setInterval(() => {
      fetchRequests()
    }, 60000) // 60 seconds

    return () => clearInterval(interval)
  }, [])

  // Handle "Process Quotation" button click
  const handleProcessQuotation = async (requestId: number, e: React.MouseEvent) => {
    e.stopPropagation() // Prevent triggering row click

    if (processingId !== null) return // Prevent multiple simultaneous processing

    try {
      setProcessingId(requestId)
      setError(null)

      // Find the request to get subject for filename
      const request = requests.find(r => r.id === requestId)
      const fileName = request ? `Email: ${request.subject}` : `Email Request ${requestId}`

      // Trigger quotation generation
      const response = await apiClient.processEmailQuotationRequest(requestId)

      console.log('[NewQuotationRequests] Quotation processing started:', response)

      // Open new tab with the document (like document upload does)
      if (response.document_id && onDocumentUploaded) {
        console.log('[NewQuotationRequests] Opening new tab for document:', response.document_id, fileName)
        onDocumentUploaded(response.document_id, fileName)
      }

      // Refresh the list to get updated status
      await fetchRequests()
    } catch (err: any) {
      console.error('Failed to process quotation:', err)
      setError(err.message || 'Failed to process quotation request')
    } finally {
      setProcessingId(null)
    }
  }

  // Handle "Ignore" button click
  const handleIgnoreRequest = async (requestId: number, e: React.MouseEvent) => {
    e.stopPropagation() // Prevent triggering row click

    if (ignoringId !== null) return // Prevent multiple simultaneous ignoring

    try {
      setIgnoringId(requestId)
      setError(null)

      // Update status to 'ignored'
      await apiClient.updateEmailQuotationRequestStatus(requestId, {
        status: 'ignored',
        notes: 'Ignored by user from dashboard'
      })

      console.log('Request ignored:', requestId)

      // Refresh the list to remove the ignored request
      await fetchRequests()
    } catch (err: any) {
      console.error('Failed to ignore request:', err)
      setError(err.message || 'Failed to ignore request')
    } finally {
      setIgnoringId(null)
    }
  }

  // Handle request row click - open new tab for AI processing
  const handleRequestClick = (requestId: number) => {
    // Find the request details
    const request = requests.find(r => r.id === requestId)
    if (!request) return

    // Open new tab with email request context for AI processing
    window.open(
      `/chat?emailRequestId=${requestId}&subject=${encodeURIComponent(request.subject)}`,
      '_blank'
    )

    onRequestSelect?.(requestId)
  }

  // Handle modal close
  const handleModalClose = () => {
    setIsModalOpen(false)
    setSelectedRequestId(null)
  }

  // Handle successful processing from modal
  const handleProcessSuccess = () => {
    fetchRequests() // Refresh the list
  }

  // Handle successful ignore from modal
  const handleIgnoreSuccess = () => {
    fetchRequests() // Refresh the list
  }

  // Get status badge color
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

  // Get status display text
  const getStatusText = (status: string) => {
    switch (status) {
      case "quotation_created":
        return "Quotation Ready"
      case "quotation_processing":
        return "Processing"
      default:
        return status.charAt(0).toUpperCase() + status.slice(1)
    }
  }

  // Format AI confidence score
  const formatConfidence = (score?: number) => {
    if (score === undefined || score === null) return "N/A"
    return `${Math.round(score * 100)}%`
  }

  // Format date
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  if (loading) {
    return (
      <Card className="border-slate-200 flex flex-col h-[calc(100vh-28rem)] min-h-[400px] max-h-[700px]">
        <CardHeader className="pb-3 px-4 py-3 flex-shrink-0">
          <CardTitle className="flex items-center text-slate-900 text-base">
            <Mail className="w-4 h-4 mr-2 text-amber-600" />
            Inbound Quotation Requests
          </CardTitle>
        </CardHeader>
        <CardContent className="px-4 pb-4 flex-1 flex items-center justify-center">
          <div className="flex items-center text-slate-500 text-sm">
            <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
            Loading requests...
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="border-slate-200 flex flex-col h-[calc(100vh-28rem)] min-h-[400px] max-h-[700px]">
        <CardHeader className="pb-3 px-4 py-3 flex-shrink-0">
          <CardTitle className="flex items-center text-slate-900 text-base">
            <Mail className="w-4 h-4 mr-2 text-amber-600" />
            Inbound Quotation Requests
          </CardTitle>
        </CardHeader>
        <CardContent className="px-4 pb-4 flex-1 flex flex-col items-center justify-center">
          <div className="flex items-center text-red-600 text-sm mb-3">
            <AlertCircle className="w-4 h-4 mr-2" />
            {error}
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => fetchRequests()}
            className="border-amber-200 text-amber-700 hover:bg-amber-50 text-xs"
          >
            <RefreshCw className="w-3 h-3 mr-2" />
            Retry
          </Button>
        </CardContent>
      </Card>
    )
  }

  if (requests.length === 0) {
    return (
      <Card className="border-slate-200 flex flex-col h-[calc(100vh-28rem)] min-h-[400px] max-h-[700px]">
        <CardHeader className="pb-3 px-4 py-3 flex-shrink-0">
          <CardTitle className="flex items-center text-slate-900 text-base">
            <Mail className="w-4 h-4 mr-2 text-amber-600" />
            Inbound Quotation Requests
          </CardTitle>
        </CardHeader>
        <CardContent className="px-4 pb-4 flex-1 flex flex-col items-center justify-center">
          <Mail className="w-8 h-8 mb-2 text-slate-300" />
          <p className="text-xs text-slate-500">No inbound quotation requests</p>
          <p className="text-xs mt-1 text-slate-400">Email requests will appear here automatically</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="border-slate-200 hover:shadow-md transition-shadow flex flex-col h-[calc(100vh-28rem)] min-h-[400px] max-h-[700px]">
      <CardHeader className="pb-3 px-4 py-3 flex-shrink-0">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center text-slate-900 text-base">
            <Mail className="w-4 h-4 mr-2 text-amber-600" />
            Inbound Quotation Requests
          </CardTitle>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => fetchRequests()}
            className="text-slate-500 hover:text-slate-700 h-6 w-6 p-0"
          >
            <RefreshCw className="w-3 h-3" />
          </Button>
        </div>
        <p className="text-xs text-slate-400 mt-0.5">
          Auto-refreshes every 60 seconds
        </p>
      </CardHeader>
      <CardContent className="px-4 pb-4 flex-1 overflow-hidden">
        <div className="space-y-3 h-full overflow-y-auto pr-2">
          {requests.map((request) => (
            <div
              key={request.id}
              className="border border-slate-200 rounded-lg p-3 hover:bg-slate-50 transition-colors cursor-pointer"
              onClick={() => handleRequestClick(request.id)}
            >
              {/* Header with subject and status */}
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1 min-w-0 mr-2">
                  <h4 className="font-semibold text-slate-900 truncate text-sm">
                    {request.subject}
                  </h4>
                  <p className="text-xs text-slate-600 mt-0.5 flex items-center">
                    <User className="w-3 h-3 mr-1" />
                    {request.sender_name || request.sender_email}
                  </p>
                </div>
                <Badge className={`${getStatusColor(request.status)} text-xs`}>
                  {getStatusText(request.status)}
                </Badge>
              </div>

              {/* Details row */}
              <div className="flex items-center justify-between text-xs mb-2">
                <div className="flex items-center space-x-3 text-slate-600">
                  <div className="flex items-center space-x-1">
                    <Mail className="w-3 h-3" />
                    <span className="truncate max-w-[120px]">{request.sender_email}</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Calendar className="w-3 h-3" />
                    <span>{formatDate(request.received_date)}</span>
                  </div>
                  {request.attachment_count > 0 && (
                    <div className="flex items-center space-x-1">
                      <FileText className="w-3 h-3" />
                      <span>{request.attachment_count} attachment{request.attachment_count > 1 ? 's' : ''}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* AI Confidence Score */}
              {request.ai_confidence_score !== undefined && request.ai_confidence_score !== null && (
                <div className="mb-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-500">AI Confidence</span>
                    <span className={`font-medium ${
                      (request.ai_confidence_score || 0) >= 0.7
                        ? 'text-emerald-700'
                        : (request.ai_confidence_score || 0) >= 0.5
                          ? 'text-amber-700'
                          : 'text-red-700'
                    }`}>
                      {formatConfidence(request.ai_confidence_score)}
                    </span>
                  </div>
                  <div className="mt-1 h-1 bg-slate-200 rounded-full overflow-hidden">
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

              {/* Action buttons */}
              <div className="mt-2 pt-2 border-t border-slate-200 flex gap-2">
                {request.quotation_id ? (
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1 border-blue-200 text-blue-700 hover:bg-blue-50 bg-transparent text-xs"
                    onClick={(e) => {
                      e.stopPropagation()
                      // Navigate to quotation view
                      window.location.href = `/quotations/${request.quotation_id}`
                    }}
                  >
                    <FileText className="w-3 h-3 mr-1" />
                    View Quotation
                  </Button>
                ) : request.status === 'pending' || request.status === 'completed' ? (
                  <>
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1 border-emerald-200 text-emerald-700 hover:bg-emerald-50 bg-transparent text-xs"
                      onClick={(e) => handleProcessQuotation(request.id, e)}
                      disabled={processingId === request.id}
                    >
                      {processingId === request.id ? (
                        <>
                          <RefreshCw className="w-3 h-3 mr-1 animate-spin" />
                          Processing...
                        </>
                      ) : (
                        <>
                          <CheckCircle className="w-3 h-3 mr-1" />
                          Process Quotation
                        </>
                      )}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1 border-red-200 text-red-700 hover:bg-red-50 bg-transparent text-xs"
                      onClick={(e) => handleIgnoreRequest(request.id, e)}
                      disabled={ignoringId === request.id}
                    >
                      {ignoringId === request.id ? (
                        <>
                          <RefreshCw className="w-3 h-3 mr-1 animate-spin" />
                          Ignoring...
                        </>
                      ) : (
                        <>
                          <XCircle className="w-3 h-3 mr-1" />
                          Ignore
                        </>
                      )}
                    </Button>
                  </>
                ) : (
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full border-amber-200 text-amber-700 hover:bg-amber-50 bg-transparent text-xs"
                    disabled
                  >
                    <AlertCircle className="w-3 h-3 mr-1" />
                    {getStatusText(request.status)}
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>
      </CardContent>

      {/* Detail Modal */}
      <EmailQuotationDetailModal
        requestId={selectedRequestId}
        isOpen={isModalOpen}
        onClose={handleModalClose}
        onProcessSuccess={handleProcessSuccess}
        onIgnoreSuccess={handleIgnoreSuccess}
      />
    </Card>
  )
}
