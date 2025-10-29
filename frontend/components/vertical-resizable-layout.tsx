"use client"

import React from "react"

import { useState, useRef, useCallback } from "react"

interface VerticalResizableLayoutProps {
  topPanel: React.ReactNode
  bottomPanel: React.ReactNode
  defaultTopHeight?: number
  minTopHeight?: number
  maxTopHeight?: number
}

export function VerticalResizableLayout({
  topPanel,
  bottomPanel,
  defaultTopHeight = 60,
  minTopHeight = 30,
  maxTopHeight = 80,
}: VerticalResizableLayoutProps) {
  const [topHeight, setTopHeight] = useState(defaultTopHeight)
  const [isDragging, setIsDragging] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleMouseMove = useCallback(
    (e: MouseEvent) => {
      if (!isDragging || !containerRef.current) return

      const containerRect = containerRef.current.getBoundingClientRect()
      const newTopHeight = ((e.clientY - containerRect.top) / containerRect.height) * 100

      const clampedHeight = Math.min(Math.max(newTopHeight, minTopHeight), maxTopHeight)
      setTopHeight(clampedHeight)
    },
    [isDragging, minTopHeight, maxTopHeight],
  )

  const handleMouseUp = useCallback(() => {
    setIsDragging(false)
  }, [])

  // Add global mouse event listeners
  React.useEffect(() => {
    if (isDragging) {
      document.addEventListener("mousemove", handleMouseMove)
      document.addEventListener("mouseup", handleMouseUp)
      document.body.style.cursor = "row-resize"
      document.body.style.userSelect = "none"

      return () => {
        document.removeEventListener("mousemove", handleMouseMove)
        document.removeEventListener("mouseup", handleMouseUp)
        document.body.style.cursor = ""
        document.body.style.userSelect = ""
      }
    }
  }, [isDragging, handleMouseMove, handleMouseUp])

  return (
    <div ref={containerRef} className="flex flex-col h-full">
      {/* Top Panel */}
      <div style={{ height: `${topHeight}%` }} className="overflow-hidden">
        {topPanel}
      </div>

      {/* Resizer */}
      <div
        className={`h-1 bg-slate-200 hover:bg-amber-400 cursor-row-resize transition-colors ${
          isDragging ? "bg-amber-400" : ""
        }`}
        onMouseDown={handleMouseDown}
      />

      {/* Bottom Panel */}
      <div style={{ height: `${100 - topHeight}%` }} className="overflow-hidden">
        {bottomPanel}
      </div>
    </div>
  )
}
