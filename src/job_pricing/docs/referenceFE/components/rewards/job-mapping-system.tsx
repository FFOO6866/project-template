"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Plus, ArrowUpDown, Globe, Building, Users } from "lucide-react"
import { Line, LineChart, XAxis, YAxis, CartesianGrid, Legend, ResponsiveContainer } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"

// Mock data for market data
const mockMarketData = [
  {
    id: "md1",
    source: "external",
    jobTitle: "Software Engineer",
    company: "TechVision Corp",
    location: "Singapore",
    industry: "Technology",
    minSalary: 80000,
    maxSalary: 120000,
    medianSalary: 95000,
    currency: "SGD",
    jobGrade: "P3",
    positionClass: 50,
    lastUpdated: "2023-10-15",
  },
  {
    id: "md2",
    source: "external",
    jobTitle: "Senior Software Engineer",
    company: "GlobalTech Solutions",
    location: "Singapore",
    industry: "Technology",
    minSalary: 100000,
    maxSalary: 150000,
    medianSalary: 125000,
    currency: "SGD",
    jobGrade: "P4",
    positionClass: 54,
    lastUpdated: "2023-10-15",
  },
  {
    id: "md3",
    source: "market",
    jobTitle: "Software Engineer",
    location: "Singapore",
    industry: "Technology",
    minSalary: 75000,
    maxSalary: 110000,
    medianSalary: 90000,
    currency: "SGD",
    lastUpdated: "2023-09-01",
  },
  {
    id: "md4",
    source: "market",
    jobTitle: "Product Manager",
    location: "Singapore",
    industry: "Technology",
    minSalary: 110000,
    maxSalary: 160000,
    medianSalary: 130000,
    currency: "SGD",
    lastUpdated: "2023-09-01",
  },
  {
    id: "md5",
    source: "internal",
    jobTitle: "Software Engineer",
    location: "Singapore",
    minSalary: 85000,
    maxSalary: 125000,
    medianSalary: 100000,
    currency: "SGD",
    jobGrade: "P3",
    positionClass: 50,
    lastUpdated: "2023-11-01",
  },
  {
    id: "md6",
    source: "internal",
    jobTitle: "Product Manager",
    location: "Singapore",
    minSalary: 120000,
    maxSalary: 170000,
    medianSalary: 140000,
    currency: "SGD",
    jobGrade: "P5",
    positionClass: 57,
    lastUpdated: "2023-11-01",
  },
]

// Mock data for comparable jobs
const mockComparableJobs = [
  {
    id: "cj1",
    jobTitle: "Software Engineer",
    source: "internal",
    location: "Singapore",
    similarity: 100,
    salary: {
      min: 85000,
      median: 100000,
      max: 125000,
    },
    currency: "SGD",
  },
  {
    id: "cj2",
    jobTitle: "Software Engineer",
    source: "external",
    company: "TechVision Corp",
    location: "Singapore",
    similarity: 95,
    salary: {
      min: 80000,
      median: 95000,
      max: 120000,
    },
    currency: "SGD",
  },
  {
    id: "cj3",
    jobTitle: "Software Engineer",
    source: "market",
    location: "Singapore",
    similarity: 90,
    salary: {
      min: 75000,
      median: 90000,
      max: 110000,
    },
    currency: "SGD",
  },
  {
    id: "cj4",
    jobTitle: "Software Developer",
    source: "market",
    location: "Singapore",
    similarity: 85,
    salary: {
      min: 70000,
      median: 85000,
      max: 105000,
    },
    currency: "SGD",
  },
  {
    id: "cj5",
    jobTitle: "Frontend Developer",
    source: "external",
    company: "InnovateSoft",
    location: "Singapore",
    similarity: 80,
    salary: {
      min: 75000,
      median: 90000,
      max: 110000,
    },
    currency: "SGD",
  },
]

// Mock data for salary trends
const mockSalaryTrends = [
  { year: 2019, internal: 85000, market: 80000, external: 82000 },
  { year: 2020, internal: 88000, market: 83000, external: 85000 },
  { year: 2021, internal: 92000, market: 86000, external: 88000 },
  { year: 2022, internal: 96000, market: 88000, external: 92000 },
  { year: 2023, internal: 100000, market: 90000, external: 95000 },
]

export function JobMappingSystem() {
  const [selectedJobTitle, setSelectedJobTitle] = useState("Software Engineer")
  const [selectedLocation, setSelectedLocation] = useState("Singapore")
  const [selectedIndustry, setSelectedIndustry] = useState("Technology")
  const [selectedJobGrade, setSelectedJobGrade] = useState("P3")

  // Filter comparable jobs based on selected criteria
  const filteredJobs = mockComparableJobs.filter(
    (job) =>
      job.jobTitle.toLowerCase().includes(selectedJobTitle.toLowerCase()) &&
      job.location.toLowerCase().includes(selectedLocation.toLowerCase()),
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Job Mapping System</h2>
          <p className="text-muted-foreground">Compare jobs and their associated pay across different sources</p>
        </div>
        <Button>
          <Plus className="mr-2 h-4 w-4" /> Add Market Data
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Job Search Criteria</CardTitle>
          <CardDescription>Filter and find comparable jobs</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <div>
              <Label htmlFor="job-title">Job Title</Label>
              <Input
                id="job-title"
                placeholder="e.g. Software Engineer"
                value={selectedJobTitle}
                onChange={(e) => setSelectedJobTitle(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="location">Location</Label>
              <Input
                id="location"
                placeholder="e.g. Singapore"
                value={selectedLocation}
                onChange={(e) => setSelectedLocation(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="industry">Industry</Label>
              <Select value={selectedIndustry} onValueChange={setSelectedIndustry}>
                <SelectTrigger id="industry">
                  <SelectValue placeholder="Select industry" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Technology">Technology</SelectItem>
                  <SelectItem value="Finance">Finance</SelectItem>
                  <SelectItem value="Healthcare">Healthcare</SelectItem>
                  <SelectItem value="Manufacturing">Manufacturing</SelectItem>
                  <SelectItem value="Retail">Retail</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="job-grade">Job Grade</Label>
              <Select value={selectedJobGrade} onValueChange={setSelectedJobGrade}>
                <SelectTrigger id="job-grade">
                  <SelectValue placeholder="Select job grade" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="P1">P1</SelectItem>
                  <SelectItem value="P2">P2</SelectItem>
                  <SelectItem value="P3">P3</SelectItem>
                  <SelectItem value="P4">P4</SelectItem>
                  <SelectItem value="P5">P5</SelectItem>
                  <SelectItem value="P6">P6</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 md:grid-cols-3">
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>Comparable Jobs</CardTitle>
            <CardDescription>Jobs matching your search criteria</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Job Title</TableHead>
                  <TableHead>Source</TableHead>
                  <TableHead>Location</TableHead>
                  <TableHead>
                    <div className="flex items-center">
                      Similarity
                      <ArrowUpDown className="ml-1 h-4 w-4" />
                    </div>
                  </TableHead>
                  <TableHead>
                    <div className="flex items-center">
                      Median Salary
                      <ArrowUpDown className="ml-1 h-4 w-4" />
                    </div>
                  </TableHead>
                  <TableHead>Salary Range</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredJobs.map((job) => (
                  <TableRow key={job.id}>
                    <TableCell className="font-medium">{job.jobTitle}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className="flex items-center gap-1">
                        {job.source === "internal" && <Users className="h-3 w-3" />}
                        {job.source === "external" && <Building className="h-3 w-3" />}
                        {job.source === "market" && <Globe className="h-3 w-3" />}
                        {job.source === "internal"
                          ? "Internal"
                          : job.source === "external"
                            ? `${job.company}`
                            : "Market"}
                      </Badge>
                    </TableCell>
                    <TableCell>{job.location}</TableCell>
                    <TableCell>
                      <div className="flex items-center">
                        <span className="mr-2">{job.similarity}%</span>
                        <div className="h-2 w-16 bg-gray-200 rounded-full overflow-hidden">
                          <div className="h-full bg-primary" style={{ width: `${job.similarity}%` }} />
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      {job.salary.median.toLocaleString()} {job.currency}
                    </TableCell>
                    <TableCell>
                      {job.salary.min.toLocaleString()} - {job.salary.max.toLocaleString()} {job.currency}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Pay for Position</CardTitle>
            <CardDescription>Recommended salary range based on comparable jobs</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div>
                <div className="flex justify-between mb-2">
                  <Label>Recommended Salary Range</Label>
                  <span className="text-sm text-muted-foreground">SGD</span>
                </div>
                <div className="text-2xl font-bold">85,000 - 110,000</div>
                <div className="text-sm text-muted-foreground mt-1">Median: 95,000</div>
              </div>

              <div>
                <Label className="mb-2 block">Percentile Position</Label>
                <div className="h-4 w-full bg-gray-200 rounded-full overflow-hidden relative">
                  <div className="h-full bg-primary" style={{ width: "60%" }} />
                  <div className="absolute top-0 left-[60%] h-4 w-0.5 bg-black transform -translate-x-1/2" />
                </div>
                <div className="flex justify-between mt-1 text-xs text-muted-foreground">
                  <span>0%</span>
                  <span>25%</span>
                  <span>50%</span>
                  <span>75%</span>
                  <span>100%</span>
                </div>
                <div className="text-center mt-2 text-sm">
                  <span className="font-medium">60th Percentile</span> relative to market
                </div>
              </div>

              <div>
                <Label className="mb-2 block">Competitiveness Ratio</Label>
                <div className="text-2xl font-bold">1.05</div>
                <div className="text-sm text-muted-foreground mt-1">5% above market median</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Salary Trends</CardTitle>
          <CardDescription>Historical salary trends for {selectedJobTitle}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[300px] relative w-full overflow-hidden">
            <ChartContainer
              config={{
                internal: {
                  label: "Internal",
                  color: "hsl(var(--chart-1))",
                },
                market: {
                  label: "Market",
                  color: "hsl(var(--chart-2))",
                },
                external: {
                  label: "External",
                  color: "hsl(var(--chart-3))",
                },
              }}
            >
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={mockSalaryTrends}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="year" />
                  <YAxis />
                  <ChartTooltip content={<ChartTooltipContent />} />
                  <Legend />
                  <Line type="monotone" dataKey="internal" stroke="var(--color-internal)" strokeWidth={2} />
                  <Line type="monotone" dataKey="market" stroke="var(--color-market)" strokeWidth={2} />
                  <Line type="monotone" dataKey="external" stroke="var(--color-external)" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </ChartContainer>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Market Data Sources</CardTitle>
          <CardDescription>View and manage market data sources</CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="external">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="external">External (Mercer/McLagan)</TabsTrigger>
              <TabsTrigger value="market">Job Market</TabsTrigger>
              <TabsTrigger value="internal">Internal</TabsTrigger>
            </TabsList>
            <TabsContent value="external" className="pt-6">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Job Title</TableHead>
                    <TableHead>Company</TableHead>
                    <TableHead>Location</TableHead>
                    <TableHead>Industry</TableHead>
                    <TableHead>Median Salary</TableHead>
                    <TableHead>Job Grade</TableHead>
                    <TableHead>Last Updated</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {mockMarketData
                    .filter((data) => data.source === "external")
                    .map((data) => (
                      <TableRow key={data.id}>
                        <TableCell className="font-medium">{data.jobTitle}</TableCell>
                        <TableCell>{data.company}</TableCell>
                        <TableCell>{data.location}</TableCell>
                        <TableCell>{data.industry}</TableCell>
                        <TableCell>
                          {data.medianSalary.toLocaleString()} {data.currency}
                        </TableCell>
                        <TableCell>{data.jobGrade}</TableCell>
                        <TableCell>{data.lastUpdated}</TableCell>
                      </TableRow>
                    ))}
                </TableBody>
              </Table>
            </TabsContent>
            <TabsContent value="market" className="pt-6">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Job Title</TableHead>
                    <TableHead>Location</TableHead>
                    <TableHead>Industry</TableHead>
                    <TableHead>Median Salary</TableHead>
                    <TableHead>Last Updated</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {mockMarketData
                    .filter((data) => data.source === "market")
                    .map((data) => (
                      <TableRow key={data.id}>
                        <TableCell className="font-medium">{data.jobTitle}</TableCell>
                        <TableCell>{data.location}</TableCell>
                        <TableCell>{data.industry}</TableCell>
                        <TableCell>
                          {data.medianSalary.toLocaleString()} {data.currency}
                        </TableCell>
                        <TableCell>{data.lastUpdated}</TableCell>
                      </TableRow>
                    ))}
                </TableBody>
              </Table>
            </TabsContent>
            <TabsContent value="internal" className="pt-6">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Job Title</TableHead>
                    <TableHead>Location</TableHead>
                    <TableHead>Median Salary</TableHead>
                    <TableHead>Job Grade</TableHead>
                    <TableHead>Last Updated</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {mockMarketData
                    .filter((data) => data.source === "internal")
                    .map((data) => (
                      <TableRow key={data.id}>
                        <TableCell className="font-medium">{data.jobTitle}</TableCell>
                        <TableCell>{data.location}</TableCell>
                        <TableCell>
                          {data.medianSalary.toLocaleString()} {data.currency}
                        </TableCell>
                        <TableCell>{data.jobGrade}</TableCell>
                        <TableCell>{data.lastUpdated}</TableCell>
                      </TableRow>
                    ))}
                </TableBody>
              </Table>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  )
}
