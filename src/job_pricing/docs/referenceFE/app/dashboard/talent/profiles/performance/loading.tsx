import { DashboardShell } from "@/components/dashboard-shell"
import { Skeleton } from "@/components/ui/skeleton"
import { Card, CardContent, CardHeader } from "@/components/ui/card"

export default function Loading() {
  return (
    <DashboardShell>
      <div className="flex flex-col space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <Skeleton className="h-8 w-48" />
            <Skeleton className="h-4 w-64 mt-2" />
          </div>
          <div className="flex items-center gap-2">
            <Skeleton className="h-9 w-64" />
            <Skeleton className="h-9 w-9" />
            <Skeleton className="h-9 w-24" />
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-4">
          <Skeleton className="h-9 w-32" />
          <Skeleton className="h-9 w-32" />
          <Skeleton className="h-9 w-32" />
          <Skeleton className="h-9 w-32" />
        </div>

        <div className="flex flex-wrap items-center gap-4">
          <Skeleton className="h-9 w-[280px]" />
          <Skeleton className="h-9 w-[280px]" />
        </div>

        {/* Main Performance Matrix and X-Factor */}
        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardHeader>
              <Skeleton className="h-5 w-40 mb-1" />
              <Skeleton className="h-4 w-60" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-[400px] w-full" />
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <Skeleton className="h-5 w-40 mb-1" />
              <Skeleton className="h-4 w-60" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-[400px] w-full" />
            </CardContent>
          </Card>
        </div>

        {/* Consciousness Map */}
        <Card>
          <CardHeader>
            <Skeleton className="h-5 w-40 mb-1" />
            <Skeleton className="h-4 w-60" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-[600px] w-full" />
          </CardContent>
        </Card>

        {/* Assessment Frameworks - 3x2 Grid */}
        <div className="grid gap-6 md:grid-cols-3">
          {/* Row 1 */}
          {[...Array(6)].map((_, i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-5 w-40 mb-1" />
                <Skeleton className="h-4 w-60" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-[400px] w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </DashboardShell>
  )
}
