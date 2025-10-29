"use client"

import type React from "react"

import { Button } from "@/components/ui/button"
import { X, Plus } from "lucide-react"

export interface ChatTab {
  id: string
  documentId: number
  fileName: string
}

/**
 * Clean up document filename for display
 * Removes any duplicate prefix patterns (e.g., PREFIX_PREFIX_... → PREFIX_...)
 */
function formatFileName(fileName: string): string {
  // Remove any duplicate prefix pattern: ABC_ABC_xyz → ABC_xyz
  // Matches: word_word_ where both words are identical (case insensitive)
  const cleaned = fileName.replace(/^([A-Za-z0-9]+)_\1_/i, '$1_')

  return cleaned
}

interface ChatTabsProps {
  tabs: ChatTab[]
  activeTabId: string | null
  onTabChange: (tabId: string) => void
  onTabClose: (tabId: string) => void
  onNewChat: () => void
}

export function ChatTabs({ tabs, activeTabId, onTabChange, onTabClose, onNewChat }: ChatTabsProps) {
  return (
    <div className="flex items-center gap-2 border-b border-slate-200 bg-white px-4 py-2">
      {/* Tab List */}
      <div className="flex items-center gap-1 flex-1 overflow-x-auto">
        {tabs.map((tab) => (
          <div
            key={tab.id}
            className={`flex items-center gap-2 px-4 py-2 rounded-t-lg border border-b-0 cursor-pointer transition-colors ${
              activeTabId === tab.id
                ? "bg-white border-slate-200 text-slate-900"
                : "bg-slate-50 border-transparent text-slate-600 hover:bg-slate-100"
            }`}
            onClick={() => onTabChange(tab.id)}
          >
            <span className="text-sm font-medium truncate max-w-[200px]" title={formatFileName(tab.fileName)}>
              {formatFileName(tab.fileName)}
            </span>
            <button
              onClick={(e) => {
                e.stopPropagation()
                onTabClose(tab.id)
              }}
              className="hover:bg-slate-200 rounded p-0.5 transition-colors"
              aria-label={`Close ${tab.fileName}`}
            >
              <X className="w-3 h-3" />
            </button>
          </div>
        ))}

        {/* New Chat Tab Button */}
        <button
          onClick={onNewChat}
          className="flex items-center gap-1 px-3 py-2 rounded-t-lg text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors"
          aria-label="New chat"
        >
          <Plus className="w-4 h-4" />
          <span className="text-sm">New Chat</span>
        </button>
      </div>
    </div>
  )
}
