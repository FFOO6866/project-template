"use client"

import type React from "react"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { Checkbox } from "@/components/ui/checkbox"
import { CalendarIcon } from "lucide-react"
import { Calendar } from "@/components/ui/calendar"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { format } from "date-fns"
import { cn } from "@/lib/utils"

export function AssessmentForm() {
  const [date, setDate] = useState<Date>()
  const [selectedTeamMembers, setSelectedTeamMembers] = useState<string[]>([])

  const teamMembers = [
    { id: "sarah-chen", name: "Sarah Chen", role: "CEO" },
    { id: "michael-rodriguez", name: "Michael Rodriguez", role: "COO" },
    { id: "aisha-johnson", name: "Aisha Johnson", role: "CFO" },
    { id: "david-kim", name: "David Kim", role: "CTO" },
    { id: "elena-petrov", name: "Elena Petrov", role: "VP Product" },
    { id: "james-wilson", name: "James Wilson", role: "VP Marketing" },
    { id: "olivia-martinez", name: "Olivia Martinez", role: "VP Sales" },
    { id: "robert-chen", name: "Robert Chen", role: "VP HR" },
  ]

  const toggleTeamMember = (id: string) => {
    setSelectedTeamMembers((prev) => (prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // Handle form submission
    console.log("Form submitted:", { date, selectedTeamMembers })
    // Reset form or show success message
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Create New Assessment</CardTitle>
        <CardDescription>Set up a new assessment for MT profiles</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="assessment-name">Assessment Name</Label>
              <Input id="assessment-name" placeholder="Enter assessment name" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="assessment-type">Assessment Type</Label>
              <Select>
                <SelectTrigger id="assessment-type">
                  <SelectValue placeholder="Select assessment type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="leadership">Leadership Assessment</SelectItem>
                  <SelectItem value="mintzberg">Mintzberg Roles</SelectItem>
                  <SelectItem value="xfactor">X-Factor Scoring</SelectItem>
                  <SelectItem value="performance">Performance Matrix</SelectItem>
                  <SelectItem value="custom">Custom Assessment</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="assessment-date">Assessment Date</Label>
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className={cn("w-full justify-start text-left font-normal", !date && "text-muted-foreground")}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {date ? format(date, "PPP") : "Select date"}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0">
                  <Calendar mode="single" selected={date} onSelect={setDate} initialFocus />
                </PopoverContent>
              </Popover>
            </div>
            <div className="space-y-2">
              <Label htmlFor="assessment-status">Status</Label>
              <Select defaultValue="scheduled">
                <SelectTrigger id="assessment-status">
                  <SelectValue placeholder="Select status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="scheduled">Scheduled</SelectItem>
                  <SelectItem value="in-progress">In Progress</SelectItem>
                  <SelectItem value="completed">Completed</SelectItem>
                  <SelectItem value="draft">Draft</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label>Team Members</Label>
            <div className="grid gap-2 mt-2">
              {teamMembers.map((member) => (
                <div key={member.id} className="flex items-center space-x-2">
                  <Checkbox
                    id={`member-${member.id}`}
                    checked={selectedTeamMembers.includes(member.id)}
                    onCheckedChange={() => toggleTeamMember(member.id)}
                  />
                  <Label htmlFor={`member-${member.id}`} className="flex items-center gap-2">
                    {member.name}
                    <span className="text-xs text-muted-foreground">({member.role})</span>
                  </Label>
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="assessment-notes">Notes</Label>
            <Textarea
              id="assessment-notes"
              placeholder="Enter any additional notes or instructions"
              className="min-h-[100px]"
            />
          </div>
        </form>
      </CardContent>
      <CardFooter className="flex justify-end gap-2">
        <Button variant="outline">Cancel</Button>
        <Button onClick={handleSubmit}>Create Assessment</Button>
      </CardFooter>
    </Card>
  )
}
