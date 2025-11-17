"use client"

import type React from "react"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { FolderOpen } from "lucide-react"

export function DocumentDirectoryForm() {
  const [formState, setFormState] = useState({
    teamMember: "",
    directoryPath: "",
    autoSync: true,
    includeSubfolders: true,
  })

  const handleChange = (field: string, value: string | boolean) => {
    setFormState((prev) => ({ ...prev, [field]: value }))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // Handle form submission
    console.log("Form submitted:", formState)
    // Reset form or show success message
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Add Directory Link</CardTitle>
        <CardDescription>Connect a document directory to a team member's profile</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="team-member">Team Member</Label>
              <Select value={formState.teamMember} onValueChange={(value) => handleChange("teamMember", value)}>
                <SelectTrigger id="team-member">
                  <SelectValue placeholder="Select team member" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="sarah-chen">Sarah Chen - CEO</SelectItem>
                  <SelectItem value="michael-rodriguez">Michael Rodriguez - COO</SelectItem>
                  <SelectItem value="aisha-johnson">Aisha Johnson - CFO</SelectItem>
                  <SelectItem value="david-kim">David Kim - CTO</SelectItem>
                  <SelectItem value="elena-petrov">Elena Petrov - VP Product</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="directory-type">Directory Type</Label>
              <Select>
                <SelectTrigger id="directory-type">
                  <SelectValue placeholder="Select directory type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="network">Network Share</SelectItem>
                  <SelectItem value="sharepoint">SharePoint</SelectItem>
                  <SelectItem value="onedrive">OneDrive</SelectItem>
                  <SelectItem value="google">Google Drive</SelectItem>
                  <SelectItem value="other">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="directory-path">Directory Path</Label>
            <div className="flex gap-2">
              <Input
                id="directory-path"
                placeholder="Enter directory path (e.g., /shared/documents/team-member)"
                value={formState.directoryPath}
                onChange={(e) => handleChange("directoryPath", e.target.value)}
                className="flex-1"
              />
              <Button variant="outline" type="button">
                <FolderOpen className="mr-2 h-4 w-4" />
                Browse
              </Button>
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="auto-sync"
                checked={formState.autoSync}
                onCheckedChange={(checked) => handleChange("autoSync", checked as boolean)}
              />
              <Label htmlFor="auto-sync">Automatically sync documents from this directory</Label>
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox
                id="include-subfolders"
                checked={formState.includeSubfolders}
                onCheckedChange={(checked) => handleChange("includeSubfolders", checked as boolean)}
              />
              <Label htmlFor="include-subfolders">Include subfolders in document sync</Label>
            </div>
          </div>
        </form>
      </CardContent>
      <CardFooter className="flex justify-end gap-2">
        <Button variant="outline">Cancel</Button>
        <Button onClick={handleSubmit}>Save Directory Link</Button>
      </CardFooter>
    </Card>
  )
}
