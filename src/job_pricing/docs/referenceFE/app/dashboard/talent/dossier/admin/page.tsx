import { DashboardShell } from "@/components/dashboard-shell"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { FileText, BarChart2, Settings } from "lucide-react"
import { Heading } from "@/components/ui/heading"
import { Text } from "@/components/ui/text"
import Link from "next/link"
import { AssessmentForm } from "@/components/assessment-form"

export default function EDossierAdminPage() {
  return (
    <DashboardShell>
      <div className="flex flex-col space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <Heading level="h1">E-Dossier Admin</Heading>
            <Text color="muted">Manage assessment frameworks and system settings</Text>
          </div>
        </div>

        {/* Submodule Navigation */}
        <div className="flex flex-wrap items-center gap-4">
          <Link href="/dashboard/talent/dossier">
            <Button variant="outline" className="h-9">
              <BarChart2 className="mr-2 h-4 w-4" />
              Employee Overview
            </Button>
          </Link>
          <Link href="/dashboard/talent/dossier/performance">
            <Button variant="outline" className="h-9">
              <BarChart2 className="mr-2 h-4 w-4" />
              Performance Matrix
            </Button>
          </Link>
          <Link href="/dashboard/talent/dossier/documents">
            <Button variant="outline" className="h-9">
              <FileText className="mr-2 h-4 w-4" />
              Document Management
            </Button>
          </Link>
          <Link href="/dashboard/talent/dossier/admin">
            <Button variant="secondary" className="h-9">
              <Settings className="mr-2 h-4 w-4" />
              Admin
            </Button>
          </Link>
        </div>

        <Tabs defaultValue="assessments" className="space-y-6">
          <TabsList>
            <TabsTrigger value="assessments">Assessment Frameworks</TabsTrigger>
            <TabsTrigger value="users">User Management</TabsTrigger>
            <TabsTrigger value="settings">System Settings</TabsTrigger>
          </TabsList>

          <TabsContent value="assessments" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Assessment Framework Management</CardTitle>
                <CardDescription>
                  Configure and customize assessment frameworks for employee evaluations
                </CardDescription>
              </CardHeader>
              <CardContent>
                <AssessmentForm />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="users" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>User Management</CardTitle>
                <CardDescription>Manage user access and permissions for the E-Dossier system</CardDescription>
              </CardHeader>
              <CardContent className="h-[400px] flex items-center justify-center text-muted-foreground">
                User management interface placeholder
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="settings" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>System Settings</CardTitle>
                <CardDescription>Configure global settings for the E-Dossier system</CardDescription>
              </CardHeader>
              <CardContent className="h-[400px] flex items-center justify-center text-muted-foreground">
                System settings interface placeholder
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardShell>
  )
}
