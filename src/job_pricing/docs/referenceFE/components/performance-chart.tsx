"use client"

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts"

const data = [
  { month: "Jan", engagement: 65, advocacy: 78, contribution: 62 },
  { month: "Feb", engagement: 68, advocacy: 82, contribution: 65 },
  { month: "Mar", engagement: 75, advocacy: 85, contribution: 71 },
  { month: "Apr", engagement: 82, advocacy: 86, contribution: 74 },
  { month: "May", engagement: 85, advocacy: 90, contribution: 76 },
  { month: "Jun", engagement: 87, advocacy: 92, contribution: 78 },
]

export function PerformanceChart() {
  return (
    <div className="h-[300px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={data}
          margin={{
            top: 5,
            right: 30,
            left: 20,
            bottom: 5,
          }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#f5f5f5" />
          <XAxis dataKey="month" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
          <YAxis
            stroke="#888888"
            fontSize={12}
            tickLine={false}
            axisLine={false}
            tickFormatter={(value) => `${value}%`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "white",
              borderRadius: "8px",
              boxShadow: "0 4px 12px rgba(0, 0, 0, 0.1)",
              border: "none",
            }}
            formatter={(value: number) => [`${value}%`, ""]}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="engagement"
            stroke="#4f46e5"
            strokeWidth={2}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
            name="Workforce Engagement"
          />
          <Line
            type="monotone"
            dataKey="advocacy"
            stroke="#0891b2"
            strokeWidth={2}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
            name="Cultural Advocacy"
          />
          <Line
            type="monotone"
            dataKey="contribution"
            stroke="#16a34a"
            strokeWidth={2}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
            name="Strategic Contribution"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
