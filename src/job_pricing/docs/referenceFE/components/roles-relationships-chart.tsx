"use client"

import { useState } from "react"
import {
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  ZAxis,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

// Sample data for the Roles & Relationships chart
const rolesData = {
  "Sarah Chen": [
    {
      role: "Strategic Leader",
      formalInfluence: 95,
      informalInfluence: 90,
      relationships: 25,
      name: "Strategic Leader",
    },
    { role: "Change Agent", formalInfluence: 85, informalInfluence: 92, relationships: 20, name: "Change Agent" },
    { role: "Mentor", formalInfluence: 80, informalInfluence: 88, relationships: 15, name: "Mentor" },
    { role: "Decision Maker", formalInfluence: 92, informalInfluence: 85, relationships: 22, name: "Decision Maker" },
    { role: "Innovator", formalInfluence: 78, informalInfluence: 82, relationships: 18, name: "Innovator" },
    { role: "Connector", formalInfluence: 75, informalInfluence: 95, relationships: 30, name: "Connector" },
  ],
  "Michael Rodriguez": [
    {
      role: "Strategic Leader",
      formalInfluence: 88,
      informalInfluence: 82,
      relationships: 20,
      name: "Strategic Leader",
    },
    { role: "Change Agent", formalInfluence: 80, informalInfluence: 78, relationships: 15, name: "Change Agent" },
    { role: "Mentor", formalInfluence: 85, informalInfluence: 90, relationships: 18, name: "Mentor" },
    { role: "Decision Maker", formalInfluence: 92, informalInfluence: 75, relationships: 22, name: "Decision Maker" },
    { role: "Innovator", formalInfluence: 70, informalInfluence: 72, relationships: 12, name: "Innovator" },
    { role: "Connector", formalInfluence: 78, informalInfluence: 88, relationships: 25, name: "Connector" },
  ],
  "Aisha Johnson": [
    {
      role: "Strategic Leader",
      formalInfluence: 90,
      informalInfluence: 85,
      relationships: 18,
      name: "Strategic Leader",
    },
    { role: "Change Agent", formalInfluence: 82, informalInfluence: 80, relationships: 15, name: "Change Agent" },
    { role: "Mentor", formalInfluence: 78, informalInfluence: 85, relationships: 12, name: "Mentor" },
    { role: "Decision Maker", formalInfluence: 95, informalInfluence: 80, relationships: 20, name: "Decision Maker" },
    { role: "Innovator", formalInfluence: 75, informalInfluence: 78, relationships: 14, name: "Innovator" },
    { role: "Connector", formalInfluence: 80, informalInfluence: 92, relationships: 22, name: "Connector" },
  ],
}

export function RolesRelationshipsChart() {
  const [selectedPerson, setSelectedPerson] = useState("Sarah Chen")

  // Get the data for the selected person
  const data = rolesData[selectedPerson as keyof typeof rolesData]

  return (
    <div className="w-full h-full">
      <div className="flex justify-end mb-4">
        <div className="w-64">
          <Select value={selectedPerson} onValueChange={setSelectedPerson}>
            <SelectTrigger>
              <SelectValue placeholder="Select team member" />
            </SelectTrigger>
            <SelectContent>
              {Object.keys(rolesData).map((person) => (
                <SelectItem key={person} value={person}>
                  {person}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
      <ResponsiveContainer width="100%" height="90%">
        <ScatterChart
          margin={{
            top: 20,
            right: 20,
            bottom: 20,
            left: 20,
          }}
        >
          <CartesianGrid />
          <XAxis
            type="number"
            dataKey="formalInfluence"
            name="Formal Influence"
            domain={[50, 100]}
            label={{ value: "Formal Influence", position: "bottom", offset: 0 }}
          />
          <YAxis
            type="number"
            dataKey="informalInfluence"
            name="Informal Influence"
            domain={[50, 100]}
            label={{ value: "Informal Influence", angle: -90, position: "left" }}
          />
          <ZAxis type="number" dataKey="relationships" range={[100, 500]} name="Relationship Count" />
          <Tooltip
            cursor={{ strokeDasharray: "3 3" }}
            formatter={(value, name) => [`${value}${name === "Relationship Count" ? "" : "%"}`, name]}
            contentStyle={{
              backgroundColor: "white",
              borderRadius: "8px",
              boxShadow: "0 4px 12px rgba(0, 0, 0, 0.1)",
              border: "none",
            }}
          />
          <Legend />
          <Scatter name={selectedPerson} data={data} fill="#4f46e5" />
        </ScatterChart>
      </ResponsiveContainer>
      <div className="flex justify-center mt-4">
        <div className="text-xs text-muted-foreground">
          Bubble size represents the number of strategic relationships in each role
        </div>
      </div>
    </div>
  )
}
