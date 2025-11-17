"use client"

import { useState, useEffect } from "react"

// Data for the AACC chart with actual MT names
const aaccData = {
  "camille-wong-yuk": [
    { dimension: "Aware", value: 92, description: "Self-awareness and situational awareness" },
    { dimension: "Align", value: 88, description: "Alignment with values and purpose" },
    { dimension: "Collaborate", value: 90, description: "Effective collaboration with others" },
    { dimension: "Co-create", value: 85, description: "Co-creation of innovative solutions" },
  ],
  "marcel-melhado": [
    { dimension: "Aware", value: 85, description: "Self-awareness and situational awareness" },
    { dimension: "Align", value: 80, description: "Alignment with values and purpose" },
    { dimension: "Collaborate", value: 88, description: "Effective collaboration with others" },
    { dimension: "Co-create", value: 78, description: "Co-creation of innovative solutions" },
  ],
  "vivian-ho": [
    { dimension: "Aware", value: 88, description: "Self-awareness and situational awareness" },
    { dimension: "Align", value: 90, description: "Alignment with values and purpose" },
    { dimension: "Collaborate", value: 85, description: "Effective collaboration with others" },
    { dimension: "Co-create", value: 82, description: "Co-creation of innovative solutions" },
  ],
  "massie-shen": [
    { dimension: "Aware", value: 90, description: "Self-awareness and situational awareness" },
    { dimension: "Align", value: 92, description: "Alignment with values and purpose" },
    { dimension: "Collaborate", value: 88, description: "Effective collaboration with others" },
    { dimension: "Co-create", value: 94, description: "Co-creation of innovative solutions" },
  ],
  "gloria-cai-xinyi": [
    { dimension: "Aware", value: 86, description: "Self-awareness and situational awareness" },
    { dimension: "Align", value: 83, description: "Alignment with values and purpose" },
    { dimension: "Collaborate", value: 80, description: "Effective collaboration with others" },
    { dimension: "Co-create", value: 78, description: "Co-creation of innovative solutions" },
  ],
  "egan-valentino": [
    { dimension: "Aware", value: 82, description: "Self-awareness and situational awareness" },
    { dimension: "Align", value: 78, description: "Alignment with values and purpose" },
    { dimension: "Collaborate", value: 85, description: "Effective collaboration with others" },
    { dimension: "Co-create", value: 88, description: "Co-creation of innovative solutions" },
  ],
  "madhav-kapoor": [
    { dimension: "Aware", value: 89, description: "Self-awareness and situational awareness" },
    { dimension: "Align", value: 87, description: "Alignment with values and purpose" },
    { dimension: "Collaborate", value: 84, description: "Effective collaboration with others" },
    { dimension: "Co-create", value: 86, description: "Co-creation of innovative solutions" },
  ],
  "shauryaa-ladha": [
    { dimension: "Aware", value: 87, description: "Self-awareness and situational awareness" },
    { dimension: "Align", value: 85, description: "Alignment with values and purpose" },
    { dimension: "Collaborate", value: 90, description: "Effective collaboration with others" },
    { dimension: "Co-create", value: 83, description: "Co-creation of innovative solutions" },
  ],
  "jane-putri": [
    { dimension: "Aware", value: 91, description: "Self-awareness and situational awareness" },
    { dimension: "Align", value: 88, description: "Alignment with values and purpose" },
    { dimension: "Collaborate", value: 86, description: "Effective collaboration with others" },
    { dimension: "Co-create", value: 84, description: "Co-creation of innovative solutions" },
  ],
  "mathew-ling": [
    { dimension: "Aware", value: 84, description: "Self-awareness and situational awareness" },
    { dimension: "Align", value: 82, description: "Alignment with values and purpose" },
    { dimension: "Collaborate", value: 87, description: "Effective collaboration with others" },
    { dimension: "Co-create", value: 85, description: "Co-creation of innovative solutions" },
  ],
  "wu-hong-rui": [
    { dimension: "Aware", value: 83, description: "Self-awareness and situational awareness" },
    { dimension: "Align", value: 86, description: "Alignment with values and purpose" },
    { dimension: "Collaborate", value: 89, description: "Effective collaboration with others" },
    { dimension: "Co-create", value: 81, description: "Co-creation of innovative solutions" },
  ],
  "ra-won-park": [
    { dimension: "Aware", value: 88, description: "Self-awareness and situational awareness" },
    { dimension: "Align", value: 90, description: "Alignment with values and purpose" },
    { dimension: "Collaborate", value: 85, description: "Effective collaboration with others" },
    { dimension: "Co-create", value: 87, description: "Co-creation of innovative solutions" },
  ],
}

// Color for the AACC dimensions
const aaccColor = "#7c3aed" // Violet

interface AACCChartProps {
  selectedMember?: string
}

export function AACCChart({ selectedMember = "" }: AACCChartProps) {
  // Get the data for the selected person
  const data = selectedMember ? aaccData[selectedMember as keyof typeof aaccData] || [] : []
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

  // Create a map of dimension to value for easier access
  const valueMap = new Map(data.map((item) => [item.dimension, item.value]))

  // Calculate node sizes based on values (scaled)
  const getNodeSize = (value: number) => Math.max(value / 5, 10)

  return (
    <div className="w-full h-full flex flex-col items-center justify-between p-2 overflow-hidden">
      {/* Top row labels */}
      <div className="grid grid-cols-2 w-full mb-1 sm:mb-2">
        <div className="text-center px-1">
          <div className="font-medium text-xs sm:text-sm truncate">Aware</div>
          <div className="text-xs text-muted-foreground line-clamp-1 sm:line-clamp-2">
            Self-awareness and situational awareness
          </div>
        </div>
        <div className="text-center px-1">
          <div className="font-medium text-xs sm:text-sm truncate">Align</div>
          <div className="text-xs text-muted-foreground line-clamp-1 sm:line-clamp-2">
            Alignment with values and purpose
          </div>
        </div>
      </div>

      {/* Visualization */}
      <div className="relative w-full flex-grow" style={{ minHeight: "120px" }}>
        <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet">
          {/* Connection lines */}
          <line
            x1="25"
            y1="25"
            x2="75"
            y2="25"
            stroke={aaccColor}
            strokeWidth={animated ? Math.max(((valueMap.get("Aware") || 0) + (valueMap.get("Align") || 0)) / 50, 1) : 0}
            opacity={animated ? ((valueMap.get("Aware") || 0) + (valueMap.get("Align") || 0)) / 200 : 0}
            strokeLinecap="round"
            style={{ transition: "opacity 1s ease-in-out, stroke-width 1s ease-in-out" }}
          />
          <line
            x1="25"
            y1="25"
            x2="25"
            y2="75"
            stroke={aaccColor}
            strokeWidth={
              animated ? Math.max(((valueMap.get("Aware") || 0) + (valueMap.get("Collaborate") || 0)) / 50, 1) : 0
            }
            opacity={animated ? ((valueMap.get("Aware") || 0) + (valueMap.get("Collaborate") || 0)) / 200 : 0}
            strokeLinecap="round"
            style={{ transition: "opacity 1s ease-in-out, stroke-width 1s ease-in-out" }}
          />
          <line
            x1="25"
            y1="25"
            x2="75"
            y2="75"
            stroke={aaccColor}
            strokeWidth={
              animated ? Math.max(((valueMap.get("Aware") || 0) + (valueMap.get("Co-create") || 0)) / 50, 1) : 0
            }
            opacity={animated ? ((valueMap.get("Aware") || 0) + (valueMap.get("Co-create") || 0)) / 200 : 0}
            strokeLinecap="round"
            style={{ transition: "opacity 1s ease-in-out, stroke-width 1s ease-in-out" }}
          />
          <line
            x1="75"
            y1="25"
            x2="25"
            y2="75"
            stroke={aaccColor}
            strokeWidth={
              animated ? Math.max(((valueMap.get("Align") || 0) + (valueMap.get("Collaborate") || 0)) / 50, 1) : 0
            }
            opacity={animated ? ((valueMap.get("Align") || 0) + (valueMap.get("Collaborate") || 0)) / 200 : 0}
            strokeLinecap="round"
            style={{ transition: "opacity 1s ease-in-out, stroke-width 1s ease-in-out" }}
          />
          <line
            x1="75"
            y1="25"
            x2="75"
            y2="75"
            stroke={aaccColor}
            strokeWidth={
              animated ? Math.max(((valueMap.get("Align") || 0) + (valueMap.get("Co-create") || 0)) / 50, 1) : 0
            }
            opacity={animated ? ((valueMap.get("Align") || 0) + (valueMap.get("Co-create") || 0)) / 200 : 0}
            strokeLinecap="round"
            style={{ transition: "opacity 1s ease-in-out, stroke-width 1s ease-in-out" }}
          />
          <line
            x1="25"
            y1="75"
            x2="75"
            y2="75"
            stroke={aaccColor}
            strokeWidth={
              animated ? Math.max(((valueMap.get("Collaborate") || 0) + (valueMap.get("Co-create") || 0)) / 50, 1) : 0
            }
            opacity={animated ? ((valueMap.get("Collaborate") || 0) + (valueMap.get("Co-create") || 0)) / 200 : 0}
            strokeLinecap="round"
            style={{ transition: "opacity 1s ease-in-out, stroke-width 1s ease-in-out" }}
          />

          {/* Nodes */}
          {data.map((item) => {
            let x, y
            switch (item.dimension) {
              case "Aware":
                x = 25
                y = 25
                break
              case "Align":
                x = 75
                y = 25
                break
              case "Collaborate":
                x = 25
                y = 75
                break
              case "Co-create":
                x = 75
                y = 75
                break
              default:
                x = 50
                y = 50
            }

            const nodeSize = animated ? getNodeSize(item.value) : 0

            return (
              <g key={item.dimension}>
                {/* Pulsing effect */}
                <circle
                  cx={x}
                  cy={y}
                  r={nodeSize * 1.3}
                  fill={aaccColor}
                  opacity="0.2"
                  className={animated ? "animate-pulse" : ""}
                />

                {/* Main node */}
                <circle cx={x} cy={y} r={nodeSize} fill={aaccColor} style={{ transition: "r 1s ease-in-out" }} />

                {/* Value text */}
                <text
                  x={x}
                  y={y}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  fill="white"
                  fontSize="4"
                  fontWeight="bold"
                >
                  {item.value}
                </text>
              </g>
            )
          })}
        </svg>
      </div>

      {/* Bottom row labels */}
      <div className="grid grid-cols-2 w-full mt-1 sm:mt-2">
        <div className="text-center px-1">
          <div className="font-medium text-xs sm:text-sm truncate">Collaborate</div>
          <div className="text-xs text-muted-foreground line-clamp-1 sm:line-clamp-2">
            Effective collaboration with others
          </div>
        </div>
        <div className="text-center px-1">
          <div className="font-medium text-xs sm:text-sm truncate">Co-create</div>
          <div className="text-xs text-muted-foreground line-clamp-1 sm:line-clamp-2">
            Co-creation of innovative solutions
          </div>
        </div>
      </div>
    </div>
  )
}
