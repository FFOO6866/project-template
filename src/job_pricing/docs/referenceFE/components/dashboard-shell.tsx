"use client"

import type React from "react"
import { cn } from "@/lib/utils"
import { Sidebar } from "@/components/sidebar"
import { TopNav } from "@/components/top-nav"
import { useSidebarState } from "@/hooks/use-sidebar-state"

interface DashboardShellProps {
  children: React.ReactNode
  className?: string
}

export function DashboardShell({ children, className }: DashboardShellProps) {
  const { expanded } = useSidebarState()

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      <div className={cn("flex flex-1 flex-col transition-all duration-300", expanded ? "pl-80" : "pl-[70px]")}>
        <TopNav />
        <main className="flex-1 p-4 lg:p-6">
          <div className={cn("mx-auto max-w-full xl:max-w-7xl", className)}>{children}</div>
        </main>
      </div>
    </div>
  )
}
