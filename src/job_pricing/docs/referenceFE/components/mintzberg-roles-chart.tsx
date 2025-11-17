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

// Sample data for the Mintzberg roles chart
const mintzbergData = {
  "camille-wong-yuk": [
    { role: "Figurehead", value: 90, category: "Interpersonal" },
    { role: "Leader", value: 95, category: "Interpersonal" },
    { role: "Liaison", value: 88, category: "Interpersonal" },
    { role: "Monitor", value: 85, category: "Informational" },
    { role: "Disseminator", value: 82, category: "Informational" },
    { role: "Spokesperson", value: 92, category: "Informational" },
    { role: "Entrepreneur", value: 94, category: "Decisional" },
    { role: "Disturbance Handler", value: 86, category: "Decisional" },
    { role: "Resource Allocator", value: 88, category: "Decisional" },
    { role: "Negotiator", value: 90, category: "Decisional" },
  ],
  "marcel-melhado": [
    { role: "Figurehead", value: 82, category: "Interpersonal" },
    { role: "Leader", value: 85, category: "Interpersonal" },
    { role: "Liaison", value: 80, category: "Interpersonal" },
    { role: "Monitor", value: 92, category: "Informational" },
    { role: "Disseminator", value: 88, category: "Informational" },
    { role: "Spokesperson", value: 78, category: "Informational" },
    { role: "Entrepreneur", value: 75, category: "Decisional" },
    { role: "Disturbance Handler", value: 90, category: "Decisional" },
    { role: "Resource Allocator", value: 94, category: "Decisional" },
    { role: "Negotiator", value: 82, category: "Decisional" },
  ],
  "vivian-ho": [
    { role: "Figurehead", value: 85, category: "Interpersonal" },
    { role: "Leader", value: 82, category: "Interpersonal" },
    { role: "Liaison", value: 90, category: "Interpersonal" },
    { role: "Monitor", value: 94, category: "Informational" },
    { role: "Disseminator", value: 90, category: "Informational" },
    { role: "Spokesperson", value: 85, category: "Informational" },
    { role: "Entrepreneur", value: 80, category: "Decisional" },
    { role: "Disturbance Handler", value: 82, category: "Decisional" },
    { role: "Resource Allocator", value: 96, category: "Decisional" },
    { role: "Negotiator", value: 88, category: "Decisional" },
  ],
  "massie-shen": [
    { role: "Figurehead", value: 88, category: "Interpersonal" },
    { role: "Leader", value: 90, category: "Interpersonal" },
    { role: "Liaison", value: 85, category: "Interpersonal" },
    { role: "Monitor", value: 89, category: "Informational" },
    { role: "Disseminator", value: 87, category: "Informational" },
    { role: "Spokesperson", value: 91, category: "Informational" },
    { role: "Entrepreneur", value: 86, category: "Decisional" },
    { role: "Disturbance Handler", value: 84, category: "Decisional" },
    { role: "Resource Allocator", value: 92, category: "Decisional" },
    { role: "Negotiator", value: 89, category: "Decisional" },
  ],
  "gloria-cai-xinyi": [
    { role: "Figurehead", value: 83, category: "Interpersonal" },
    { role: "Leader", value: 81, category: "Interpersonal" },
    { role: "Liaison", value: 87, category: "Interpersonal" },
    { role: "Monitor", value: 90, category: "Informational" },
    { role: "Disseminator", value: 85, category: "Informational" },
    { role: "Spokesperson", value: 82, category: "Informational" },
    { role: "Entrepreneur", value: 88, category: "Decisional" },
    { role: "Disturbance Handler", value: 80, category: "Decisional" },
    { role: "Resource Allocator", value: 84, category: "Decisional" },
    { role: "Negotiator", value: 86, category: "Decisional" },
  ],
  "egan-valentino": [
    { role: "Figurehead", value: 80, category: "Interpersonal" },
    { role: "Leader", value: 78, category: "Interpersonal" },
    { role: "Liaison", value: 92, category: "Interpersonal" },
    { role: "Monitor", value: 85, category: "Informational" },
    { role: "Disseminator", value: 93, category: "Informational" },
    { role: "Spokesperson", value: 89, category: "Informational" },
    { role: "Entrepreneur", value: 82, category: "Decisional" },
    { role: "Disturbance Handler", value: 79, category: "Decisional" },
    { role: "Resource Allocator", value: 81, category: "Decisional" },
    { role: "Negotiator", value: 84, category: "Decisional" },
  ],
  "madhav-kapoor": [
    { role: "Figurehead", value: 84, category: "Interpersonal" },
    { role: "Leader", value: 87, category: "Interpersonal" },
    { role: "Liaison", value: 89, category: "Interpersonal" },
    { role: "Monitor", value: 93, category: "Informational" },
    { role: "Disseminator", value: 86, category: "Informational" },
    { role: "Spokesperson", value: 82, category: "Informational" },
    { role: "Entrepreneur", value: 91, category: "Decisional" },
    { role: "Disturbance Handler", value: 85, category: "Decisional" },
    { role: "Resource Allocator", value: 88, category: "Decisional" },
    { role: "Negotiator", value: 83, category: "Decisional" },
  ],
  "shauryaa-ladha": [
    { role: "Figurehead", value: 86, category: "Interpersonal" },
    { role: "Leader", value: 89, category: "Interpersonal" },
    { role: "Liaison", value: 83, category: "Interpersonal" },
    { role: "Monitor", value: 87, category: "Informational" },
    { role: "Disseminator", value: 84, category: "Informational" },
    { role: "Spokesperson", value: 88, category: "Informational" },
    { role: "Entrepreneur", value: 85, category: "Decisional" },
    { role: "Disturbance Handler", value: 90, category: "Decisional" },
    { role: "Resource Allocator", value: 82, category: "Decisional" },
    { role: "Negotiator", value: 87, category: "Decisional" },
  ],
  "jane-putri": [
    { role: "Figurehead", value: 82, category: "Interpersonal" },
    { role: "Leader", value: 85, category: "Interpersonal" },
    { role: "Liaison", value: 88, category: "Interpersonal" },
    { role: "Monitor", value: 91, category: "Informational" },
    { role: "Disseminator", value: 89, category: "Informational" },
    { role: "Spokesperson", value: 83, category: "Informational" },
    { role: "Entrepreneur", value: 87, category: "Decisional" },
    { role: "Disturbance Handler", value: 84, category: "Decisional" },
    { role: "Resource Allocator", value: 90, category: "Decisional" },
    { role: "Negotiator", value: 86, category: "Decisional" },
  ],
  "mathew-ling": [
    { role: "Figurehead", value: 81, category: "Interpersonal" },
    { role: "Leader", value: 84, category: "Interpersonal" },
    { role: "Liaison", value: 87, category: "Interpersonal" },
    { role: "Monitor", value: 90, category: "Informational" },
    { role: "Disseminator", value: 88, category: "Informational" },
    { role: "Spokesperson", value: 82, category: "Informational" },
    { role: "Entrepreneur", value: 86, category: "Decisional" },
    { role: "Disturbance Handler", value: 83, category: "Decisional" },
    { role: "Resource Allocator", value: 89, category: "Decisional" },
    { role: "Negotiator", value: 85, category: "Decisional" },
  ],
  "wu-hong-rui": [
    { role: "Figurehead", value: 83, category: "Interpersonal" },
    { role: "Leader", value: 80, category: "Interpersonal" },
    { role: "Liaison", value: 86, category: "Interpersonal" },
    { role: "Monitor", value: 89, category: "Informational" },
    { role: "Disseminator", value: 92, category: "Informational" },
    { role: "Spokesperson", value: 85, category: "Informational" },
    { role: "Entrepreneur", value: 82, category: "Decisional" },
    { role: "Disturbance Handler", value: 87, category: "Decisional" },
    { role: "Resource Allocator", value: 84, category: "Decisional" },
    { role: "Negotiator", value: 88, category: "Decisional" },
  ],
  "ra-won-park": [
    { role: "Figurehead", value: 85, category: "Interpersonal" },
    { role: "Leader", value: 88, category: "Interpersonal" },
    { role: "Liaison", value: 82, category: "Interpersonal" },
    { role: "Monitor", value: 86, category: "Informational" },
    { role: "Disseminator", value: 83, category: "Informational" },
    { role: "Spokesperson", value: 87, category: "Informational" },
    { role: "Entrepreneur", value: 84, category: "Decisional" },
    { role: "Disturbance Handler", value: 89, category: "Decisional" },
    { role: "Resource Allocator", value: 86, category: "Decisional" },
    { role: "Negotiator", value: 83, category: "Decisional" },
  ],
}

interface MintzbergRolesChartProps {
  selectedMember?: string
}

export function MintzbergRolesChart({ selectedMember = "all" }: MintzbergRolesChartProps) {
  const [localSelectedMember, setLocalSelectedMember] = useState<string>(() => {
    // Initialize with the passed selectedMember or the first person in the data
    return selectedMember !== "all" ? selectedMember : Object.keys(mintzbergData)[0]
  })

  // Update local state when prop changes
  useEffect(() => {
    if (selectedMember !== "all") {
      setLocalSelectedMember(selectedMember)
    }
  }, [selectedMember])

  // Get the data for the selected person
  const data = mintzbergData[localSelectedMember as keyof typeof mintzbergData] || []

  // Group data by category for the legend
  const categories = Array.from(new Set(data.map((item) => item.category)))

  // Define colors for different categories
  const categoryColors = {
    Interpersonal: "#4f46e5", // Indigo
    Informational: "#0891b2", // Cyan
    Decisional: "#16a34a", // Green
  }

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
              {Object.keys(mintzbergData).map((person) => (
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
          <PolarAngleAxis dataKey="role" tick={{ fontSize: 12 }} />
          <PolarRadiusAxis angle={30} domain={[0, 100]} />
          <Tooltip
            formatter={(value) => [`${value}%`, "Score"]}
            contentStyle={{
              backgroundColor: "white",
              borderRadius: "8px",
              boxShadow: "0 4px 12px rgba(0, 0, 0, 0.1)",
              border: "none",
            }}
            labelFormatter={(label) => {
              const item = data.find((d) => d.role === label)
              return `${label} (${item?.category || "Unknown"})`
            }}
          />
          <Radar
            name={localSelectedMember
              .split("-")
              .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
              .join(" ")}
            dataKey="value"
            stroke="#4f46e5"
            fill="#4f46e5"
            fillOpacity={0.6}
          />
          <Legend />
        </RadarChart>
      </ResponsiveContainer>
      <div className="flex justify-center gap-6 mt-4">
        {categories.map((category) => (
          <div key={category} className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: categoryColors[category as keyof typeof categoryColors] }}
            />
            <span className="text-xs font-medium">{category} Roles</span>
          </div>
        ))}
      </div>
    </div>
  )
}
