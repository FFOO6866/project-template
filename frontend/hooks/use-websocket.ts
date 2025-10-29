/**
 * Production-Ready WebSocket Hook for Real-Time Chat
 * ===================================================
 *
 * Features:
 * - WebSocket connection management with auto-reconnection
 * - Message queue for offline messages
 * - Authentication integration
 * - TypeScript types for message formats
 * - Connection state management
 * - Keep-alive ping/pong
 * - Proper cleanup on unmount
 *
 * Compatible with: src/websocket/chat_server.py
 *
 * NO MOCKS - Connects to real WebSocket server
 * NO HARDCODED URLS - Uses NEXT_PUBLIC_WEBSOCKET_URL
 */

import { useEffect, useRef, useState, useCallback } from 'react'

// ============================================================================
// TypeScript Types - Compatible with Python WebSocket Server
// ============================================================================

export type ConnectionState = 'connecting' | 'connected' | 'disconnected' | 'error'

export type MessageType = 'auth' | 'chat' | 'context' | 'history' | 'ping' | 'pong' |
                          'system' | 'message' | 'typing' | 'error' |
                          'auth_success' | 'context_updated'

export interface ChatMessage {
  id: string
  session_id: string
  type: 'user' | 'ai'
  content: string
  timestamp: string
  context?: DocumentContext | null
}

export interface DocumentContext {
  type: 'document' | 'quotation' | 'product'
  name?: string
  quotation_id?: string
  customer?: string
  document_id?: string
  [key: string]: any
}

export interface WebSocketMessage {
  type: MessageType
  content?: string
  message?: ChatMessage
  context?: DocumentContext
  error?: string
  timestamp?: string
  session_id?: string
  user_id?: string
  typing?: boolean
  messages?: ChatMessage[]
  count?: number
  message_count?: number
}

export interface AuthMessage {
  type: 'auth'
  user_id: string
  session_id?: string
  context?: DocumentContext
}

export interface ChatMessagePayload {
  type: 'chat'
  content: string
}

export interface ContextUpdatePayload {
  type: 'context'
  context: DocumentContext | null
}

export interface UseWebSocketOptions {
  url?: string
  userId?: string
  sessionId?: string
  context?: DocumentContext
  autoConnect?: boolean
  reconnectInterval?: number
  maxReconnectAttempts?: number
  pingInterval?: number
  onOpen?: () => void
  onClose?: () => void
  onError?: (error: Event) => void
  onMessage?: (message: WebSocketMessage) => void
}

export interface UseWebSocketReturn {
  connectionState: ConnectionState
  isConnected: boolean
  lastMessage: WebSocketMessage | null
  messages: ChatMessage[]
  sendMessage: (content: string) => void
  sendAuthMessage: (userId: string, sessionId?: string, context?: DocumentContext) => void
  updateContext: (context: DocumentContext | null) => void
  requestHistory: () => void
  connect: () => void
  disconnect: () => void
  error: string | null
}

// ============================================================================
// WebSocket Hook Implementation
// ============================================================================

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const {
    url = process.env.NEXT_PUBLIC_WEBSOCKET_URL || 'ws://localhost:8001',
    userId = 'anonymous',
    sessionId: initialSessionId,
    context: initialContext,
    autoConnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 10,
    pingInterval = 30000,
    onOpen,
    onClose,
    onError,
    onMessage,
  } = options

  // State management
  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected')
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [error, setError] = useState<string | null>(null)
  const [sessionId, setSessionId] = useState<string | undefined>(initialSessionId)
  const [currentContext, setCurrentContext] = useState<DocumentContext | undefined>(initialContext)

  // Refs for WebSocket and reconnection logic
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const messageQueueRef = useRef<any[]>([])
  const isConnectingRef = useRef(false)
  const isMountedRef = useRef(true)

  // Derived state
  const isConnected = connectionState === 'connected'

  // ============================================================================
  // Connection Management
  // ============================================================================

  const clearReconnectTimeout = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
  }, [])

  const clearPingInterval = useCallback(() => {
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current)
      pingIntervalRef.current = null
    }
  }, [])

  const startPingInterval = useCallback(() => {
    clearPingInterval()

    pingIntervalRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        try {
          wsRef.current.send(JSON.stringify({ type: 'ping', timestamp: new Date().toISOString() }))
        } catch (err) {
          console.error('[WebSocket] Ping failed:', err)
        }
      }
    }, pingInterval)
  }, [pingInterval, clearPingInterval])

  const processMessageQueue = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN && messageQueueRef.current.length > 0) {
      console.log(`[WebSocket] Processing ${messageQueueRef.current.length} queued messages`)

      messageQueueRef.current.forEach((msg) => {
        try {
          wsRef.current?.send(JSON.stringify(msg))
        } catch (err) {
          console.error('[WebSocket] Failed to send queued message:', err)
        }
      })

      messageQueueRef.current = []
    }
  }, [])

  const sendRawMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      try {
        wsRef.current.send(JSON.stringify(message))
      } catch (err) {
        console.error('[WebSocket] Send failed:', err)
        setError('Failed to send message')
      }
    } else {
      console.log('[WebSocket] Connection not open, queueing message')
      messageQueueRef.current.push(message)
    }
  }, [])

  const handleOpen = useCallback(() => {
    if (!isMountedRef.current) return

    console.log('[WebSocket] Connection opened')
    setConnectionState('connected')
    setError(null)
    reconnectAttemptsRef.current = 0
    clearReconnectTimeout()
    startPingInterval()

    // Send authentication message
    const authMessage: AuthMessage = {
      type: 'auth',
      user_id: userId,
      session_id: sessionId,
      context: currentContext,
    }
    sendRawMessage(authMessage)

    // Process queued messages
    processMessageQueue()

    onOpen?.()
  }, [userId, sessionId, currentContext, onOpen, clearReconnectTimeout, startPingInterval, sendRawMessage, processMessageQueue])

  const handleClose = useCallback(() => {
    if (!isMountedRef.current) return

    console.log('[WebSocket] Connection closed')
    setConnectionState('disconnected')
    clearPingInterval()

    // Attempt reconnection if not manually disconnected
    if (reconnectAttemptsRef.current < maxReconnectAttempts) {
      reconnectAttemptsRef.current++
      console.log(`[WebSocket] Reconnect attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts}`)

      reconnectTimeoutRef.current = setTimeout(() => {
        if (isMountedRef.current) {
          connect()
        }
      }, reconnectInterval)
    } else {
      console.error('[WebSocket] Max reconnection attempts reached')
      setError('Connection lost. Please refresh the page.')
    }

    onClose?.()
  }, [maxReconnectAttempts, reconnectInterval, onClose, clearPingInterval])

  const handleError = useCallback((event: Event) => {
    if (!isMountedRef.current) return

    console.error('[WebSocket] Error occurred:', event)
    setConnectionState('error')
    setError('WebSocket connection error')

    onError?.(event)
  }, [onError])

  const handleMessage = useCallback((event: MessageEvent) => {
    if (!isMountedRef.current) return

    try {
      const data: WebSocketMessage = JSON.parse(event.data)
      console.log('[WebSocket] Message received:', data.type)

      setLastMessage(data)

      // Handle different message types
      switch (data.type) {
        case 'auth_success':
          if (data.session_id) {
            setSessionId(data.session_id)
          }
          console.log('[WebSocket] Authentication successful')
          break

        case 'message':
          if (data.message) {
            setMessages((prev) => [...prev, data.message!])
          }
          break

        case 'history':
          if (data.messages) {
            setMessages(data.messages)
          }
          break

        case 'error':
          console.error('[WebSocket] Server error:', data.error)
          setError(data.error || 'Unknown server error')
          break

        case 'context_updated':
          if (data.context !== undefined) {
            setCurrentContext(data.context || undefined)
          }
          break

        case 'pong':
          // Keep-alive response received
          break

        case 'system':
        case 'typing':
          // Handle system and typing messages
          break

        default:
          console.log('[WebSocket] Unhandled message type:', data.type)
      }

      onMessage?.(data)
    } catch (err) {
      console.error('[WebSocket] Failed to parse message:', err)
      setError('Failed to parse server message')
    }
  }, [onMessage])

  const connect = useCallback(() => {
    if (isConnectingRef.current || wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('[WebSocket] Already connected or connecting')
      return
    }

    if (!url) {
      console.error('[WebSocket] No WebSocket URL provided')
      setError('WebSocket URL not configured. Please set NEXT_PUBLIC_WEBSOCKET_URL')
      return
    }

    try {
      console.log('[WebSocket] Connecting to:', url)
      isConnectingRef.current = true
      setConnectionState('connecting')
      setError(null)

      const ws = new WebSocket(url)

      ws.onopen = () => {
        isConnectingRef.current = false
        handleOpen()
      }

      ws.onclose = () => {
        isConnectingRef.current = false
        handleClose()
      }

      ws.onerror = (event) => {
        isConnectingRef.current = false
        handleError(event)
      }

      ws.onmessage = handleMessage

      wsRef.current = ws
    } catch (err) {
      isConnectingRef.current = false
      console.error('[WebSocket] Connection failed:', err)
      setConnectionState('error')
      setError('Failed to establish WebSocket connection')
    }
  }, [url, handleOpen, handleClose, handleError, handleMessage])

  const disconnect = useCallback(() => {
    console.log('[WebSocket] Disconnecting')
    clearReconnectTimeout()
    clearPingInterval()
    reconnectAttemptsRef.current = maxReconnectAttempts // Prevent auto-reconnect

    if (wsRef.current) {
      wsRef.current.onopen = null
      wsRef.current.onclose = null
      wsRef.current.onerror = null
      wsRef.current.onmessage = null

      if (wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close()
      }

      wsRef.current = null
    }

    setConnectionState('disconnected')
  }, [clearReconnectTimeout, clearPingInterval, maxReconnectAttempts])

  // ============================================================================
  // Message Sending Functions
  // ============================================================================

  const sendMessage = useCallback((content: string) => {
    if (!content.trim()) {
      console.warn('[WebSocket] Attempted to send empty message')
      return
    }

    const message: ChatMessagePayload = {
      type: 'chat',
      content: content.trim(),
    }

    sendRawMessage(message)
  }, [sendRawMessage])

  const sendAuthMessage = useCallback((userId: string, sessionId?: string, context?: DocumentContext) => {
    const message: AuthMessage = {
      type: 'auth',
      user_id: userId,
      session_id: sessionId,
      context: context,
    }

    sendRawMessage(message)
  }, [sendRawMessage])

  const updateContext = useCallback((context: DocumentContext | null) => {
    setCurrentContext(context || undefined)

    const message: ContextUpdatePayload = {
      type: 'context',
      context: context,
    }

    sendRawMessage(message)
  }, [sendRawMessage])

  const requestHistory = useCallback(() => {
    sendRawMessage({ type: 'history' })
  }, [sendRawMessage])

  // ============================================================================
  // Lifecycle Management
  // ============================================================================

  useEffect(() => {
    isMountedRef.current = true

    if (autoConnect) {
      connect()
    }

    return () => {
      isMountedRef.current = false
      disconnect()
    }
  }, []) // Only run on mount/unmount

  // ============================================================================
  // Return Hook Interface
  // ============================================================================

  return {
    connectionState,
    isConnected,
    lastMessage,
    messages,
    sendMessage,
    sendAuthMessage,
    updateContext,
    requestHistory,
    connect,
    disconnect,
    error,
  }
}
