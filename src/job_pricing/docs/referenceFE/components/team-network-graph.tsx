"use client"

import { useEffect, useRef } from "react"
import * as d3 from "d3"

// Sample data for the team network graph
const nodes = [
  { id: "Sarah Chen", group: 1, role: "CEO" },
  { id: "Michael Rodriguez", group: 1, role: "COO" },
  { id: "Aisha Johnson", group: 1, role: "CFO" },
  { id: "David Kim", group: 1, role: "CTO" },
  { id: "Elena Petrov", group: 2, role: "VP Product" },
  { id: "James Wilson", group: 2, role: "VP Marketing" },
  { id: "Olivia Martinez", group: 2, role: "VP Sales" },
  { id: "Robert Chen", group: 2, role: "VP HR" },
]

const links = [
  { source: "Sarah Chen", target: "Michael Rodriguez", value: 5, type: "direct" },
  { source: "Sarah Chen", target: "Aisha Johnson", value: 5, type: "direct" },
  { source: "Sarah Chen", target: "David Kim", value: 5, type: "direct" },
  { source: "Michael Rodriguez", target: "Elena Petrov", value: 4, type: "direct" },
  { source: "Michael Rodriguez", target: "James Wilson", value: 3, type: "direct" },
  { source: "Michael Rodriguez", target: "Olivia Martinez", value: 4, type: "direct" },
  { source: "Michael Rodriguez", target: "Robert Chen", value: 3, type: "direct" },
  { source: "Aisha Johnson", target: "Olivia Martinez", value: 2, type: "collaboration" },
  { source: "David Kim", target: "Elena Petrov", value: 5, type: "direct" },
  { source: "Elena Petrov", target: "James Wilson", value: 3, type: "collaboration" },
  { source: "James Wilson", target: "Olivia Martinez", value: 4, type: "direct" },
  { source: "Robert Chen", target: "Sarah Chen", value: 2, type: "collaboration" },
  { source: "Robert Chen", target: "Olivia Martinez", value: 2, type: "collaboration" },
  { source: "David Kim", target: "James Wilson", value: 2, type: "collaboration" },
  { source: "Aisha Johnson", target: "Robert Chen", value: 2, type: "collaboration" },
]

export function TeamNetworkGraph() {
  const svgRef = useRef<SVGSVGElement>(null)

  useEffect(() => {
    if (!svgRef.current) return

    // Clear any existing SVG content
    d3.select(svgRef.current).selectAll("*").remove()

    const width = svgRef.current.clientWidth
    const height = svgRef.current.clientHeight

    // Create the SVG container
    const svg = d3
      .select(svgRef.current)
      .attr("width", width)
      .attr("height", height)
      .attr("viewBox", [0, 0, width, height])
      .attr("style", "max-width: 100%; height: auto;")

    // Create a group for the graph
    const g = svg.append("g")

    // Create a color scale for node groups
    const color = d3.scaleOrdinal().domain(["1", "2"]).range(["#4f46e5", "#0891b2"])

    // Create a color scale for link types
    const linkColor = d3.scaleOrdinal().domain(["direct", "collaboration"]).range(["#9ca3af", "#d1d5db"])

    // Create a simulation with forces
    const simulation = d3
      .forceSimulation(nodes)
      .force(
        "link",
        d3
          .forceLink(links)
          .id((d: any) => d.id)
          .distance((d: any) => 150 / d.value),
      )
      .force("charge", d3.forceManyBody().strength(-400))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("x", d3.forceX(width / 2).strength(0.1))
      .force("y", d3.forceY(height / 2).strength(0.1))

    // Create links
    const link = g
      .append("g")
      .attr("stroke-opacity", 0.6)
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("stroke", (d: any) => linkColor(d.type))
      .attr("stroke-width", (d: any) => Math.sqrt(d.value))

    // Create nodes
    const node = g
      .append("g")
      .attr("stroke", "#fff")
      .attr("stroke-width", 1.5)
      .selectAll("circle")
      .data(nodes)
      .join("circle")
      .attr("r", (d: any) => (d.group === 1 ? 12 : 10))
      .attr("fill", (d: any) => color(d.group.toString()))
      .call(d3.drag<SVGCircleElement, any>().on("start", dragstarted).on("drag", dragged).on("end", dragended) as any)

    // Add node labels
    const labels = g
      .append("g")
      .attr("class", "labels")
      .selectAll("text")
      .data(nodes)
      .join("text")
      .attr("text-anchor", "middle")
      .attr("dy", (d: any) => (d.group === 1 ? -20 : -18))
      .attr("font-size", (d: any) => (d.group === 1 ? "12px" : "11px"))
      .attr("font-weight", (d: any) => (d.group === 1 ? "bold" : "normal"))
      .text((d: any) => d.id)
      .attr("pointer-events", "none")

    // Add role labels
    const roleLabels = g
      .append("g")
      .attr("class", "role-labels")
      .selectAll("text")
      .data(nodes)
      .join("text")
      .attr("text-anchor", "middle")
      .attr("dy", (d: any) => (d.group === 1 ? -5 : -3))
      .attr("font-size", "9px")
      .attr("fill", "#6b7280")
      .text((d: any) => d.role)
      .attr("pointer-events", "none")

    // Add tooltips
    node.append("title").text((d: any) => `${d.id} (${d.role})`)

    // Update positions on simulation tick
    simulation.on("tick", () => {
      link
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y)

      node.attr("cx", (d: any) => d.x).attr("cy", (d: any) => d.y)

      labels.attr("x", (d: any) => d.x).attr("y", (d: any) => d.y)
      roleLabels.attr("x", (d: any) => d.x).attr("y", (d: any) => d.y)
    })

    // Drag functions
    function dragstarted(event: any, d: any) {
      if (!event.active) simulation.alphaTarget(0.3).restart()
      d.fx = d.x
      d.fy = d.y
    }

    function dragged(event: any, d: any) {
      d.fx = event.x
      d.fy = event.y
    }

    function dragended(event: any, d: any) {
      if (!event.active) simulation.alphaTarget(0)
      d.fx = null
      d.fy = null
    }

    // Add zoom functionality
    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.5, 5])
      .on("zoom", (event) => {
        g.attr("transform", event.transform)
      })

    svg.call(zoom as any)

    // Add legend
    const legend = svg
      .append("g")
      .attr("class", "legend")
      .attr("transform", `translate(${width - 150}, 20)`)

    // Node legend
    const nodeLegend = legend.append("g").attr("class", "node-legend")

    nodeLegend
      .append("text")
      .attr("x", 0)
      .attr("y", 0)
      .attr("font-size", "10px")
      .attr("font-weight", "bold")
      .text("Team Members")

    // C-Suite
    nodeLegend.append("circle").attr("cx", 10).attr("cy", 20).attr("r", 6).attr("fill", color("1"))

    nodeLegend.append("text").attr("x", 25).attr("y", 23).attr("font-size", "9px").text("C-Suite")

    // VP Level
    nodeLegend.append("circle").attr("cx", 10).attr("cy", 40).attr("r", 6).attr("fill", color("2"))

    nodeLegend.append("text").attr("x", 25).attr("y", 43).attr("font-size", "9px").text("VP Level")

    // Link legend
    const linkLegend = legend.append("g").attr("class", "link-legend").attr("transform", "translate(0, 60)")

    linkLegend.append("text").attr('x", 0)  "translate(0, 60)')

    linkLegend
      .append("text")
      .attr("x", 0)
      .attr("y", 0)
      .attr("font-size", "10px")
      .attr("font-weight", "bold")
      .text("Relationships")

    // Direct reporting
    linkLegend
      .append("line")
      .attr("x1", 0)
      .attr("y1", 20)
      .attr("x2", 20)
      .attr("y2", 20)
      .attr("stroke", linkColor("direct"))
      .attr("stroke-width", 2)

    linkLegend.append("text").attr("x", 25).attr("y", 23).attr("font-size", "9px").text("Direct Reporting")

    // Collaboration
    linkLegend
      .append("line")
      .attr("x1", 0)
      .attr("y1", 40)
      .attr("x2", 20)
      .attr("y2", 40)
      .attr("stroke", linkColor("collaboration"))
      .attr("stroke-width", 2)

    linkLegend.append("text").attr("x", 25).attr("y", 43).attr("font-size", "9px").text("Collaboration")

    return () => {
      simulation.stop()
    }
  }, [])

  return <svg ref={svgRef} className="w-full h-full" />
}
