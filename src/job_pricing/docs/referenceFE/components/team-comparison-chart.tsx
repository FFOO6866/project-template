"use client"

import { useState } from "react"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LabelList } from "recharts"
import { Button } from "@/components/ui/button"
import { ChevronDown } from "lucide-react"
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

// Sample data for the team comparison chart
const competencyData = [
  {
    name: "Strategic Thinking",
    "Sarah Chen": 95,
    "Michael Rodriguez": 82,
    "Aisha Johnson": 88,
    "David Kim": 90,
    "Elena Petrov": 85,
    "James Wilson": 78,
    "Olivia Martinez": 75,
    "Robert Chen": 80,
  },
  {
    name: "Leadership",
    "Sarah Chen": 92,
    "Michael Rodriguez": 85,
    "Aisha Johnson": 78,
    "David Kim": 82,
    "Elena Petrov": 88,
    "James Wilson": 80,
    "Olivia Martinez": 84,
    "Robert Chen": 90,
  },
  {
    name: "Innovation",
    "Sarah Chen": 88,
    "Michael Rodriguez": 75,
    "Aisha Johnson": 70,
    "David Kim": 95,
    "Elena Petrov": 92,
    "James Wilson": 85,
    "Olivia Martinez": 72,
    "Robert Chen": 68,
  },
  {
    name: "Communication",
    "Sarah Chen": 90,
    "Michael Rodriguez": 82,
    "Aisha Johnson": 85,
    "David Kim": 75,
    "Elena Petrov": 80,
    "James Wilson": 92,
    "Olivia Martinez": 94,
    "Robert Chen": 88,
  },
  {
    name: "Execution",
    "Sarah Chen": 85,
    "Michael Rodriguez": 94,
    "Aisha Johnson": 90,
    "David Kim": 82,
    "Elena Petrov": 78,
    "James Wilson": 75,
    "Olivia Martinez": 88,
    "Robert Chen": 80,
  },
]

// Define colors for each team member
const memberColors = {
  "Sarah Chen": "#4f46e5", // Indigo
  "Michael Rodriguez": "#0891b2", // Cyan
  "Aisha Johnson": "#16a34a", // Green
  "David Kim": "#2563eb", // Blue
  "Elena Petrov": "#7c3aed", // Violet
  "James Wilson": "#db2777", // Pink
  "Olivia Martinez": "#ea580c", // Orange
  "Robert Chen": "#6b7280", // Gray
}

export function TeamComparisonChart() {
  // State to track which team members are selected for display
  const [selectedMembers, setSelectedMembers] = useState<string[]>(Object.keys(memberColors).slice(0, 4))

  // Toggle a team member's selection
  const toggleMember = (member: string) => {
    if (selectedMembers.includes(member)) {
      setSelectedMembers(selectedMembers.filter((m) => m !== member))
    } else {
      setSelectedMembers([...selectedMembers, member])
    }
  }

  // Filter the data to only include selected members
  const filteredData = competencyData.map((item) => {
    const filteredItem: any = { name: item.name }
    selectedMembers.forEach((member) => {
      filteredItem[member] = item[member as keyof typeof item]
    })
    return filteredItem
  })

  return (
    <div className="w-full h-full">
      <div className="flex justify-end mb-4">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" className="h-8">
              Select Team Members <ChevronDown className="ml-2 h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel>Team Members</DropdownMenuLabel>
            <DropdownMenuSeparator />
            {Object.keys(memberColors).map((member) => (
              <DropdownMenuCheckboxItem
                key={member}
                checked={selectedMembers.includes(member)}
                onCheckedChange={() => toggleMember(member)}
              >
                {member}
              </DropdownMenuCheckboxItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
      <ResponsiveContainer width="100%" height="90%">
        <BarChart data={filteredData} layout="vertical" margin={{ top: 20, right: 30, left: 100, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
          <XAxis type="number" domain={[0, 100]} tickCount={6} />
          <YAxis dataKey="name" type="category" width={90} />
          <Tooltip
            formatter={(value) => [`${value}%`, ""]}
            contentStyle={{
              backgroundColor: "white",
              borderRadius: "8px",
              boxShadow: "0 4px 12px rgba(0, 0, 0, 0.1)",
              border: "none",
            }}
          />
          <Legend />
          {selectedMembers.map((member) => (
            <Bar
              key={member}
              dataKey={member}
              fill={memberColors[member as keyof typeof memberColors]}
              barSize={20}
              stackId="stack"
            >
              <LabelList
                dataKey={member}
                position="right"
                formatter={(value: number) => (value > 15 ? `${value}%` : "")}
              />
            </Bar>
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
