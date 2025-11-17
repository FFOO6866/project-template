"use client"

import type React from "react"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { FileIcon as FilePdf, FileSpreadsheet, FileText, File } from "lucide-react"

export function DocumentTypeForm() {
  const [formState, setFormState] = useState({
    name: "",
    description: "",
    defaultDirectory: "/documents/{name}/{document-type}",
    icon: "FileText",
  })

  const handleChange = (field: string, value: string) => {
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
        <CardTitle>Add Document Type</CardTitle>
        <CardDescription>Define a new document type for team member profiles</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="type-name">Type Name</Label>
              <Input
                id="type-name"
                placeholder="Enter document type name"
                value={formState.name}
                onChange={(e) => handleChange("name", e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="icon-type">Icon</Label>
              <Select value={formState.icon} onValueChange={(value) => handleChange("icon", value)}>
                <SelectTrigger id="icon-type">
                  <SelectValue placeholder="Select icon" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="FilePdf">
                    <div className="flex items-center gap-2">
                      <FilePdf className="h-4 w-4 text-red-500" />
                      PDF Document
                    </div>
                  </SelectItem>
                  <SelectItem value="FileSpreadsheet">
                    <div className="flex items-center gap-2">
                      <FileSpreadsheet className="h-4 w-4 text-green-500" />
                      Spreadsheet
                    </div>
                  </SelectItem>
                  <SelectItem value="FileText">
                    <div className="flex items-center gap-2">
                      <FileText className="h-4 w-4 text-blue-500" />
                      Text Document
                    </div>
                  </SelectItem>
                  <SelectItem value="File">
                    <div className="flex items-center gap-2">
                      <File className="h-4 w-4 text-purple-500" />
                      Generic File
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="type-description">Description</Label>
            <Textarea
              id="type-description"
              placeholder="Enter a description for this document type"
              value={formState.description}
              onChange={(e) => handleChange("description", e.target.value)}
              rows={3}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="default-directory">Default Directory Path</Label>
            <Input
              id="default-directory"
              placeholder="Enter default directory path for this document type"
              value={formState.defaultDirectory}
              onChange={(e) => handleChange("defaultDirectory", e.target.value)}
            />
            <p className="text-xs text-muted-foreground mt-1">
              Variables: {"{name}"} - Team member name, {"{document-type}"} - Document type
            </p>
          </div>
        </form>
      </CardContent>
      <CardFooter className="flex justify-end gap-2">
        <Button variant="outline">Cancel</Button>
        <Button onClick={handleSubmit}>Save Document Type</Button>
      </CardFooter>
    </Card>
  )
}
