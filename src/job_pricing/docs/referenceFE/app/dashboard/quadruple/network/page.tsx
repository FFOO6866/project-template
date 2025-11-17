import { DashboardShell } from "@/components/dashboard-shell"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { Download, ZoomIn, ZoomOut } from "lucide-react"
import { NetworkGraph } from "@/components/network-graph"

export default function NetworkPage() {
  return (
    <DashboardShell>
      <div className="flex flex-col space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold tracking-tight">Network & Advocacy</h2>
            <p className="text-muted-foreground">
              Force-directed graphs and chord diagrams showing relationship dynamics
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" className="h-9">
              <Download className="mr-2 h-4 w-4" />
              Export
            </Button>
          </div>
        </div>

        <Tabs defaultValue="network" className="space-y-6">
          <TabsList>
            <TabsTrigger value="network">Network Graph</TabsTrigger>
            <TabsTrigger value="influence">Influence Map</TabsTrigger>
            <TabsTrigger value="chord">Relationship Chord</TabsTrigger>
          </TabsList>

          <TabsContent value="network" className="space-y-6">
            <Card className="overflow-hidden">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <div>
                  <CardTitle>Organizational Network Analysis</CardTitle>
                  <CardDescription>Force-directed graph showing communication patterns and influence</CardDescription>
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
                <div className="h-[600px] w-full bg-gray-50 p-6">
                  <NetworkGraph />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="influence" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Influence Heatmap</CardTitle>
                <CardDescription>Visualizing influence patterns across departments and roles</CardDescription>
              </CardHeader>
              <CardContent className="h-[500px] flex items-center justify-center text-muted-foreground">
                Influence heatmap visualization placeholder
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="chord" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Relationship Chord Diagram</CardTitle>
                <CardDescription>Visualizing relationships and interactions between departments</CardDescription>
              </CardHeader>
              <CardContent className="h-[500px] flex items-center justify-center text-muted-foreground">
                Chord diagram visualization placeholder
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Key Influencers</CardTitle>
              <CardDescription>Individuals with the highest network centrality and influence</CardDescription>
            </CardHeader>
            <CardContent className="h-[300px] flex items-center justify-center text-muted-foreground">
              Key influencers visualization placeholder
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Collaboration Patterns</CardTitle>
              <CardDescription>Analysis of cross-functional collaboration and communication</CardDescription>
            </CardHeader>
            <CardContent className="h-[300px] flex items-center justify-center text-muted-foreground">
              Collaboration patterns visualization placeholder
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardShell>
  )
}
