import type React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

interface InsightCardProps {
  icon: React.ElementType
  title: string
  description: string
  category: "People" | "Process" | "Performance"
  impact: "High" | "Medium" | "Low"
  confidence?: number
  className?: string
}

export function InsightCard({
  icon: Icon,
  title,
  description,
  category,
  impact,
  confidence,
  className,
}: InsightCardProps) {
  const categoryColors = {
    People: "bg-blue-50 text-blue-700 border-blue-200",
    Process: "bg-cyan-50 text-cyan-700 border-cyan-200",
    Performance: "bg-green-50 text-green-700 border-green-200",
  }

  const impactColors = {
    High: "bg-red-50 text-red-700 border-red-200",
    Medium: "bg-amber-50 text-amber-700 border-amber-200",
    Low: "bg-emerald-50 text-emerald-700 border-emerald-200",
  }

  const confidenceColors = (value: number) => {
    if (value > 90) return "bg-green-500"
    if (value > 80) return "bg-blue-500"
    if (value > 70) return "bg-amber-500"
    return "bg-red-500"
  }

  return (
    <Card className={cn("overflow-hidden transition-all duration-300 hover:shadow-md", className)}>
      <div
        className={`h-1 w-full ${
          category === "People" ? "bg-blue-500" : category === "Process" ? "bg-cyan-500" : "bg-green-500"
        }`}
      />
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <div
              className={`flex h-8 w-8 items-center justify-center rounded-full ${
                category === "People"
                  ? "bg-blue-100 text-blue-700"
                  : category === "Process"
                    ? "bg-cyan-100 text-cyan-700"
                    : "bg-green-100 text-green-700"
              }`}
            >
              <Icon className="h-4 w-4" />
            </div>
            <CardTitle className="text-base font-medium">{title}</CardTitle>
          </div>
          <div className="flex items-center gap-2">
            <Badge className={categoryColors[category]}>{category}</Badge>
            <Badge className={impactColors[impact]}>{impact}</Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">{description}</p>
        {confidence !== undefined && (
          <>
            <div className="mt-4 flex items-center justify-between">
              <div className="text-xs text-muted-foreground">AI Confidence</div>
              <div className="text-xs font-medium">{confidence}%</div>
            </div>
            <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-gray-100">
              <div
                className={`h-full rounded-full ${confidenceColors(confidence)}`}
                style={{ width: `${confidence}%` }}
              />
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}
