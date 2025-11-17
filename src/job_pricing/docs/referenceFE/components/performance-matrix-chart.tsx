"use client"

import { useEffect, useRef } from "react"
import * as d3 from "d3"

// Realistic data for the management trainees with performance, potential, and quantum leadership scores
const teamMembers = [
  {
    id: "camille-wong-yuk",
    name: "Camille Wong Yuk",
    role: "Management Trainee",
    performance: 85,
    potential: 88,
    quantumLeadership: {
      followership: 87,
      coaching: 84,
      leadershipDrive: 89,
      collaboration: 86,
      strategicPartnerships: 83,
      conflictManagement: 82,
    },
  },
  {
    id: "marcel-melhado",
    name: "Marcel Melhado",
    role: "Management Trainee",
    performance: 83,
    potential: 85,
    quantumLeadership: {
      followership: 85,
      coaching: 81,
      leadershipDrive: 84,
      collaboration: 86,
      strategicPartnerships: 82,
      conflictManagement: 80,
    },
  },
  {
    id: "vivian-ho",
    name: "Vivian Ho",
    role: "Management Trainee",
    performance: 88,
    potential: 82,
    quantumLeadership: {
      followership: 84,
      coaching: 89,
      leadershipDrive: 83,
      collaboration: 85,
      strategicPartnerships: 90,
      conflictManagement: 86,
    },
  },
  {
    id: "massie-shen",
    name: "Massie Shen",
    role: "Management Trainee",
    performance: 86,
    potential: 84,
    quantumLeadership: {
      followership: 88,
      coaching: 85,
      leadershipDrive: 83,
      collaboration: 87,
      strategicPartnerships: 84,
      conflictManagement: 85,
    },
  },
  {
    id: "gloria-cai-xinyi",
    name: "Gloria Cai Xinyi",
    role: "Management Trainee",
    performance: 84,
    potential: 87,
    quantumLeadership: {
      followership: 86,
      coaching: 88,
      leadershipDrive: 85,
      collaboration: 83,
      strategicPartnerships: 87,
      conflictManagement: 84,
    },
  },
  {
    id: "egan-valentino",
    name: "Egan Valentino",
    role: "Management Trainee",
    performance: 82,
    potential: 89,
    quantumLeadership: {
      followership: 89,
      coaching: 83,
      leadershipDrive: 90,
      collaboration: 81,
      strategicPartnerships: 84,
      conflictManagement: 82,
    },
  },
  {
    id: "madhav-kapoor",
    name: "Madhav Kapoor",
    role: "Management Trainee",
    performance: 87,
    potential: 83,
    quantumLeadership: {
      followership: 83,
      coaching: 86,
      leadershipDrive: 88,
      collaboration: 85,
      strategicPartnerships: 89,
      conflictManagement: 87,
    },
  },
  {
    id: "shauryaa-ladha",
    name: "Shauryaa Ladha",
    role: "Management Trainee",
    performance: 85,
    potential: 85,
    quantumLeadership: {
      followership: 85,
      coaching: 85,
      leadershipDrive: 86,
      collaboration: 84,
      strategicPartnerships: 85,
      conflictManagement: 85,
    },
  },
  {
    id: "jane-putri",
    name: "Jane Putri",
    role: "Management Trainee",
    performance: 89,
    potential: 81,
    quantumLeadership: {
      followership: 82,
      coaching: 90,
      leadershipDrive: 84,
      collaboration: 88,
      strategicPartnerships: 86,
      conflictManagement: 89,
    },
  },
  {
    id: "mathew-ling",
    name: "Mathew Ling",
    role: "Management Trainee",
    performance: 84,
    potential: 86,
    quantumLeadership: {
      followership: 87,
      coaching: 84,
      leadershipDrive: 85,
      collaboration: 86,
      strategicPartnerships: 83,
      conflictManagement: 84,
    },
  },
  {
    id: "wu-hong-rui",
    name: "Wu Hong Rui",
    role: "Management Trainee",
    performance: 83,
    potential: 88,
    quantumLeadership: {
      followership: 89,
      coaching: 82,
      leadershipDrive: 87,
      collaboration: 83,
      strategicPartnerships: 84,
      conflictManagement: 81,
    },
  },
  {
    id: "ra-won-park",
    name: "Ra Won Park",
    role: "Management Trainee",
    performance: 86,
    potential: 85,
    quantumLeadership: {
      followership: 84,
      coaching: 87,
      leadershipDrive: 85,
      collaboration: 86,
      strategicPartnerships: 85,
      conflictManagement: 88,
    },
  },
]

interface PerformanceMatrixChartProps {
  selectedMember?: string
}

export function PerformanceMatrixChart({ selectedMember = "all" }: PerformanceMatrixChartProps) {
  const svgRef = useRef<SVGSVGElement>(null)

  useEffect(() => {
    if (!svgRef.current) return

    // Clear any existing SVG content
    d3.select(svgRef.current).selectAll("*").remove()

    const width = svgRef.current.clientWidth
    const height = svgRef.current.clientHeight
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

    // Create scales
    const xScale = d3.scaleLinear().domain([70, 95]).range([0, innerWidth])
    const yScale = d3.scaleLinear().domain([70, 95]).range([innerHeight, 0])

    // Create grid lines
    const gridLinesX = [75, 80, 85, 90]
    const gridLinesY = [75, 80, 85, 90]

    // Add vertical grid lines
    g.selectAll(".grid-line-x")
      .data(gridLinesX)
      .join("line")
      .attr("class", "grid-line-x")
      .attr("x1", (d) => xScale(d))
      .attr("y1", 0)
      .attr("x2", (d) => xScale(d))
      .attr("y2", innerHeight)
      .attr("stroke", "#e5e7eb")
      .attr("stroke-dasharray", "3,3")

    // Add horizontal grid lines
    g.selectAll(".grid-line-y")
      .data(gridLinesY)
      .join("line")
      .attr("class", "grid-line-y")
      .attr("x1", 0)
      .attr("y1", (d) => yScale(d))
      .attr("x2", innerWidth)
      .attr("y2", (d) => yScale(d))
      .attr("stroke", "#e5e7eb")
      .attr("stroke-dasharray", "3,3")

    // Add quadrant labels
    const quadrants = [
      {
        x: innerWidth * 0.25,
        y: innerHeight * 0.25,
        label: "Future Stars",
        description: "High Leadership Drive & Followership",
      },
      {
        x: innerWidth * 0.75,
        y: innerHeight * 0.25,
        label: "Star Performers",
        description: "Strong Coaching & Strategic Partnerships",
      },
      {
        x: innerWidth * 0.25,
        y: innerHeight * 0.75,
        label: "Solid Contributors",
        description: "Reliable Collaboration & Teamwork",
      },
      {
        x: innerWidth * 0.75,
        y: innerHeight * 0.75,
        label: "High Performers",
        description: "Excellent Conflict Management",
      },
    ]

    g.selectAll(".quadrant-label")
      .data(quadrants)
      .join("text")
      .attr("class", "quadrant-label")
      .attr("x", (d) => d.x)
      .attr("y", (d) => d.y)
      .attr("text-anchor", "middle")
      .attr("font-size", "12px")
      .attr("font-weight", "bold")
      .text((d) => d.label)

    g.selectAll(".quadrant-description")
      .data(quadrants)
      .join("text")
      .attr("class", "quadrant-description")
      .attr("x", (d) => d.x)
      .attr("y", (d) => d.y + 20)
      .attr("text-anchor", "middle")
      .attr("font-size", "10px")
      .attr("fill", "#6b7280")
      .text((d) => d.description)

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
      .text("Performance")

    g.append("text")
      .attr("transform", "rotate(-90)")
      .attr("x", -innerHeight / 2)
      .attr("y", -40)
      .attr("text-anchor", "middle")
      .attr("font-size", "12px")
      .attr("font-weight", "bold")
      .text("Potential")

    // Add dots for team members
    g.selectAll(".dot")
      .data(teamMembers)
      .join("circle")
      .attr("class", "dot")
      .attr("cx", (d) => xScale(d.performance))
      .attr("cy", (d) => yScale(d.potential))
      .attr("r", (d) => (d.id === selectedMember ? 10 : 6))
      .attr("fill", (d) => (d.id === selectedMember ? "#4f46e5" : "#9ca3af"))
      .attr("stroke", (d) => (d.id === selectedMember ? "#ffffff" : "none"))
      .attr("stroke-width", 2)
      .attr("opacity", (d) => (selectedMember === "all" || d.id === selectedMember ? 1 : 0.5))
      .style("cursor", "pointer")
      .append("title")
      .text(
        (d) => `${d.name} (${d.role})
Performance: ${d.performance}%
Potential: ${d.potential}%
X-Factor Scores:
- Followership: ${d.quantumLeadership.followership}%
- Coaching & Compassionate Leadership: ${d.quantumLeadership.coaching}%
- Leadership Drive: ${d.quantumLeadership.leadershipDrive}%
- Collaboration & Teamwork: ${d.quantumLeadership.collaboration}%
- Strategic Partnerships: ${d.quantumLeadership.strategicPartnerships}%
- Conflict Management: ${d.quantumLeadership.conflictManagement}%`,
      )

    // Add labels for the dots
    g.selectAll(".dot-label")
      .data(teamMembers)
      .join("text")
      .attr("class", "dot-label")
      .attr("x", (d) => xScale(d.performance))
      .attr("y", (d) => yScale(d.potential) - 12)
      .attr("text-anchor", "middle")
      .attr("font-size", "10px")
      .attr("font-weight", (d) => (d.id === selectedMember ? "bold" : "normal"))
      .attr("fill", (d) => (d.id === selectedMember ? "#4f46e5" : "#6b7280"))
      .attr("opacity", (d) => {
        if (selectedMember === "all") return 1
        return d.id === selectedMember ? 1 : 0.5
      })
      .text((d) => d.name.split(" ")[0]) // Show only first name

    // Add quadrant dividers
    const midPointX = 82.5 // Middle point for performance quadrants
    const midPointY = 82.5 // Middle point for potential quadrants

    // Vertical divider
    g.append("line")
      .attr("x1", xScale(midPointX))
      .attr("y1", 0)
      .attr("x2", xScale(midPointX))
      .attr("y2", innerHeight)
      .attr("stroke", "#9ca3af")
      .attr("stroke-width", 1)

    // Horizontal divider
    g.append("line")
      .attr("x1", 0)
      .attr("y1", yScale(midPointY))
      .attr("x2", innerWidth)
      .attr("y2", yScale(midPointY))
      .attr("stroke", "#9ca3af")
      .attr("stroke-width", 1)
  }, [selectedMember])

  return <svg ref={svgRef} className="w-full h-full" />
}
