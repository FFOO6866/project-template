"use client"

import type React from "react"
import { useState } from "react"
import { cn } from "@/lib/utils"
import { useAuth } from "@/contexts/AuthContext"
import { Button } from "@/components/ui/button"
import { LogOut, User, Sparkles, ChevronLeft, ChevronRight, Upload, Database } from "lucide-react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import Image from "next/image"

interface DashboardShellProps {
  children: React.ReactNode
  className?: string
}

const TPC_LOGO = "https://media.licdn.com/dms/image/v2/D560BAQFDI5kO4zQQ-A/company-logo_200_200/company-logo_200_200/0/1712914296519/tsao_pao_chee_logo?e=2147483647&v=beta&t=HuxbzYLDy06ThTde7q_riZcW2HuzpjyhNnCIGcsGkIU"

export function DashboardShell({ children, className }: DashboardShellProps) {
  const { user, logout } = useAuth()
  const pathname = usePathname()
  const [collapsed, setCollapsed] = useState(false)

  const navigation = [
    {
      name: "Dynamic Job Pricing",
      href: "/job-pricing",
      icon: Sparkles,
      current: pathname === "/job-pricing",
      description: "AI-Powered Salary Recommendations",
      disabled: false
    },
    {
      name: "Mercer Data Mgmt",
      href: "/mercer-upload",
      icon: Database,
      current: pathname === "/mercer-upload",
      description: "Import Mercer Market Data",
      disabled: true
    }
  ]

  return (
    <div className="flex min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Sidebar */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex flex-col bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 shadow-2xl transition-all duration-300",
          collapsed ? "w-20" : "w-72"
        )}
      >
        {/* Logo & Company Name */}
        <div className="flex h-20 items-center justify-center border-b border-slate-700/50 bg-slate-900/50 backdrop-blur-sm px-4">
          {!collapsed ? (
            <div className="flex items-center gap-3 w-full">
              <div className="relative h-12 w-12 flex-shrink-0 rounded-lg overflow-hidden bg-white p-1 shadow-lg">
                <Image
                  src={TPC_LOGO}
                  alt="TPC Logo"
                  width={48}
                  height={48}
                  className="object-contain"
                  unoptimized
                />
              </div>
              <div className="flex-1 min-w-0">
                <h1 className="text-sm font-bold text-white truncate">Tsao Pao Chee</h1>
                <p className="text-xs text-slate-400 truncate">Job Pricing Engine</p>
              </div>
            </div>
          ) : (
            <div className="relative h-10 w-10 rounded-lg overflow-hidden bg-white p-1 shadow-lg">
              <Image
                src={TPC_LOGO}
                alt="TPC Logo"
                width={40}
                height={40}
                className="object-contain"
                unoptimized
              />
            </div>
          )}
        </div>

        {/* Toggle Button */}
        <div className="flex justify-end px-3 py-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setCollapsed(!collapsed)}
            className="h-8 w-8 p-0 text-slate-400 hover:text-white hover:bg-slate-700/50"
          >
            {collapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <ChevronLeft className="h-4 w-4" />
            )}
          </Button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 px-3 py-2">
          {navigation.map((item) => {
            const Icon = item.icon
            const isDisabled = item.disabled

            const linkContent = (
              <>
                <Icon className={cn("h-5 w-5 flex-shrink-0", item.current && "drop-shadow-sm")} />
                {!collapsed && (
                  <div className="flex-1 min-w-0">
                    <div className="truncate">{item.name}</div>
                    {item.description && (
                      <div className="truncate text-xs opacity-70 mt-0.5">
                        {item.description}
                      </div>
                    )}
                  </div>
                )}
              </>
            )

            if (isDisabled) {
              return (
                <div
                  key={item.name}
                  title={collapsed ? `${item.name} (Coming Soon)` : undefined}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-3 text-sm font-medium cursor-not-allowed text-slate-500"
                  )}
                >
                  {linkContent}
                </div>
              )
            }

            return (
              <Link
                key={item.name}
                href={item.href}
                title={collapsed ? item.name : undefined}
                className={cn(
                  "group relative flex items-center gap-3 rounded-lg px-3 py-3 text-sm font-medium transition-all duration-200",
                  item.current
                    ? "bg-gradient-to-r from-blue-600 to-blue-500 text-white shadow-lg shadow-blue-500/30"
                    : "text-slate-300 hover:bg-slate-700/50 hover:text-white"
                )}
              >
                {linkContent}
              </Link>
            )
          })}
        </nav>

        {/* User Info & Logout */}
        {user && (
          <div className="border-t border-slate-700/50 bg-slate-900/50 backdrop-blur-sm p-4">
            {!collapsed ? (
              <div className="space-y-3">
                <div className="flex items-center gap-3 px-1">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-blue-600 text-white shadow-lg flex-shrink-0">
                    <User className="h-5 w-5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="truncate text-sm font-semibold text-white">
                      {user.full_name || user.username}
                    </p>
                    <p className="truncate text-xs text-slate-400 capitalize">{user.role.replace('_', ' ')}</p>
                  </div>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={logout}
                  className="w-full gap-2 border-slate-600 bg-slate-800/50 text-slate-200 hover:bg-slate-700 hover:text-white hover:border-slate-500"
                >
                  <LogOut className="h-4 w-4" />
                  Logout
                </Button>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-blue-600 text-white shadow-lg">
                  <User className="h-5 w-5" />
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={logout}
                  className="h-9 w-9 p-0 text-slate-400 hover:text-white hover:bg-slate-700/50"
                  title="Logout"
                >
                  <LogOut className="h-4 w-4" />
                </Button>
              </div>
            )}
          </div>
        )}
      </aside>

      {/* Main Content */}
      <div
        className={cn(
          "flex flex-1 flex-col transition-all duration-300",
          collapsed ? "ml-20" : "ml-72"
        )}
      >
        <main className="flex-1 p-6 lg:p-8">
          <div className={cn("mx-auto max-w-full xl:max-w-7xl", className)}>{children}</div>
        </main>
      </div>
    </div>
  )
}
