"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { FileText, Download, Eye } from "lucide-react"

interface DocumentViewerProps {
  documentId: string
  onClose: () => void
}

export function DocumentViewer({ documentId, onClose }: DocumentViewerProps) {
  const [activeTab, setActiveTab] = useState<"content" | "details">("content")

  // Sample document data - in real app, fetch by documentId
  const document = {
    id: documentId,
    name: "Marina Corp RFP",
    type: "RFP",
    uploadDate: "2024-01-15",
    size: "2.4 MB",
    status: "processed",
    content: `
      REQUEST FOR PROPOSAL
      Marina Bay Dock Construction Project
      
      Project Overview:
      Marina Corp is seeking qualified suppliers for the complete hardware supply for our new marina dock construction project. This project involves the construction of a 200-meter floating dock system capable of accommodating vessels up to 50 feet in length.
      
      Required Materials:
      
      1. Marine Fasteners
         - Stainless steel bolts, M12x80mm (Quantity: 200)
         - Grade 316 stainless steel required for marine environment
         - Must meet ASTM A193 standards
      
      2. Corrosion-Resistant Hardware
         - Washers compatible with M12 bolts (Quantity: 400)
         - Marine-grade coating required
         - 25-year corrosion warranty preferred
      
      3. Safety Equipment
         - Coast Guard approved life rings with 30m rope (Quantity: 12)
         - Must meet USCG standards
         - High-visibility orange color required
      
      Technical Specifications:
      - All materials must be suitable for saltwater marine environment
      - Compliance with Singapore maritime safety standards required
      - Installation support may be required
      
      Project Timeline:
      - RFP Response Due: January 22, 2024
      - Project Start: February 1, 2024
      - Completion Required: March 15, 2024
      
      Budget: Estimated $45,000 - $50,000
      
      Contact Information:
      Sarah Johnson, Project Manager
      Marina Corp Pte Ltd
      Email: sarah.johnson@marinacorp.com
      Phone: +65 6123 4567
    `,
  }

  return (
    <div className="h-full flex flex-col bg-white border border-slate-200 rounded-xl shadow-lg">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-6 rounded-t-xl">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">{document.name}</h1>
            <p className="text-blue-100 text-sm">Document Viewer</p>
          </div>
          <div className="flex items-center space-x-4">
            <Badge className="bg-emerald-500 text-white">{document.status}</Badge>
            <Button variant="ghost" size="sm" onClick={onClose} className="hover:bg-white/20 text-white">
              ✕
            </Button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200">
        <div className="flex">
          <button
            onClick={() => setActiveTab("content")}
            className={`flex items-center space-x-2 py-4 px-6 border-b-2 font-medium transition-colors ${
              activeTab === "content"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-slate-600 hover:text-slate-900"
            }`}
          >
            <FileText className="w-5 h-5" />
            <span>Content</span>
          </button>
          <button
            onClick={() => setActiveTab("details")}
            className={`flex items-center space-x-2 py-4 px-6 border-b-2 font-medium transition-colors ${
              activeTab === "details"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-slate-600 hover:text-slate-900"
            }`}
          >
            <Eye className="w-5 h-5" />
            <span>Details</span>
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === "content" && (
          <div className="prose max-w-none">
            <pre className="whitespace-pre-wrap text-sm text-slate-700 leading-relaxed">{document.content}</pre>
          </div>
        )}

        {activeTab === "details" && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <FileText className="w-5 h-5 mr-2" />
                  Document Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-slate-600">Document Type</label>
                    <p className="text-slate-900">{document.type}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-slate-600">File Size</label>
                    <p className="text-slate-900">{document.size}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-slate-600">Upload Date</label>
                    <p className="text-slate-900">{new Date(document.uploadDate).toLocaleDateString()}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-slate-600">Status</label>
                    <Badge className="bg-emerald-100 text-emerald-800">{document.status}</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>

      {/* Footer Actions */}
      <div className="border-t border-slate-200 p-4">
        <div className="flex justify-between">
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
          <Button className="bg-blue-600 hover:bg-blue-700">
            <Download className="w-4 h-4 mr-2" />
            Download
          </Button>
        </div>
      </div>
    </div>
  )
}
