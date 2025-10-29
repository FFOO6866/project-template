/**
 * Lightweight Markdown Renderer
 * Handles the specific markdown patterns used in AI responses
 */

import React from 'react'

interface MarkdownRendererProps {
  content: string
  className?: string
}

export function MarkdownRenderer({ content, className = '' }: MarkdownRendererProps) {
  const renderContent = () => {
    // Split by lines for processing
    const lines = content.split('\n')
    const elements: React.ReactNode[] = []
    let key = 0

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i]

      // Horizontal rule
      if (line.trim() === '---') {
        elements.push(<hr key={key++} className="my-4 border-slate-300" />)
        continue
      }

      // Empty lines
      if (line.trim() === '') {
        elements.push(<div key={key++} className="h-2" />)
        continue
      }

      // Headers (bold lines that start with **)
      if (line.startsWith('**') && line.endsWith('**')) {
        const text = line.slice(2, -2)
        elements.push(
          <h3 key={key++} className="font-bold text-slate-900 mb-2">
            {text}
          </h3>
        )
        continue
      }

      // List items with emoji icons
      const listMatch = line.match(/^(\d+\.|\-|\*)\s*(.*)$/)
      if (listMatch) {
        const itemContent = listMatch[2]
        elements.push(
          <div key={key++} className="ml-4 mb-1">
            {renderInlineMarkdown(itemContent)}
          </div>
        )
        continue
      }

      // Regular lines with potential inline markdown
      elements.push(
        <p key={key++} className="mb-2">
          {renderInlineMarkdown(line)}
        </p>
      )
    }

    return elements
  }

  const renderInlineMarkdown = (text: string) => {
    // Handle bold text **text**
    const parts: (string | React.ReactElement)[] = []
    let remaining = text
    let partKey = 0

    while (remaining.length > 0) {
      const boldMatch = remaining.match(/\*\*([^*]+)\*\*/)

      if (boldMatch && boldMatch.index !== undefined) {
        // Add text before bold
        if (boldMatch.index > 0) {
          parts.push(remaining.slice(0, boldMatch.index))
        }

        // Add bold text
        parts.push(
          <strong key={partKey++} className="font-semibold">
            {boldMatch[1]}
          </strong>
        )

        // Continue with remaining text
        remaining = remaining.slice(boldMatch.index + boldMatch[0].length)
      } else {
        // No more bold text, add remaining
        parts.push(remaining)
        break
      }
    }

    return parts
  }

  return (
    <div className={`markdown-content ${className}`}>
      {renderContent()}
    </div>
  )
}
