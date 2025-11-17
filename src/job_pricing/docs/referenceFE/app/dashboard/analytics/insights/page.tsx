import { DashboardShell } from "@/components/dashboard-shell"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Heading } from "@/components/ui/heading"
import { Text } from "@/components/ui/text"
import { Section } from "@/components/ui/section"
import { InsightCard } from "@/components/ui/insight-card"
import { Lightbulb, Zap, TrendingUp, Users, Building2, Download, Filter } from "lucide-react"

export default function AIInsightsPage() {
  return (
    <DashboardShell>
      <div className="flex flex-col space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <Heading level="h1">AI Insights & Recommendations</Heading>
            <Text color="muted">AI-driven insight cards with interactive, narrative-based recommendations</Text>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" className="h-9">
              <Filter className="mr-2 h-4 w-4" />
              Filter
            </Button>
            <Button variant="outline" size="sm" className="h-9">
              <Download className="mr-2 h-4 w-4" />
              Export
            </Button>
          </div>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          <InsightCard
            icon={Zap}
            title="Leadership Development Impact"
            description="Leadership programs are showing positive impact on engagement scores. Consider expanding the mentorship component based on feedback analysis."
            category="People"
            impact="High"
            confidence={92}
          />
          <InsightCard
            icon={Users}
            title="CCC Initiative Expansion"
            description="Consider expanding the CCC initiatives based on positive cultural advocacy trends. Focus on cross-departmental collaboration events."
            category="Process"
            impact="Medium"
            confidence={87}
          />
          <InsightCard
            icon={TrendingUp}
            title="Investment Pillar Attention"
            description="Strategic contribution in the Investment pillar needs attention. Resource allocation analysis shows 23% underinvestment compared to targets."
            category="Performance"
            impact="High"
            confidence={95}
          />
          <InsightCard
            icon={Building2}
            title="Organizational Structure Optimization"
            description="Current span of control in middle management is suboptimal. Consider restructuring to improve information flow and decision-making speed."
            category="Process"
            impact="Medium"
            confidence={83}
          />
          <InsightCard
            icon={Lightbulb}
            title="Talent Retention Risk"
            description="Predictive analysis indicates elevated retention risk in the engineering department. Recommend targeted engagement initiatives."
            category="People"
            impact="High"
            confidence={89}
          />
          <InsightCard
            icon={TrendingUp}
            title="Performance Trend Anomaly"
            description="Unusual pattern detected in Q2 performance metrics for the marketing team. Investigate potential external factors or reporting issues."
            category="Performance"
            impact="Medium"
            confidence={78}
          />
        </div>

        <Section
          title="AI Recommendation Engine"
          description="Interactive scenario modeling based on AI-generated recommendations"
        >
          <Card>
            <CardContent className="h-[400px] flex items-center justify-center text-muted-foreground">
              AI recommendation engine visualization placeholder
            </CardContent>
          </Card>
        </Section>

        <div className="grid gap-6 md:grid-cols-2">
          <Section title="Insight Trends" description="Historical analysis of AI-generated insights and their impact">
            <Card>
              <CardContent className="h-[300px] flex items-center justify-center text-muted-foreground">
                Insight trends visualization placeholder
              </CardContent>
            </Card>
          </Section>
          <Section
            title="Recommendation Effectiveness"
            description="Measuring the impact of implemented AI recommendations"
          >
            <Card>
              <CardContent className="h-[300px] flex items-center justify-center text-muted-foreground">
                Recommendation effectiveness visualization placeholder
              </CardContent>
            </Card>
          </Section>
        </div>
      </div>
    </DashboardShell>
  )
}
