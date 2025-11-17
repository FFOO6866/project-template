"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Heading } from "@/components/ui/heading"
import { Text } from "@/components/ui/text"
import {
  TrendingUp,
  TrendingDown,
  Building2,
  Users,
  Target,
  AlertTriangle,
  CheckCircle,
  Clock,
  BarChart3,
  PieChart,
  Activity,
} from "lucide-react"
import { DashboardShell } from "@/components/dashboard-shell"

export default function MarketIntelligencePage() {
  const [activeTab, setActiveTab] = useState("overview")
  const [selectedIndustry, setSelectedIndustry] = useState("all")
  const [selectedLocation, setSelectedLocation] = useState("singapore")
  const [selectedTimeframe, setSelectedTimeframe] = useState("6months")

  // Market Intelligence Summary Data
  const marketSummary = {
    totalJobs: 2847,
    avgSalaryIncrease: 8.5,
    topSkillsInDemand: ["Digital Transformation", "ESG", "Data Analytics", "Project Management"],
    marketTrend: "growing",
    competitiveIndex: 78,
  }

  // TPC Group specific market data
  const tpcMarketData = [
    {
      role: "Property Development Manager",
      market: "Hot",
      avgSalary: "SGD 8,500 - 12,000",
      demand: "High",
      competition: "Intense",
      keyCompetitors: ["CapitaLand", "City Developments", "UOL Group"],
      trend: "up",
      change: "+12%",
    },
    {
      role: "Hospitality Operations Director",
      market: "Stable",
      avgSalary: "SGD 12,000 - 18,000",
      demand: "Medium",
      competition: "Moderate",
      keyCompetitors: ["Shangri-La", "Marina Bay Sands", "Resorts World"],
      trend: "up",
      change: "+6%",
    },
    {
      role: "Investment Analyst",
      market: "Competitive",
      avgSalary: "SGD 6,500 - 9,500",
      demand: "High",
      competition: "Very High",
      keyCompetitors: ["Temasek", "GIC", "Mapletree"],
      trend: "up",
      change: "+15%",
    },
    {
      role: "Asset Management Specialist",
      market: "Growing",
      avgSalary: "SGD 7,000 - 11,000",
      demand: "Medium",
      competition: "High",
      keyCompetitors: ["Keppel REIT", "CapitaLand Investment", "Frasers Property"],
      trend: "up",
      change: "+9%",
    },
  ]

  // Competitor Analysis Data
  const competitorData = [
    {
      company: "CapitaLand Group",
      industry: "Property Development",
      employees: "13,000+",
      avgSalary: "SGD 8,200",
      benefits: "Comprehensive medical, 15 days AL, Performance bonus",
      strengths: ["Market leader", "Strong brand", "Regional presence"],
      weaknesses: ["Bureaucratic", "Slow decision making"],
      recentMoves: "Launched CapitaLand Investment Management in 2021",
    },
    {
      company: "City Developments Ltd",
      industry: "Property & Hospitality",
      employees: "8,500+",
      avgSalary: "SGD 7,800",
      benefits: "Medical coverage, 14 days AL, Variable bonus",
      strengths: ["Diversified portfolio", "Strong financials", "Innovation focus"],
      weaknesses: ["Limited tech adoption", "Traditional culture"],
      recentMoves: "Acquired Millennium Hotels in 2020",
    },
    {
      company: "Shangri-La Group",
      industry: "Hospitality",
      employees: "40,000+",
      avgSalary: "SGD 6,500",
      benefits: "Hotel discounts, Medical, 12 days AL",
      strengths: ["Luxury brand", "Asian expertise", "Service excellence"],
      weaknesses: ["COVID impact", "High turnover"],
      recentMoves: "Digital transformation initiative launched 2023",
    },
    {
      company: "Frasers Property",
      industry: "Real Estate",
      employees: "3,500+",
      avgSalary: "SGD 8,900",
      benefits: "Flexible work, Medical, 16 days AL, Wellness programs",
      strengths: ["Sustainability focus", "Innovation", "Employee-centric"],
      weaknesses: ["Smaller scale", "Limited brand recognition"],
      recentMoves: "Launched Frasers Experience in 2022",
    },
  ]

  // AI Insights Data
  const aiInsights = [
    {
      type: "Opportunity",
      title: "Digital Transformation Roles",
      description:
        "High demand for digital transformation specialists in property sector. TPC can capitalize by offering competitive packages.",
      impact: "High",
      urgency: "Medium",
      recommendation: "Create specialized digital roles with 15-20% salary premium",
    },
    {
      type: "Threat",
      title: "Hospitality Talent Shortage",
      description: "Post-COVID recovery creating intense competition for experienced hospitality professionals.",
      impact: "High",
      urgency: "High",
      recommendation: "Implement retention bonuses and accelerated career progression",
    },
    {
      type: "Trend",
      title: "ESG Expertise Premium",
      description: "Sustainability and ESG roles commanding 25% salary premium across property and investment sectors.",
      impact: "Medium",
      urgency: "Low",
      recommendation: "Develop internal ESG capabilities and adjust compensation bands",
    },
    {
      type: "Risk",
      title: "Tech Talent War",
      description:
        "Technology roles in traditional industries facing 40% salary inflation due to tech company competition.",
      impact: "High",
      urgency: "High",
      recommendation: "Review tech role compensation and consider equity components",
    },
  ]

  const getMarketTrendIcon = (trend: string) => {
    return trend === "up" ? (
      <TrendingUp className="h-4 w-4 text-green-500" />
    ) : (
      <TrendingDown className="h-4 w-4 text-red-500" />
    )
  }

  const getInsightIcon = (type: string) => {
    switch (type) {
      case "Opportunity":
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case "Threat":
        return <AlertTriangle className="h-5 w-5 text-red-500" />
      case "Trend":
        return <TrendingUp className="h-5 w-5 text-blue-500" />
      case "Risk":
        return <AlertTriangle className="h-5 w-5 text-orange-500" />
      default:
        return <Activity className="h-5 w-5 text-gray-500" />
    }
  }

  return (
    <DashboardShell>
      <div className="space-y-6">
        <div>
          <Heading level="h1" className="mb-2">
            Market Intelligence Hub
          </Heading>
          <Text size="lg" color="muted">
            Real-time market insights and competitive intelligence for TPC Group's talent strategy
          </Text>
        </div>

        {/* Summary Dashboard */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Job Postings</CardTitle>
              <Building2 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{marketSummary.totalJobs.toLocaleString()}</div>
              <Text size="xs" color="muted">
                Property & Hospitality sectors
              </Text>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg Salary Growth</CardTitle>
              <TrendingUp className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">+{marketSummary.avgSalaryIncrease}%</div>
              <Text size="xs" color="muted">
                Year over year
              </Text>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Market Competitiveness</CardTitle>
              <Target className="h-4 w-4 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">{marketSummary.competitiveIndex}/100</div>
              <Text size="xs" color="muted">
                TPC competitive index
              </Text>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Top Skills Demand</CardTitle>
              <Users className="h-4 w-4 text-purple-500" />
            </CardHeader>
            <CardContent>
              <div className="space-y-1">
                {marketSummary.topSkillsInDemand.slice(0, 2).map((skill, index) => (
                  <Badge key={index} variant="secondary" className="text-xs">
                    {skill}
                  </Badge>
                ))}
              </div>
              <Text size="xs" color="muted">
                Most in-demand
              </Text>
            </CardContent>
          </Card>
        </div>

        {/* Filters */}
        <Card>
          <CardHeader>
            <CardTitle>Market Filters</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Industry Focus</label>
                <select
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                  value={selectedIndustry}
                  onChange={(e) => setSelectedIndustry(e.target.value)}
                >
                  <option value="all">All TPC Sectors</option>
                  <option value="property">Property Development</option>
                  <option value="hospitality">Hospitality</option>
                  <option value="investment">Investment Management</option>
                  <option value="asset">Asset Management</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Location</label>
                <select
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                  value={selectedLocation}
                  onChange={(e) => setSelectedLocation(e.target.value)}
                >
                  <option value="singapore">Singapore</option>
                  <option value="malaysia">Malaysia</option>
                  <option value="thailand">Thailand</option>
                  <option value="indonesia">Indonesia</option>
                  <option value="regional">Regional</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Timeframe</label>
                <select
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                  value={selectedTimeframe}
                  onChange={(e) => setSelectedTimeframe(e.target.value)}
                >
                  <option value="1month">Last Month</option>
                  <option value="3months">Last 3 Months</option>
                  <option value="6months">Last 6 Months</option>
                  <option value="1year">Last Year</option>
                </select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Tab Navigation */}
        <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
          <button
            onClick={() => setActiveTab("overview")}
            className={`flex-1 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
              activeTab === "overview" ? "bg-white text-gray-900 shadow-sm" : "text-gray-600 hover:text-gray-900"
            }`}
          >
            Market Overview
          </button>
          <button
            onClick={() => setActiveTab("trends")}
            className={`flex-1 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
              activeTab === "trends" ? "bg-white text-gray-900 shadow-sm" : "text-gray-600 hover:text-gray-900"
            }`}
          >
            Market Trends
          </button>
          <button
            onClick={() => setActiveTab("competitors")}
            className={`flex-1 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
              activeTab === "competitors" ? "bg-white text-gray-900 shadow-sm" : "text-gray-600 hover:text-gray-900"
            }`}
          >
            Competitor Analysis
          </button>
          <button
            onClick={() => setActiveTab("insights")}
            className={`flex-1 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
              activeTab === "insights" ? "bg-white text-gray-900 shadow-sm" : "text-gray-600 hover:text-gray-900"
            }`}
          >
            AI Insights
          </button>
        </div>

        {/* Market Overview Tab */}
        {activeTab === "overview" && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>TPC Group Role Market Analysis</CardTitle>
                <CardDescription>Key roles across TPC's business portfolio and their market dynamics</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {tpcMarketData.map((role, index) => (
                    <div key={index} className="border rounded-lg p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <Heading level="h4" className="mb-1">
                            {role.role}
                          </Heading>
                          <Text size="sm" color="muted">
                            {role.avgSalary}
                          </Text>
                        </div>
                        <div className="flex items-center gap-2">
                          {getMarketTrendIcon(role.trend)}
                          <Text
                            size="sm"
                            weight="medium"
                            className={role.trend === "up" ? "text-green-600" : "text-red-600"}
                          >
                            {role.change}
                          </Text>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-3">
                        <div>
                          <Text size="xs" color="muted">
                            Market Status
                          </Text>
                          <Badge
                            variant={
                              role.market === "Hot"
                                ? "destructive"
                                : role.market === "Growing"
                                  ? "default"
                                  : "secondary"
                            }
                          >
                            {role.market}
                          </Badge>
                        </div>
                        <div>
                          <Text size="xs" color="muted">
                            Demand Level
                          </Text>
                          <Text size="sm" weight="medium">
                            {role.demand}
                          </Text>
                        </div>
                        <div>
                          <Text size="xs" color="muted">
                            Competition
                          </Text>
                          <Text size="sm" weight="medium">
                            {role.competition}
                          </Text>
                        </div>
                        <div>
                          <Text size="xs" color="muted">
                            Trend
                          </Text>
                          <Text size="sm" weight="medium" className="text-green-600">
                            {role.change}
                          </Text>
                        </div>
                      </div>

                      <div>
                        <Text size="xs" color="muted" className="mb-1">
                          Key Competitors:
                        </Text>
                        <div className="flex flex-wrap gap-1">
                          {role.keyCompetitors.map((competitor, idx) => (
                            <Badge key={idx} variant="outline" className="text-xs">
                              {competitor}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Market Trends Tab */}
        {activeTab === "trends" && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="h-5 w-5" />
                    Salary Trends by Sector
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <Text size="sm">Property Development</Text>
                      <div className="flex items-center gap-2">
                        <div className="w-24 bg-gray-200 rounded-full h-2">
                          <div className="bg-green-500 h-2 rounded-full" style={{ width: "75%" }}></div>
                        </div>
                        <Text size="sm" weight="medium" className="text-green-600">
                          +12%
                        </Text>
                      </div>
                    </div>
                    <div className="flex justify-between items-center">
                      <Text size="sm">Hospitality</Text>
                      <div className="flex items-center gap-2">
                        <div className="w-24 bg-gray-200 rounded-full h-2">
                          <div className="bg-blue-500 h-2 rounded-full" style={{ width: "45%" }}></div>
                        </div>
                        <Text size="sm" weight="medium" className="text-blue-600">
                          +6%
                        </Text>
                      </div>
                    </div>
                    <div className="flex justify-between items-center">
                      <Text size="sm">Investment Management</Text>
                      <div className="flex items-center gap-2">
                        <div className="w-24 bg-gray-200 rounded-full h-2">
                          <div className="bg-purple-500 h-2 rounded-full" style={{ width: "85%" }}></div>
                        </div>
                        <Text size="sm" weight="medium" className="text-purple-600">
                          +15%
                        </Text>
                      </div>
                    </div>
                    <div className="flex justify-between items-center">
                      <Text size="sm">Asset Management</Text>
                      <div className="flex items-center gap-2">
                        <div className="w-24 bg-gray-200 rounded-full h-2">
                          <div className="bg-orange-500 h-2 rounded-full" style={{ width: "55%" }}></div>
                        </div>
                        <Text size="sm" weight="medium" className="text-orange-600">
                          +9%
                        </Text>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <PieChart className="h-5 w-5" />
                    Skills in High Demand
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {[
                      { skill: "Digital Transformation", demand: 92, growth: "+28%" },
                      { skill: "ESG & Sustainability", demand: 78, growth: "+45%" },
                      { skill: "Data Analytics", demand: 85, growth: "+22%" },
                      { skill: "Project Management", demand: 71, growth: "+15%" },
                      { skill: "Customer Experience", demand: 68, growth: "+18%" },
                    ].map((item, index) => (
                      <div key={index} className="flex justify-between items-center">
                        <div>
                          <Text size="sm" weight="medium">
                            {item.skill}
                          </Text>
                          <Text size="xs" color="muted">
                            Demand: {item.demand}%
                          </Text>
                        </div>
                        <Badge variant="secondary">{item.growth}</Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Regional Market Comparison</CardTitle>
                <CardDescription>Salary benchmarks across TPC's operational markets</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full border-collapse">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-2 text-sm font-medium">Role Level</th>
                        <th className="text-left p-2 text-sm font-medium">Singapore</th>
                        <th className="text-left p-2 text-sm font-medium">Malaysia</th>
                        <th className="text-left p-2 text-sm font-medium">Thailand</th>
                        <th className="text-left p-2 text-sm font-medium">Indonesia</th>
                        <th className="text-left p-2 text-sm font-medium">Growth Trend</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="border-b">
                        <td className="p-2 text-sm font-medium">Director Level</td>
                        <td className="p-2 text-sm">SGD 15,000 - 25,000</td>
                        <td className="p-2 text-sm">MYR 18,000 - 28,000</td>
                        <td className="p-2 text-sm">THB 120,000 - 180,000</td>
                        <td className="p-2 text-sm">IDR 45M - 70M</td>
                        <td className="p-2 text-sm text-green-600">+8-12%</td>
                      </tr>
                      <tr className="border-b">
                        <td className="p-2 text-sm font-medium">Manager Level</td>
                        <td className="p-2 text-sm">SGD 8,000 - 15,000</td>
                        <td className="p-2 text-sm">MYR 10,000 - 18,000</td>
                        <td className="p-2 text-sm">THB 60,000 - 120,000</td>
                        <td className="p-2 text-sm">IDR 25M - 45M</td>
                        <td className="p-2 text-sm text-green-600">+6-10%</td>
                      </tr>
                      <tr className="border-b">
                        <td className="p-2 text-sm font-medium">Senior Executive</td>
                        <td className="p-2 text-sm">SGD 5,000 - 8,000</td>
                        <td className="p-2 text-sm">MYR 6,000 - 10,000</td>
                        <td className="p-2 text-sm">THB 35,000 - 60,000</td>
                        <td className="p-2 text-sm">IDR 15M - 25M</td>
                        <td className="p-2 text-sm text-blue-600">+4-8%</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Competitor Analysis Tab */}
        {activeTab === "competitors" && (
          <div className="space-y-6">
            {competitorData.map((competitor, index) => (
              <Card key={index}>
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle>{competitor.company}</CardTitle>
                      <CardDescription>
                        {competitor.industry} • {competitor.employees} employees
                      </CardDescription>
                    </div>
                    <Badge variant="outline">{competitor.avgSalary} avg</Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-4">
                      <div>
                        <Text size="sm" weight="medium" className="mb-2">
                          Benefits Package
                        </Text>
                        <Text size="sm" color="muted">
                          {competitor.benefits}
                        </Text>
                      </div>
                      <div>
                        <Text size="sm" weight="medium" className="mb-2">
                          Recent Strategic Moves
                        </Text>
                        <Text size="sm" color="muted">
                          {competitor.recentMoves}
                        </Text>
                      </div>
                    </div>
                    <div className="space-y-4">
                      <div>
                        <Text size="sm" weight="medium" className="mb-2">
                          Key Strengths
                        </Text>
                        <div className="flex flex-wrap gap-1">
                          {competitor.strengths.map((strength, idx) => (
                            <Badge key={idx} variant="secondary" className="text-xs">
                              {strength}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      <div>
                        <Text size="sm" weight="medium" className="mb-2">
                          Potential Weaknesses
                        </Text>
                        <div className="flex flex-wrap gap-1">
                          {competitor.weaknesses.map((weakness, idx) => (
                            <Badge key={idx} variant="outline" className="text-xs">
                              {weakness}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* AI Insights Tab */}
        {activeTab === "insights" && (
          <div className="space-y-6">
            {aiInsights.map((insight, index) => (
              <Card key={index}>
                <CardHeader>
                  <div className="flex items-start gap-3">
                    {getInsightIcon(insight.type)}
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <CardTitle className="text-lg">{insight.title}</CardTitle>
                        <Badge
                          variant={
                            insight.type === "Opportunity"
                              ? "default"
                              : insight.type === "Threat"
                                ? "destructive"
                                : "secondary"
                          }
                        >
                          {insight.type}
                        </Badge>
                      </div>
                      <Text size="sm" color="muted">
                        {insight.description}
                      </Text>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div>
                      <Text size="xs" color="muted">
                        Impact Level
                      </Text>
                      <Badge
                        variant={
                          insight.impact === "High"
                            ? "destructive"
                            : insight.impact === "Medium"
                              ? "default"
                              : "secondary"
                        }
                      >
                        {insight.impact}
                      </Badge>
                    </div>
                    <div>
                      <Text size="xs" color="muted">
                        Urgency
                      </Text>
                      <Badge
                        variant={
                          insight.urgency === "High"
                            ? "destructive"
                            : insight.urgency === "Medium"
                              ? "default"
                              : "secondary"
                        }
                      >
                        {insight.urgency}
                      </Badge>
                    </div>
                    <div>
                      <Text size="xs" color="muted">
                        Status
                      </Text>
                      <div className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        <Text size="xs">Under Review</Text>
                      </div>
                    </div>
                  </div>
                  <div className="p-3 bg-blue-50 rounded-lg">
                    <Text size="sm" weight="medium" className="mb-1">
                      Recommended Action
                    </Text>
                    <Text size="sm">{insight.recommendation}</Text>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </DashboardShell>
  )
}
