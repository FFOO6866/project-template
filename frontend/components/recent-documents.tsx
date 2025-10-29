"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { FileText, Calendar, User, Eye } from "lucide-react"

interface RecentDocumentsProps {
  onDocumentSelect: (documentId: string) => void
}

export function RecentDocuments({ onDocumentSelect }: RecentDocumentsProps) {
  const recentDocuments = [
    {
      id: "rfp-001",
      name: "Marina Corp RFP",
      type: "RFP",
      customer: "Marina Corp",
      date: "2024-01-15",
      status: "completed",
      value: "$47,200",
    },
    {
      id: "quote-002",
      name: "Workshop Equipment List",
      type: "Quote Request",
      customer: "TechCorp",
      date: "2024-01-14",
      status: "processing",
      value: "$23,500",
    },
    {
      id: "order-003",
      name: "Plumbing Reorder",
      type: "Purchase Order",
      customer: "BuildRight",
      date: "2024-01-13",
      status: "sent",
      value: "$8,900",
    },
    {
      id: "quote-004",
      name: "Industrial Supplies Quote",
      type: "RFQ",
      customer: "Manufacturing Plus",
      date: "2024-01-12",
      status: "pending",
      value: "$65,400",
    },
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-emerald-100 text-emerald-800"
      case "processing":
        return "bg-amber-100 text-amber-800"
      case "sent":
        return "bg-blue-100 text-blue-800"
      case "pending":
        return "bg-slate-100 text-slate-800"
      default:
        return "bg-slate-100 text-slate-800"
    }
  }

  return (
    <Card className="border-slate-200 hover:shadow-md transition-shadow">
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center text-slate-900">
          <FileText className="w-5 h-5 mr-2 text-amber-600" />
          Recent Documents
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {recentDocuments.map((doc) => (
            <div
              key={doc.id}
              className="border border-slate-200 rounded-lg p-4 hover:bg-slate-50 transition-colors cursor-pointer"
              onClick={() => onDocumentSelect(doc.id)}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1 min-w-0">
                  <h4 className="font-semibold text-slate-900 truncate">{doc.name}</h4>
                  <p className="text-sm text-slate-600">{doc.type}</p>
                </div>
                <Badge className={getStatusColor(doc.status)}>{doc.status}</Badge>
              </div>

              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center space-x-4 text-slate-600">
                  <div className="flex items-center space-x-1">
                    <User className="w-4 h-4" />
                    <span>{doc.customer}</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Calendar className="w-4 h-4" />
                    <span>{new Date(doc.date).toLocaleDateString()}</span>
                  </div>
                </div>
                <span className="font-semibold text-amber-600">{doc.value}</span>
              </div>

              <div className="mt-3 pt-3 border-t border-slate-200">
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full border-amber-200 text-amber-700 hover:bg-amber-50 bg-transparent"
                  onClick={(e) => {
                    e.stopPropagation()
                    onDocumentSelect(doc.id)
                  }}
                >
                  <Eye className="w-4 h-4 mr-2" />
                  View Details
                </Button>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
