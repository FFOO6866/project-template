"use client"

import { useState, useEffect } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { TrendingUp, FileText, Clock, DollarSign, Loader2 } from "lucide-react"

interface MetricsData {
  totalDocuments: number
  pendingQuotes: number
  monthlyValue: number
  winRate: number
}

export function MetricsBar() {
  const [metrics, setMetrics] = useState<MetricsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const token = localStorage.getItem('access_token')
        if (!token) {
          throw new Error('No authentication token')
        }

        // Fetch real document counts from API
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002'}/api/documents?page=1&page_size=1000`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        })

        if (!response.ok) {
          throw new Error(`API error: ${response.status}`)
        }

        const data = await response.json()

        // Calculate real metrics from actual data
        const totalDocs = data.total || 0
        const pendingDocs = data.documents?.filter((doc: any) =>
          doc.ai_status === 'pending' || doc.ai_status === 'processing'
        ).length || 0

        setMetrics({
          totalDocuments: totalDocs,
          pendingQuotes: pendingDocs,
          monthlyValue: 0, // TODO: Calculate from real quotes when available
          winRate: 0, // TODO: Calculate from real conversion data when available
        })
        setLoading(false)
      } catch (err) {
        console.error('Failed to fetch metrics:', err)
        setError(err instanceof Error ? err.message : 'Unknown error')
        setLoading(false)
      }
    }

    fetchMetrics()
  }, [])

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i} className="border-slate-200">
            <CardContent className="p-6">
              <div className="flex items-center justify-center h-24">
                <Loader2 className="w-6 h-6 text-slate-400 animate-spin" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  if (error || !metrics) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-6">
            <p className="text-sm text-red-600">Failed to load metrics</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  const metricsDisplay = [
    {
      title: "Total Documents",
      value: metrics.totalDocuments.toString(),
      change: "Real-time",
      trend: "up",
      icon: FileText,
      color: "text-blue-600",
      bgColor: "bg-blue-100",
    },
    {
      title: "Processing",
      value: metrics.pendingQuotes.toString(),
      change: "Live data",
      trend: "up",
      icon: Clock,
      color: "text-amber-600",
      bgColor: "bg-amber-100",
    },
    {
      title: "This Month",
      value: metrics.monthlyValue > 0 ? `$${(metrics.monthlyValue / 1000).toFixed(0)}K` : "N/A",
      change: "Coming soon",
      trend: "up",
      icon: DollarSign,
      color: "text-emerald-600",
      bgColor: "bg-emerald-100",
    },
    {
      title: "Win Rate",
      value: metrics.winRate > 0 ? `${metrics.winRate}%` : "N/A",
      change: "Coming soon",
      trend: "up",
      icon: TrendingUp,
      color: "text-purple-600",
      bgColor: "bg-purple-100",
    },
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      {metricsDisplay.map((metric, index) => (
        <Card key={index} className="border-slate-200 hover:shadow-md transition-shadow">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-600 mb-1">{metric.title}</p>
                <p className="text-2xl font-bold text-slate-900">{metric.value}</p>
                <p className={`text-sm ${metric.color} flex items-center mt-1`}>
                  <TrendingUp className="w-4 h-4 mr-1" />
                  {metric.change}
                </p>
              </div>
              <div className={`${metric.bgColor} ${metric.color} p-3 rounded-lg`}>
                <metric.icon className="w-6 h-6" />
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
