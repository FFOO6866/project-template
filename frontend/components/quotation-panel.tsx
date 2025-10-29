"use client"

import { useState, useEffect } from "react"
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
  X,
  MessageSquare,
  AlertCircle,
  Plus,
  ArrowLeft,
} from "lucide-react"

interface QuotationPanelProps {
  documentId: string
  onClose: () => void
  onRequestResize: (size: "minimize" | "maximize" | "equal") => void
}

interface QuoteItem {
  product: string
  description: string
  quantity: number
  unitPrice: string
  totalPrice: string
}

interface GeneratedQuote {
  items: QuoteItem[]
  subtotal: string
  discount: string
  tax: string
  total: string
  validUntil: string
  terms: string
}

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
  generatedQuote: GeneratedQuote
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

export function QuotationPanel({ documentId, onClose, onRequestResize }: QuotationPanelProps) {
  const [activeTab, setActiveTab] = useState<"overview" | "analysis" | "quote">("quote")
  const [isEditing, setIsEditing] = useState(false)
  const [notes, setNotes] = useState("")
  const [editingItems, setEditingItems] = useState<{ [key: number]: boolean }>({})
  const [editedQuote, setEditedQuote] = useState<GeneratedQuote>({
    items: [],
    subtotal: "",
    discount: "",
    tax: "",
    total: "",
    validUntil: "",
    terms: "",
  })

  const data = sampleRFPData // In real app, fetch by documentId

  // Initialize editedQuote with data from sampleRFPData
  useEffect(() => {
    if (data?.generatedQuote) {
      setEditedQuote({
        items: [...data.generatedQuote.items],
        subtotal: data.generatedQuote.subtotal,
        discount: data.generatedQuote.discount,
        tax: data.generatedQuote.tax,
        total: data.generatedQuote.total,
        validUntil: data.generatedQuote.validUntil,
        terms: data.generatedQuote.terms,
      })
    }
  }, [data])

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

  const updateItemTotal = (index: number, quantity: number, unitPrice: string) => {
    const price = Number.parseFloat(unitPrice.replace("$", "")) || 0
    const total = quantity * price
    return `$${total.toFixed(2)}`
  }

  const addNewItem = () => {
    const newItem: QuoteItem = {
      product: "New Product",
      description: "Product description",
      quantity: 1,
      unitPrice: "$0.00",
      totalPrice: "$0.00",
    }
    const newItems = [...editedQuote.items, newItem]
    setEditedQuote({ ...editedQuote, items: newItems })
    setEditingItems({ ...editingItems, [editedQuote.items.length]: true })
  }

  const removeItem = (index: number) => {
    const newItems = editedQuote.items.filter((_, i) => i !== index)
    setEditedQuote({ ...editedQuote, items: newItems })
    const newEditingItems = { ...editingItems }
    delete newEditingItems[index]
    setEditingItems(newEditingItems)
  }

  const updateItem = (index: number, field: keyof QuoteItem, value: string | number) => {
    const newItems = [...editedQuote.items]
    newItems[index] = { ...newItems[index], [field]: value }

    // Auto-calculate total when quantity or unit price changes
    if (field === "quantity" || field === "unitPrice") {
      const quantity = field === "quantity" ? (value as number) : newItems[index].quantity
      const unitPrice = field === "unitPrice" ? (value as string) : newItems[index].unitPrice
      newItems[index].totalPrice = updateItemTotal(index, quantity, unitPrice)
    }

    setEditedQuote({ ...editedQuote, items: newItems })
  }

  // Don't render until editedQuote is properly initialized
  if (!editedQuote.items || editedQuote.items.length === 0) {
    return (
      <div className="h-full flex items-center justify-center bg-white border border-slate-200 rounded-xl shadow-lg shadow-slate-200/50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-600 mx-auto mb-4"></div>
          <p className="text-slate-600">Loading quotation...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col bg-white border border-slate-200 rounded-xl shadow-lg shadow-slate-200/50">
      {/* Header */}
      <div className="bg-gradient-to-r from-amber-600 to-red-600 text-white p-6 rounded-t-xl flex-shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="h-8 w-8 p-0 hover:bg-white/20 text-white rounded-lg"
            >
              <ArrowLeft className="w-4 h-4" />
            </Button>
            <div className="flex-1 min-w-0">
              <h1 className="text-2xl font-bold truncate">{data.name}</h1>
              <p className="text-amber-100 text-sm truncate">{data.rfpDetails.projectName}</p>
            </div>
          </div>
          <div className="flex items-center space-x-4 ml-4">
            <Badge className={`${getStatusColor(data.rfpDetails.status)} text-white capitalize`}>
              {data.rfpDetails.status}
            </Badge>
            <div className="text-right">
              <div className="text-2xl font-bold">{data.aiAnalysis.totalEstimate}</div>
              <div className="text-amber-100 text-sm">Est. Value</div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="h-8 w-8 p-0 hover:bg-white/20 text-white rounded-lg ml-2"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="bg-slate-50 border-b border-slate-200 p-4 flex items-center justify-between flex-shrink-0">
        <div className="text-sm text-slate-600 flex items-center space-x-2">
          <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
          <span>
            <strong>AI Chat active</strong> - Ask questions about this quotation in the chat panel →
          </span>
        </div>
        <div className="flex items-center space-x-3">
          <Button
            variant="outline"
            size="sm"
            className="border-slate-300 text-slate-700 hover:bg-slate-100 bg-transparent"
          >
            <Download className="w-4 h-4 mr-2" />
            Download PDF
          </Button>
          <Button
            size="sm"
            className="bg-gradient-to-r from-amber-600 to-red-600 hover:from-amber-700 hover:to-red-700"
          >
            <Send className="w-4 h-4 mr-2" />
            Send Quote
          </Button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-slate-200 bg-white flex-shrink-0">
        <div className="flex">
          {[
            { id: "quote", label: "Quotation", icon: DollarSign },
            { id: "overview", label: "Overview", icon: FileText },
            { id: "analysis", label: "AI Analysis", icon: MessageSquare },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center space-x-2 py-4 px-6 border-b-2 font-medium transition-colors ${
                activeTab === tab.id
                  ? "border-red-600 text-red-600 bg-red-50/50"
                  : "border-transparent text-slate-600 hover:text-slate-900 hover:bg-slate-50"
              }`}
            >
              <tab.icon className="w-5 h-5" />
              <span>{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Content - Now with full height and better spacing */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-8 space-y-8">
          {activeTab === "quote" && (
            <>
              {/* Customer Info Header */}
              <div className="bg-gradient-to-r from-slate-50 to-amber-50/30 rounded-xl p-6 border border-slate-200">
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <h3 className="font-semibold text-slate-900 text-lg mb-3">{data.customer.company}</h3>
                    <p className="text-slate-700 font-medium">{data.customer.name}</p>
                    <p className="text-slate-600">{data.customer.contact}</p>
                  </div>
                  <div className="text-right">
                    <div className="flex items-center justify-end space-x-2 mb-2">
                      <Mail className="w-4 h-4 text-slate-400" />
                      <span className="text-slate-700">{data.customer.email}</span>
                    </div>
                    <div className="flex items-center justify-end space-x-2">
                      <Phone className="w-4 h-4 text-slate-400" />
                      <span className="text-slate-700">{data.customer.phone}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Quote Items */}
              <Card className="border-slate-200">
                <CardHeader className="pb-6">
                  <CardTitle className="flex items-center justify-between text-slate-900 text-xl">
                    <span className="flex items-center">
                      <DollarSign className="w-6 h-6 mr-3 text-amber-600" />
                      Generated Quotation
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
                          <th className="text-left py-4 text-slate-600 font-semibold">Product</th>
                          <th className="text-left py-4 text-slate-600 font-semibold">Description</th>
                          <th className="text-center py-4 text-slate-600 font-semibold">Qty</th>
                          <th className="text-right py-4 text-slate-600 font-semibold">Unit Price</th>
                          <th className="text-right py-4 text-slate-600 font-semibold">Total</th>
                          {isEditing && <th className="text-center py-4 text-slate-600 font-semibold">Actions</th>}
                        </tr>
                      </thead>
                      <tbody>
                        {editedQuote.items.map((item, index) => (
                          <tr key={index} className="border-b border-slate-100 hover:bg-slate-50">
                            <td className="py-5">
                              {editingItems[index] ? (
                                <input
                                  type="text"
                                  value={item.product}
                                  onChange={(e) => updateItem(index, "product", e.target.value)}
                                  className="w-full px-2 py-1 border border-slate-300 rounded text-sm font-medium"
                                />
                              ) : (
                                <span className="font-medium text-slate-900">{item.product}</span>
                              )}
                            </td>
                            <td className="py-5">
                              {editingItems[index] ? (
                                <input
                                  type="text"
                                  value={item.description}
                                  onChange={(e) => updateItem(index, "description", e.target.value)}
                                  className="w-full px-2 py-1 border border-slate-300 rounded text-sm"
                                />
                              ) : (
                                <span className="text-slate-700">{item.description}</span>
                              )}
                            </td>
                            <td className="py-5 text-center">
                              {editingItems[index] ? (
                                <input
                                  type="number"
                                  value={item.quantity}
                                  onChange={(e) => updateItem(index, "quantity", Number.parseInt(e.target.value) || 0)}
                                  className="w-20 px-2 py-1 border border-slate-300 rounded text-sm text-center"
                                />
                              ) : (
                                <span className="text-slate-900">{item.quantity}</span>
                              )}
                            </td>
                            <td className="py-5 text-right">
                              {editingItems[index] ? (
                                <input
                                  type="text"
                                  value={item.unitPrice}
                                  onChange={(e) => updateItem(index, "unitPrice", e.target.value)}
                                  className="w-24 px-2 py-1 border border-slate-300 rounded text-sm text-right"
                                />
                              ) : (
                                <span className="text-slate-900">{item.unitPrice}</span>
                              )}
                            </td>
                            <td className="py-5 text-right">
                              <span className="font-semibold text-slate-900">{item.totalPrice}</span>
                            </td>
                            {isEditing && (
                              <td className="py-5 text-center">
                                <div className="flex items-center justify-center space-x-2">
                                  {editingItems[index] ? (
                                    <>
                                      <Button
                                        size="sm"
                                        variant="outline"
                                        onClick={() => {
                                          setEditingItems({ ...editingItems, [index]: false })
                                        }}
                                        className="h-8 w-8 p-0 border-emerald-300 text-emerald-600 hover:bg-emerald-50"
                                      >
                                        <CheckCircle className="w-4 h-4" />
                                      </Button>
                                      <Button
                                        size="sm"
                                        variant="outline"
                                        onClick={() => removeItem(index)}
                                        className="h-8 w-8 p-0 border-red-300 text-red-600 hover:bg-red-50"
                                      >
                                        <X className="w-4 h-4" />
                                      </Button>
                                    </>
                                  ) : (
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      onClick={() => {
                                        setEditingItems({ ...editingItems, [index]: true })
                                      }}
                                      className="h-8 w-8 p-0 border-amber-300 text-amber-600 hover:bg-amber-50"
                                    >
                                      <Edit3 className="w-4 h-4" />
                                    </Button>
                                  )}
                                </div>
                              </td>
                            )}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {isEditing && (
                    <div className="mt-4 flex justify-start">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={addNewItem}
                        className="border-slate-300 text-slate-700 hover:bg-slate-100 bg-transparent"
                      >
                        <Plus className="w-4 h-4 mr-2" />
                        Add Item
                      </Button>
                    </div>
                  )}

                  {/* Quote Summary */}
                  <div className="mt-8 border-t border-slate-200 pt-8">
                    <div className="flex justify-end">
                      <div className="w-96 space-y-4">
                        <div className="flex justify-between text-lg">
                          <span className="text-slate-600">Subtotal:</span>
                          {isEditing ? (
                            <input
                              type="text"
                              value={editedQuote.subtotal}
                              onChange={(e) => setEditedQuote({ ...editedQuote, subtotal: e.target.value })}
                              className="px-2 py-1 border border-slate-300 rounded text-right font-semibold"
                            />
                          ) : (
                            <span className="text-slate-900 font-semibold">{editedQuote.subtotal}</span>
                          )}
                        </div>
                        <div className="flex justify-between text-lg">
                          <span className="text-slate-600">Discount:</span>
                          {isEditing ? (
                            <input
                              type="text"
                              value={editedQuote.discount}
                              onChange={(e) => setEditedQuote({ ...editedQuote, discount: e.target.value })}
                              className="px-2 py-1 border border-slate-300 rounded text-right font-semibold text-emerald-600"
                            />
                          ) : (
                            <span className="text-emerald-600 font-semibold">-{editedQuote.discount}</span>
                          )}
                        </div>
                        <div className="flex justify-between text-lg">
                          <span className="text-slate-600">Tax (GST):</span>
                          {isEditing ? (
                            <input
                              type="text"
                              value={editedQuote.tax}
                              onChange={(e) => setEditedQuote({ ...editedQuote, tax: e.target.value })}
                              className="px-2 py-1 border border-slate-300 rounded text-right font-semibold"
                            />
                          ) : (
                            <span className="text-slate-900 font-semibold">{editedQuote.tax}</span>
                          )}
                        </div>
                        <div className="flex justify-between border-t border-slate-200 pt-4 text-2xl font-bold">
                          <span className="text-slate-900">Total:</span>
                          {isEditing ? (
                            <input
                              type="text"
                              value={editedQuote.total}
                              onChange={(e) => setEditedQuote({ ...editedQuote, total: e.target.value })}
                              className="px-2 py-1 border border-slate-300 rounded text-right font-bold text-red-600 text-2xl"
                            />
                          ) : (
                            <span className="text-red-600">{editedQuote.total}</span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Terms */}
                  <div className="mt-8 p-6 bg-gradient-to-r from-slate-50 to-amber-50/30 rounded-lg border border-slate-200">
                    <h4 className="font-semibold text-slate-900 mb-4 text-lg">Terms & Conditions</h4>
                    <div className="grid grid-cols-2 gap-6">
                      <div>
                        <span className="text-slate-600">Valid until:</span>
                        {isEditing ? (
                          <input
                            type="date"
                            value={editedQuote.validUntil}
                            onChange={(e) => setEditedQuote({ ...editedQuote, validUntil: e.target.value })}
                            className="ml-2 px-2 py-1 border border-slate-300 rounded font-semibold"
                          />
                        ) : (
                          <span className="ml-2 font-semibold text-slate-900">
                            {new Date(editedQuote.validUntil).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                      <div>
                        <span className="text-slate-600">Payment Terms:</span>
                        {isEditing ? (
                          <input
                            type="text"
                            value={editedQuote.terms}
                            onChange={(e) => setEditedQuote({ ...editedQuote, terms: e.target.value })}
                            className="ml-2 px-2 py-1 border border-slate-300 rounded font-semibold"
                          />
                        ) : (
                          <span className="ml-2 font-semibold text-slate-900">{editedQuote.terms}</span>
                        )}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Notes Section */}
              <Card className="border-slate-200">
                <CardHeader className="pb-4">
                  <CardTitle className="text-slate-900 text-lg">Sales Notes</CardTitle>
                </CardHeader>
                <CardContent>
                  <Textarea
                    placeholder="Add your notes about this quotation, customer requirements, or follow-up actions..."
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    className="min-h-[120px] border-slate-200 focus:border-red-400 focus:ring-red-400/20"
                  />
                </CardContent>
              </Card>
            </>
          )}

          {/* Other tabs content remains the same but with better spacing */}
          {activeTab === "overview" && (
            <>
              {/* Customer Information */}
              <Card className="border-slate-200">
                <CardHeader className="pb-6">
                  <CardTitle className="flex items-center text-slate-900 text-xl">
                    <User className="w-6 h-6 mr-3 text-amber-600" />
                    Customer Information
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-8">
                    <div className="space-y-6">
                      <div>
                        <label className="text-sm font-semibold text-slate-600 uppercase tracking-wide">Company</label>
                        <p className="text-slate-900 font-semibold text-lg mt-1">{data.customer.company}</p>
                      </div>
                      <div>
                        <label className="text-sm font-semibold text-slate-600 uppercase tracking-wide">
                          Contact Person
                        </label>
                        <p className="text-slate-900 font-medium mt-1">{data.customer.name}</p>
                        <p className="text-slate-600">{data.customer.contact}</p>
                      </div>
                    </div>
                    <div className="space-y-6">
                      <div className="flex items-center space-x-3">
                        <Mail className="w-5 h-5 text-slate-400" />
                        <span className="text-slate-900">{data.customer.email}</span>
                      </div>
                      <div className="flex items-center space-x-3">
                        <Phone className="w-5 h-5 text-slate-400" />
                        <span className="text-slate-900">{data.customer.phone}</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* RFP Details */}
              <Card className="border-slate-200">
                <CardHeader className="pb-6">
                  <CardTitle className="flex items-center text-slate-900 text-xl">
                    <Calendar className="w-6 h-6 mr-3 text-amber-600" />
                    RFP Details
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-8 mb-6">
                    <div>
                      <label className="text-sm font-semibold text-slate-600 uppercase tracking-wide">
                        Submitted Date
                      </label>
                      <p className="text-slate-900 font-medium text-lg mt-1">
                        {new Date(data.rfpDetails.submittedDate).toLocaleDateString()}
                      </p>
                    </div>
                    <div>
                      <label className="text-sm font-semibold text-slate-600 uppercase tracking-wide">Due Date</label>
                      <p className="text-red-600 font-bold text-lg mt-1">
                        {new Date(data.rfpDetails.dueDate).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <div>
                    <label className="text-sm font-semibold text-slate-600 uppercase tracking-wide">
                      Project Description
                    </label>
                    <p className="text-slate-900 mt-2 leading-relaxed">{data.rfpDetails.description}</p>
                  </div>
                </CardContent>
              </Card>

              {/* Requirements */}
              <Card className="border-slate-200">
                <CardHeader className="pb-6">
                  <CardTitle className="flex items-center text-slate-900 text-xl">
                    <CheckCircle className="w-6 h-6 mr-3 text-amber-600" />
                    Requirements Breakdown
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-8">
                    {data.requirements.map((category, categoryIndex) => (
                      <div key={categoryIndex}>
                        <h4 className="font-bold text-slate-900 mb-4 text-lg">{category.category}</h4>
                        <div className="space-y-4">
                          {category.items.map((item, itemIndex) => (
                            <div
                              key={itemIndex}
                              className="border border-slate-200 rounded-lg p-6 hover:bg-slate-50 transition-colors"
                            >
                              <div className="flex justify-between items-start mb-3">
                                <h5 className="font-semibold text-slate-900 text-lg">{item.description}</h5>
                                <div className="flex items-center space-x-3">
                                  <Badge className={`${getConfidenceColor(item.confidence)}`}>
                                    {item.confidence}% match
                                  </Badge>
                                  <span className="font-bold text-slate-900 text-lg">{item.estimatedPrice}</span>
                                </div>
                              </div>
                              <div className="grid grid-cols-3 gap-6">
                                <div>
                                  <span className="text-slate-600 font-medium">Quantity:</span>
                                  <span className="ml-2 font-semibold">{item.quantity}</span>
                                </div>
                                <div>
                                  <span className="text-slate-600 font-medium">Specifications:</span>
                                  <span className="ml-2">{item.specifications}</span>
                                </div>
                                {item.matchedProduct && (
                                  <div>
                                    <span className="text-slate-600 font-medium">Matched Product:</span>
                                    <span className="ml-2 text-amber-700 font-semibold">{item.matchedProduct}</span>
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
            </>
          )}

          {activeTab === "analysis" && (
            <>
              {/* AI Summary */}
              <Card className="border-slate-200">
                <CardHeader className="pb-6">
                  <CardTitle className="flex items-center text-slate-900 text-xl">
                    <MessageSquare className="w-6 h-6 mr-3 text-amber-600" />
                    AI Analysis Summary
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-slate-700 leading-relaxed text-lg">{data.aiAnalysis.summary}</p>
                </CardContent>
              </Card>

              {/* Key Requirements */}
              <Card className="border-slate-200">
                <CardHeader className="pb-6">
                  <CardTitle className="text-slate-900 text-xl">Key Requirements</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-4">
                    {data.aiAnalysis.keyRequirements.map((req, index) => (
                      <li key={index} className="flex items-start space-x-3">
                        <CheckCircle className="w-5 h-5 text-emerald-500 mt-1 flex-shrink-0" />
                        <span className="text-slate-700 leading-relaxed">{req}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>

              {/* Recommendations */}
              <Card className="border-slate-200">
                <CardHeader className="pb-6">
                  <CardTitle className="text-slate-900 text-xl">AI Recommendations</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-4">
                    {data.aiAnalysis.recommendations.map((rec, index) => (
                      <li key={index} className="flex items-start space-x-3">
                        <div className="w-5 h-5 bg-amber-100 rounded-full flex items-center justify-center mt-1 flex-shrink-0">
                          <div className="w-2.5 h-2.5 bg-amber-600 rounded-full"></div>
                        </div>
                        <span className="text-slate-700 leading-relaxed">{rec}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>

              {/* Risk Factors */}
              <Card className="border-slate-200">
                <CardHeader className="pb-6">
                  <CardTitle className="flex items-center text-slate-900 text-xl">
                    <AlertCircle className="w-6 h-6 mr-3 text-red-600" />
                    Risk Factors
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-4">
                    {data.aiAnalysis.riskFactors.map((risk, index) => (
                      <li key={index} className="flex items-start space-x-3">
                        <AlertCircle className="w-5 h-5 text-red-500 mt-1 flex-shrink-0" />
                        <span className="text-slate-700 leading-relaxed">{risk}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
