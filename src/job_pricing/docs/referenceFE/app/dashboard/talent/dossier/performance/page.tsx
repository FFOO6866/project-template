"use client"

import { DashboardShell } from "@/components/dashboard-shell"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Filter, Search, Download, FileText, BarChart2, Settings, Info } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Heading } from "@/components/ui/heading"
import { Text } from "@/components/ui/text"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import Link from "next/link"
import { PerformanceMatrixChart } from "@/components/performance-matrix-chart"
import { Badge } from "@/components/ui/badge"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { useEffect, useState } from "react"
import { useSearchParams } from "next/navigation"
import { ConsciousnessMapChart } from "@/components/consciousness-map-chart"
import { XFactorRadarChart } from "@/components/x-factor-radar-chart"
import { LeadershipAttributesChart } from "@/components/leadership-attributes-chart"
import { MintzbergRolesChart } from "@/components/mintzberg-roles-chart"
import { FourMindsetsChart } from "@/components/four-mindsets-chart"
import { IRTFChart } from "@/components/irtf-chart"
import { AACCChart } from "@/components/aacc-chart"
import { TeamDynamicsChart } from "@/components/team-dynamics-chart"

// List of all employees
const employees = [
  { id: "alex-morgan", name: "Alex Morgan", role: "Senior Project Manager" },
  { id: "sarah-chen", name: "Sarah Chen", role: "VP of Product" },
  { id: "james-wilson", name: "James Wilson", role: "UX Designer" },
  { id: "olivia-martinez", name: "Olivia Martinez", role: "Marketing Director" },
  { id: "robert-chen", name: "Robert Chen", role: "Software Engineer" },
  { id: "michael-rodriguez", name: "Michael Rodriguez", role: "Data Scientist" },
  { id: "aisha-johnson", name: "Aisha Johnson", role: "Product Manager" },
  { id: "david-kim", name: "David Kim", role: "Operations Manager" },
  { id: "elena-petrov", name: "Elena Petrov", role: "HR Director" },
]

export default function EDossierPerformancePage() {
  const searchParams = useSearchParams()
  const employeeParam = searchParams ? searchParams.get("employee") : null

  // State for selected employee
  const [selectedEmployee, setSelectedEmployee] = useState<string>("")

  // Set the selected employee based on URL parameter when component mounts
  useEffect(() => {
    if (employeeParam) {
      const matchedEmployee = employees.find((e) => e.id === employeeParam)
      if (matchedEmployee) {
        setSelectedEmployee(matchedEmployee.id)
      }
    }
  }, [employeeParam])

  // Get the selected employee's full name
  const getSelectedEmployeeName = () => {
    if (!selectedEmployee) return "Select Employee"
    const employee = employees.find((e) => e.id === selectedEmployee)
    return employee ? `${employee.name} - ${employee.role}` : "Select Employee"
  }

  return (
    <DashboardShell>
      <div className="flex flex-col space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <Heading level="h1">Performance Matrix</Heading>
            <Text color="muted">Comprehensive individual performance assessment frameworks</Text>
          </div>
          <div className="flex items-center gap-2">
            <div className="relative w-64">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input type="search" placeholder="Search employees..." className="w-full pl-8" />
            </div>
            <Button variant="outline" size="icon">
              <Filter className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="sm" className="h-9">
              <Download className="mr-2 h-4 w-4" />
              Export
            </Button>
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
            <Button variant="secondary" className="h-9">
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
            <Button variant="outline" className="h-9">
              <Settings className="mr-2 h-4 w-4" />
              Admin
            </Button>
          </Link>
        </div>

        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <Text size="sm" weight="medium">
              Employee:
            </Text>
            <Select value={selectedEmployee} onValueChange={setSelectedEmployee}>
              <SelectTrigger className="w-[220px] h-9">
                <SelectValue placeholder="Select Employee" />
              </SelectTrigger>
              <SelectContent>
                {employees.map((employee) => (
                  <SelectItem key={employee.id} value={employee.id}>
                    {employee.name} - {employee.role}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-center gap-2">
            <Text size="sm" weight="medium">
              Assessment Period:
            </Text>
            <Select defaultValue="2023">
              <SelectTrigger className="w-[180px] h-9">
                <SelectValue placeholder="2023" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="2023">2023</SelectItem>
                <SelectItem value="2022">2022</SelectItem>
                <SelectItem value="2021">2021</SelectItem>
                <SelectItem value="2020">2020</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Main Performance Matrix and X-Factor */}
        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <div>
                <CardTitle className="flex items-center gap-2">
                  Performance Matrix
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Info className="h-4 w-4 text-muted-foreground cursor-help" />
                      </TooltipTrigger>
                      <TooltipContent className="max-w-sm">
                        <p>
                          The TPC Performance Matrix plots employees based on their performance (results) and potential
                          (capabilities).
                        </p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </CardTitle>
                <CardDescription>Employees plotted by performance and potential</CardDescription>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
                  2023 Assessment
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="h-[400px]">
              <PerformanceMatrixChart selectedMember={selectedEmployee} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <div>
                <CardTitle className="flex items-center gap-2">
                  X-Factor Scoring
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Info className="h-4 w-4 text-muted-foreground cursor-help" />
                      </TooltipTrigger>
                      <TooltipContent className="max-w-sm">
                        <p>
                          X-Factor scoring measures exceptional qualities that differentiate high performers in the TPC
                          context.
                        </p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </CardTitle>
                <CardDescription>Exceptional qualities that differentiate high performers</CardDescription>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
                  2023 Assessment
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="h-[400px]">
              <XFactorRadarChart selectedMember={selectedEmployee} />
            </CardContent>
          </Card>
        </div>

        {/* Consciousness Map */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              Consciousness Map
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Info className="h-4 w-4 text-muted-foreground cursor-help" />
                  </TooltipTrigger>
                  <TooltipContent className="max-w-sm">
                    <p>
                      Based on Dr. David R. Hawkins' Map of Consciousness, this assessment tracks an individual's
                      evolution through stages of awareness and consciousness.
                    </p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </CardTitle>
            <CardDescription>Assessment of consciousness evolution and development</CardDescription>
          </CardHeader>
          <CardContent className="h-[600px]">
            <ConsciousnessMapChart selectedMember={selectedEmployee} />
          </CardContent>
        </Card>

        {/* Assessment Frameworks - 3x2 Grid */}
        <div className="grid gap-6 md:grid-cols-3">
          {/* Row 1 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                Quantum Leadership
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Info className="h-4 w-4 text-muted-foreground cursor-help" />
                    </TooltipTrigger>
                    <TooltipContent className="max-w-sm">
                      <p>
                        TPC's Quantum Leadership framework measures leadership capabilities across multiple dimensions
                        including vision, adaptability, and influence.
                      </p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </CardTitle>
              <CardDescription>Leadership capabilities assessment</CardDescription>
            </CardHeader>
            <CardContent className="h-[400px]">
              <LeadershipAttributesChart selectedMember={selectedEmployee} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                Mintzberg Roles
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Info className="h-4 w-4 text-muted-foreground cursor-help" />
                    </TooltipTrigger>
                    <TooltipContent className="max-w-sm">
                      <p>
                        Based on Henry Mintzberg's management roles framework, this assessment evaluates managers across
                        interpersonal, informational, and decisional roles.
                      </p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </CardTitle>
              <CardDescription>Management roles assessment</CardDescription>
            </CardHeader>
            <CardContent className="h-[400px]">
              <MintzbergRolesChart selectedMember={selectedEmployee} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                4 Mindsets Framework
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Info className="h-4 w-4 text-muted-foreground cursor-help" />
                    </TooltipTrigger>
                    <TooltipContent className="max-w-sm">
                      <p>
                        The 4 Mindsets framework evaluates cognitive approaches across Fixed, Growth, Benefit, and
                        Abundance mindsets, measuring adaptability and potential.
                      </p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </CardTitle>
              <CardDescription>Cognitive approaches assessment</CardDescription>
            </CardHeader>
            <CardContent className="h-[400px]">
              <FourMindsetsChart selectedMember={selectedEmployee} />
            </CardContent>
          </Card>

          {/* Row 2 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                IRTF Assessment
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Info className="h-4 w-4 text-muted-foreground cursor-help" />
                    </TooltipTrigger>
                    <TooltipContent className="max-w-sm">
                      <p>
                        The IRTF (In-search, Research, Think-through, Follow-through) framework evaluates how
                        individuals approach problem-solving and execution across four key dimensions.
                      </p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </CardTitle>
              <CardDescription>Problem-solving approach assessment</CardDescription>
            </CardHeader>
            <CardContent className="h-[400px]">
              <IRTFChart selectedMember={selectedEmployee} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                AACC Assessment
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Info className="h-4 w-4 text-muted-foreground cursor-help" />
                    </TooltipTrigger>
                    <TooltipContent className="max-w-sm">
                      <p>
                        The AACC (Aware-Align-Collaborate-Co-create) framework measures an individual's progression
                        through stages of collaborative maturity and consciousness.
                      </p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </CardTitle>
              <CardDescription>Collaborative maturity assessment</CardDescription>
            </CardHeader>
            <CardContent className="h-[400px]">
              <AACCChart selectedMember={selectedEmployee} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                Roles & Relationship
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Info className="h-4 w-4 text-muted-foreground cursor-help" />
                    </TooltipTrigger>
                    <TooltipContent className="max-w-sm">
                      <p>
                        This assessment evaluates how individuals understand and fulfill their roles within a larger
                        system, measuring factors like role alignment, collaborative value, and relationship quality.
                      </p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </CardTitle>
              <CardDescription>Role fulfillment assessment</CardDescription>
            </CardHeader>
            <CardContent className="h-[400px]">
              <TeamDynamicsChart selectedMember={selectedEmployee} />
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardShell>
  )
}
