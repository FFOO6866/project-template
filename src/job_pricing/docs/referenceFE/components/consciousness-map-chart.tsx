"use client"

import { useEffect, useRef } from "react"
import { Badge } from "@/components/ui/badge"
import * as d3 from "d3"

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

// Sample data based on David R. Hawkins' Map of Consciousness
const consciousnessData = {
  "camille-wong-yuk": {
    currentLevel: "Love",
    energeticLog: 500,
    emotionalState: "Reverence",
    viewOfLife: "Benign",
    godView: "Loving",
    process: "Revelation",
    history: [
      { year: "2023H1", level: "Love", value: 500 },
      { year: "2023H2", level: "Love", value: 510 },
      { year: "2024H1", level: "Love", value: 520 },
      { year: "2024H2", level: "Joy", value: 540 },
    ],
  },
  "marcel-melhado": {
    currentLevel: "Acceptance",
    energeticLog: 350,
    emotionalState: "Forgiveness",
    viewOfLife: "Harmonious",
    godView: "Merciful",
    process: "Transcendence",
    history: [
      { year: "2023H1", level: "Willingness", value: 310 },
      { year: "2023H2", level: "Acceptance", value: 350 },
      { year: "2024H1", level: "Acceptance", value: 360 },
      { year: "2024H2", level: "Acceptance", value: 370 },
    ],
  },
  "vivian-ho": {
    currentLevel: "Reason",
    energeticLog: 400,
    emotionalState: "Understanding",
    viewOfLife: "Meaningful",
    godView: "Wise",
    process: "Abstraction",
    history: [
      { year: "2023H1", level: "Acceptance", value: 350 },
      { year: "2023H2", level: "Reason", value: 380 },
      { year: "2024H1", level: "Reason", value: 400 },
      { year: "2024H2", level: "Reason", value: 410 },
    ],
  },
  "massie-shen": {
    currentLevel: "Joy",
    energeticLog: 540,
    emotionalState: "Serenity",
    viewOfLife: "Complete",
    godView: "One",
    process: "Transfiguration",
    history: [
      { year: "2023H1", level: "Love", value: 500 },
      { year: "2023H2", level: "Love", value: 520 },
      { year: "2024H1", level: "Joy", value: 540 },
      { year: "2024H2", level: "Joy", value: 550 },
    ],
  },
  "gloria-cai-xinyi": {
    currentLevel: "Willingness",
    energeticLog: 310,
    emotionalState: "Optimism",
    viewOfLife: "Hopeful",
    godView: "Enabling",
    process: "Intention",
    history: [
      { year: "2023H1", level: "Neutrality", value: 260 },
      { year: "2023H2", level: "Willingness", value: 300 },
      { year: "2024H1", level: "Willingness", value: 310 },
      { year: "2024H2", level: "Willingness", value: 320 },
    ],
  },
  "egan-valentino": {
    currentLevel: "Neutrality",
    energeticLog: 250,
    emotionalState: "Trust",
    viewOfLife: "Satisfactory",
    godView: "Permitting",
    process: "Release",
    history: [
      { year: "2023H1", level: "Courage", value: 220 },
      { year: "2023H2", level: "Neutrality", value: 240 },
      { year: "2024H1", level: "Neutrality", value: 250 },
      { year: "2024H2", level: "Neutrality", value: 260 },
    ],
  },
  "madhav-kapoor": {
    currentLevel: "Reason",
    energeticLog: 400,
    emotionalState: "Understanding",
    viewOfLife: "Meaningful",
    godView: "Wise",
    process: "Abstraction",
    history: [
      { year: "2023H1", level: "Acceptance", value: 370 },
      { year: "2023H2", level: "Reason", value: 390 },
      { year: "2024H1", level: "Reason", value: 400 },
      { year: "2024H2", level: "Reason", value: 410 },
    ],
  },
  "shauryaa-ladha": {
    currentLevel: "Acceptance",
    energeticLog: 350,
    emotionalState: "Forgiveness",
    viewOfLife: "Harmonious",
    godView: "Merciful",
    process: "Transcendence",
    history: [
      { year: "2023H1", level: "Willingness", value: 320 },
      { year: "2023H2", level: "Acceptance", value: 340 },
      { year: "2024H1", level: "Acceptance", value: 350 },
      { year: "2024H2", level: "Acceptance", value: 360 },
    ],
  },
  "jane-putri": {
    currentLevel: "Willingness",
    energeticLog: 310,
    emotionalState: "Optimism",
    viewOfLife: "Hopeful",
    godView: "Enabling",
    process: "Intention",
    history: [
      { year: "2023H1", level: "Neutrality", value: 270 },
      { year: "2023H2", level: "Willingness", value: 300 },
      { year: "2024H1", level: "Willingness", value: 310 },
      { year: "2024H2", level: "Willingness", value: 315 },
    ],
  },
  "mathew-ling": {
    currentLevel: "Acceptance",
    energeticLog: 350,
    emotionalState: "Forgiveness",
    viewOfLife: "Harmonious",
    godView: "Merciful",
    process: "Transcendence",
    history: [
      { year: "2023H1", level: "Willingness", value: 320 },
      { year: "2023H2", level: "Acceptance", value: 340 },
      { year: "2024H1", level: "Acceptance", value: 350 },
      { year: "2024H2", level: "Acceptance", value: 355 },
    ],
  },
  "wu-hong-rui": {
    currentLevel: "Neutrality",
    energeticLog: 250,
    emotionalState: "Trust",
    viewOfLife: "Satisfactory",
    godView: "Permitting",
    process: "Release",
    history: [
      { year: "2023H1", level: "Courage", value: 220 },
      { year: "2023H2", level: "Neutrality", value: 240 },
      { year: "2024H1", level: "Neutrality", value: 250 },
      { year: "2024H2", level: "Neutrality", value: 255 },
    ],
  },
  "ra-won-park": {
    currentLevel: "Willingness",
    energeticLog: 310,
    emotionalState: "Optimism",
    viewOfLife: "Hopeful",
    godView: "Enabling",
    process: "Intention",
    history: [
      { year: "2023H1", level: "Neutrality", value: 260 },
      { year: "2023H2", level: "Willingness", value: 300 },
      { year: "2024H1", level: "Willingness", value: 310 },
      { year: "2024H2", level: "Willingness", value: 320 },
    ],
  },
}

interface ConsciousnessMapChartProps {
  selectedMember?: string
}

interface HistoryItem {
  year: string
  value: number
  level: string
}

interface PersonData {
  currentLevel: string
  energeticLog: number
  emotionalState: string
  viewOfLife: string
  godView: string
  process: string
  history: HistoryItem[]
}

export function ConsciousnessMapChart({ selectedMember = "all" }: ConsciousnessMapChartProps) {
  const svgRef = useRef<SVGSVGElement>(null)

  // Safely get the person data with fallback
  const personData: PersonData =
    selectedMember && selectedMember !== "all" && consciousnessData[selectedMember]
      ? consciousnessData[selectedMember]
      : {
          currentLevel: "Unknown",
          energeticLog: 0,
          emotionalState: "Unknown",
          viewOfLife: "Unknown",
          godView: "Unknown",
          process: "Unknown",
          history: [],
        }

  useEffect(() => {
    if (!svgRef.current) return

    // Clear any existing SVG content
    d3.select(svgRef.current).selectAll("*").remove()

    const width = svgRef.current.clientWidth
    const height = 400 // Fixed height to prevent flattening
    const margin = { top: 40, right: 40, bottom: 60, left: 60 }
    const innerWidth = width - margin.left - margin.right
    const innerHeight = height - margin.top - margin.bottom

    // Create the SVG container
    const svg = d3
      .select(svgRef.current)
      .attr("width", width)
      .attr("height", height)
      .attr("viewBox", [0, 0, width, height])
      .attr("style", "max-width: 100%; height: auto;")

    // Create a group for the chart
    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`)

    // If no specific member is selected, show a message
    if (selectedMember === "all") {
      g.append("text")
        .attr("x", innerWidth / 2)
        .attr("y", innerHeight / 2)
        .attr("text-anchor", "middle")
        .attr("font-size", "16px")
        .attr("fill", "#6b7280")
        .text("Please select a team member to view their consciousness map")
      return
    }

    // Create scales for the timeline
    const xScale = d3.scalePoint().domain(["2023H1", "2023H2", "2024H1", "2024H2"]).range([0, innerWidth]).padding(0.5)

    const yScale = d3.scaleLinear().domain([0, 700]).range([innerHeight, 0])

    // Create the line generator
    const line = d3
      .line<{ year: string; value: number }>()
      .x((d) => xScale(d.year) as number)
      .y((d) => yScale(d.value))
      .curve(d3.curveMonotoneX)

    // Add the consciousness level bands
    const paradigms = [
      { name: "Survival", min: 0, max: 200, color: "#ffcdd2" },
      { name: "Reason & Integrity", min: 200, max: 500, color: "#c5e1a5" },
      { name: "Spiritual", min: 500, max: 700, color: "#d1c4e9" },
    ]

    // Add paradigm bands
    g.selectAll(".paradigm-band")
      .data(paradigms)
      .join("rect")
      .attr("class", "paradigm-band")
      .attr("x", 0)
      .attr("y", (d) => yScale(d.max))
      .attr("width", innerWidth)
      .attr("height", (d) => yScale(d.min) - yScale(d.max))
      .attr("fill", (d) => d.color)
      .attr("opacity", 0.2)

    // Add paradigm labels
    g.selectAll(".paradigm-label")
      .data(paradigms)
      .join("text")
      .attr("class", "paradigm-label")
      .attr("x", innerWidth - 10)
      .attr("y", (d) => yScale((d.min + d.max) / 2))
      .attr("text-anchor", "end")
      .attr("font-size", "12px")
      .attr("font-weight", "bold")
      .attr("fill", "#6b7280")
      .text((d) => d.name)

    // Add consciousness level lines
    g.selectAll(".level-line")
      .data(consciousnessLevels)
      .join("line")
      .attr("class", "level-line")
      .attr("x1", 0)
      .attr("y1", (d) => yScale(d.value))
      .attr("x2", innerWidth)
      .attr("y2", (d) => yScale(d.value))
      .attr("stroke", "#e5e7eb")
      .attr("stroke-dasharray", "3,3")

    // Add consciousness level labels
    g.selectAll(".level-label")
      .data(consciousnessLevels)
      .join("text")
      .attr("class", "level-label")
      .attr("x", 0)
      .attr("y", (d) => yScale(d.value) - 5)
      .attr("font-size", "10px")
      .attr("fill", "#6b7280")
      .text((d) => `${d.level} (${d.value})`)

    // Add the timeline path
    if (personData.history && personData.history.length > 0) {
      g.append("path")
        .datum(personData.history)
        .attr("fill", "none")
        .attr("stroke", "#4f46e5")
        .attr("stroke-width", 3)
        .attr("d", line)

      // Add dots for each data point
      g.selectAll(".dot")
        .data(personData.history)
        .join("circle")
        .attr("class", "dot")
        .attr("cx", (d) => xScale(d.year))
        .attr("cy", (d) => yScale(d.value))
        .attr("r", 5)
        .attr("fill", "#4f46e5")
        .attr("stroke", "#ffffff")
        .attr("stroke-width", 2)
        .append("title")
        .text((d) => `${d.year}: ${d.level} (${d.value})`)

      // Add year labels
      g.selectAll(".year-label")
        .data(personData.history)
        .join("text")
        .attr("class", "year-label")
        .attr("x", (d) => xScale(d.year))
        .attr("y", innerHeight + 20)
        .attr("text-anchor", "middle")
        .attr("font-size", "10px")
        .attr("fill", "#6b7280")
        .text((d) => d.year)

      // Add current level indicator
      g.append("line")
        .attr("x1", 0)
        .attr("y1", yScale(personData.energeticLog))
        .attr("x2", innerWidth)
        .attr("y2", yScale(personData.energeticLog))
        .attr("stroke", "#4f46e5")
        .attr("stroke-width", 2)
        .attr("stroke-dasharray", "5,5")

      g.append("text")
        .attr("x", innerWidth / 2)
        .attr("y", yScale(personData.energeticLog) - 10)
        .attr("text-anchor", "middle")
        .attr("font-size", "12px")
        .attr("font-weight", "bold")
        .attr("fill", "#4f46e5")
        .text(`Current: ${personData.currentLevel} (${personData.energeticLog})`)
    }

    // Add axes
    const xAxis = d3.axisBottom(xScale)
    const yAxis = d3.axisLeft(yScale)

    g.append("g")
      .attr("transform", `translate(0,${innerHeight})`)
      .call(xAxis)
      .call((g) => g.select(".domain").remove())
      .call((g) => g.selectAll(".tick line").attr("stroke", "#e5e7eb"))

    g.append("g")
      .call(yAxis)
      .call((g) => g.select(".domain").remove())
      .call((g) => g.selectAll(".tick line").attr("stroke", "#e5e7eb"))

    // Add axis labels
    g.append("text")
      .attr("x", innerWidth / 2)
      .attr("y", innerHeight + 40)
      .attr("text-anchor", "middle")
      .attr("font-size", "12px")
      .attr("font-weight", "bold")
      .text("Year")

    g.append("text")
      .attr("transform", "rotate(-90)")
      .attr("x", -innerHeight / 2)
      .attr("y", -40)
      .attr("text-anchor", "middle")
      .attr("font-size", "12px")
      .attr("font-weight", "bold")
      .text("Consciousness Level")
  }, [selectedMember, personData])

  // Find the current level details
  const currentLevelDetails = consciousnessLevels.find((level) => level.level === personData.currentLevel) || {
    level: "Unknown",
    value: 0,
    color: "#e0e0e0",
    paradigm: "Unknown",
  }

  // Get the color for a specific level
  const getLevelColor = (levelName: string) => {
    const level = consciousnessLevels.find((l) => l.level === levelName)
    return level ? level.color : "#e0e0e0"
  }

  return (
    <div className="w-full h-full flex flex-col">
      <div className="flex items-center mb-4">
        <div className="text-sm font-medium mr-2">Current Level:</div>
        <Badge
          className="px-3 py-1 text-sm font-medium"
          style={{
            backgroundColor: `${getLevelColor(personData.currentLevel)}80`,
            color: "#333",
          }}
        >
          {personData.currentLevel} ({personData.energeticLog})
        </Badge>
      </div>

      <div className="flex-1 overflow-hidden" style={{ height: "400px" }}>
        {/* Consciousness Map Visualization */}
        <svg ref={svgRef} className="w-full h-full" />
      </div>

      {/* Details section */}
      {selectedMember !== "all" && (
        <div className="mt-4 grid grid-cols-5 gap-4 bg-white p-4 rounded-lg shadow-sm">
          <div className="space-y-1">
            <div className="text-xs text-gray-500">Emotional State</div>
            <div className="font-medium">{personData.emotionalState}</div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-gray-500">View of Life</div>
            <div className="font-medium">{personData.viewOfLife}</div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-gray-500">God View</div>
            <div className="font-medium">{personData.godView}</div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-gray-500">Process</div>
            <div className="font-medium">{personData.process}</div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-gray-500">Paradigm</div>
            <div className="font-medium">{currentLevelDetails.paradigm}</div>
          </div>
        </div>
      )}

      <div className="mt-4 text-xs text-center text-gray-500">Based on Dr. David R. Hawkins' Map of Consciousness</div>
    </div>
  )
}
