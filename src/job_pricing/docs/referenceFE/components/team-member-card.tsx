"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Progress } from "@/components/ui/progress"
import { User, ChevronRight } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { ConsciousnessLineIndicator } from "./consciousness-line-indicator"

interface TeamMemberCardProps {
  name: string
  role: string
  department: string
  imageUrl?: string
  strengths: string[]
  rmrrScore: number
  leadershipScore: number
  influenceScore: number
  consciousnessLevel?: string
  consciousnessValue?: number
  className?: string
}

export function TeamMemberCard({
  name,
  role,
  department,
  imageUrl,
  strengths,
  rmrrScore,
  leadershipScore,
  influenceScore,
  consciousnessLevel = "Acceptance",
  consciousnessValue = 350,
  className,
}: TeamMemberCardProps) {
  // Get initials for avatar fallback
  const initials = name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .substring(0, 2)

  // Determine score color based on value
  const getScoreColor = (score: number) => {
    if (score >= 90) return "bg-green-500"
    if (score >= 80) return "bg-blue-500"
    if (score >= 70) return "bg-yellow-500"
    return "bg-red-500"
  }

  // Generate profile URL - link to performance matrix page
  const profileUrl = `/dashboard/talent/profiles/performance?member=${name.toLowerCase().replace(/\s+/g, "-")}`

  return (
    <Card className={cn("overflow-hidden transition-all duration-300 hover:shadow-md", className)}>
      <CardContent className="p-4">
        {/* Top section with avatar, name, role, department */}
        <div className="flex items-start gap-4 mb-4">
          {/* Avatar */}
          <Avatar className="h-16 w-16 border-2 border-white shadow-md">
            {imageUrl ? (
              <AvatarImage src={imageUrl || "/placeholder.svg"} alt={name} />
            ) : (
              <AvatarFallback className="text-lg bg-primary text-primary-foreground">
                {initials || <User className="h-8 w-8" />}
              </AvatarFallback>
            )}
          </Avatar>

          {/* Name, role, department */}
          <div>
            <h3 className="text-lg font-bold">{name}</h3>
            <p className="text-sm text-muted-foreground">{role}</p>
            <Badge variant="outline" className="mt-1">
              {department}
            </Badge>
          </div>
        </div>

        {/* Bottom section with all metrics and content */}
        <div className="w-full">
          {/* Consciousness Line Indicator */}
          <div className="mb-3">
            <ConsciousnessLineIndicator level={consciousnessLevel} value={consciousnessValue} />
          </div>

          {/* Key metrics */}
          <div className="space-y-2 mb-3">
            <div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">X Factor 1</span>
                <span className="text-sm font-medium">{rmrrScore}%</span>
              </div>
              <Progress value={rmrrScore} className={`h-2 mt-1 ${getScoreColor(rmrrScore)}`} />
            </div>

            <div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">X Factor 2</span>
                <span className="text-sm font-medium">{leadershipScore}%</span>
              </div>
              <Progress value={leadershipScore} className={`h-2 mt-1 ${getScoreColor(leadershipScore)}`} />
            </div>

            <div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">X Factor 3</span>
                <span className="text-sm font-medium">{influenceScore}%</span>
              </div>
              <Progress value={influenceScore} className={`h-2 mt-1 ${getScoreColor(influenceScore)}`} />
            </div>
          </div>

          {/* Strengths - moved below X Factor metrics */}
          <div className="mb-3">
            <div className="flex flex-wrap gap-1.5">
              {strengths.map((strength, index) => (
                <Badge key={index} variant="secondary" className="font-normal text-xs">
                  {strength}
                </Badge>
              ))}
            </div>
          </div>

          {/* View profile link */}
          <div className="mt-2 flex justify-end">
            <Link href={profileUrl}>
              <Button variant="ghost" size="sm" className="text-sm gap-1 text-primary hover:text-primary">
                View Profile <ChevronRight className="h-4 w-4" />
              </Button>
            </Link>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
