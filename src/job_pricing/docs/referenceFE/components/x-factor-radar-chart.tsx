"use client"

import { useEffect, useState } from "react"
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Legend,
  ResponsiveContainer,
  Tooltip,
} from "recharts"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

// Updated data for management trainees
const teamMembersData = {
  "camille-wong-yuk": [
    { axis: "Followership", value: 85 },
    { axis: "Coaching & Compassionate Leadership", value: 78 },
    { axis: "Leadership Drive", value: 82 },
    { axis: "Collaboration & Teamwork", value: 88 },
    { axis: "Strategic Partnerships", value: 90 },
    { axis: "Conflict Management", value: 83 },
  ],
  "marcel-melhado": [
    { axis: "Followership", value: 80 },
    { axis: "Coaching & Compassionate Leadership", value: 85 },
    { axis: "Leadership Drive", value: 75 },
    { axis: "Collaboration & Teamwork", value: 83 },
    { axis: "Strategic Partnerships", value: 87 },
    { axis: "Conflict Management", value: 81 },
  ],
  "vivian-ho": [
    { axis: "Followership", value: 88 },
    { axis: "Coaching & Compassionate Leadership", value: 79 },
    { axis: "Leadership Drive", value: 81 },
    { axis: "Collaboration & Teamwork", value: 90 },
    { axis: "Strategic Partnerships", value: 84 },
    { axis: "Conflict Management", value: 86 },
  ],
  "massie-shen": [
    { axis: "Followership", value: 86 },
    { axis: "Coaching & Compassionate Leadership", value: 80 },
    { axis: "Leadership Drive", value: 83 },
    { axis: "Collaboration & Teamwork", value: 85 },
    { axis: "Strategic Partnerships", value: 82 },
    { axis: "Conflict Management", value: 84 },
  ],
  "gloria-cai-xinyi": [
    { axis: "Followership", value: 84 },
    { axis: "Coaching & Compassionate Leadership", value: 87 },
    { axis: "Leadership Drive", value: 81 },
    { axis: "Collaboration & Teamwork", value: 79 },
    { axis: "Strategic Partnerships", value: 86 },
    { axis: "Conflict Management", value: 85 },
  ],
  "egan-valentino": [
    { axis: "Followership", value: 78 },
    { axis: "Coaching & Compassionate Leadership", value: 89 },
    { axis: "Leadership Drive", value: 82 },
    { axis: "Collaboration & Teamwork", value: 80 },
    { axis: "Strategic Partnerships", value: 85 },
    { axis: "Conflict Management", value: 83 },
  ],
  "madhav-kapoor": [
    { axis: "Followership", value: 87 },
    { axis: "Coaching & Compassionate Leadership", value: 90 },
    { axis: "Leadership Drive", value: 80 },
    { axis: "Collaboration & Teamwork", value: 85 },
    { axis: "Strategic Partnerships", value: 82 },
    { axis: "Conflict Management", value: 88 },
  ],
  "shauryaa-ladha": [
    { axis: "Followership", value: 85 },
    { axis: "Coaching & Compassionate Leadership", value: 79 },
    { axis: "Leadership Drive", value: 84 },
    { axis: "Collaboration & Teamwork", value: 88 },
    { axis: "Strategic Partnerships", value: 86 },
    { axis: "Conflict Management", value: 82 },
  ],
  "jane-putri": [
    { axis: "Followership", value: 89 },
    { axis: "Coaching & Compassionate Leadership", value: 78 },
    { axis: "Leadership Drive", value: 81 },
    { axis: "Collaboration & Teamwork", value: 86 },
    { axis: "Strategic Partnerships", value: 83 },
    { axis: "Conflict Management", value: 85 },
  ],
  "mathew-ling": [
    { axis: "Followership", value: 84 },
    { axis: "Coaching & Compassionate Leadership", value: 85 },
    { axis: "Leadership Drive", value: 82 },
    { axis: "Collaboration & Teamwork", value: 80 },
    { axis: "Strategic Partnerships", value: 88 },
    { axis: "Conflict Management", value: 86 },
  ],
  "wu-hong-rui": [
    { axis: "Followership", value: 83 },
    { axis: "Coaching & Compassionate Leadership", value: 88 },
    { axis: "Leadership Drive", value: 79 },
    { axis: "Collaboration & Teamwork", value: 82 },
    { axis: "Strategic Partnerships", value: 85 },
    { axis: "Conflict Management", value: 84 },
  ],
  "ra-won-park": [
    { axis: "Followership", value: 86 },
    { axis: "Coaching & Compassionate Leadership", value: 80 },
    { axis: "Leadership Drive", value: 85 },
    { axis: "Collaboration & Teamwork", value: 84 },
    { axis: "Strategic Partnerships", value: 87 },
    { axis: "Conflict Management", value: 82 },
  ],
}

interface XFactorRadarChartProps {
  selectedMember?: string
}

export function XFactorRadarChart({ selectedMember = "all" }: XFactorRadarChartProps) {
  const [localSelectedMember, setLocalSelectedMember] = useState<string>(() => {
    // Initialize with the passed selectedMember or the first person in the data
    return selectedMember !== "all" ? selectedMember : Object.keys(teamMembersData)[0]
  })

  // Update local state when prop changes
  useEffect(() => {
    if (selectedMember !== "all") {
      setLocalSelectedMember(selectedMember)
    }
  }, [selectedMember])

  // Get the data for the selected person
  const data = teamMembersData[localSelectedMember as keyof typeof teamMembersData] || []

  return (
    <div className="w-full h-full">
      <div className="flex justify-end mb-4">
        <div className="w-64">
          <Select
            value={localSelectedMember}
            onValueChange={setLocalSelectedMember}
            disabled={selectedMember !== "all"}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select team member" />
            </SelectTrigger>
            <SelectContent>
              {Object.keys(teamMembersData).map((person) => (
                <SelectItem key={person} value={person}>
                  {person
                    .split("-")
                    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
                    .join(" ")}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
      <ResponsiveContainer width="100%" height="80%">
        <RadarChart cx="50%" cy="50%" outerRadius="80%" data={data}>
          <PolarGrid />
          <PolarAngleAxis dataKey="axis" />
          <PolarRadiusAxis angle={30} domain={[0, 100]} />
          <Tooltip
            formatter={(value) => [`${value}%`, "Score"]}
            contentStyle={{
              backgroundColor: "white",
              borderRadius: "8px",
              boxShadow: "0 4px 12px rgba(0, 0, 0, 0.1)",
              border: "none",
            }}
          />
          <Radar name="X-Factor Score" dataKey="value" stroke="#4f46e5" fill="#4f46e5" fillOpacity={0.6} />
          <Legend />
        </RadarChart>
      </ResponsiveContainer>
      <div className="flex justify-center mt-4">
        <div className="text-xs text-center max-w-md text-muted-foreground">
          The X-Factor assessment measures exceptional qualities that differentiate high performers across five key
          dimensions.
        </div>
      </div>
    </div>
  )
}
