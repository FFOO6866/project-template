"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Plus, Edit, Download, Upload } from "lucide-react"

// Mock data for performance matrix
const mockPerformanceMatrix = {
  id: "pm1",
  name: "Standard Performance Matrix",
  description: "Standard performance-based variable bonus matrix",
  rows: [
    { id: "pl1", name: "Exceptional", description: "Consistently exceeds expectations", minScore: 90, maxScore: 100 },
    { id: "pl2", name: "Exceeds Expectations", description: "Often exceeds expectations", minScore: 80, maxScore: 89 },
    {
      id: "pl3",
      name: "Meets Expectations",
      description: "Consistently meets expectations",
      minScore: 70,
      maxScore: 79,
    },
    { id: "pl4", name: "Partially Meets", description: "Sometimes meets expectations", minScore: 60, maxScore: 69 },
    { id: "pl5", name: "Does Not Meet", description: "Rarely meets expectations", minScore: 0, maxScore: 59 },
  ],
  columns: [
    { id: "pp1", name: "Below Market", description: "Below market rate", minPercentile: 0, maxPercentile: 25 },
    { id: "pp2", name: "Low Market", description: "Low market rate", minPercentile: 26, maxPercentile: 50 },
    { id: "pp3", name: "Mid Market", description: "Mid market rate", minPercentile: 51, maxPercentile: 75 },
    { id: "pp4", name: "High Market", description: "High market rate", minPercentile: 76, maxPercentile: 100 },
  ],
  cells: [
    { rowId: "pl1", columnId: "pp1", bonusPercentage: 20 },
    { rowId: "pl1", columnId: "pp2", bonusPercentage: 25 },
    { rowId: "pl1", columnId: "pp3", bonusPercentage: 30 },
    { rowId: "pl1", columnId: "pp4", bonusPercentage: 35 },

    { rowId: "pl2", columnId: "pp1", bonusPercentage: 15 },
    { rowId: "pl2", columnId: "pp2", bonusPercentage: 20 },
    { rowId: "pl2", columnId: "pp3", bonusPercentage: 25 },
    { rowId: "pl2", columnId: "pp4", bonusPercentage: 30 },

    { rowId: "pl3", columnId: "pp1", bonusPercentage: 10 },
    { rowId: "pl3", columnId: "pp2", bonusPercentage: 15 },
    { rowId: "pl3", columnId: "pp3", bonusPercentage: 20 },
    { rowId: "pl3", columnId: "pp4", bonusPercentage: 25 },

    { rowId: "pl4", columnId: "pp1", bonusPercentage: 5 },
    { rowId: "pl4", columnId: "pp2", bonusPercentage: 10 },
    { rowId: "pl4", columnId: "pp3", bonusPercentage: 15 },
    { rowId: "pl4", columnId: "pp4", bonusPercentage: 20 },

    { rowId: "pl5", columnId: "pp1", bonusPercentage: 0 },
    { rowId: "pl5", columnId: "pp2", bonusPercentage: 0 },
    { rowId: "pl5", columnId: "pp3", bonusPercentage: 5 },
    { rowId: "pl5", columnId: "pp4", bonusPercentage: 10 },
  ],
}

// Mock data for employee compensation with mock-up names
const mockEmployeeCompensation = [
  {
    employeeId: "emp1",
    employeeName: "Alex Morgan",
    jobTitle: "Software Engineer",
    jobGrade: "P3",
    baseSalary: 100000,
    payPositionPercentile: 60,
    performanceScore: 85,
    bonusPercentage: 25,
    bonusAmount: 25000,
    totalCompensation: 125000,
    currency: "SGD",
    effectiveDate: "2023-12-31",
  },
  {
    employeeId: "emp2",
    employeeName: "Jordan Lee",
    jobTitle: "Senior Software Engineer",
    jobGrade: "P4",
    baseSalary: 130000,
    payPositionPercentile: 70,
    performanceScore: 92,
    bonusPercentage: 30,
    bonusAmount: 39000,
    totalCompensation: 169000,
    currency: "SGD",
    effectiveDate: "2023-12-31",
  },
  {
    employeeId: "emp3",
    employeeName: "Taylor Singh",
    jobTitle: "Product Manager",
    jobGrade: "P5",
    baseSalary: 140000,
    payPositionPercentile: 65,
    performanceScore: 88,
    bonusPercentage: 25,
    bonusAmount: 35000,
    totalCompensation: 175000,
    currency: "SGD",
    effectiveDate: "2023-12-31",
  },
  {
    employeeId: "emp4",
    employeeName: "Casey Wong",
    jobTitle: "UX Designer",
    jobGrade: "P3",
    baseSalary: 95000,
    payPositionPercentile: 55,
    performanceScore: 78,
    bonusPercentage: 20,
    bonusAmount: 19000,
    totalCompensation: 114000,
    currency: "SGD",
    effectiveDate: "2023-12-31",
  },
  {
    employeeId: "emp5",
    employeeName: "Riley Patel",
    jobTitle: "Marketing Manager",
    jobGrade: "P4",
    baseSalary: 120000,
    payPositionPercentile: 60,
    performanceScore: 75,
    bonusPercentage: 20,
    bonusAmount: 24000,
    totalCompensation: 144000,
    currency: "SGD",
    effectiveDate: "2023-12-31",
  },
]

export function PayForPerformanceSystem() {
  const [selectedMatrix, setSelectedMatrix] = useState(mockPerformanceMatrix)
  const [editMode, setEditMode] = useState(false)
  const [selectedCell, setSelectedCell] = useState(null)

  const getPerformanceLevelColor = (level) => {
    const index = mockPerformanceMatrix.rows.findIndex((row) => row.id === level.id)
    const colors = [
      "bg-green-100 text-green-800",
      "bg-blue-100 text-blue-800",
      "bg-yellow-100 text-yellow-800",
      "bg-orange-100 text-orange-800",
      "bg-red-100 text-red-800",
    ]
    return colors[index] || "bg-gray-100 text-gray-800"
  }

  const getPayPositionColor = (level) => {
    const index = mockPerformanceMatrix.columns.findIndex((col) => col.id === level.id)
    const colors = [
      "bg-purple-100 text-purple-800",
      "bg-indigo-100 text-indigo-800",
      "bg-cyan-100 text-cyan-800",
      "bg-teal-100 text-teal-800",
    ]
    return colors[index] || "bg-gray-100 text-gray-800"
  }

  const getCellColor = (rowId, columnId) => {
    const cell = mockPerformanceMatrix.cells.find((cell) => cell.rowId === rowId && cell.columnId === columnId)
    if (!cell) return "bg-gray-50"

    if (cell.bonusPercentage >= 30) return "bg-green-100"
    if (cell.bonusPercentage >= 20) return "bg-blue-100"
    if (cell.bonusPercentage >= 10) return "bg-yellow-100"
    if (cell.bonusPercentage > 0) return "bg-orange-100"
    return "bg-red-100"
  }

  const handleCellClick = (cell) => {
    setSelectedCell(cell)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Pay for Performance System</h2>
          <p className="text-muted-foreground">Create and manage performance-based variable bonus matrices</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">
            <Upload className="mr-2 h-4 w-4" /> Import
          </Button>
          <Button>
            <Plus className="mr-2 h-4 w-4" /> New Matrix
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <div className="flex justify-between items-start">
            <div>
              <CardTitle>Performance Matrix</CardTitle>
              <CardDescription>Define bonus percentages based on performance and pay position</CardDescription>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={() => setEditMode(!editMode)}>
                <Edit className="mr-2 h-4 w-4" /> {editMode ? "View Mode" : "Edit Mode"}
              </Button>
              <Button variant="outline" size="sm">
                <Download className="mr-2 h-4 w-4" /> Export
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Label htmlFor="matrix-name">Matrix Name</Label>
                <Input id="matrix-name" value={selectedMatrix.name} disabled={!editMode} />
              </div>
              <div>
                <Label htmlFor="matrix-description">Description</Label>
                <Input id="matrix-description" value={selectedMatrix.description} disabled={!editMode} />
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr>
                    <th className="border p-2 bg-gray-50 w-40">Performance Level</th>
                    {selectedMatrix.columns.map((column) => (
                      <th key={column.id} className="border p-2 text-center">
                        <div className={`inline-block px-2 py-1 rounded-md text-xs ${getPayPositionColor(column)}`}>
                          {column.name}
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">
                          {column.minPercentile}% - {column.maxPercentile}%
                        </div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {selectedMatrix.rows.map((row) => (
                    <tr key={row.id}>
                      <td className="border p-2">
                        <div className={`inline-block px-2 py-1 rounded-md text-xs ${getPerformanceLevelColor(row)}`}>
                          {row.name}
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">
                          {row.minScore} - {row.maxScore}
                        </div>
                      </td>
                      {selectedMatrix.columns.map((column) => {
                        const cell = selectedMatrix.cells.find(
                          (cell) => cell.rowId === row.id && cell.columnId === column.id,
                        )
                        return (
                          <td
                            key={`${row.id}-${column.id}`}
                            className={`border p-2 text-center ${getCellColor(row.id, column.id)} cursor-pointer hover:opacity-80`}
                            onClick={() => handleCellClick(cell)}
                          >
                            {cell ? `${cell.bonusPercentage}%` : "N/A"}
                          </td>
                        )
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {selectedCell && editMode && (
              <div className="p-4 border rounded-md bg-gray-50">
                <h3 className="font-medium mb-3">Edit Bonus Percentage</h3>
                <div className="grid gap-4 md:grid-cols-3">
                  <div>
                    <Label>Performance Level</Label>
                    <div className="font-medium mt-1">
                      {selectedMatrix.rows.find((row) => row.id === selectedCell.rowId)?.name}
                    </div>
                  </div>
                  <div>
                    <Label>Pay Position</Label>
                    <div className="font-medium mt-1">
                      {selectedMatrix.columns.find((col) => col.id === selectedCell.columnId)?.name}
                    </div>
                  </div>
                  <div>
                    <Label htmlFor="bonus-percentage">Bonus Percentage</Label>
                    <div className="flex items-center gap-2">
                      <Input
                        id="bonus-percentage"
                        type="number"
                        value={selectedCell.bonusPercentage}
                        className="w-20"
                      />
                      <span>%</span>
                    </div>
                  </div>
                </div>
                <div className="flex justify-end gap-2 mt-4">
                  <Button variant="outline" size="sm" onClick={() => setSelectedCell(null)}>
                    Cancel
                  </Button>
                  <Button size="sm">Update</Button>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Employee Compensation</CardTitle>
          <CardDescription>View and manage employee compensation and variable bonuses</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Employee</TableHead>
                <TableHead>Job Title</TableHead>
                <TableHead>Job Grade</TableHead>
                <TableHead>Base Salary</TableHead>
                <TableHead>Pay Position</TableHead>
                <TableHead>Performance Score</TableHead>
                <TableHead>Bonus %</TableHead>
                <TableHead>Bonus Amount</TableHead>
                <TableHead>Total Compensation</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {mockEmployeeCompensation.map((employee) => (
                <TableRow key={employee.employeeId}>
                  <TableCell className="font-medium">{employee.employeeName}</TableCell>
                  <TableCell>{employee.jobTitle}</TableCell>
                  <TableCell>{employee.jobGrade}</TableCell>
                  <TableCell>
                    {employee.baseSalary.toLocaleString()} {employee.currency}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center">
                      <span className="mr-2">{employee.payPositionPercentile}%</span>
                      <div className="h-2 w-16 bg-gray-200 rounded-full overflow-hidden">
                        <div className="h-full bg-primary" style={{ width: `${employee.payPositionPercentile}%` }} />
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center">
                      <span className="mr-2">{employee.performanceScore}</span>
                      <div className="h-2 w-16 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className={`h-full ${
                            employee.performanceScore >= 90
                              ? "bg-green-500"
                              : employee.performanceScore >= 80
                                ? "bg-blue-500"
                                : employee.performanceScore >= 70
                                  ? "bg-yellow-500"
                                  : employee.performanceScore >= 60
                                    ? "bg-orange-500"
                                    : "bg-red-500"
                          }`}
                          style={{ width: `${employee.performanceScore}%` }}
                        />
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>{employee.bonusPercentage}%</TableCell>
                  <TableCell>
                    {employee.bonusAmount.toLocaleString()} {employee.currency}
                  </TableCell>
                  <TableCell className="font-medium">
                    {employee.totalCompensation.toLocaleString()} {employee.currency}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}
