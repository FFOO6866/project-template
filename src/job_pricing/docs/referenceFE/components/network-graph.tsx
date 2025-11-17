"use client"

import { useEffect, useRef } from "react"
import * as d3 from "d3"

// Sample data for the network graph
const nodes = [
  { id: "CEO", group: 1 },
  { id: "COO", group: 1 },
  { id: "CFO", group: 1 },
  { id: "CTO", group: 1 },
  { id: "VP Product", group: 2 },
  { id: "VP Marketing", group: 2 },
  { id: "VP Sales", group: 2 },
  { id: "VP HR", group: 2 },
  { id: "Product Manager 1", group: 3 },
  { id: "Product Manager 2", group: 3 },
  { id: "Marketing Manager", group: 3 },
  { id: "Sales Manager", group: 3 },
  { id: "HR Manager", group: 3 },
  { id: "Developer 1", group: 4 },
  { id: "Developer 2", group: 4 },
  { id: "Developer 3", group: 4 },
  { id: "Designer 1", group: 4 },
  { id: "Designer 2", group: 4 },
  { id: "Marketing Specialist", group: 4 },
  { id: "Sales Rep 1", group: 4 },
  { id: "Sales Rep 2", group: 4 },
  { id: "HR Specialist", group: 4 },
]

const links = [
  { source: "CEO", target: "COO", value: 5 },
  { source: "CEO", target: "CFO", value: 5 },
  { source: "CEO", target: "CTO", value: 5 },
  { source: "COO", target: "VP Product", value: 3 },
  { source: "COO", target: "VP Marketing", value: 3 },
  { source: "COO", target: "VP Sales", value: 3 },
  { source: "COO", target: "VP HR", value: 3 },
  { source: "VP Product", target: "Product Manager 1", value: 2 },
  { source: "VP Product", target: "Product Manager 2", value: 2 },
  { source: "VP Marketing", target: "Marketing Manager", value: 2 },
  { source: "VP Sales", target: "Sales Manager", value: 2 },
  { source: "VP HR", target: "HR Manager", value: 2 },
  { source: "Product Manager 1", target: "Developer 1", value: 1 },
  { source: "Product Manager 1", target: "Developer 2", value: 1 },
  { source: "Product Manager 2", target: "Developer 3", value: 1 },
  { source: "Product Manager 2", target: "Designer 1", value: 1 },
  { source: "Marketing Manager", target: "Designer 2", value: 1 },
  { source: "Marketing Manager", target: "Marketing Specialist", value: 1 },
  { source: "Sales Manager", target: "Sales Rep 1", value: 1 },
  { source: "Sales Manager", target: "Sales Rep 2", value: 1 },
  { source: "HR Manager", target: "HR Specialist", value: 1 },
  // Cross-functional connections
  { source: "Developer 1", target: "Designer 1", value: 1 },
  { source: "Developer 2", target: "Designer 2", value: 1 },
  { source: "Marketing Specialist", target: "Sales Rep 1", value: 1 },
  { source: "Product Manager 1", target: "Marketing Manager", value: 1 },
  { source: "VP Product", target: "VP Marketing", value: 2 },
  { source: "VP Marketing", target: "VP Sales", value: 2 },
]

export function NetworkGraph() {
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
    const color = d3.scaleOrdinal(d3.schemeCategory10)

    // Create a simulation with forces
    const simulation = d3
      .forceSimulation(nodes)
      .force(
        "link",
        d3
          .forceLink(links)
          .id((d: any) => d.id)
          .distance((d: any) => 100 / d.value),
      )
      .force("charge", d3.forceManyBody().strength(-400))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("x", d3.forceX(width / 2).strength(0.1))
      .force("y", d3.forceY(height / 2).strength(0.1))

    // Create links
    const link = g
      .append("g")
      .attr("stroke", "#999")
      .attr("stroke-opacity", 0.6)
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("stroke-width", (d: any) => Math.sqrt(d.value))

    // Create nodes
    const node = g
      .append("g")
      .attr("stroke", "#fff")
      .attr("stroke-width", 1.5)
      .selectAll("circle")
      .data(nodes)
      .join("circle")
      .attr("r", (d: any) => (d.group === 1 ? 12 : d.group === 2 ? 10 : d.group === 3 ? 8 : 6))
      .attr("fill", (d: any) => color(d.group))
      .call(d3.drag<SVGCircleElement, any>().on("start", dragstarted).on("drag", dragged).on("end", dragended) as any)

    // Add node labels
    const labels = g
      .append("g")
      .attr("class", "labels")
      .selectAll("text")
      .data(nodes)
      .join("text")
      .attr("text-anchor", "middle")
      .attr("dy", "0.35em")
      .attr("font-size", (d: any) => (d.group === 1 ? "10px" : d.group === 2 ? "8px" : "6px"))
      .text((d: any) => d.id)
      .attr("pointer-events", "none")

    // Add tooltips
    node.append("title").text((d: any) => d.id)

    // Update positions on simulation tick
    simulation.on("tick", () => {
      link
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y)

      node.attr("cx", (d: any) => d.x).attr("cy", (d: any) => d.y)

      labels.attr("x", (d: any) => d.x).attr("y", (d: any) => d.y)
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

    return () => {
      simulation.stop()
    }
  }, [])

  return <svg ref={svgRef} className="w-full h-full" />
}
