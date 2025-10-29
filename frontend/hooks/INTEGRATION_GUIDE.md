# WebSocket Hook Integration Guide

## Quick Start

This guide shows how to integrate the `useWebSocket` hook into the existing chat components.

## Step 1: Environment Configuration

Add to `frontend/.env.local`:

```bash
# Development
NEXT_PUBLIC_WEBSOCKET_URL=ws://localhost:8001

# Production (when deploying)
# NEXT_PUBLIC_WEBSOCKET_URL=wss://your-domain.com/ws
```

## Step 2: Start WebSocket Server

Using Docker Compose:

```bash
# Start WebSocket server
docker-compose up horme-websocket

# Or start all services
docker-compose up
```

Manual start (for development):

```bash
cd src/websocket
python chat_server.py
```

## Step 3: Update Chat Components

### Option A: Update `chat-interface.tsx`

Replace simulated chat with real WebSocket:

```tsx
"use client"

import { useEffect, useRef } from "react"
import { useWebSocket } from "@/hooks/use-websocket"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { MessageSquare, Send, Bot, User, Sparkles, AlertCircle } from "lucide-react"

interface ChatInterfaceProps {
  documentId?: string
  documentName?: string
  isCompact?: boolean
}

export function ChatInterface({ documentId, documentName, isCompact = false }: ChatInterfaceProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Real WebSocket connection
  const {
    isConnected,
    connectionState,
    messages,
    sendMessage,
    lastMessage,
    error,
  } = useWebSocket({
    userId: 'user123', // TODO: Replace with actual user ID from auth
    context: documentId ? {
      type: 'document',
      document_id: documentId,
      name: documentName || 'Document'
    } : undefined,
    autoConnect: true,
  })

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  // Check for typing indicator
  const isTyping = lastMessage?.type === 'typing' && lastMessage.typing === true

  const handleSendMessage = (content: string) => {
    if (content.trim() && isConnected) {
      sendMessage(content)
    }
  }

  const quickActions = documentId
    ? [
        "Explain the pricing breakdown",
        "What are the delivery terms?",
        "Can we adjust quantities?",
        "Show alternative products",
      ]
    : ["How do I upload a document?", "What file types are supported?", "Show me recent quotes", "Help with pricing"]

  return (
    <Card className={`border-slate-200 ${isCompact ? "h-full" : "hover:shadow-md transition-shadow"}`}>
      <CardHeader className={`${isCompact ? "pb-2 px-4 py-3" : "pb-4"}`}>
        <CardTitle className={`flex items-center text-slate-900 ${isCompact ? "text-base" : ""}`}>
          <MessageSquare className={`${isCompact ? "w-4 h-4" : "w-5 h-5"} mr-2 text-amber-600`} />
          AI Assistant
          {documentId && <Badge className="ml-2 bg-emerald-100 text-emerald-800 text-xs">Document Active</Badge>}

          {/* Connection Status Badge */}
          {connectionState === 'connected' && (
            <Badge className="ml-2 bg-green-100 text-green-800 text-xs">●Connected</Badge>
          )}
          {connectionState === 'connecting' && (
            <Badge className="ml-2 bg-yellow-100 text-yellow-800 text-xs">●Connecting...</Badge>
          )}
          {connectionState === 'disconnected' && (
            <Badge className="ml-2 bg-red-100 text-red-800 text-xs">●Disconnected</Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className={`${isCompact ? "px-4 pb-3" : ""}`}>
        {/* Error Display */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start space-x-2">
            <AlertCircle className="w-4 h-4 text-red-600 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm text-red-800">{error}</p>
              <button
                onClick={() => window.location.reload()}
                className="text-xs text-red-600 underline mt-1"
              >
                Reload page
              </button>
            </div>
          </div>
        )}

        <div className={`flex flex-col ${isCompact ? "h-48" : "h-96"}`}>
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
                    <p>{message.content}</p>
                    <p className={`text-xs mt-1 ${message.type === "user" ? "text-amber-100" : "text-slate-500"}`}>
                      {new Date(message.timestamp).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </p>
                  </div>
                </div>
              </div>
            ))}

            {/* Typing Indicator */}
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
                    onClick={() => handleSendMessage(action)}
                    disabled={!isConnected}
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
              id="chat-input"
              placeholder={
                !isConnected
                  ? "Connecting to chat server..."
                  : documentId
                  ? "Ask about this quotation..."
                  : "Ask me anything..."
              }
              className={`flex-1 border-slate-300 focus:border-amber-400 focus:ring-amber-400/20 ${isCompact ? "text-sm h-8" : ""}`}
              disabled={!isConnected}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  const input = e.currentTarget
                  handleSendMessage(input.value)
                  input.value = ''
                }
              }}
            />
            <Button
              onClick={(e) => {
                const input = document.getElementById('chat-input') as HTMLInputElement
                if (input?.value.trim()) {
                  handleSendMessage(input.value)
                  input.value = ''
                }
              }}
              disabled={!isConnected}
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
```

### Option B: Create New Component

Create `frontend/components/websocket-chat.tsx`:

```tsx
"use client"

import { useEffect, useRef, useState } from "react"
import { useWebSocket, type DocumentContext } from "@/hooks/use-websocket"

interface WebSocketChatProps {
  userId: string
  documentId?: string
  documentName?: string
  context?: DocumentContext
}

export function WebSocketChat({ userId, documentId, documentName, context }: WebSocketChatProps) {
  const [input, setInput] = useState("")
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const {
    isConnected,
    connectionState,
    messages,
    sendMessage,
    lastMessage,
    error,
  } = useWebSocket({
    userId,
    context: context || (documentId ? {
      type: 'document',
      document_id: documentId,
      name: documentName || 'Document'
    } : undefined),
    autoConnect: true,
  })

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const isTyping = lastMessage?.type === 'typing' && lastMessage.typing === true

  const handleSend = () => {
    if (input.trim() && isConnected) {
      sendMessage(input)
      setInput("")
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Connection Status */}
      <div className="p-2 bg-slate-100 border-b">
        <div className="flex items-center justify-between">
          <span className="text-sm">
            Status: <strong className={
              connectionState === 'connected' ? 'text-green-600' :
              connectionState === 'connecting' ? 'text-yellow-600' :
              'text-red-600'
            }>{connectionState}</strong>
          </span>
          {documentName && (
            <span className="text-sm text-slate-600">
              Document: <strong>{documentName}</strong>
            </span>
          )}
        </div>
        {error && (
          <div className="mt-2 text-sm text-red-600">{error}</div>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[70%] rounded-lg px-4 py-2 ${
              msg.type === 'user'
                ? 'bg-blue-600 text-white'
                : 'bg-slate-200 text-slate-900'
            }`}>
              <p>{msg.content}</p>
              <p className="text-xs mt-1 opacity-70">
                {new Date(msg.timestamp).toLocaleTimeString()}
              </p>
            </div>
          </div>
        ))}

        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-slate-200 rounded-lg px-4 py-2">
              <div className="flex space-x-1">
                <span className="animate-bounce">●</span>
                <span className="animate-bounce" style={{ animationDelay: '0.1s' }}>●</span>
                <span className="animate-bounce" style={{ animationDelay: '0.2s' }}>●</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t">
        <div className="flex space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder={isConnected ? "Type a message..." : "Connecting..."}
            disabled={!isConnected}
            className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={handleSend}
            disabled={!isConnected || !input.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  )
}
```

## Step 4: Test the Integration

### 1. Start Services

```bash
# Terminal 1: Start WebSocket server
docker-compose up horme-websocket

# Terminal 2: Start frontend
cd frontend
npm run dev
```

### 2. Open Browser

Navigate to `http://localhost:3000` and open the chat interface.

### 3. Verify Connection

- Check connection status badge shows "Connected"
- Send a test message
- Verify AI response is received
- Check for typing indicator

### 4. Test Features

**Basic Chat:**
- Send message → Receive AI response
- Check message timestamps
- Verify message order

**Disconnect/Reconnect:**
- Stop WebSocket server
- Verify status shows "Disconnected"
- Send message (should be queued)
- Start WebSocket server
- Verify auto-reconnect
- Verify queued message is sent

**Context Switching:**
- Load a document
- Verify context is sent to server
- Ask document-specific question
- Verify AI provides context-aware response

## Step 5: Production Deployment

### Frontend Configuration

Update `.env.production`:

```bash
NEXT_PUBLIC_WEBSOCKET_URL=wss://your-domain.com/ws
```

### WebSocket Server Configuration

Ensure WebSocket server is accessible via reverse proxy (nginx):

```nginx
# nginx configuration
location /ws {
    proxy_pass http://horme-websocket:8001;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

### SSL/TLS Setup

Ensure SSL certificates are configured for secure WebSocket (wss://).

## Troubleshooting

### Connection Failed

**Problem:** Status shows "error" or "disconnected"

**Solutions:**
1. Check WebSocket server is running:
   ```bash
   docker-compose ps horme-websocket
   ```
2. Check `NEXT_PUBLIC_WEBSOCKET_URL` is set correctly
3. Check browser console for errors
4. Verify network connectivity

### Messages Not Sending

**Problem:** Messages disappear but no response

**Solutions:**
1. Check `isConnected` is `true`
2. Check browser console for errors
3. Check WebSocket server logs:
   ```bash
   docker-compose logs horme-websocket
   ```
4. Verify authentication is successful

### Typing Indicator Not Working

**Problem:** No typing indicator shown

**Solutions:**
1. Check server sends `typing` messages
2. Verify `lastMessage` is updating
3. Check typing indicator condition:
   ```tsx
   const isTyping = lastMessage?.type === 'typing' && lastMessage.typing === true
   ```

### Context Not Working

**Problem:** AI responses are not context-aware

**Solutions:**
1. Verify context is passed to hook
2. Check server logs for context updates
3. Ensure context format matches server expectations
4. Test context update function:
   ```tsx
   updateContext({
     type: 'document',
     document_id: 'test_123',
     name: 'Test Document'
   })
   ```

## Advanced Integration

### With Authentication

```tsx
import { useAuth } from '@/hooks/use-auth'
import { useWebSocket } from '@/hooks/use-websocket'

function AuthenticatedChat() {
  const { user } = useAuth()

  const { isConnected, messages, sendMessage } = useWebSocket({
    userId: user?.id || 'anonymous',
    sessionId: user?.sessionId,
    autoConnect: !!user,
  })

  // ... rest of component
}
```

### With Context Management

```tsx
import { useWebSocket } from '@/hooks/use-websocket'

function ContextAwareChat({ documents, quotations, products }) {
  const [currentContext, setCurrentContext] = useState(null)

  const { updateContext, messages, sendMessage } = useWebSocket({
    userId: 'user123',
    context: currentContext,
  })

  const switchToDocument = (doc) => {
    const newContext = {
      type: 'document',
      document_id: doc.id,
      name: doc.name
    }
    setCurrentContext(newContext)
    updateContext(newContext)
  }

  // ... rest of component
}
```

### With Message History

```tsx
import { useEffect } from 'react'
import { useWebSocket } from '@/hooks/use-websocket'

function ChatWithHistory({ sessionId }) {
  const {
    isConnected,
    messages,
    sendMessage,
    requestHistory
  } = useWebSocket({
    userId: 'user123',
    sessionId,
    autoConnect: true,
  })

  useEffect(() => {
    if (isConnected) {
      requestHistory()
    }
  }, [isConnected, requestHistory])

  // ... rest of component
}
```

## Summary

1. ✅ Set `NEXT_PUBLIC_WEBSOCKET_URL` in `.env.local`
2. ✅ Start WebSocket server with Docker Compose
3. ✅ Import and use `useWebSocket` hook
4. ✅ Replace simulated chat with real WebSocket
5. ✅ Add connection state indicators
6. ✅ Add error handling UI
7. ✅ Test all features (send, receive, reconnect, context)
8. ✅ Deploy to production with SSL/TLS

**The WebSocket hook is now integrated and ready for real-time chat!**
