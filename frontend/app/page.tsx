"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Header } from "@/components/header"
import { MetricsBar } from "@/components/metrics-bar"
import { DocumentUpload } from "@/components/document-upload"
import { ChatInterface } from "@/components/chat-interface"
import { ChatTabs, type ChatTab } from "@/components/chat-tabs"
import { NewQuotationRequests } from "@/components/new-quotation-requests"
import { QuotationPanel } from "@/components/quotation-panel"
import { FloatingChat } from "@/components/floating-chat"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { FileText, Loader2 } from "lucide-react"
import { apiClient } from "@/lib/api-client"

// Document names mapping
const documentNames: Record<string, string> = {
  "rfp-001": "Marina Corp RFP",
  "quote-002": "Workshop Equipment List",
  "order-003": "Plumbing Reorder",
  "quote-004": "Industrial Supplies Quote",
}

export default function SalesAssistantPortal() {
  const router = useRouter()

  // Authentication state
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isCheckingAuth, setIsCheckingAuth] = useState(true)

  // Tab management state
  const [chatTabs, setChatTabs] = useState<ChatTab[]>([])
  const [activeTabId, setActiveTabId] = useState<string | null>(null)

  const [selectedDocument, setSelectedDocument] = useState<string | null>(null)
  const [selectedRequest, setSelectedRequest] = useState<number | null>(null)

  // Check authentication on mount
  useEffect(() => {
    const checkAuth = () => {
      const token = localStorage.getItem('access_token')

      if (!token) {
        console.log('[Dashboard] No access token found, redirecting to login')
        router.push('/login')
        return
      }

      console.log('[Dashboard] User authenticated, setting token in apiClient')
      // CRITICAL: Set the token in apiClient so all API calls are authenticated
      apiClient.setAuthToken(token)

      setIsAuthenticated(true)
      setIsCheckingAuth(false)
    }

    checkAuth()
  }, [router])

  // Show loading screen while checking authentication
  if (isCheckingAuth) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-amber-50/20 to-red-50/10 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-amber-600 mx-auto animate-spin mb-4" />
          <p className="text-slate-600">Loading...</p>
        </div>
      </div>
    )
  }

  // Don't render dashboard if not authenticated (prevents flash of content)
  if (!isAuthenticated) {
    return null
  }

  const handleDocumentSelect = (documentId: string) => {
    setSelectedDocument(documentId)
  }

  const handleRequestSelect = (requestId: number) => {
    // For now, just log the selection
    // In future, this could open a detail modal or navigate to processing page
    console.log('Email quotation request selected:', requestId)
    // Optional: You can set state to show a detail modal here
    setSelectedRequest(requestId)
  }

  const handleDocumentClose = () => {
    setSelectedDocument(null)
  }

  const handleChatClose = () => {
    // For floating chat, we might want to keep it available
    // or close it completely based on UX preference
  }

  // Tab handlers
  const handleDocumentUploaded = (documentId: number, fileName: string) => {
    console.log('[Dashboard] Document uploaded:', documentId, fileName)

    // Create new tab
    const newTab: ChatTab = {
      id: `tab-${documentId}-${Date.now()}`,
      documentId,
      fileName
    }

    // Add tab and make it active
    setChatTabs(prev => [...prev, newTab])
    setActiveTabId(newTab.id)

    console.log('[Dashboard] Created new tab:', newTab.id)
  }

  const handleTabChange = (tabId: string) => {
    console.log('[Dashboard] Switching to tab:', tabId)
    setActiveTabId(tabId)
  }

  const handleTabClose = (tabId: string) => {
    console.log('[Dashboard] Closing tab:', tabId)

    setChatTabs(prev => {
      const filtered = prev.filter(tab => tab.id !== tabId)

      // If closing the active tab, switch to another tab or null
      if (activeTabId === tabId) {
        if (filtered.length > 0) {
          // Switch to the last tab
          setActiveTabId(filtered[filtered.length - 1].id)
        } else {
          // No tabs left
          setActiveTabId(null)
        }
      }

      return filtered
    })
  }

  const handleNewChat = () => {
    console.log('[Dashboard] Creating new empty chat')
    // For now, just clear active tab to show default chat
    setActiveTabId(null)
  }

  // Get active tab data
  const activeTab = chatTabs.find(tab => tab.id === activeTabId)

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-amber-50/20 to-red-50/10">
      <Header />

      <div className="max-w-[1600px] mx-auto px-6 py-8">
        <div className="flex justify-between items-center mb-8">
          <h2 className="text-2xl font-bold text-slate-900">Sales Assistant Dashboard</h2>
          <Link href="/documents">
            <Button className="bg-gradient-to-r from-amber-600 to-red-600 hover:from-amber-700 hover:to-red-700 shadow-lg">
              <FileText className="w-4 h-4 mr-2" />
              View All Documents
            </Button>
          </Link>
        </div>

        <MetricsBar />

        {selectedDocument ? (
          // Two-panel layout: Left (original) | Right (full quotation)
          <div className="grid grid-cols-12 gap-8 h-[700px]">
            {/* Left Panel - Original */}
            <div className="col-span-4 space-y-6">
              <DocumentUpload onDocumentUploaded={(documentId) => setSelectedDocument(documentId.toString())} />
              <NewQuotationRequests onRequestSelect={handleRequestSelect} />
            </div>

            {/* Right Panel - Full height quotation */}
            <div className="col-span-8">
              <QuotationPanel
                documentId={selectedDocument}
                onClose={handleDocumentClose}
                onRequestResize={() => {}} // No longer needed for floating chat
              />
            </div>
          </div>
        ) : (
          // Default dashboard layout
          <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">
            <div className="xl:col-span-4 space-y-6">
              <DocumentUpload onDocumentUploaded={handleDocumentUploaded} />
              <NewQuotationRequests
                onRequestSelect={handleRequestSelect}
                onDocumentUploaded={handleDocumentUploaded}
              />
            </div>

            <div className="xl:col-span-8">
              {/* Chat Tabs and Interface */}
              <div className="bg-white rounded-lg shadow-md overflow-hidden">
                {/* Show tabs only if there are tabs */}
                {chatTabs.length > 0 && (
                  <ChatTabs
                    tabs={chatTabs}
                    activeTabId={activeTabId}
                    onTabChange={handleTabChange}
                    onTabClose={handleTabClose}
                    onNewChat={handleNewChat}
                  />
                )}

                {/* Chat Interface */}
                <div className="p-4">
                  {activeTab ? (
                    <ChatInterface
                      key={activeTab.id}
                      documentId={activeTab.documentId.toString()}
                      documentName={activeTab.fileName}
                    />
                  ) : (
                    <ChatInterface key="default-chat" />
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Floating Chat - Always visible when document is selected */}
      {selectedDocument && (
        <FloatingChat
          documentId={selectedDocument}
          documentName={documentNames[selectedDocument]}
          onClose={handleChatClose}
        />
      )}
    </div>
  )
}
