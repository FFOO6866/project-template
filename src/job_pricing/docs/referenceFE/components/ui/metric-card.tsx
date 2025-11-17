import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"

interface MetricCardProps {
  title: string
  value: string
  change?: string
  trend?: "up" | "down" | "neutral"
  description?: string
  category: "people" | "process" | "performance" | "business" | "investment" | "advocacy" | "philanthropy"
  className?: string
}

export function MetricCard({
  title,
  value,
  change,
  trend = "neutral",
  description,
  category,
  className,
}: MetricCardProps) {
  const categoryColors = {
    people: {
      bar: "bg-blue-500",
      badge: "bg-blue-50 text-blue-700",
    },
    process: {
      bar: "bg-cyan-500",
      badge: "bg-cyan-50 text-cyan-700",
    },
    performance: {
      bar: "bg-green-500",
      badge: "bg-green-50 text-green-700",
    },
    business: {
      bar: "bg-blue-500",
      badge: "bg-blue-50 text-blue-700",
    },
    investment: {
      bar: "bg-violet-500",
      badge: "bg-violet-50 text-violet-700",
    },
    advocacy: {
      bar: "bg-pink-500",
      badge: "bg-pink-50 text-pink-700",
    },
    philanthropy: {
      bar: "bg-orange-500",
      badge: "bg-orange-50 text-orange-700",
    },
  }

  const trendColors = {
    up: "bg-green-50 text-green-700",
    down: "bg-red-50 text-red-700",
    neutral: "bg-gray-50 text-gray-700",
  }

  // Gracefully fall back to the "people" palette if an unknown category is supplied
  const palette = categoryColors[category] ?? categoryColors.people

  return (
    <Card className={cn("overflow-hidden", className)}>
      <div className={`h-1 w-full ${palette.bar}`} />
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-baseline justify-between">
          <div className="text-2xl font-bold">{value}</div>
          {change && (
            <div className={`flex items-center rounded-full px-2 py-1 text-xs font-medium ${trendColors[trend]}`}>
              {change}
            </div>
          )}
        </div>
        {description && <p className="mt-1 text-xs text-muted-foreground">{description}</p>}
      </CardContent>
    </Card>
  )
}
