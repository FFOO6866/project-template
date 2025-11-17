import { DashboardShell } from "@/components/dashboard-shell"
import { Heading } from "@/components/ui/heading"
import { Section } from "@/components/ui/section"
import { Skeleton } from "@/components/ui/skeleton"

export default function RewardsLoading() {
  return (
    <DashboardShell>
      <Section>
        <Heading level={1}>Value-based Rewards (RRRR)</Heading>
        <div className="mt-6">
          <Skeleton className="h-10 w-full" />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
            <Skeleton className="h-[300px] w-full" />
            <Skeleton className="h-[300px] w-full" />
            <Skeleton className="h-[300px] w-full" />
          </div>
        </div>
      </Section>
    </DashboardShell>
  )
}
