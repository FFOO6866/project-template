"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Textarea } from "@/components/ui/textarea"
import {
  FileText,
  Download,
  Send,
  Edit3,
  CheckCircle,
  User,
  Calendar,
  DollarSign,
  Phone,
  Mail,
  ArrowLeft,
  MessageSquare,
  AlertCircle,
} from "lucide-react"

interface RFPData {
  id: string
  name: string
  customer: {
    name: string
    contact: string
    email: string
    phone: string
    company: string
  }
  rfpDetails: {
    submittedDate: string
    dueDate: string
    projectName: string
    description: string
    estimatedValue: string
    status: "processing" | "completed" | "sent" | "pending"
  }
  requirements: {
    category: string
    items: {
      description: string
      quantity: number
      specifications: string
      estimatedPrice: string
      matchedProduct?: string
      confidence: number
    }[]
  }[]
  aiAnalysis: {
    summary: string
    keyRequirements: string[]
    recommendations: string[]
    riskFactors: string[]
    totalEstimate: string
  }
  generatedQuote: {
    items: {
      product: string
      description: string
      quantity: number
      unitPrice: string
      totalPrice: string
    }[]
    subtotal: string
    discount: string
    tax: string
    total: string
    validUntil: string
    terms: string
  }
}

const sampleRFPData: RFPData = {
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

interface RFPViewerProps {
  rfpId: string
  onClose: () => void
}

export function RFPViewer({ rfpId, onClose }: RFPViewerProps) {
  const [activeTab, setActiveTab] = useState<"overview" | "analysis" | "quote">("overview")
  const [isEditing, setIsEditing] = useState(false)
  const [notes, setNotes] = useState("")

  const data = sampleRFPData // In real app, fetch by rfpId

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
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-amber-600 to-red-600 text-white p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Button variant="ghost" size="sm" onClick={onClose} className="text-white hover:bg-white/20 rounded-xl">
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back
              </Button>
              <div>
                <h1 className="text-2xl font-bold">{data.name}</h1>
                <p className="text-amber-100">{data.rfpDetails.projectName}</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <Badge className={`${getStatusColor(data.rfpDetails.status)} text-white capitalize`}>
                {data.rfpDetails.status}
              </Badge>
              <div className="text-right">
                <div className="text-2xl font-bold">{data.aiAnalysis.totalEstimate}</div>
                <div className="text-amber-100 text-sm">Estimated Value</div>
              </div>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="border-b border-slate-200 bg-slate-50">
          <div className="flex space-x-8 px-6">
            {[
              { id: "overview", label: "Overview", icon: FileText },
              { id: "analysis", label: "AI Analysis", icon: MessageSquare },
              { id: "quote", label: "Generated Quote", icon: DollarSign },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center space-x-2 py-4 px-2 border-b-2 font-medium transition-colors ${
                  activeTab === tab.id
                    ? "border-red-600 text-red-600"
                    : "border-transparent text-slate-600 hover:text-slate-900"
                }`}
              >
                <tab.icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {activeTab === "overview" && (
            <div className="space-y-6">
              {/* Customer Information */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center text-slate-900">
                    <User className="w-5 h-5 mr-2 text-amber-600" />
                    Customer Information
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-6">
                    <div className="space-y-4">
                      <div>
                        <label className="text-sm font-medium text-slate-600">Company</label>
                        <p className="text-slate-900 font-medium">{data.customer.company}</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-slate-600">Contact Person</label>
                        <p className="text-slate-900">{data.customer.name}</p>
                        <p className="text-slate-600 text-sm">{data.customer.contact}</p>
                      </div>
                    </div>
                    <div className="space-y-4">
                      <div className="flex items-center space-x-2">
                        <Mail className="w-4 h-4 text-slate-400" />
                        <span className="text-slate-900">{data.customer.email}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Phone className="w-4 h-4 text-slate-400" />
                        <span className="text-slate-900">{data.customer.phone}</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* RFP Details */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center text-slate-900">
                    <Calendar className="w-5 h-5 mr-2 text-amber-600" />
                    RFP Details
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-6 mb-4">
                    <div>
                      <label className="text-sm font-medium text-slate-600">Submitted Date</label>
                      <p className="text-slate-900">{new Date(data.rfpDetails.submittedDate).toLocaleDateString()}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-slate-600">Due Date</label>
                      <p className="text-slate-900 font-medium text-red-600">
                        {new Date(data.rfpDetails.dueDate).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-slate-600">Project Description</label>
                    <p className="text-slate-900 mt-1">{data.rfpDetails.description}</p>
                  </div>
                </CardContent>
              </Card>

              {/* Requirements */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center text-slate-900">
                    <CheckCircle className="w-5 h-5 mr-2 text-amber-600" />
                    Requirements Breakdown
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    {data.requirements.map((category, categoryIndex) => (
                      <div key={categoryIndex}>
                        <h4 className="font-semibold text-slate-900 mb-3">{category.category}</h4>
                        <div className="space-y-3">
                          {category.items.map((item, itemIndex) => (
                            <div
                              key={itemIndex}
                              className="border border-slate-200 rounded-lg p-4 hover:bg-slate-50 transition-colors"
                            >
                              <div className="flex justify-between items-start mb-2">
                                <h5 className="font-medium text-slate-900">{item.description}</h5>
                                <div className="flex items-center space-x-2">
                                  <Badge className={`text-xs ${getConfidenceColor(item.confidence)}`}>
                                    {item.confidence}% match
                                  </Badge>
                                  <span className="font-semibold text-slate-900">{item.estimatedPrice}</span>
                                </div>
                              </div>
                              <div className="grid grid-cols-3 gap-4 text-sm">
                                <div>
                                  <span className="text-slate-600">Quantity:</span>
                                  <span className="ml-2 font-medium">{item.quantity}</span>
                                </div>
                                <div>
                                  <span className="text-slate-600">Specifications:</span>
                                  <span className="ml-2">{item.specifications}</span>
                                </div>
                                {item.matchedProduct && (
                                  <div>
                                    <span className="text-slate-600">Matched Product:</span>
                                    <span className="ml-2 text-amber-700 font-medium">{item.matchedProduct}</span>
                                  </div>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {activeTab === "analysis" && (
            <div className="space-y-6">
              {/* AI Summary */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center text-slate-900">
                    <MessageSquare className="w-5 h-5 mr-2 text-amber-600" />
                    AI Analysis Summary
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-slate-700 leading-relaxed">{data.aiAnalysis.summary}</p>
                </CardContent>
              </Card>

              {/* Key Requirements */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-slate-900">Key Requirements</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {data.aiAnalysis.keyRequirements.map((req, index) => (
                      <li key={index} className="flex items-start space-x-2">
                        <CheckCircle className="w-4 h-4 text-emerald-500 mt-0.5 flex-shrink-0" />
                        <span className="text-slate-700">{req}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>

              {/* Recommendations */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-slate-900">AI Recommendations</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {data.aiAnalysis.recommendations.map((rec, index) => (
                      <li key={index} className="flex items-start space-x-2">
                        <div className="w-4 h-4 bg-amber-100 rounded-full flex items-center justify-center mt-0.5 flex-shrink-0">
                          <div className="w-2 h-2 bg-amber-600 rounded-full"></div>
                        </div>
                        <span className="text-slate-700">{rec}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>

              {/* Risk Factors */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center text-slate-900">
                    <AlertCircle className="w-5 h-5 mr-2 text-red-600" />
                    Risk Factors
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {data.aiAnalysis.riskFactors.map((risk, index) => (
                      <li key={index} className="flex items-start space-x-2">
                        <AlertCircle className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />
                        <span className="text-slate-700">{risk}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            </div>
          )}

          {activeTab === "quote" && (
            <div className="space-y-6">
              {/* Quote Items */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between text-slate-900">
                    <span className="flex items-center">
                      <DollarSign className="w-5 h-5 mr-2 text-amber-600" />
                      Generated Quote
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setIsEditing(!isEditing)}
                      className="border-amber-200 text-amber-700 hover:bg-amber-50"
                    >
                      <Edit3 className="w-4 h-4 mr-2" />
                      {isEditing ? "Save Changes" : "Edit Quote"}
                    </Button>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-slate-200">
                          <th className="text-left py-3 text-slate-600 font-medium">Product</th>
                          <th className="text-left py-3 text-slate-600 font-medium">Description</th>
                          <th className="text-center py-3 text-slate-600 font-medium">Qty</th>
                          <th className="text-right py-3 text-slate-600 font-medium">Unit Price</th>
                          <th className="text-right py-3 text-slate-600 font-medium">Total</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.generatedQuote.items.map((item, index) => (
                          <tr key={index} className="border-b border-slate-100">
                            <td className="py-3 font-medium text-slate-900">{item.product}</td>
                            <td className="py-3 text-slate-700">{item.description}</td>
                            <td className="py-3 text-center text-slate-900">{item.quantity}</td>
                            <td className="py-3 text-right text-slate-900">{item.unitPrice}</td>
                            <td className="py-3 text-right font-medium text-slate-900">{item.totalPrice}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Quote Summary */}
                  <div className="mt-6 border-t border-slate-200 pt-4">
                    <div className="flex justify-end">
                      <div className="w-64 space-y-2">
                        <div className="flex justify-between">
                          <span className="text-slate-600">Subtotal:</span>
                          <span className="text-slate-900">{data.generatedQuote.subtotal}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-600">Discount:</span>
                          <span className="text-emerald-600">-{data.generatedQuote.discount}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-600">Tax (GST):</span>
                          <span className="text-slate-900">{data.generatedQuote.tax}</span>
                        </div>
                        <div className="flex justify-between border-t border-slate-200 pt-2 font-bold text-lg">
                          <span className="text-slate-900">Total:</span>
                          <span className="text-red-600">{data.generatedQuote.total}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Terms */}
                  <div className="mt-6 p-4 bg-slate-50 rounded-lg">
                    <h4 className="font-medium text-slate-900 mb-2">Terms & Conditions</h4>
                    <p className="text-slate-700 text-sm">
                      Valid until: {new Date(data.generatedQuote.validUntil).toLocaleDateString()}
                    </p>
                    <p className="text-slate-700 text-sm">Payment Terms: {data.generatedQuote.terms}</p>
                  </div>
                </CardContent>
              </Card>

              {/* Notes Section */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-slate-900">Sales Notes</CardTitle>
                </CardHeader>
                <CardContent>
                  <Textarea
                    placeholder="Add your notes about this RFP, customer requirements, or follow-up actions..."
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    className="min-h-[100px] border-slate-200 focus:border-red-400 focus:ring-red-400/20"
                  />
                </CardContent>
              </Card>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="border-t border-slate-200 bg-slate-50 p-6">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <Button variant="outline" className="border-slate-300 text-slate-700 hover:bg-slate-100 bg-transparent">
                <Download className="w-4 h-4 mr-2" />
                Download PDF
              </Button>
              <Button variant="outline" className="border-slate-300 text-slate-700 hover:bg-slate-100 bg-transparent">
                <FileText className="w-4 h-4 mr-2" />
                View Original RFP
              </Button>
            </div>
            <div className="flex items-center space-x-3">
              <Button
                variant="outline"
                className="border-amber-200 text-amber-700 hover:bg-amber-50 bg-transparent"
                onClick={() => setIsEditing(true)}
              >
                <Edit3 className="w-4 h-4 mr-2" />
                Modify Quote
              </Button>
              <Button className="bg-gradient-to-r from-amber-600 to-red-600 hover:from-amber-700 hover:to-red-700 shadow-lg">
                <Send className="w-4 h-4 mr-2" />
                Send to Customer
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
