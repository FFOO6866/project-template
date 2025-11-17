"use client"

import { usePathname } from "next/navigation"
import {
  BarChart3,
  Users,
  LineChart,
  Building2,
  Network,
  Settings,
  GitMerge,
  UserCog,
  Target,
  Award,
  Briefcase,
  TrendingUp,
  HeartHandshake,
  Gem,
  BrainCircuit,
  Zap,
  Presentation,
  MessageSquare,
  ChevronLeft,
  ChevronRight,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { useSidebarState } from "@/hooks/use-sidebar-state"

const sidebarItems = [
  {
    title: "1. Attract & Recruit",
    items: [
      {
        title: "Dynamic Job Pricing",
        href: "/dashboard/job-pricing",
        icon: TrendingUp,
        disabled: false, // Keep active
      },
      {
        title: "AI Job Description Writer",
        href: "/dashboard/job-description-writer",
        icon: BrainCircuit,
        disabled: true, // Grey out
      },
      {
        title: "Market Intelligence",
        href: "/dashboard/market-intelligence",
        icon: LineChart,
        disabled: true, // Grey out
      },
      {
        title: "Talent Pipeline Engine",
        href: "/dashboard/talent-pipeline",
        icon: Users,
        disabled: true, // Grey out
      },
      {
        title: "Sourcing Dashboard",
        href: "/dashboard/sourcing",
        icon: Network,
        disabled: true, // Grey out
      },
    ],
  },
  {
    title: "2. Hire & Onboard",
    items: [
      {
        title: "RMRR Matching Engine",
        href: "/dashboard/rmrr-matching",
        icon: Target,
        disabled: true, // Grey out
      },
      {
        title: "Psychometric Assessment Hub",
        href: "/dashboard/psychometric-assessments",
        icon: BrainCircuit,
        disabled: true, // Grey out
      },
      {
        title: "e-Dossier Onboarding",
        href: "/dashboard/onboarding",
        icon: UserCog,
        disabled: true, // Grey out
      },
      {
        title: "New Hire Analytics",
        href: "/dashboard/new-hire-analytics",
        icon: BarChart3,
        disabled: true, // Grey out
      },
      {
        title: "30-60-90 Day Tracking",
        href: "/dashboard/new-hire-tracking",
        icon: Presentation,
        disabled: true, // Grey out
      },
    ],
  },
  {
    title: "3. Develop & Learn",
    items: [
      {
        title: "Learning & Development Hub",
        href: "/dashboard/learning-development",
        icon: Presentation,
        disabled: true, // Grey out
      },
      {
        title: "AI-Curated Learning Journeys",
        href: "/dashboard/learning-journeys",
        icon: BrainCircuit,
        disabled: true, // Grey out
      },
      {
        title: "Career Pathways & Mobility",
        href: "/dashboard/career-pathways",
        icon: GitMerge,
        disabled: true, // Grey out
      },
      {
        title: "Skills Analytics",
        href: "/dashboard/skills-analytics",
        icon: Zap,
        disabled: true, // Grey out
      },
      {
        title: "Succession Planning",
        href: "/dashboard/succession",
        icon: Network,
        disabled: true, // Grey out
      },
    ],
  },
  {
    title: "4. Perform & Coach",
    items: [
      {
        title: "Performance Management Studio",
        href: "/dashboard/performance",
        icon: Award,
        disabled: true, // Grey out
      },
      {
        title: "OKR & KPI Alignment",
        href: "/dashboard/okr-kpi",
        icon: Target,
        disabled: true, // Grey out
      },
      {
        title: "AI Coach Console",
        href: "/dashboard/ai-coach",
        icon: BrainCircuit,
        disabled: true, // Grey out
      },
      {
        title: "360° Survey Management",
        href: "/dashboard/360-surveys",
        icon: MessageSquare,
        disabled: true, // Grey out
      },
      {
        title: "Leadership Development",
        href: "/dashboard/leadership-development",
        icon: Award,
        disabled: true, // Grey out
      },
    ],
  },
  {
    title: "5. Reward & Recognize",
    items: [
      {
        title: "Pay-for-Value (RRRR)",
        href: "/dashboard/pay-for-value",
        icon: Gem,
        disabled: true, // Grey out
      },
      {
        title: "Job Evaluation (IPE)",
        href: "/dashboard/job-evaluation",
        icon: Building2,
        disabled: true, // Grey out
      },
      {
        title: "Total Rewards Strategy",
        href: "/dashboard/total-rewards",
        icon: HeartHandshake,
        disabled: true, // Grey out
      },
      {
        title: "Recognition Engine",
        href: "/dashboard/recognition",
        icon: Award,
        disabled: true, // Grey out
      },
      {
        title: "Incentive Modeling",
        href: "/dashboard/incentive-modeling",
        icon: TrendingUp,
        disabled: true, // Grey out
      },
    ],
  },
  {
    title: "6. Retain & Transition",
    items: [
      {
        title: "Engagement & Culture",
        href: "/dashboard/engagement",
        icon: MessageSquare,
        disabled: true, // Grey out
      },
      {
        title: "Culture Pulse & Heatmaps",
        href: "/dashboard/culture-pulse",
        icon: BarChart3,
        disabled: true, // Grey out
      },
      {
        title: "Career Transition Hub",
        href: "/dashboard/career-transition",
        icon: GitMerge,
        disabled: true, // Grey out
      },
      {
        title: "Exit Survey Analytics",
        href: "/dashboard/exit-analytics",
        icon: LineChart,
        disabled: true, // Grey out
      },
      {
        title: "Retention Analytics",
        href: "/dashboard/retention-analytics",
        icon: Users,
        disabled: true, // Grey out
      },
    ],
  },
  {
    title: "Intelligence & Insights",
    items: [
      {
        title: "Predictive Analytics",
        href: "/dashboard/predictive-insights",
        icon: LineChart,
        disabled: true, // Grey out
      },
      {
        title: "AI-Powered Insights",
        href: "/dashboard/ai-insights",
        icon: BrainCircuit,
        disabled: true, // Grey out
      },
      {
        title: "Benchmarking",
        href: "/dashboard/benchmarking",
        icon: Briefcase,
        disabled: true, // Grey out
      },
      {
        title: "Trend Analysis",
        href: "/dashboard/trend-analysis",
        icon: TrendingUp,
        disabled: true, // Grey out
      },
    ],
  },
  {
    title: "System Administration",
    items: [
      {
        title: "User Management",
        href: "/dashboard/user-management",
        icon: UserCog,
        disabled: true, // Grey out
      },
      {
        title: "P&O Reports",
        href: "/dashboard/po-reports",
        icon: BarChart3,
        disabled: true, // Grey out
      },
      {
        title: "Integration Settings",
        href: "/dashboard/integrations",
        icon: Network,
        disabled: true, // Grey out
      },
      {
        title: "System Configuration",
        href: "/dashboard/system-config",
        icon: Settings,
        disabled: true, // Grey out
      },
    ],
  },
]

export function Sidebar() {
  const pathname = usePathname()
  const { expanded, setExpanded } = useSidebarState()

  return (
    <div
      className={cn(
        "fixed inset-y-0 left-0 flex h-full flex-col bg-[#111827] transition-all duration-300 z-30",
        expanded ? "w-80" : "w-[70px]", // Increased from w-72 to w-80
      )}
    >
      <div className="flex h-16 items-center justify-between border-b border-gray-800 px-4">
        <Link href="/dashboard" className={cn("flex items-center", expanded ? "justify-start" : "justify-center")}>
          {expanded ? (
            <span className="text-xl font-bold text-white">TPC Talent Verse</span>
          ) : (
            <span className="text-xl font-bold text-white">TPC</span>
          )}
        </Link>

        <Button
          variant="ghost"
          size="icon"
          onClick={() => setExpanded(!expanded)}
          className="h-8 w-8 rounded-full text-gray-400 hover:text-white"
          aria-label={expanded ? "Collapse sidebar" : "Expand sidebar"}
        >
          {expanded ? <ChevronLeft className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
        </Button>
      </div>
      <div className="flex-1 overflow-auto py-4 scrollbar-thin scrollbar-thumb-gray-800 scrollbar-track-transparent">
        <nav className="grid items-start px-2 text-sm">
          {sidebarItems.map((section, index) => (
            <div key={index}>
              {expanded && <h3 className="mb-2 text-xs font-semibold text-gray-400 px-2">{section.title}</h3>}
              <div className="grid gap-1">
                {section.items.map((item, itemIndex) => {
                  const isDisabled = item.disabled
                  const isActive = pathname === item.href && !isDisabled

                  if (isDisabled) {
                    return (
                      <div
                        key={itemIndex}
                        className={cn(
                          "flex items-center gap-3 rounded-lg px-2 py-2 text-gray-600 cursor-not-allowed opacity-50",
                          !expanded && "justify-center",
                        )}
                        title={!expanded ? `${item.title} (Coming Soon)` : "Coming Soon"}
                      >
                        <item.icon className="h-4 w-4 flex-shrink-0" />
                        {expanded && (
                          <span className="text-sm whitespace-nowrap overflow-hidden text-ellipsis w-full">
                            {item.shortTitle || item.title}
                          </span>
                        )}
                      </div>
                    )
                  }

                  return (
                    <Link
                      key={itemIndex}
                      href={item.href}
                      className={cn(
                        "flex items-center gap-3 rounded-lg px-2 py-2 text-gray-400 transition-all hover:text-white",
                        isActive ? "bg-gray-800 text-white" : "transparent",
                        !expanded && "justify-center",
                      )}
                      title={!expanded ? item.title : undefined}
                    >
                      <item.icon className="h-4 w-4 flex-shrink-0" />
                      {expanded && (
                        <span className="text-sm whitespace-nowrap overflow-hidden text-ellipsis w-full">
                          {item.shortTitle || item.title}
                        </span>
                      )}
                    </Link>
                  )
                })}
              </div>
            </div>
          ))}
        </nav>
      </div>
      <div className="mt-auto border-t border-gray-800 p-4">
        <div
          className={cn(
            "flex items-center gap-3 rounded-lg px-3 py-2 text-gray-600 cursor-not-allowed opacity-50",
            !expanded && "justify-center w-full",
          )}
          title={!expanded ? "Settings (Coming Soon)" : "Coming Soon"}
        >
          <Settings className="h-4 w-4 flex-shrink-0" />
          {expanded && <span className="truncate">Settings</span>}
        </div>
      </div>
    </div>
  )
}
