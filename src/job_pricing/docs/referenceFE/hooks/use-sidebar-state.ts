"use client"

import { useState, useEffect } from "react"

// Custom hook to manage sidebar state across components
export function useSidebarState() {
  const [expanded, setExpanded] = useState(true)

  // Initialize from localStorage on mount
  useEffect(() => {
    if (typeof window !== "undefined") {
      const savedState = localStorage.getItem("sidebarExpanded")
      if (savedState !== null) {
        setExpanded(savedState === "true")
      }
    }
  }, [])

  // Update function that also updates localStorage and dispatches an event
  const updateExpanded = (newState: boolean) => {
    setExpanded(newState)
    if (typeof window !== "undefined") {
      localStorage.setItem("sidebarExpanded", newState.toString())

      // Dispatch a custom event so other components can react
      window.dispatchEvent(new Event("sidebarStateChange"))
    }
  }

  return { expanded, setExpanded: updateExpanded }
}
