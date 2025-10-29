"use client"

import { useState, useEffect, Suspense } from "react"
import { useSearchParams } from "next/navigation"
import { ChatInterface } from "@/components/chat-interface"
import { Header } from "@/components/header"
import { apiClient } from "@/lib/api-client"
import { Loader2, AlertCircle } from "lucide-react"

function ChatPageContent() {
  const searchParams = useSearchParams()
  const documentId = searchParams.get('documentId')
  const fileName = searchParams.get('fileName')
  const emailRequestId = searchParams.get('emailRequestId')
  const emailSubject = searchParams.get('subject')

  const [contextName, setContextName] = useState<string | null>(fileName || emailSubject)
  const [contextType, setContextType] = useState<'document' | 'email' | null>(
    emailRequestId ? 'email' : documentId ? 'document' : null
  )
  const [loading, setLoading] = useState(!!(documentId || emailRequestId))
  const [error, setError] = useState<string | null>(null)

  // Fetch context details from API
  useEffect(() => {
    async function fetchContext() {
      setLoading(true)

      // Handle email quotation request
      if (emailRequestId) {
        try {
          setError(null)
          // Fetch real email request from API - NO MOCK DATA
          const emailRequest = await apiClient.getEmailQuotationRequest(parseInt(emailRequestId))

          setContextName(emailRequest.subject || emailSubject || 'Email Quotation Request')
          setContextType('email')
          setLoading(false)
        } catch (err: any) {
          console.error('Failed to fetch email request:', err)
          setError('Could not load email details')
          setContextName(emailSubject || 'Email Quotation Request')
          setContextType('email')
          setLoading(false)
        }
        return
      }

      // Handle document upload
      if (documentId) {
        try {
          setError(null)
          // Fetch real document from API - NO MOCK DATA
          const document = await apiClient.getDocument(parseInt(documentId))

          setContextName(document.name || fileName || 'Document')
          setContextType('document')
          setLoading(false)
        } catch (err: any) {
          console.error('Failed to fetch document details:', err)
          setError('Could not load document details')
          setContextName(fileName || 'Document')
          setContextType('document')
          setLoading(false)
        }
        return
      }

      // No context
      setLoading(false)
    }

    fetchContext()
  }, [documentId, fileName, emailRequestId, emailSubject])

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-amber-50/20 to-red-50/10">
      <Header />

      <div className="max-w-[1600px] mx-auto px-6 py-8">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-slate-900">AI Sales Assistant</h2>
          {contextType === 'email' && contextName ? (
            <p className="text-slate-600">
              Processing email quotation: <span className="font-semibold text-amber-700">{contextName}</span>
            </p>
          ) : contextType === 'document' && contextName ? (
            <p className="text-slate-600">
              Discussing quotation for: <span className="font-semibold text-amber-700">{contextName}</span>
            </p>
          ) : (
            <p className="text-slate-600">Chat with your AI assistant about products, quotes, and customers</p>
          )}
        </div>

        {error && (
          <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-start">
            <AlertCircle className="w-5 h-5 text-amber-600 mr-2 flex-shrink-0 mt-0.5" />
            <p className="text-amber-700 text-sm">{error}</p>
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 text-amber-600 animate-spin mr-3" />
            <p className="text-slate-600">
              Loading {contextType === 'email' ? 'email request' : 'document'} details...
            </p>
          </div>
        ) : (
          <ChatInterface
            documentId={documentId || emailRequestId || undefined}
            documentName={contextName || undefined}
            emailRequestId={emailRequestId ? parseInt(emailRequestId) : undefined}
          />
        )}
      </div>
    </div>
  )
}

export default function ChatPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-amber-50/20 to-red-50/10">
        <Header />
        <div className="max-w-[1600px] mx-auto px-6 py-8">
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 text-amber-600 animate-spin mr-3" />
            <p className="text-slate-600">Loading chat...</p>
          </div>
        </div>
      </div>
    }>
      <ChatPageContent />
    </Suspense>
  )
}
