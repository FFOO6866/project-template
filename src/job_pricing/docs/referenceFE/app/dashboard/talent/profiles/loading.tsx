import { DashboardShell } from "@/components/dashboard-shell"
import { Skeleton } from "@/components/ui/skeleton"
import { Card, CardContent } from "@/components/ui/card"

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
          <Skeleton className="h-9 w-[280px]" />
          <Skeleton className="h-9 w-[280px]" />
          <Skeleton className="h-9 w-[280px]" />
          <Skeleton className="h-9 w-[280px]" />
        </div>

        <div className="flex flex-wrap items-center gap-4">
          <Skeleton className="h-9 w-[280px]" />
          <Skeleton className="h-9 w-[280px]" />
          <Skeleton className="h-9 w-[120px]" />
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <Card key={i}>
              <div className="h-2 w-full bg-muted" />
              <CardContent className="p-6">
                <div className="flex items-start gap-4">
                  <Skeleton className="h-16 w-16 rounded-full" />
                  <div className="flex-1">
                    <Skeleton className="h-5 w-32 mb-1" />
                    <Skeleton className="h-4 w-24 mb-1" />
                    <Skeleton className="h-5 w-20" />

                    <div className="mt-4">
                      <div className="flex gap-1.5 mb-4">
                        <Skeleton className="h-5 w-20 rounded-full" />
                        <Skeleton className="h-5 w-24 rounded-full" />
                        <Skeleton className="h-5 w-16 rounded-full" />
                      </div>
                    </div>

                    <div className="space-y-3 mt-4">
                      {Array.from({ length: 3 }).map((_, j) => (
                        <div key={j}>
                          <div className="flex items-center justify-between mb-1">
                            <Skeleton className="h-3 w-20" />
                            <Skeleton className="h-3 w-8" />
                          </div>
                          <Skeleton className="h-2 w-full" />
                        </div>
                      ))}
                    </div>

                    <div className="mt-4 flex justify-end">
                      <Skeleton className="h-8 w-24" />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        <Skeleton className="h-10 w-96 mt-6" />
        <Skeleton className="h-[500px] w-full" />
      </div>
    </DashboardShell>
  )
}
