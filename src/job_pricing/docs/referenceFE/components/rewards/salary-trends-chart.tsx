"use client"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Text } from "@/components/ui/text"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts"

// Updated data to include a third line for comparison
const data = [
  { year: "2018", market: 85000, company: 82000, role: 80000 },
  { year: "2019", market: 87500, company: 84000, role: 82500 },
  { year: "2020", market: 90000, company: 88000, role: 85000 },
  { year: "2021", market: 95000, company: 92000, role: 88000 },
  { year: "2022", market: 102000, company: 97000, role: 92000 },
  { year: "2023", market: 108000, company: 103000, role: 95000 },
]

interface SalaryTrendsChartProps {
  className?: string
}

export function SalaryTrendsChart({ className }: SalaryTrendsChartProps) {
  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle>Salary Trends</CardTitle>
        <Text className="text-muted-foreground">Historical salary trends for Software Engineer</Text>
      </CardHeader>
      <CardContent>
        <div className="h-[350px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={data}
              margin={{
                top: 10,
                right: 30,
                left: 20,
                bottom: 30, // Increased to make room for legend
              }}
            >
              <CartesianGrid vertical={false} strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="year" axisLine={true} tickLine={true} tick={{ fontSize: 12 }} />
              <YAxis
                domain={[75000, 100000]}
                axisLine={true}
                tickLine={true}
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => value.toLocaleString()}
              />
              <Tooltip
                formatter={(value) => [`$${value.toLocaleString()}`, undefined]}
                labelFormatter={(label) => `Year: ${label}`}
                contentStyle={{ border: "1px solid #f0f0f0", borderRadius: "4px", padding: "8px" }}
              />
              <Legend verticalAlign="bottom" height={36} wrapperStyle={{ paddingTop: "10px" }} />
              <Line
                type="monotone"
                dataKey="market"
                name="Market Average"
                stroke="#333"
                strokeWidth={1.5}
                dot={{ r: 4, strokeWidth: 1 }}
                activeDot={{ r: 6 }}
              />
              <Line
                type="monotone"
                dataKey="company"
                name="Company Average"
                stroke="#555"
                strokeWidth={1.5}
                dot={{ r: 4, strokeWidth: 1 }}
                activeDot={{ r: 6 }}
              />
              <Line
                type="monotone"
                dataKey="role"
                name="Role Average"
                stroke="#777"
                strokeWidth={1.5}
                dot={{ r: 4, strokeWidth: 1 }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}
