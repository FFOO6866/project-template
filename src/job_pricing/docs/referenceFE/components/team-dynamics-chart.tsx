"use client"

import { useState, useEffect } from "react"

// Data for the Team Dynamics chart with actual MT names
const rolesRelationshipData = {
  "camille-wong-yuk": [
    { dimension: "Psychological Safety", value: 92 },
    { dimension: "Collective Intelligence", value: 88 },
    { dimension: "Collaborative Efficiency", value: 85 },
    { dimension: "Conflict Resolution", value: 90 },
    { dimension: "Team Cohesion", value: 94 },
    { dimension: "Shared Leadership", value: 86 },
  ],
  "marcel-melhado": [
    { dimension: "Psychological Safety", value: 85 },
    { dimension: "Collective Intelligence", value: 80 },
    { dimension: "Collaborative Efficiency", value: 92 },
    { dimension: "Conflict Resolution", value: 88 },
    { dimension: "Team Cohesion", value: 82 },
    { dimension: "Shared Leadership", value: 78 },
  ],
  "vivian-ho": [
    { dimension: "Psychological Safety", value: 88 },
    { dimension: "Collective Intelligence", value: 92 },
    { dimension: "Collaborative Efficiency", value: 85 },
    { dimension: "Conflict Resolution", value: 82 },
    { dimension: "Team Cohesion", value: 80 },
    { dimension: "Shared Leadership", value: 90 },
  ],
  "massie-shen": [
    { dimension: "Psychological Safety", value: 90 },
    { dimension: "Collective Intelligence", value: 87 },
    { dimension: "Collaborative Efficiency", value: 84 },
    { dimension: "Conflict Resolution", value: 89 },
    { dimension: "Team Cohesion", value: 92 },
    { dimension: "Shared Leadership", value: 85 },
  ],
  "gloria-cai-xinyi": [
    { dimension: "Psychological Safety", value: 86 },
    { dimension: "Collective Intelligence", value: 83 },
    { dimension: "Collaborative Efficiency", value: 88 },
    { dimension: "Conflict Resolution", value: 81 },
    { dimension: "Team Cohesion", value: 85 },
    { dimension: "Shared Leadership", value: 79 },
  ],
  "egan-valentino": [
    { dimension: "Psychological Safety", value: 83 },
    { dimension: "Collective Intelligence", value: 89 },
    { dimension: "Collaborative Efficiency", value: 86 },
    { dimension: "Conflict Resolution", value: 80 },
    { dimension: "Team Cohesion", value: 84 },
    { dimension: "Shared Leadership", value: 91 },
  ],
  "madhav-kapoor": [
    { dimension: "Psychological Safety", value: 87 },
    { dimension: "Collective Intelligence", value: 84 },
    { dimension: "Collaborative Efficiency", value: 90 },
    { dimension: "Conflict Resolution", value: 85 },
    { dimension: "Team Cohesion", value: 88 },
    { dimension: "Shared Leadership", value: 82 },
  ],
  "shauryaa-ladha": [
    { dimension: "Psychological Safety", value: 89 },
    { dimension: "Collective Intelligence", value: 86 },
    { dimension: "Collaborative Efficiency", value: 83 },
    { dimension: "Conflict Resolution", value: 87 },
    { dimension: "Team Cohesion", value: 90 },
    { dimension: "Shared Leadership", value: 84 },
  ],
  "jane-putri": [
    { dimension: "Psychological Safety", value: 85 },
    { dimension: "Collective Intelligence", value: 88 },
    { dimension: "Collaborative Efficiency", value: 91 },
    { dimension: "Conflict Resolution", value: 84 },
    { dimension: "Team Cohesion", value: 87 },
    { dimension: "Shared Leadership", value: 83 },
  ],
  "mathew-ling": [
    { dimension: "Psychological Safety", value: 84 },
    { dimension: "Collective Intelligence", value: 87 },
    { dimension: "Collaborative Efficiency", value: 82 },
    { dimension: "Conflict Resolution", value: 86 },
    { dimension: "Team Cohesion", value: 89 },
    { dimension: "Shared Leadership", value: 85 },
  ],
  "wu-hong-rui": [
    { dimension: "Psychological Safety", value: 82 },
    { dimension: "Collective Intelligence", value: 85 },
    { dimension: "Collaborative Efficiency", value: 89 },
    { dimension: "Conflict Resolution", value: 83 },
    { dimension: "Team Cohesion", value: 86 },
    { dimension: "Shared Leadership", value: 88 },
  ],
  "ra-won-park": [
    { dimension: "Psychological Safety", value: 88 },
    { dimension: "Collective Intelligence", value: 85 },
    { dimension: "Collaborative Efficiency", value: 82 },
    { dimension: "Conflict Resolution", value: 89 },
    { dimension: "Team Cohesion", value: 86 },
    { dimension: "Shared Leadership", value: 84 },
  ],
}

// Function to get color based on value
const getHexColor = (value: number) => {
  if (value >= 90) return "#059669" // Dark green
  if (value >= 85) return "#10b981" // Green
  if (value >= 80) return "#34d399" // Light green
  if (value >= 75) return "#6ee7b7" // Very light green
  return "#a7f3d0" // Pale green
}

// Function to generate hexagon points
const generateHexagonPoints = (centerX: number, centerY: number, size: number) => {
  const points = []
  for (let i = 0; i < 6; i++) {
    const angleDeg = 60 * i - 30
    const angleRad = (Math.PI / 180) * angleDeg
    const x = centerX + size * Math.cos(angleRad)
    const y = centerY + size * Math.sin(angleRad)
    points.push(`${x},${y}`)
  }
  return points.join(" ")
}

// Shortened dimension names for small screens
const shortDimensionNames = {
  "Psychological Safety": "Psych Safety",
  "Collective Intelligence": "Collective Int",
  "Collaborative Efficiency": "Collab Efficiency",
  "Conflict Resolution": "Conflict Res",
  "Team Cohesion": "Team Cohesion",
  "Shared Leadership": "Shared Lead",
}

interface TeamDynamicsChartProps {
  selectedMember?: string
}

export function TeamDynamicsChart({ selectedMember = "" }: TeamDynamicsChartProps) {
  // Get the data for the selected person
  const data = selectedMember ? rolesRelationshipData[selectedMember as keyof typeof rolesRelationshipData] || [] : []
  const [animated, setAnimated] = useState(false)
  const [windowWidth, setWindowWidth] = useState(0)

  // Reset animation when selected member changes
  useEffect(() => {
    setAnimated(false)
    const timer = setTimeout(() => setAnimated(true), 100)
    return () => clearTimeout(timer)
  }, [selectedMember])

  // Track window width for responsive text
  useEffect(() => {
    const handleResize = () => {
      setWindowWidth(window.innerWidth)
    }

    // Set initial width
    setWindowWidth(window.innerWidth)

    window.addEventListener("resize", handleResize)
    return () => window.removeEventListener("resize", handleResize)
  }, [])

  if (!selectedMember || !data.length) {
    return (
      <div className="w-full h-full flex items-center justify-center">
        <div className="text-muted-foreground">Please select a team member to view data</div>
      </div>
    )
  }

  // Hexagon positions (arranged in a honeycomb pattern)
  const hexPositions = [
    { x: 50, y: 25 }, // Top center
    { x: 75, y: 40 }, // Top right
    { x: 75, y: 70 }, // Bottom right
    { x: 50, y: 85 }, // Bottom center
    { x: 25, y: 70 }, // Bottom left
    { x: 25, y: 40 }, // Top left
  ]

  // Use smaller hexagons on small screens
  const hexSize = animated ? (windowWidth < 640 ? 12 : 15) : 0

  return (
    <div className="w-full h-full flex items-center justify-center overflow-hidden p-2">
      <div className="relative w-full h-full" style={{ minHeight: "200px" }}>
        <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet">
          {/* Connecting lines */}
          <g opacity="0.3">
            <line x1="50" y1="25" x2="75" y2="40" stroke="#10b981" strokeWidth="1" />
            <line x1="75" y1="40" x2="75" y2="70" stroke="#10b981" strokeWidth="1" />
            <line x1="75" y1="70" x2="50" y2="85" stroke="#10b981" strokeWidth="1" />
            <line x1="50" y1="85" x2="25" y2="70" stroke="#10b981" strokeWidth="1" />
            <line x1="25" y1="70" x2="25" y2="40" stroke="#10b981" strokeWidth="1" />
            <line x1="25" y1="40" x2="50" y2="25" stroke="#10b981" strokeWidth="1" />
            <line x1="50" y1="25" x2="50" y2="85" stroke="#10b981" strokeWidth="1" />
            <line x1="25" y1="40" x2="75" y2="70" stroke="#10b981" strokeWidth="1" />
            <line x1="75" y1="40" x2="25" y2="70" stroke="#10b981" strokeWidth="1" />
          </g>

          {/* Hexagons */}
          {data.map((item, index) => {
            const pos = hexPositions[index]
            const hexPoints = generateHexagonPoints(pos.x, pos.y, hexSize)
            const color = getHexColor(item.value)

            return (
              <g
                key={item.dimension}
                className={animated ? "animate-pulse" : ""}
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                <polygon
                  points={hexPoints}
                  fill={color}
                  stroke="#047857"
                  strokeWidth="0.5"
                  style={{ transition: "all 0.5s ease-in-out" }}
                />
                <text
                  x={pos.x}
                  y={pos.y}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  fill="#ffffff"
                  fontSize="4"
                  fontWeight="bold"
                >
                  {item.value}
                </text>

                {/* Dimension labels directly in SVG for better control */}
                <text
                  x={pos.x}
                  y={pos.y + (index === 0 || index === 3 ? (index === 0 ? -20 : 20) : 0)}
                  dx={index === 1 || index === 2 ? 20 : index === 4 || index === 5 ? -20 : 0}
                  textAnchor={index === 1 || index === 2 ? "start" : index === 4 || index === 5 ? "end" : "middle"}
                  fill="#374151"
                  fontSize="3.5"
                  fontWeight="500"
                  className="pointer-events-none"
                >
                  {windowWidth < 640
                    ? shortDimensionNames[item.dimension as keyof typeof shortDimensionNames]
                    : item.dimension}
                </text>
              </g>
            )
          })}
        </svg>
      </div>
    </div>
  )
}
