"use client"

import { useState } from "react"
import { DashboardShell } from "@/components/dashboard-shell"
import { Heading } from "@/components/ui/heading"
import { Text } from "@/components/ui/text"
import { Section } from "@/components/ui/section"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { JobEvaluationSystem } from "@/components/rewards/job-evaluation-system"
import { JobMappingSystem } from "@/components/rewards/job-mapping-system"
import { PayForPerformanceSystem } from "@/components/rewards/pay-for-performance-system"

export default function RewardsPage() {
  const [activeTab, setActiveTab] = useState("job-evaluation")

  return (
    <DashboardShell>
      <Section>
        <Heading level={1}>Value-based Rewards (RRRR)</Heading>
        <Text className="text-muted-foreground">
          Comprehensive rewards management system based on the Mercer Job Evaluation methodology
        </Text>
      </Section>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Rewards Management System</CardTitle>
          <CardDescription>Manage job evaluations, market mapping, and performance-based compensation</CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="job-evaluation" onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="job-evaluation">Job Evaluation</TabsTrigger>
              <TabsTrigger value="job-mapping">Job Mapping</TabsTrigger>
              <TabsTrigger value="pay-for-performance">Pay for Performance</TabsTrigger>
            </TabsList>
            <TabsContent value="job-evaluation" className="pt-6">
              <JobEvaluationSystem />
            </TabsContent>
            <TabsContent value="job-mapping" className="pt-6">
              <JobMappingSystem />
            </TabsContent>
            <TabsContent value="pay-for-performance" className="pt-6">
              <PayForPerformanceSystem />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </DashboardShell>
  )
}
