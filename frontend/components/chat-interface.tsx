"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { MessageSquare, Send, Bot, User, Sparkles } from "lucide-react"
import { MarkdownRenderer } from "./markdown-renderer"

interface Message {
  id: string
  type: "user" | "assistant"
  content: string
  timestamp: Date
}

interface ChatInterfaceProps {
  documentId?: string
  documentName?: string
  emailRequestId?: number
  isCompact?: boolean
}

export function ChatInterface({ documentId, documentName, emailRequestId, isCompact = false }: ChatInterfaceProps) {
  // Consistent time formatting to prevent hydration errors
  const formatTime = (date: Date) => {
    const hours = date.getHours().toString().padStart(2, '0')
    const minutes = date.getMinutes().toString().padStart(2, '0')
    return `${hours}:${minutes}`
  }

  // Determine initial message based on context
  const getInitialMessage = () => {
    if (emailRequestId) {
      return `I'm looking at the email request for "${documentName}" now. Give me a moment to pull together what you need.`
    }
    if (documentId) {
      return `Got it. I'm going through "${documentName}" now to find what you're looking for. Shouldn't take long.`
    }
    return "Hey! I can help you search our catalog, analyze quotes, or answer product questions. What do you need?"
  }

  // Use a static timestamp for the initial message to prevent hydration errors
  const [messages, setMessages] = useState<Message[]>(() => {
    // Create initial message with a fixed timestamp
    const now = new Date()
    now.setSeconds(0) // Round to the nearest minute for consistency
    now.setMilliseconds(0)

    return [{
      id: "1",
      type: "assistant",
      content: getInitialMessage(),
      timestamp: now,
    }]
  })
  const [inputValue, setInputValue] = useState("")
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const hasShownCompletionRef = useRef(false)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Poll document status when a document is uploaded
  useEffect(() => {
    if (!documentId) return

    // Reset completion flag when document changes
    hasShownCompletionRef.current = false

    const checkDocumentStatus = async () => {
      try {
        const response = await fetch(`http://localhost:8002/api/documents/${documentId}`)
        const doc = await response.json()

        console.log('[ChatInterface] Document status:', doc.ai_status, doc)

        if (doc.ai_status === 'completed') {
          // Only add message once
          if (!hasShownCompletionRef.current) {
            hasShownCompletionRef.current = true

            const extractedData = doc.ai_extracted_data
            console.log('[ChatInterface] Extracted data:', extractedData)

            // Check if we have items
            if (extractedData && extractedData.requirements && extractedData.requirements.items && extractedData.requirements.items.length > 0) {
              // TRIGGER PROACTIVE ANALYSIS
              // Instead of showing hardcoded message, call backend AI to analyze and create quotation
              console.log('[ChatInterface] Triggering proactive RFP analysis...')

              setIsTyping(true)

              // Call backend chat API to trigger proactive analysis
              try {
                const response = await fetch('http://localhost:8002/api/chat', {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json',
                  },
                  body: JSON.stringify({
                    message: 'Please analyze this RFP and generate a quotation',  // Triggers proactive mode
                    document_id: parseInt(documentId),
                    context: {
                      history: []  // Empty history = first message = proactive mode
                    }
                  })
                })

                if (!response.ok) {
                  throw new Error(`API error: ${response.statusText}`)
                }

                const data = await response.json()
                console.log('[ChatInterface] Proactive analysis response:', data)

                // Add AI proactive analysis to chat
                const proactiveMessage: Message = {
                  id: `proactive-${Date.now()}`,
                  type: "assistant",
                  content: data.response,
                  timestamp: new Date()
                }

                setMessages(prev => [...prev, proactiveMessage])
                setIsTyping(false)

              } catch (error) {
                console.error('[ChatInterface] Proactive analysis failed:', error)

                // Fallback to simple message if backend fails
                const fallbackMessage: Message = {
                  id: `fallback-${Date.now()}`,
                  type: "assistant",
                  content: `I've analyzed "${documentName}" and found ${extractedData.requirements.items.length} items. Let me know how I can help with this RFP!`,
                  timestamp: new Date()
                }
                setMessages(prev => [...prev, fallbackMessage])
                setIsTyping(false)
              }

            } else {
              // No items extracted - show error message
              const errorMessage: Message = {
                id: `no-items-${Date.now()}`,
                type: "assistant",
                content: `Couldn't pull anything specific from "${documentName}". The format might be unusual or it's mostly text without clear product lists.\n\nTell me what you're looking for and I'll search the catalog for you.`,
                timestamp: new Date()
              }
              setMessages(prev => [...prev, errorMessage])
              setIsTyping(false)
            }
          }
        } else if (doc.ai_status === 'processing') {
          // Show processing status
          setIsTyping(true)
        } else if (doc.ai_status === 'error') {
          // Only show error once
          if (!hasShownCompletionRef.current) {
            hasShownCompletionRef.current = true

            const errorMessage: Message = {
              id: `error-${Date.now()}`,
              type: "assistant",
              content: `Hit a snag with "${documentName}". Just tell me what you need and I'll search for it directly.`,
              timestamp: new Date()
            }

            setMessages(prev => [...prev, errorMessage])
            setIsTyping(false)
          }
        }
      } catch (error) {
        console.error('[ChatInterface] Error checking document status:', error)
      }
    }

    // Start polling every 3 seconds
    const interval = setInterval(checkDocumentStatus, 3000)

    // Initial check
    checkDocumentStatus()

    // Cleanup on unmount
    return () => {
      clearInterval(interval)
    }
  }, [documentId, documentName])

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: "user",
      content: inputValue,
      timestamp: new Date(),
    }

    const messageText = inputValue
    setMessages((prev) => [...prev, userMessage])
    setInputValue("")
    setIsTyping(true)

    try {
      // Convert messages to OpenAI conversation format for context
      // Filter out the initial greeting and only include real conversations
      const conversationHistory = messages
        .filter(msg => msg.id !== "1") // Exclude initial greeting
        .map(msg => ({
          role: msg.type === "user" ? "user" : "assistant",
          content: msg.content
        }))

      console.log('[ChatInterface] Sending conversation history:', conversationHistory.length, 'messages')

      // REAL AI CALL - NO MOCK DATA
      // Call backend API with real OpenAI integration + conversation context
      const response = await fetch('http://localhost:8002/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: messageText,
          document_id: documentId ? parseInt(documentId) : null,
          context: {
            history: conversationHistory
          }
        })
      })

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`)
      }

      const data = await response.json()

      // Add real AI response from backend
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        type: "assistant",
        content: data.response, // Real AI response from OpenAI + product database
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, aiResponse])
      setIsTyping(false)
    } catch (error) {
      console.error('[ChatInterface] Error calling chat API:', error)

      // Show error message to user
      const errorResponse: Message = {
        id: (Date.now() + 1).toString(),
        type: "assistant",
        content: "I apologize, but I'm having trouble connecting to the product database right now. Please try again in a moment.",
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, errorResponse])
      setIsTyping(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const quickActions = documentId
    ? [
        "Show all extracted items",
        "Find alternative products",
        "Adjust pricing and quantities",
        "Generate quotation PDF",
      ]
    : ["Upload RFP document", "Search product catalog", "Show recent quotations", "How can you help?"]

  return (
    <Card className={`border-slate-200 ${isCompact ? "h-full" : "hover:shadow-md transition-shadow"}`}>
      <CardHeader className={`${isCompact ? "pb-2 px-4 py-3" : "pb-4"}`}>
        <CardTitle className={`flex items-center text-slate-900 ${isCompact ? "text-base" : ""}`}>
          <MessageSquare className={`${isCompact ? "w-4 h-4" : "w-5 h-5"} mr-2 text-amber-600`} />
          AI Assistant
          {documentId && <Badge className="ml-2 bg-emerald-100 text-emerald-800 text-xs">Document Active</Badge>}
        </CardTitle>
      </CardHeader>
      <CardContent className={`${isCompact ? "px-4 pb-3" : ""}`}>
        <div className={`flex flex-col ${isCompact ? "h-48" : "h-[calc(100vh-20rem)] min-h-96 max-h-[800px]"}`}>
          {/* Messages */}
          <div className="flex-1 overflow-y-auto space-y-4 mb-4">
            {messages.map((message) => (
              <div key={message.id} className={`flex ${message.type === "user" ? "justify-end" : "justify-start"}`}>
                <div
                  className={`flex items-start space-x-2 max-w-[80%] ${
                    message.type === "user" ? "flex-row-reverse space-x-reverse" : ""
                  }`}
                >
                  <div
                    className={`${isCompact ? "w-6 h-6" : "w-8 h-8"} rounded-full flex items-center justify-center flex-shrink-0 ${
                      message.type === "user" ? "bg-amber-600 text-white" : "bg-slate-100 text-slate-600"
                    }`}
                  >
                    {message.type === "user" ? (
                      <User className={`${isCompact ? "w-3 h-3" : "w-4 h-4"}`} />
                    ) : (
                      <Bot className={`${isCompact ? "w-3 h-3" : "w-4 h-4"}`} />
                    )}
                  </div>
                  <div
                    className={`rounded-lg px-3 py-2 ${isCompact ? "text-sm" : ""} ${
                      message.type === "user" ? "bg-amber-600 text-white" : "bg-slate-100 text-slate-900"
                    }`}
                  >
                    {message.type === "assistant" ? (
                      <MarkdownRenderer content={message.content} className="text-slate-900" />
                    ) : (
                      <p className="text-white">{message.content}</p>
                    )}
                    <p className={`text-xs mt-1 ${message.type === "user" ? "text-amber-100" : "text-slate-500"}`}>
                      {formatTime(message.timestamp)}
                    </p>
                  </div>
                </div>
              </div>
            ))}

            {isTyping && (
              <div className="flex justify-start">
                <div className="flex items-start space-x-2">
                  <div
                    className={`${isCompact ? "w-6 h-6" : "w-8 h-8"} rounded-full bg-slate-100 text-slate-600 flex items-center justify-center`}
                  >
                    <Bot className={`${isCompact ? "w-3 h-3" : "w-4 h-4"}`} />
                  </div>
                  <div className="bg-slate-100 rounded-lg px-3 py-2">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"></div>
                      <div
                        className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"
                        style={{ animationDelay: "0.1s" }}
                      ></div>
                      <div
                        className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"
                        style={{ animationDelay: "0.2s" }}
                      ></div>
                    </div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Actions */}
          {!isCompact && (
            <div className="mb-4">
              <div className="flex flex-wrap gap-2">
                {quickActions.map((action, index) => (
                  <Button
                    key={index}
                    variant="outline"
                    size="sm"
                    className="text-xs border-slate-300 text-slate-600 hover:bg-slate-100 bg-transparent"
                    onClick={() => setInputValue(action)}
                  >
                    <Sparkles className="w-3 h-3 mr-1" />
                    {action}
                  </Button>
                ))}
              </div>
            </div>
          )}

          {/* Input */}
          <div className="flex space-x-2">
            <Input
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={documentId ? "Ask about this quotation..." : "Ask me anything..."}
              className={`flex-1 border-slate-300 focus:border-amber-400 focus:ring-amber-400/20 ${isCompact ? "text-sm h-8" : ""}`}
            />
            <Button
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || isTyping}
              className={`bg-gradient-to-r from-amber-600 to-red-600 hover:from-amber-700 hover:to-red-700 ${isCompact ? "h-8 w-8 p-0" : ""}`}
            >
              <Send className={`${isCompact ? "w-3 h-3" : "w-4 h-4"}`} />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
