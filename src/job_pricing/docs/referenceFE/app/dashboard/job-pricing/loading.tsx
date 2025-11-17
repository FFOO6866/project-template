import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { DashboardShell } from "@/components/dashboard-shell"

export default function JobPricingLoading() {
  return (
    <DashboardShell>
      <div className="space-y-6">
        <div className="space-y-2">
          <div className="h-8 w-64 bg-gray-200 rounded animate-pulse" />
          <div className="h-4 w-96 bg-gray-200 rounded animate-pulse" />
        </div>

        <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
          <div className="flex-1 px-4 py-2 bg-white rounded-md">
            <div className="h-4 w-16 bg-gray-200 rounded animate-pulse" />
          </div>
          <div className="flex-1 px-4 py-2">
            <div className="h-4 w-20 bg-gray-200 rounded animate-pulse" />
          </div>
          <div className="flex-1 px-4 py-2">
            <div className="h-4 w-24 bg-gray-200 rounded animate-pulse" />
          </div>
        </div>

        <Card>
          <CardHeader>
            <div className="h-6 w-48 bg-gray-200 rounded animate-pulse" />
            <div className="h-4 w-72 bg-gray-200 rounded animate-pulse" />
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="space-y-2">
                  <div className="h-4 w-24 bg-gray-200 rounded animate-pulse" />
                  <div className="h-10 w-full bg-gray-200 rounded animate-pulse" />
                </div>
              ))}
            </div>
            <div className="space-y-2">
              <div className="h-4 w-32 bg-gray-200 rounded animate-pulse" />
              <div className="h-32 w-full bg-gray-200 rounded animate-pulse" />
            </div>
            <div className="h-10 w-full bg-gray-200 rounded animate-pulse" />
          </CardContent>
        </Card>
      </div>
    </DashboardShell>
  )
}
