"use client"

import { cn } from "@/lib/utils"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"

interface ConsciousnessLineIndicatorProps {
  level: string
  value: number
  className?: string
}

// Define consciousness levels based on Hawkins' Map
const consciousnessLevels = [
  { level: "Shame", value: 20, color: "#ffcdd2", paradigm: "Survival" },
  { level: "Guilt", value: 30, color: "#ffcdd2", paradigm: "Survival" },
  { level: "Apathy", value: 50, color: "#ffcdd2", paradigm: "Survival" },
  { level: "Grief", value: 75, color: "#ffcdd2", paradigm: "Survival" },
  { level: "Fear", value: 100, color: "#ffab91", paradigm: "Survival" },
  { level: "Desire", value: 125, color: "#ffab91", paradigm: "Survival" },
  { level: "Anger", value: 150, color: "#ffab91", paradigm: "Survival" },
  { level: "Pride", value: 175, color: "#ffe082", paradigm: "Survival" },
  { level: "Courage", value: 200, color: "#fff59d", paradigm: "Reason & Integrity" },
  { level: "Neutrality", value: 250, color: "#dcedc8", paradigm: "Reason & Integrity" },
  { level: "Willingness", value: 310, color: "#c5e1a5", paradigm: "Reason & Integrity" },
  { level: "Acceptance", value: 350, color: "#c5e1a5", paradigm: "Reason & Integrity" },
  { level: "Reason", value: 400, color: "#b3e5fc", paradigm: "Reason & Integrity" },
  { level: "Love", value: 500, color: "#d1c4e9", paradigm: "Spiritual" },
  { level: "Joy", value: 540, color: "#d1c4e9", paradigm: "Spiritual" },
  { level: "Peace", value: 600, color: "#d1c4e9", paradigm: "Spiritual" },
  { level: "Enlightenment", value: 700, color: "#e1bee7", paradigm: "Spiritual" },
]

// Key markers to show on the line (without labels)
const keyMarkers = [{ value: 200 }, { value: 350 }, { value: 500 }, { value: 700 }]

export function ConsciousnessLineIndicator({ level, value, className }: ConsciousnessLineIndicatorProps) {
  // Find the level details
  const levelDetails = consciousnessLevels.find((l) => l.level === level) || {
    level,
    value,
    color: "#e0e0e0",
    paradigm: "Unknown",
  }

  // Calculate position percentage (0-700 scale)
  const maxValue = 700
  const positionPercentage = (value / maxValue) * 100

  // Get paradigm color
  const getParadigmColor = (val: number) => {
    if (val >= 500) return "bg-purple-50" // Spiritual
    if (val >= 200) return "bg-green-50" // Reason & Integrity
    return "bg-red-50" // Survival
  }

  return (
    <div>
      {/* Added level name above the consciousness bar */}
      <div className="flex justify-between items-center mb-1">
        <span className="text-sm font-medium">{level}</span>
      </div>

      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <div className={cn("relative w-full h-8 rounded-md overflow-hidden", className)}>
              {/* Paradigm background sections */}
              <div className="absolute inset-0 flex w-full h-full">
                <div className="bg-red-50 w-[28.5%] h-full" /> {/* Survival: 0-200 */}
                <div className="bg-green-50 w-[42.8%] h-full" /> {/* Reason: 200-500 */}
                <div className="bg-purple-50 w-[28.7%] h-full" /> {/* Spiritual: 500-700 */}
              </div>

              {/* Scale markers (without labels) */}
              <div className="absolute inset-0 w-full h-full">
                {keyMarkers.map((marker) => (
                  <div
                    key={marker.value}
                    className="absolute top-0 bottom-0 w-px bg-gray-400"
                    style={{ left: `${(marker.value / maxValue) * 100}%` }}
                  />
                ))}
              </div>

              {/* Current level indicator */}
              <div className="absolute top-0 w-px h-full bg-black" style={{ left: `${positionPercentage}%` }}>
                <div
                  className="absolute -top-1 transform -translate-x-1/2 w-3 h-3 rotate-45 border-2 border-black"
                  style={{ backgroundColor: levelDetails.color }}
                />
                <div className="absolute top-3 transform -translate-x-1/2 text-[10px] font-bold whitespace-nowrap">
                  {value}
                </div>
              </div>
            </div>
          </TooltipTrigger>
          <TooltipContent>
            <div className="text-sm">
              <p className="font-bold">
                {level} - {value}
              </p>
              <p>Paradigm: {levelDetails.paradigm}</p>
            </div>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    </div>
  )
}
