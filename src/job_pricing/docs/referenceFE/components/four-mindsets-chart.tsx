"use client"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts"

// Sample data for the 4 Mindsets framework
const mindsetData = {
  "camille-wong-yuk": [
    { mindset: "Fixed Mindset", value: 35, description: "Belief that abilities are static" },
    { mindset: "Growth Mindset", value: 92, description: "Belief that abilities can be developed" },
    { mindset: "Benefit Mindset", value: 88, description: "Focus on collective wellbeing" },
    { mindset: "Abundance Mindset", value: 90, description: "Belief in unlimited possibilities" },
  ],
  "marcel-melhado": [
    { mindset: "Fixed Mindset", value: 42, description: "Belief that abilities are static" },
    { mindset: "Growth Mindset", value: 85, description: "Belief that abilities can be developed" },
    { mindset: "Benefit Mindset", value: 78, description: "Focus on collective wellbeing" },
    { mindset: "Abundance Mindset", value: 82, description: "Belief in unlimited possibilities" },
  ],
  "vivian-ho": [
    { mindset: "Fixed Mindset", value: 30, description: "Belief that abilities are static" },
    { mindset: "Growth Mindset", value: 88, description: "Belief that abilities can be developed" },
    { mindset: "Benefit Mindset", value: 90, description: "Focus on collective wellbeing" },
    { mindset: "Abundance Mindset", value: 85, description: "Belief in unlimited possibilities" },
  ],
  "massie-shen": [
    { mindset: "Fixed Mindset", value: 28, description: "Belief that abilities are static" },
    { mindset: "Growth Mindset", value: 90, description: "Belief that abilities can be developed" },
    { mindset: "Benefit Mindset", value: 82, description: "Focus on collective wellbeing" },
    { mindset: "Abundance Mindset", value: 88, description: "Belief in unlimited possibilities" },
  ],
  "gloria-cai-xinyi": [
    { mindset: "Fixed Mindset", value: 38, description: "Belief that abilities are static" },
    { mindset: "Growth Mindset", value: 84, description: "Belief that abilities can be developed" },
    { mindset: "Benefit Mindset", value: 79, description: "Focus on collective wellbeing" },
    { mindset: "Abundance Mindset", value: 83, description: "Belief in unlimited possibilities" },
  ],
  "egan-valentino": [
    { mindset: "Fixed Mindset", value: 45, description: "Belief that abilities are static" },
    { mindset: "Growth Mindset", value: 80, description: "Belief that abilities can be developed" },
    { mindset: "Benefit Mindset", value: 75, description: "Focus on collective wellbeing" },
    { mindset: "Abundance Mindset", value: 78, description: "Belief in unlimited possibilities" },
  ],
  "madhav-kapoor": [
    { mindset: "Fixed Mindset", value: 32, description: "Belief that abilities are static" },
    { mindset: "Growth Mindset", value: 87, description: "Belief that abilities can be developed" },
    { mindset: "Benefit Mindset", value: 83, description: "Focus on collective wellbeing" },
    { mindset: "Abundance Mindset", value: 85, description: "Belief in unlimited possibilities" },
  ],
  "shauryaa-ladha": [
    { mindset: "Fixed Mindset", value: 36, description: "Belief that abilities are static" },
    { mindset: "Growth Mindset", value: 86, description: "Belief that abilities can be developed" },
    { mindset: "Benefit Mindset", value: 81, description: "Focus on collective wellbeing" },
    { mindset: "Abundance Mindset", value: 84, description: "Belief in unlimited possibilities" },
  ],
  "jane-putri": [
    { mindset: "Fixed Mindset", value: 33, description: "Belief that abilities are static" },
    { mindset: "Growth Mindset", value: 89, description: "Belief that abilities can be developed" },
    { mindset: "Benefit Mindset", value: 85, description: "Focus on collective wellbeing" },
    { mindset: "Abundance Mindset", value: 87, description: "Belief in unlimited possibilities" },
  ],
  "mathew-ling": [
    { mindset: "Fixed Mindset", value: 40, description: "Belief that abilities are static" },
    { mindset: "Growth Mindset", value: 83, description: "Belief that abilities can be developed" },
    { mindset: "Benefit Mindset", value: 80, description: "Focus on collective wellbeing" },
    { mindset: "Abundance Mindset", value: 82, description: "Belief in unlimited possibilities" },
  ],
  "wu-hong-rui": [
    { mindset: "Fixed Mindset", value: 37, description: "Belief that abilities are static" },
    { mindset: "Growth Mindset", value: 85, description: "Belief that abilities can be developed" },
    { mindset: "Benefit Mindset", value: 82, description: "Focus on collective wellbeing" },
    { mindset: "Abundance Mindset", value: 80, description: "Belief in unlimited possibilities" },
  ],
  "ra-won-park": [
    { mindset: "Fixed Mindset", value: 34, description: "Belief that abilities are static" },
    { mindset: "Growth Mindset", value: 88, description: "Belief that abilities can be developed" },
    { mindset: "Benefit Mindset", value: 84, description: "Focus on collective wellbeing" },
    { mindset: "Abundance Mindset", value: 86, description: "Belief in unlimited possibilities" },
  ],
}

interface FourMindsetsChartProps {
  selectedMember?: string
}

export function FourMindsetsChart({ selectedMember = "" }: FourMindsetsChartProps) {
  // Get the data for the selected person
  const data = selectedMember ? mindsetData[selectedMember as keyof typeof mindsetData] || [] : []

  // Define colors for different mindsets
  const getMindsetColor = (mindset: string) => {
    switch (mindset) {
      case "Fixed Mindset":
        return "#ef4444" // Red for fixed mindset (lower is better)
      case "Growth Mindset":
        return "#3b82f6" // Blue for growth mindset
      case "Benefit Mindset":
        return "#10b981" // Green for benefit mindset
      case "Abundance Mindset":
        return "#8b5cf6" // Purple for abundance mindset
      default:
        return "#6b7280" // Gray for unknown
    }
  }

  if (!selectedMember || !data.length) {
    return (
      <div className="w-full h-full flex items-center justify-center">
        <div className="text-muted-foreground">Please select a team member to view data</div>
      </div>
    )
  }

  return (
    <div className="w-full h-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 20, right: 20, left: 50, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
          <XAxis type="number" domain={[0, 100]} tickCount={6} />
          <YAxis dataKey="mindset" type="category" width={100} />
          <Tooltip
            formatter={(value) => [`${value}%`, "Score"]}
            contentStyle={{
              backgroundColor: "white",
              borderRadius: "8px",
              boxShadow: "0 4px 12px rgba(0, 0, 0, 0.1)",
              border: "none",
            }}
            labelFormatter={(label) => {
              const item = data.find((d) => d.mindset === label)
              return `${label}: ${item?.description}`
            }}
          />
          <Bar dataKey="value">
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getMindsetColor(entry.mindset)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
