"use client"
import { useState } from "react"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, Legend } from "recharts"
import { Button } from "@/components/ui/button"
import { ChevronDown, Info } from "lucide-react"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Tooltip as UITooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"

// Attribute descriptions for tooltips
const attributeDescriptions = {
  Followership: "Respects & aligns with leadership vision & values.",
  "Coaching & Compassionate Leadership": "Supports others' growth & well-being through guidance & care.",
  "Leadership Drive": "Believes in own potential & contributions to own happiness & success.",
  "Collaboration & Teamwork":
    "Values collaboration, seeks harmony & fosters teamwork. [Mintzberg's Collaborative mindset]",
  "Strategic Partnerships": "Develops & nurtures partnerships for collaboration & synergy.",
  "Conflict Management": "Manages conflicts openly & transparently.",
  Coherency: "Seeks understanding & alignment within the organizational context.",
  Stewardship: "Ethical management of resources with truthfulness, integrity & accountability.",
  "Creativity & Critical Thinking":
    "Seeks alternative perspectives & turns ideas into practical results. [Mintzberg's Analytical mindset]",
  Entrepreneurship: "Adapts to ambiguity & seeks opportunities with perseverance. [Mintzberg's Action mindset]",
  "Commitment to Self-cultivation":
    "Proactively cultivates personal growth & clarity of purpose. [Mintzberg's Reflective mindset]",
  "Holistic Worldview & Attitude":
    "Considers broader impact & adopts a positive attitude. [Mintzberg's Worldly mindset]",
}

// Updated data with all 12 quantum leadership attributes
const leadershipData = {
  "camille-wong-yuk": [
    { attribute: "Followership", value: 95 },
    { attribute: "Coaching & Compassionate Leadership", value: 90 },
    { attribute: "Leadership Drive", value: 92 },
    { attribute: "Collaboration & Teamwork", value: 88 },
    { attribute: "Strategic Partnerships", value: 85 },
    { attribute: "Conflict Management", value: 94 },
    { attribute: "Coherency", value: 96 },
    { attribute: "Stewardship", value: 91 },
    { attribute: "Creativity & Critical Thinking", value: 93 },
    { attribute: "Entrepreneurship", value: 89 },
    { attribute: "Commitment to Self-cultivation", value: 94 },
    { attribute: "Holistic Worldview & Attitude", value: 92 },
  ],
  "marcel-melhado": [
    { attribute: "Followership", value: 82 },
    { attribute: "Coaching & Compassionate Leadership", value: 88 },
    { attribute: "Leadership Drive", value: 80 },
    { attribute: "Collaboration & Teamwork", value: 75 },
    { attribute: "Strategic Partnerships", value: 90 },
    { attribute: "Conflict Management", value: 78 },
    { attribute: "Coherency", value: 85 },
    { attribute: "Stewardship", value: 80 },
    { attribute: "Creativity & Critical Thinking", value: 86 },
    { attribute: "Entrepreneurship", value: 84 },
    { attribute: "Commitment to Self-cultivation", value: 79 },
    { attribute: "Holistic Worldview & Attitude", value: 81 },
  ],
  "vivian-ho": [
    { attribute: "Followership", value: 88 },
    { attribute: "Coaching & Compassionate Leadership", value: 82 },
    { attribute: "Leadership Drive", value: 85 },
    { attribute: "Collaboration & Teamwork", value: 80 },
    { attribute: "Strategic Partnerships", value: 92 },
    { attribute: "Conflict Management", value: 84 },
    { attribute: "Coherency", value: 90 },
    { attribute: "Stewardship", value: 83 },
    { attribute: "Creativity & Critical Thinking", value: 87 },
    { attribute: "Entrepreneurship", value: 81 },
    { attribute: "Commitment to Self-cultivation", value: 86 },
    { attribute: "Holistic Worldview & Attitude", value: 89 },
  ],
  "massie-shen": [
    { attribute: "Followership", value: 90 },
    { attribute: "Coaching & Compassionate Leadership", value: 87 },
    { attribute: "Leadership Drive", value: 93 },
    { attribute: "Collaboration & Teamwork", value: 89 },
    { attribute: "Strategic Partnerships", value: 84 },
    { attribute: "Conflict Management", value: 91 },
    { attribute: "Coherency", value: 88 },
    { attribute: "Stewardship", value: 86 },
    { attribute: "Creativity & Critical Thinking", value: 90 },
    { attribute: "Entrepreneurship", value: 85 },
    { attribute: "Commitment to Self-cultivation", value: 92 },
    { attribute: "Holistic Worldview & Attitude", value: 87 },
  ],
  "gloria-cai-xinyi": [
    { attribute: "Followership", value: 84 },
    { attribute: "Coaching & Compassionate Leadership", value: 89 },
    { attribute: "Leadership Drive", value: 82 },
    { attribute: "Collaboration & Teamwork", value: 78 },
    { attribute: "Strategic Partnerships", value: 85 },
    { attribute: "Conflict Management", value: 80 },
    { attribute: "Coherency", value: 87 },
    { attribute: "Stewardship", value: 83 },
    { attribute: "Creativity & Critical Thinking", value: 81 },
    { attribute: "Entrepreneurship", value: 86 },
    { attribute: "Commitment to Self-cultivation", value: 79 },
    { attribute: "Holistic Worldview & Attitude", value: 84 },
  ],
  "egan-valentino": [
    { attribute: "Followership", value: 78 },
    { attribute: "Coaching & Compassionate Leadership", value: 92 },
    { attribute: "Leadership Drive", value: 80 },
    { attribute: "Collaboration & Teamwork", value: 85 },
    { attribute: "Strategic Partnerships", value: 79 },
    { attribute: "Conflict Management", value: 83 },
    { attribute: "Coherency", value: 81 },
    { attribute: "Stewardship", value: 88 },
    { attribute: "Creativity & Critical Thinking", value: 84 },
    { attribute: "Entrepreneurship", value: 91 },
    { attribute: "Commitment to Self-cultivation", value: 82 },
    { attribute: "Holistic Worldview & Attitude", value: 80 },
  ],
  "madhav-kapoor": [
    { attribute: "Followership", value: 91 },
    { attribute: "Coaching & Compassionate Leadership", value: 85 },
    { attribute: "Leadership Drive", value: 87 },
    { attribute: "Collaboration & Teamwork", value: 93 },
    { attribute: "Strategic Partnerships", value: 88 },
    { attribute: "Conflict Management", value: 82 },
    { attribute: "Coherency", value: 84 },
    { attribute: "Stewardship", value: 80 },
    { attribute: "Creativity & Critical Thinking", value: 92 },
    { attribute: "Entrepreneurship", value: 89 },
    { attribute: "Commitment to Self-cultivation", value: 83 },
    { attribute: "Holistic Worldview & Attitude", value: 86 },
  ],
  "shauryaa-ladha": [
    { attribute: "Followership", value: 86 },
    { attribute: "Coaching & Compassionate Leadership", value: 83 },
    { attribute: "Leadership Drive", value: 89 },
    { attribute: "Collaboration & Teamwork", value: 82 },
    { attribute: "Strategic Partnerships", value: 87 },
    { attribute: "Conflict Management", value: 85 },
    { attribute: "Coherency", value: 90 },
    { attribute: "Stewardship", value: 84 },
    { attribute: "Creativity & Critical Thinking", value: 88 },
    { attribute: "Entrepreneurship", value: 83 },
    { attribute: "Commitment to Self-cultivation", value: 91 },
    { attribute: "Holistic Worldview & Attitude", value: 85 },
  ],
  "jane-putri": [
    { attribute: "Followership", value: 93 },
    { attribute: "Coaching & Compassionate Leadership", value: 84 },
    { attribute: "Leadership Drive", value: 86 },
    { attribute: "Collaboration & Teamwork", value: 81 },
    { attribute: "Strategic Partnerships", value: 89 },
    { attribute: "Conflict Management", value: 87 },
    { attribute: "Coherency", value: 85 },
    { attribute: "Stewardship", value: 82 },
    { attribute: "Creativity & Critical Thinking", value: 90 },
    { attribute: "Entrepreneurship", value: 83 },
    { attribute: "Commitment to Self-cultivation", value: 88 },
    { attribute: "Holistic Worldview & Attitude", value: 91 },
  ],
  "mathew-ling": [
    { attribute: "Followership", value: 85 },
    { attribute: "Coaching & Compassionate Leadership", value: 88 },
    { attribute: "Leadership Drive", value: 83 },
    { attribute: "Collaboration & Teamwork", value: 87 },
    { attribute: "Strategic Partnerships", value: 81 },
    { attribute: "Conflict Management", value: 84 },
    { attribute: "Coherency", value: 82 },
    { attribute: "Stewardship", value: 89 },
    { attribute: "Creativity & Critical Thinking", value: 86 },
    { attribute: "Entrepreneurship", value: 90 },
    { attribute: "Commitment to Self-cultivation", value: 84 },
    { attribute: "Holistic Worldview & Attitude", value: 83 },
  ],
  "wu-hong-rui": [
    { attribute: "Followership", value: 82 },
    { attribute: "Coaching & Compassionate Leadership", value: 90 },
    { attribute: "Leadership Drive", value: 84 },
    { attribute: "Collaboration & Teamwork", value: 79 },
    { attribute: "Strategic Partnerships", value: 83 },
    { attribute: "Conflict Management", value: 86 },
    { attribute: "Coherency", value: 80 },
    { attribute: "Stewardship", value: 85 },
    { attribute: "Creativity & Critical Thinking", value: 81 },
    { attribute: "Entrepreneurship", value: 92 },
    { attribute: "Commitment to Self-cultivation", value: 84 },
    { attribute: "Holistic Worldview & Attitude", value: 82 },
  ],
  "ra-won-park": [
    { attribute: "Followership", value: 87 },
    { attribute: "Coaching & Compassionate Leadership", value: 85 },
    { attribute: "Leadership Drive", value: 90 },
    { attribute: "Collaboration & Teamwork", value: 83 },
    { attribute: "Strategic Partnerships", value: 86 },
    { attribute: "Conflict Management", value: 88 },
    { attribute: "Coherency", value: 84 },
    { attribute: "Stewardship", value: 87 },
    { attribute: "Creativity & Critical Thinking", value: 89 },
    { attribute: "Entrepreneurship", value: 85 },
    { attribute: "Commitment to Self-cultivation", value: 91 },
    { attribute: "Holistic Worldview & Attitude", value: 86 },
  ],
}

// Color legend for the chart
const colorLegend = [
  { value: "Excellent (90-100)", color: "#16a34a" },
  { value: "Good (80-89)", color: "#2563eb" },
  { value: "Average (70-79)", color: "#f59e0b" },
  { value: "Below Average (<70)", color: "#dc2626" },
]

interface LeadershipAttributesChartProps {
  selectedMember?: string
}

export function LeadershipAttributesChart({ selectedMember = "" }: LeadershipAttributesChartProps) {
  // State for sorting options
  const [sortBy, setSortBy] = useState<"default" | "ascending" | "descending">("default")

  // Get the data for the selected person
  const data = selectedMember ? leadershipData[selectedMember as keyof typeof leadershipData] || [] : []

  // Sort the data based on the selected option
  const sortedData = [...data].sort((a, b) => {
    if (sortBy === "ascending") return a.value - b.value
    if (sortBy === "descending") return b.value - a.value
    return 0 // default order
  })

  // Define colors for different attribute ranges
  const getBarColor = (value: number) => {
    if (value >= 90) return "#16a34a" // Green for excellent
    if (value >= 80) return "#2563eb" // Blue for good
    if (value >= 70) return "#f59e0b" // Amber for average
    return "#dc2626" // Red for below average
  }

  // Calculate average score
  const averageScore = data.length ? Math.round(data.reduce((sum, item) => sum + item.value, 0) / data.length) : 0

  if (!selectedMember || !data.length) {
    return (
      <div className="w-full h-full flex items-center justify-center">
        <div className="text-muted-foreground">Please select a team member to view data</div>
      </div>
    )
  }

  // Custom tooltip component for the chart
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div className="bg-white p-3 rounded-lg shadow-md border border-gray-200">
          <p className="font-medium">{data.attribute}</p>
          <p className="text-sm text-gray-600">
            {attributeDescriptions[data.attribute as keyof typeof attributeDescriptions]}
          </p>
          <p className="font-bold mt-1">{`Score: ${data.value}%`}</p>
        </div>
      )
    }
    return null
  }

  return (
    <div className="w-full h-full flex flex-col">
      <div className="flex justify-between items-center mb-4 px-2">
        <div className="flex items-center gap-2">
          <span className="font-medium">Average Score: </span>
          <span
            className={`font-bold ${
              averageScore >= 90
                ? "text-green-600"
                : averageScore >= 80
                  ? "text-blue-600"
                  : averageScore >= 70
                    ? "text-amber-600"
                    : "text-red-600"
            }`}
          >
            {averageScore}%
          </span>
        </div>
        <div className="flex items-center gap-2">
          <TooltipProvider>
            <UITooltip>
              <TooltipTrigger asChild>
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  <Info className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent className="max-w-xs">
                <p>This chart shows quantum leadership attributes scores. Hover over bars for details.</p>
              </TooltipContent>
            </UITooltip>
          </TooltipProvider>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" className="h-8">
                Sort <ChevronDown className="ml-1 h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              <DropdownMenuItem onClick={() => setSortBy("default")}>Default Order</DropdownMenuItem>
              <DropdownMenuItem onClick={() => setSortBy("ascending")}>Lowest to Highest</DropdownMenuItem>
              <DropdownMenuItem onClick={() => setSortBy("descending")}>Highest to Lowest</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      <div className="flex-1">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={sortedData} layout="vertical" margin={{ top: 20, right: 20, left: 180, bottom: 30 }}>
            <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
            <XAxis type="number" domain={[0, 100]} tickCount={6} />
            <YAxis dataKey="attribute" type="category" width={170} tick={{ fontSize: 11 }} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="value">
              {Array.isArray(sortedData) &&
                sortedData.map((entry, index) => <Cell key={`cell-${index}`} fill={getBarColor(entry.value)} />)}
            </Bar>
            <Legend
              payload={colorLegend.map((item) => ({
                value: item.value,
                type: "square",
                color: item.color,
              }))}
              verticalAlign="bottom"
              height={36}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
