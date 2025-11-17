"use client"

import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"

// Data for the IRTF chart with actual MT names
const irtfData = {
  "camille-wong-yuk": [
    { dimension: "In-search", value: 88, description: "Exploring possibilities and opportunities" },
    { dimension: "Research", value: 92, description: "Gathering and analyzing information" },
    { dimension: "Think-through", value: 95, description: "Strategic planning and decision-making" },
    { dimension: "Follow-through", value: 85, description: "Execution and implementation" },
  ],
  "marcel-melhado": [
    { dimension: "In-search", value: 75, description: "Exploring possibilities and opportunities" },
    { dimension: "Research", value: 82, description: "Gathering and analyzing information" },
    { dimension: "Think-through", value: 80, description: "Strategic planning and decision-making" },
    { dimension: "Follow-through", value: 94, description: "Execution and implementation" },
  ],
  "vivian-ho": [
    { dimension: "In-search", value: 80, description: "Exploring possibilities and opportunities" },
    { dimension: "Research", value: 95, description: "Gathering and analyzing information" },
    { dimension: "Think-through", value: 88, description: "Strategic planning and decision-making" },
    { dimension: "Follow-through", value: 90, description: "Execution and implementation" },
  ],
  "massie-shen": [
    { dimension: "In-search", value: 90, description: "Exploring possibilities and opportunities" },
    { dimension: "Research", value: 85, description: "Gathering and analyzing information" },
    { dimension: "Think-through", value: 82, description: "Strategic planning and decision-making" },
    { dimension: "Follow-through", value: 78, description: "Execution and implementation" },
  ],
  "gloria-cai-xinyi": [
    { dimension: "In-search", value: 87, description: "Exploring possibilities and opportunities" },
    { dimension: "Research", value: 83, description: "Gathering and analyzing information" },
    { dimension: "Think-through", value: 79, description: "Strategic planning and decision-making" },
    { dimension: "Follow-through", value: 85, description: "Execution and implementation" },
  ],
  "egan-valentino": [
    { dimension: "In-search", value: 92, description: "Exploring possibilities and opportunities" },
    { dimension: "Research", value: 78, description: "Gathering and analyzing information" },
    { dimension: "Think-through", value: 75, description: "Strategic planning and decision-making" },
    { dimension: "Follow-through", value: 82, description: "Execution and implementation" },
  ],
  "madhav-kapoor": [
    { dimension: "In-search", value: 89, description: "Exploring possibilities and opportunities" },
    { dimension: "Research", value: 86, description: "Gathering and analyzing information" },
    { dimension: "Think-through", value: 84, description: "Strategic planning and decision-making" },
    { dimension: "Follow-through", value: 80, description: "Execution and implementation" },
  ],
  "shauryaa-ladha": [
    { dimension: "In-search", value: 81, description: "Exploring possibilities and opportunities" },
    { dimension: "Research", value: 84, description: "Gathering and analyzing information" },
    { dimension: "Think-through", value: 87, description: "Strategic planning and decision-making" },
    { dimension: "Follow-through", value: 90, description: "Execution and implementation" },
  ],
  "jane-putri": [
    { dimension: "In-search", value: 83, description: "Exploring possibilities and opportunities" },
    { dimension: "Research", value: 91, description: "Gathering and analyzing information" },
    { dimension: "Think-through", value: 88, description: "Strategic planning and decision-making" },
    { dimension: "Follow-through", value: 85, description: "Execution and implementation" },
  ],
  "mathew-ling": [
    { dimension: "In-search", value: 86, description: "Exploring possibilities and opportunities" },
    { dimension: "Research", value: 82, description: "Gathering and analyzing information" },
    { dimension: "Think-through", value: 79, description: "Strategic planning and decision-making" },
    { dimension: "Follow-through", value: 88, description: "Execution and implementation" },
  ],
  "wu-hong-rui": [
    { dimension: "In-search", value: 90, description: "Exploring possibilities and opportunities" },
    { dimension: "Research", value: 85, description: "Gathering and analyzing information" },
    { dimension: "Think-through", value: 82, description: "Strategic planning and decision-making" },
    { dimension: "Follow-through", value: 78, description: "Execution and implementation" },
  ],
  "ra-won-park": [
    { dimension: "In-search", value: 84, description: "Exploring possibilities and opportunities" },
    { dimension: "Research", value: 87, description: "Gathering and analyzing information" },
    { dimension: "Think-through", value: 90, description: "Strategic planning and decision-making" },
    { dimension: "Follow-through", value: 83, description: "Execution and implementation" },
  ],
}

// Color mapping for different score ranges
const getColor = (value: number) => {
  if (value >= 90) return "#10b981" // Green for high scores
  if (value >= 80) return "#3b82f6" // Blue for good scores
  if (value >= 70) return "#f59e0b" // Yellow for average scores
  return "#ef4444" // Red for low scores
}

interface IRTFChartProps {
  selectedMember?: string
}

export function IRTFChart({ selectedMember = "" }: IRTFChartProps) {
  // Get the data for the selected person
  const data = selectedMember ? irtfData[selectedMember as keyof typeof irtfData] || [] : []
  const [animated, setAnimated] = useState(false)

  // Reset animation when selected member changes
  useEffect(() => {
    setAnimated(false)
    const timer = setTimeout(() => setAnimated(true), 100)
    return () => clearTimeout(timer)
  }, [selectedMember])

  if (!selectedMember || !data.length) {
    return (
      <div className="w-full h-full flex items-center justify-center">
        <div className="text-muted-foreground">Please select a team member to view data</div>
      </div>
    )
  }

  return (
    <div className="w-full h-full flex items-center justify-center overflow-hidden p-2">
      <div className="w-full max-w-full grid grid-cols-2 gap-3 sm:gap-4">
        {data.map((item) => (
          <Card key={item.dimension} className="p-3 flex flex-col items-center justify-center overflow-hidden">
            <div className="text-sm font-medium mb-1 text-center truncate w-full">{item.dimension}</div>
            <div className="relative w-full aspect-square max-w-[100px] flex items-center justify-center">
              {/* Background circle */}
              <div className="absolute w-full h-full rounded-full border-8 border-gray-100"></div>

              {/* Animated progress circle */}
              <svg className="absolute w-full h-full" viewBox="0 0 100 100">
                <circle
                  cx="50"
                  cy="50"
                  r="46"
                  fill="none"
                  stroke={getColor(item.value)}
                  strokeWidth="8"
                  strokeDasharray={`${animated ? item.value * 2.9 : 0} 1000`}
                  strokeLinecap="round"
                  transform="rotate(-90 50 50)"
                  style={{ transition: "stroke-dasharray 1s ease-in-out" }}
                />
              </svg>

              {/* Value text */}
              <div className="text-xl sm:text-2xl font-bold">{item.value}%</div>
            </div>
            <div className="text-xs text-center text-muted-foreground mt-1 px-1 line-clamp-2 h-8">
              {item.description}
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
