"use client"

import { useState } from "react"
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

// Sample data for the Consciousness Shift chart
const consciousnessData = {
  "Sarah Chen": [
    { year: 2018, level: 65, stage: "Systemic" },
    { year: 2019, level: 72, stage: "Systemic" },
    { year: 2020, level: 78, stage: "Systemic" },
    { year: 2021, level: 85, stage: "Integral" },
    { year: 2022, level: 90, stage: "Integral" },
    { year: 2023, level: 94, stage: "Integral" },
  ],
  "Michael Rodriguez": [
    { year: 2018, level: 60, stage: "Achievement" },
    { year: 2019, level: 68, stage: "Achievement" },
    { year: 2020, level: 75, stage: "Systemic" },
    { year: 2021, level: 80, stage: "Systemic" },
    { year: 2022, level: 85, stage: "Systemic" },
    { year: 2023, level: 88, stage: "Integral" },
  ],
  "Aisha Johnson": [
    { year: 2018, level: 70, stage: "Systemic" },
    { year: 2019, level: 75, stage: "Systemic" },
    { year: 2020, level: 80, stage: "Systemic" },
    { year: 2021, level: 82, stage: "Systemic" },
    { year: 2022, level: 88, stage: "Integral" },
    { year: 2023, level: 92, stage: "Integral" },
  ],
}

// Define consciousness stages and their thresholds
const consciousnessStages = [
  { name: "Ego-centric", threshold: 40, color: "#ef4444" }, // Red
  { name: "Achievement", threshold: 60, color: "#f59e0b" }, // Amber
  { name: "Systemic", threshold: 80, color: "#3b82f6" }, // Blue
  { name: "Integral", threshold: 90, color: "#8b5cf6" }, // Purple
  { name: "Holistic", threshold: 100, color: "#10b981" }, // Green
]

export function ConsciousnessShiftChart() {
  const [selectedPerson, setSelectedPerson] = useState("Sarah Chen")

  // Get the data for the selected person
  const data = consciousnessData[selectedPerson as keyof typeof consciousnessData]

  // Get the stage color based on consciousness level
  const getStageColor = (level: number) => {
    for (let i = consciousnessStages.length - 1; i >= 0; i--) {
      if (level <= consciousnessStages[i].threshold) {
        return consciousnessStages[i].color
      }
    }
    return consciousnessStages[0].color
  }

  // Get the current stage name
  const getCurrentStage = () => {
    const currentLevel = data[data.length - 1].level
    for (let i = consciousnessStages.length - 1; i >= 0; i--) {
      if (currentLevel <= consciousnessStages[i].threshold) {
        return consciousnessStages[i].name
      }
    }
    return consciousnessStages[0].name
  }

  return (
    <div className="w-full h-full">
      <div className="flex justify-between mb-4">
        <div className="flex items-center">
          <div className="text-sm font-medium mr-2">Current Stage:</div>
          <div
            className="px-2 py-1 rounded-full text-xs font-medium"
            style={{
              backgroundColor: getStageColor(data[data.length - 1].level) + "20",
              color: getStageColor(data[data.length - 1].level),
            }}
          >
            {getCurrentStage()}
          </div>
        </div>
        <div className="w-64">
          <Select value={selectedPerson} onValueChange={setSelectedPerson}>
            <SelectTrigger>
              <SelectValue placeholder="Select team member" />
            </SelectTrigger>
            <SelectContent>
              {Object.keys(consciousnessData).map((person) => (
                <SelectItem key={person} value={person}>
                  {person}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
      <ResponsiveContainer width="100%" height="80%">
        <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="year" />
          <YAxis domain={[0, 100]} />
          <Tooltip
            formatter={(value) => [`${value}`, "Consciousness Level"]}
            contentStyle={{
              backgroundColor: "white",
              borderRadius: "8px",
              boxShadow: "0 4px 12px rgba(0, 0, 0, 0.1)",
              border: "none",
            }}
            labelFormatter={(label) => `Year: ${label}`}
          />
          <Legend />
          <Area
            type="monotone"
            dataKey="level"
            name="Consciousness Level"
            stroke="#8b5cf6"
            fill="#8b5cf6"
            fillOpacity={0.3}
          />
        </AreaChart>
      </ResponsiveContainer>
      <div className="flex justify-center gap-2 mt-4">
        {consciousnessStages.map((stage) => (
          <div key={stage.name} className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: stage.color }} />
            <span className="text-xs font-medium">{stage.name}</span>
          </div>
        ))}
      </div>
      <div className="flex justify-center mt-2">
        <div className="text-xs text-center max-w-md text-muted-foreground">
          The Consciousness Shift framework tracks an individual's evolution through stages of awareness, from
          ego-centric to holistic consciousness.
        </div>
      </div>
    </div>
  )
}
