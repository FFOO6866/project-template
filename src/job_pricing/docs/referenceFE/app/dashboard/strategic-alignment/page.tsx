import { DashboardShell } from "@/components/dashboard-shell"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Download, ZoomIn, ZoomOut } from "lucide-react"
import { Heading } from "@/components/ui/heading"
import { Text } from "@/components/ui/text"
import { Section } from "@/components/ui/section"

export default function StrategicAlignmentPage() {
  return (
    <DashboardShell>
      <div className="flex flex-col space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <Heading level="h1">Strategic Alignment</Heading>
            <Text color="muted">Interactive visualization of HR initiatives linked to organizational goals</Text>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" className="h-9">
              <Download className="mr-2 h-4 w-4" />
              Export
            </Button>
          </div>
        </div>

        <Card className="overflow-hidden">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <div>
              <CardTitle>Strategic Initiative Alignment Map</CardTitle>
              <CardDescription>
                Visualizing how HR initiatives connect to organizational pillars and outcomes
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="icon" className="h-8 w-8">
                <ZoomOut className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="icon" className="h-8 w-8">
                <ZoomIn className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="relative h-[600px] w-full bg-gray-50 p-6">
              <div className="flex h-full items-center justify-center">
                <p className="text-muted-foreground">Strategic alignment visualization placeholder</p>
              </div>
              <div className="absolute bottom-4 right-4 flex items-center gap-2 rounded-lg bg-white p-2 shadow-md">
                <div className="flex items-center gap-1">
                  <div className="h-3 w-3 rounded-full bg-blue-500"></div>
                  <span className="text-xs">HR Initiatives</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="h-3 w-3 rounded-full bg-green-500"></div>
                  <span className="text-xs">Business Outcomes</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="h-3 w-3 rounded-full bg-purple-500"></div>
                  <span className="text-xs">Strategic Pillars</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid gap-6 md:grid-cols-2">
          <Section
            title="Initiative Impact"
            description="Measuring the impact of HR initiatives on organizational goals"
          >
            <Card>
              <CardContent className="h-[300px] flex items-center justify-center text-muted-foreground">
                Initiative impact visualization placeholder
              </CardContent>
            </Card>
          </Section>
          <Section
            title="Strategic Gap Analysis"
            description="Identifying gaps between current initiatives and strategic objectives"
          >
            <Card>
              <CardContent className="h-[300px] flex items-center justify-center text-muted-foreground">
                Gap analysis visualization placeholder
              </CardContent>
            </Card>
          </Section>
        </div>
      </div>
    </DashboardShell>
  )
}
