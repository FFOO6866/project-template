import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { DashboardShell } from "@/components/dashboard-shell"

export default function MarketIntelligenceLoading() {
  return (
    <DashboardShell>
      <div className="space-y-6">
        <div>
          <div className="h-8 w-64 bg-gray-200 rounded animate-pulse mb-2" />
          <div className="h-4 w-96 bg-gray-200 rounded animate-pulse" />
        </div>

        {/* Summary Cards Loading */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <div className="h-4 w-24 bg-gray-200 rounded animate-pulse" />
                <div className="h-4 w-4 bg-gray-200 rounded animate-pulse" />
              </CardHeader>
              <CardContent>
                <div className="h-8 w-16 bg-gray-200 rounded animate-pulse mb-2" />
                <div className="h-3 w-20 bg-gray-200 rounded animate-pulse" />
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Filters Loading */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1">
                <div className="h-10 w-full bg-gray-200 rounded animate-pulse" />
              </div>
              <div className="flex gap-2">
                <div className="h-10 w-32 bg-gray-200 rounded animate-pulse" />
                <div className="h-10 w-32 bg-gray-200 rounded animate-pulse" />
                <div className="h-10 w-24 bg-gray-200 rounded animate-pulse" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Content Loading */}
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardContent className="pt-6">
                <div className="flex items-start justify-between">
                  <div className="space-y-2 flex-1">
                    <div className="h-6 w-48 bg-gray-200 rounded animate-pulse" />
                    <div className="h-4 w-64 bg-gray-200 rounded animate-pulse" />
                    <div className="flex gap-2">
                      <div className="h-6 w-16 bg-gray-200 rounded animate-pulse" />
                      <div className="h-6 w-20 bg-gray-200 rounded animate-pulse" />
                      <div className="h-6 w-18 bg-gray-200 rounded animate-pulse" />
                    </div>
                  </div>
                  <div className="text-right space-y-1">
                    <div className="h-6 w-32 bg-gray-200 rounded animate-pulse" />
                    <div className="h-4 w-24 bg-gray-200 rounded animate-pulse" />
                    <div className="h-8 w-28 bg-gray-200 rounded animate-pulse" />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </DashboardShell>
  )
}
