"use client"

import { DashboardShell } from "@/components/dashboard-shell"
import { ComingSoonPage } from "@/components/coming-soon-page"

export default function SettingsPage() {
  return (
    <DashboardShell>
      <ComingSoonPage
        title="Settings"
        description="User settings and preferences will be available in the next release."
      />
    </DashboardShell>
  )
}
