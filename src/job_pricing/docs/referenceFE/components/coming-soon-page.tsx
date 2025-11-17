"use client"

import { DashboardShell } from "@/components/dashboard-shell"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Construction, ArrowRight } from "lucide-react"
import Link from "next/link"

interface ComingSoonPageProps {
  title: string
  description?: string
}

export function ComingSoonPage({ title, description }: ComingSoonPageProps) {
  return (
    <DashboardShell>
      <div className="flex items-center justify-center min-h-[60vh]">
        <Card className="w-full max-w-md text-center">
          <CardHeader className="pb-4">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-orange-100">
              <Construction className="h-8 w-8 text-orange-600" />
            </div>
            <CardTitle className="text-2xl">{title}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-muted-foreground">
              {description || "This feature is currently under development and will be available soon."}
            </p>
            <p className="text-sm text-muted-foreground">
              For now, you can explore our Dynamic Job Pricing module which is fully functional.
            </p>
            <Link href="/dashboard/job-pricing">
              <Button className="w-full">
                Go to Dynamic Job Pricing
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    </DashboardShell>
  )
}

export default ComingSoonPage
