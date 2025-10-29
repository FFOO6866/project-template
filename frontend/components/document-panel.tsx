"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Textarea } from "@/components/ui/textarea"
import { FileText, Download, Eye, Calendar, User, X } from "lucide-react"

interface DocumentPanelProps {
  documentId: string
  onClose: () => void
}

export function DocumentPanel({ documentId, onClose }: DocumentPanelProps) {
  const [activeTab, setActiveTab] = useState<"overview" | "analysis" | "quote">("overview")
  const [isEditing, setIsEditing] = useState(false)
  const [notes, setNotes] = useState("")

  // Sample document data - in real app, fetch by documentId
  const document = {
    id: documentId,
    name: "Marina Corp RFP",
    type: "RFP",
    customer: "Marina Corp Pte Ltd",
    contact: "Sarah Johnson",
    uploadDate: "2024-01-15",
    size: "2.4 MB",
    status: "processed",
    summary:
      "Request for marine-grade hardware for dock construction project. Includes stainless steel fasteners, safety equipment, and corrosion-resistant components.",
    keyPoints: [
      "Marine-grade materials required",
      "316 stainless steel specification",
      "Coast Guard approved safety equipment",
      "Delivery within 3 weeks",
      "Installation support may be needed",
    ],
  }

  const sampleRFPData = {
    id: "rfp-001",
    name: "Marina Corp RFP",
    customer: {
      name: "Sarah Johnson",
      contact: "Project Manager",
      email: "sarah.johnson@marinacorp.com",
      phone: "+65 6123 4567",
      company: "Marina Corp Pte Ltd",
    },
    rfpDetails: {
      submittedDate: "2024-01-15",
      dueDate: "2024-01-22",
      projectName: "Marina Bay Dock Construction",
      description:
        "Complete hardware supply for new marina dock construction including marine-grade fasteners, safety equipment, and structural components.",
      estimatedValue: "$45,000",
      status: "completed",
    },
    requirements: [
      {
        category: "Marine Fasteners",
        items: [
          {
            description: "Stainless steel bolts, M12x80mm",
            quantity: 200,
            specifications: "316 grade stainless steel, marine environment",
            estimatedPrice: "$8,400",
            matchedProduct: "SS316 Hex Bolt M12x80",
            confidence: 95,
          },
          {
            description: "Corrosion-resistant washers",
            quantity: 400,
            specifications: "Compatible with M12 bolts, marine grade",
            estimatedPrice: "$1,200",
            matchedProduct: "SS316 Flat Washer M12",
            confidence: 92,
          },
        ],
      },
      {
        category: "Safety Equipment",
        items: [
          {
            description: "Life rings with rope",
            quantity: 12,
            specifications: "Coast guard approved, 30m rope",
            estimatedPrice: "$2,400",
            matchedProduct: 'Marine Life Ring 24" with 30m Rope',
            confidence: 88,
          },
        ],
      },
    ],
    aiAnalysis: {
      summary:
        "This RFP is for a marina construction project requiring marine-grade hardware. High-value opportunity with standard specifications.",
      keyRequirements: [
        "All materials must be marine-grade (saltwater resistant)",
        "Compliance with Singapore maritime safety standards",
        "Delivery required within 3 weeks",
        "Installation support may be needed",
      ],
      recommendations: [
        "Offer bulk discount for quantities over 100 units",
        "Suggest upgraded 316L stainless steel for better corrosion resistance",
        "Include installation service package",
        "Provide extended warranty for marine environment",
      ],
      riskFactors: [
        "Tight delivery timeline",
        "Weather-dependent installation",
        "Potential for scope changes during construction",
      ],
      totalEstimate: "$47,200",
    },
    generatedQuote: {
      items: [
        {
          product: "SS316 Hex Bolt M12x80",
          description: "Stainless steel bolts, marine grade",
          quantity: 200,
          unitPrice: "$42.00",
          totalPrice: "$8,400.00",
        },
        {
          product: "SS316 Flat Washer M12",
          description: "Stainless steel washers",
          quantity: 400,
          unitPrice: "$3.00",
          totalPrice: "$1,200.00",
        },
        {
          product: 'Marine Life Ring 24"',
          description: "Life ring with 30m rope",
          quantity: 12,
          unitPrice: "$200.00",
          totalPrice: "$2,400.00",
        },
      ],
      subtotal: "$12,000.00",
      discount: "$600.00 (5%)",
      tax: "$1,197.00",
      total: "$12,597.00",
      validUntil: "2024-02-15",
      terms: "Net 30 days, FOB Singapore",
    },
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-emerald-500"
      case "processing":
        return "bg-amber-600"
      case "sent":
        return "bg-blue-500"
      case "pending":
        return "bg-slate-500"
      default:
        return "bg-slate-500"
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 90) return "text-emerald-600 bg-emerald-100"
    if (confidence >= 75) return "text-amber-600 bg-amber-100"
    return "text-red-600 bg-red-100"
  }

  return (
    <div className="h-full flex flex-col bg-white border border-slate-200 rounded-xl shadow-lg">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-6 rounded-t-xl flex-shrink-0">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">{document.name}</h1>
            <p className="text-blue-100 text-sm">
              {document.type} • {document.size}
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <Badge className="bg-emerald-500 text-white">{document.status}</Badge>
            <Button variant="ghost" size="sm" onClick={onClose} className="h-8 w-8 p-0 hover:bg-white/20 text-white">
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* Document Info */}
        <Card className="border-slate-200">
          <CardHeader className="pb-4">
            <CardTitle className="flex items-center text-slate-900">
              <FileText className="w-5 h-5 mr-2" />
              Document Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center space-x-3">
                <User className="w-5 h-5 text-slate-400" />
                <div>
                  <p className="font-medium text-slate-900">{document.customer}</p>
                  <p className="text-slate-600 text-sm">{document.contact}</p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <Calendar className="w-5 h-5 text-slate-400" />
                <div>
                  <p className="font-medium text-slate-900">Uploaded</p>
                  <p className="text-slate-600 text-sm">{new Date(document.uploadDate).toLocaleDateString()}</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* AI Summary */}
        <Card className="border-slate-200">
          <CardHeader className="pb-4">
            <CardTitle className="text-slate-900">AI Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-slate-700 leading-relaxed mb-4">{document.summary}</p>
            <div>
              <h4 className="font-semibold text-slate-900 mb-3">Key Points:</h4>
              <ul className="space-y-2">
                {document.keyPoints.map((point, index) => (
                  <li key={index} className="flex items-start space-x-2">
                    <div className="w-2 h-2 bg-amber-600 rounded-full mt-2 flex-shrink-0"></div>
                    <span className="text-slate-700">{point}</span>
                  </li>
                ))}
              </ul>
            </div>
          </CardContent>
        </Card>

        {/* Navigation Tabs */}
        <div className="border-b border-slate-200 bg-white flex-shrink-0">
          <div className="flex">
            {[
              { id: "overview", label: "Overview", icon: FileText },
              { id: "analysis", label: "AI Analysis", icon: FileText },
              { id: "quote", label: "Quote", icon: FileText },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center space-x-2 py-3 px-4 border-b-2 font-medium transition-colors text-sm ${
                  activeTab === tab.id
                    ? "border-red-600 text-red-600 bg-red-50/50"
                    : "border-transparent text-slate-600 hover:text-slate-900 hover:bg-slate-50"
                }`}
              >
                <tab.icon className="w-4 h-4" />
                <span className="hidden sm:inline">{tab.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          <div className="p-4 space-y-4">
            {activeTab === "overview" && (
              <>
                {/* Customer Information */}
                <Card className="border-slate-200">
                  <CardHeader className="pb-3">
                    <CardTitle className="flex items-center text-slate-900 text-base">
                      <User className="w-4 h-4 mr-2 text-amber-600" />
                      Customer
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div>
                      <label className="text-xs font-medium text-slate-600 uppercase tracking-wide">Company</label>
                      <p className="text-slate-900 font-medium">{sampleRFPData.customer.company}</p>
                    </div>
                    <div>
                      <label className="text-xs font-medium text-slate-600 uppercase tracking-wide">Contact</label>
                      <p className="text-slate-900">{sampleRFPData.customer.name}</p>
                      <p className="text-slate-600 text-sm">{sampleRFPData.customer.contact}</p>
                    </div>
                    <div className="flex flex-col space-y-1">
                      <div className="flex items-center space-x-2">
                        <span className="text-slate-900 text-sm">{sampleRFPData.customer.email}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-slate-900 text-sm">{sampleRFPData.customer.phone}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* RFP Details */}
                <Card className="border-slate-200">
                  <CardHeader className="pb-3">
                    <CardTitle className="flex items-center text-slate-900 text-base">
                      <Calendar className="w-4 h-4 mr-2 text-amber-600" />
                      RFP Details
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-xs font-medium text-slate-600 uppercase tracking-wide">Submitted</label>
                        <p className="text-slate-900 text-sm">
                          {new Date(sampleRFPData.rfpDetails.submittedDate).toLocaleDateString()}
                        </p>
                      </div>
                      <div>
                        <label className="text-xs font-medium text-slate-600 uppercase tracking-wide">Due Date</label>
                        <p className="text-red-600 font-medium text-sm">
                          {new Date(sampleRFPData.rfpDetails.dueDate).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    <div>
                      <label className="text-xs font-medium text-slate-600 uppercase tracking-wide">Description</label>
                      <p className="text-slate-900 text-sm leading-relaxed">{sampleRFPData.rfpDetails.description}</p>
                    </div>
                  </CardContent>
                </Card>

                {/* Requirements */}
                <Card className="border-slate-200">
                  <CardHeader className="pb-3">
                    <CardTitle className="flex items-center text-slate-900 text-base">
                      <FileText className="w-4 h-4 mr-2 text-amber-600" />
                      Requirements
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {sampleRFPData.requirements.map((category, categoryIndex) => (
                      <div key={categoryIndex}>
                        <h4 className="font-semibold text-slate-900 mb-2 text-sm">{category.category}</h4>
                        <div className="space-y-2">
                          {category.items.map((item, itemIndex) => (
                            <div
                              key={itemIndex}
                              className="border border-slate-200 rounded-lg p-3 hover:bg-slate-50 transition-colors"
                            >
                              <div className="flex justify-between items-start mb-2">
                                <h5 className="font-medium text-slate-900 text-sm">{item.description}</h5>
                                <div className="flex items-center space-x-1">
                                  <span className="font-semibold text-slate-900 text-sm">{item.estimatedPrice}</span>
                                </div>
                              </div>
                              <div className="space-y-1 text-xs">
                                <div>
                                  <span className="text-slate-600">Qty:</span>
                                  <span className="ml-1 font-medium">{item.quantity}</span>
                                </div>
                                <div>
                                  <span className="text-slate-600">Specs:</span>
                                  <span className="ml-1">{item.specifications}</span>
                                </div>
                                {item.matchedProduct && (
                                  <div>
                                    <span className="text-slate-600">Match:</span>
                                    <span className="ml-1 text-amber-700 font-medium">{item.matchedProduct}</span>
                                  </div>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              </>
            )}

            {activeTab === "analysis" && (
              <>
                {/* AI Summary */}
                <Card className="border-slate-200">
                  <CardHeader className="pb-4">
                    <CardTitle className="flex items-center text-slate-900">
                      <FileText className="w-5 h-5 mr-2" />
                      AI Summary
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-slate-700 leading-relaxed mb-4">{sampleRFPData.aiAnalysis.summary}</p>
                    <div>
                      <h4 className="font-semibold text-slate-900 mb-3">Key Requirements:</h4>
                      <ul className="space-y-2">
                        {sampleRFPData.aiAnalysis.keyRequirements.map((req, index) => (
                          <li key={index} className="flex items-start space-x-2">
                            <div className="w-2 h-2 bg-amber-600 rounded-full mt-2 flex-shrink-0"></div>
                            <span className="text-slate-700">{req}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-semibold text-slate-900 mb-3">Recommendations:</h4>
                      <ul className="space-y-2">
                        {sampleRFPData.aiAnalysis.recommendations.map((rec, index) => (
                          <li key={index} className="flex items-start space-x-2">
                            <div className="w-2 h-2 bg-blue-600 rounded-full mt-2 flex-shrink-0"></div>
                            <span className="text-slate-700">{rec}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-semibold text-slate-900 mb-3">Risk Factors:</h4>
                      <ul className="space-y-2">
                        {sampleRFPData.aiAnalysis.riskFactors.map((risk, index) => (
                          <li key={index} className="flex items-start space-x-2">
                            <div className="w-2 h-2 bg-red-600 rounded-full mt-2 flex-shrink-0"></div>
                            <span className="text-slate-700">{risk}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </CardContent>
                </Card>
              </>
            )}

            {activeTab === "quote" && (
              <>
                {/* Quote Items */}
                <Card className="border-slate-200">
                  <CardHeader className="pb-4">
                    <CardTitle className="flex items-center justify-between text-slate-900 text-base">
                      <span className="flex items-center">
                        <FileText className="w-5 h-5 mr-2 text-amber-600" />
                        Generated Quote
                      </span>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setIsEditing(!isEditing)}
                        className="border-amber-200 text-amber-700 hover:bg-amber-50 h-7 text-xs"
                      >
                        Edit
                      </Button>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {sampleRFPData.generatedQuote.items.map((item, index) => (
                        <div key={index} className="border border-slate-200 rounded-lg p-3">
                          <div className="flex justify-between items-start mb-2">
                            <div className="flex-1">
                              <h5 className="font-medium text-slate-900 text-sm">{item.product}</h5>
                              <p className="text-slate-600 text-xs">{item.description}</p>
                            </div>
                            <div className="text-right">
                              <div className="font-semibold text-slate-900 text-sm">{item.totalPrice}</div>
                              <div className="text-slate-600 text-xs">
                                {item.quantity} × {item.unitPrice}
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Quote Summary */}
                    <div className="mt-4 border-t border-slate-200 pt-4">
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-slate-600">Subtotal:</span>
                          <span className="text-slate-900">{sampleRFPData.generatedQuote.subtotal}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-600">Discount:</span>
                          <span className="text-emerald-600">-{sampleRFPData.generatedQuote.discount}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-600">Tax (GST):</span>
                          <span className="text-slate-900">{sampleRFPData.generatedQuote.tax}</span>
                        </div>
                        <div className="flex justify-between border-t border-slate-200 pt-2 font-bold">
                          <span className="text-slate-900">Total:</span>
                          <span className="text-red-600">{sampleRFPData.generatedQuote.total}</span>
                        </div>
                      </div>
                    </div>

                    {/* Terms */}
                    <div className="mt-4 p-3 bg-slate-50 rounded-lg">
                      <h4 className="font-medium text-slate-900 mb-1 text-sm">Terms & Conditions</h4>
                      <p className="text-slate-700 text-xs">
                        Valid until: {new Date(sampleRFPData.generatedQuote.validUntil).toLocaleDateString()}
                      </p>
                      <p className="text-slate-700 text-xs">Payment: {sampleRFPData.generatedQuote.terms}</p>
                    </div>
                  </CardContent>
                </Card>

                {/* Notes Section */}
                <Card className="border-slate-200">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-slate-900 text-base">Sales Notes</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <Textarea
                      placeholder="Add notes about this RFP..."
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                      className="min-h-[80px] border-slate-200 focus:border-red-400 focus:ring-red-400/20 text-sm"
                    />
                  </CardContent>
                </Card>
              </>
            )}
          </div>
        </div>

        {/* Footer Actions */}
        <div className="border-t border-slate-200 p-4 flex-shrink-0">
          <div className="flex justify-between">
            <Button variant="outline" onClick={onClose}>
              Close
            </Button>
            <div className="flex space-x-2">
              <Button variant="outline">
                <Eye className="w-4 h-4 mr-2" />
                View Full
              </Button>
              <Button className="bg-blue-600 hover:bg-blue-700">
                <Download className="w-4 h-4 mr-2" />
                Download
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
