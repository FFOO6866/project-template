/**
 * Example Usage: useWebSocket Hook
 * ==================================
 *
 * This file demonstrates how to use the production-ready WebSocket hook
 * for real-time chat functionality in React components.
 *
 * IMPORTANT: Ensure NEXT_PUBLIC_WEBSOCKET_URL is set in your .env.local file
 */

"use client"

import { useEffect } from 'react'
import { useWebSocket, type DocumentContext } from './use-websocket'

// ============================================================================
// Example 1: Basic Chat Component
// ============================================================================

export function BasicChatExample() {
  const {
    connectionState,
    isConnected,
    messages,
    sendMessage,
    error,
  } = useWebSocket({
    userId: 'user123',
    autoConnect: true,
  })

  return (
    <div className="chat-container">
      {/* Connection Status */}
      <div className="status-bar">
        Status: {connectionState}
        {error && <span className="error">{error}</span>}
      </div>

      {/* Messages Display */}
      <div className="messages">
        {messages.map((msg) => (
          <div key={msg.id} className={`message ${msg.type}`}>
            <strong>{msg.type === 'user' ? 'You' : 'AI'}:</strong>
            <p>{msg.content}</p>
            <small>{new Date(msg.timestamp).toLocaleString()}</small>
          </div>
        ))}
      </div>

      {/* Message Input */}
      <div className="input-area">
        <input
          type="text"
          placeholder="Type a message..."
          disabled={!isConnected}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && e.currentTarget.value.trim()) {
              sendMessage(e.currentTarget.value)
              e.currentTarget.value = ''
            }
          }}
        />
      </div>
    </div>
  )
}

// ============================================================================
// Example 2: Chat with Document Context
// ============================================================================

export function DocumentChatExample({ documentId, documentName }: {
  documentId: string
  documentName: string
}) {
  const context: DocumentContext = {
    type: 'document',
    document_id: documentId,
    name: documentName,
  }

  const {
    isConnected,
    messages,
    sendMessage,
    updateContext,
    lastMessage,
  } = useWebSocket({
    userId: 'user123',
    context,
    autoConnect: true,
  })

  // Handle context-aware greeting
  useEffect(() => {
    if (lastMessage?.type === 'auth_success') {
      console.log('Authenticated! AI will provide context-aware responses.')
    }
  }, [lastMessage])

  const handleContextChange = (newDocId: string, newDocName: string) => {
    updateContext({
      type: 'document',
      document_id: newDocId,
      name: newDocName,
    })
  }

  return (
    <div className="document-chat">
      <h3>Chat about: {documentName}</h3>

      {/* Connection indicator */}
      {!isConnected && <div className="warning">Connecting...</div>}

      {/* Messages */}
      <div className="messages">
        {messages.map((msg) => (
          <div key={msg.id} className={msg.type}>
            {msg.content}
          </div>
        ))}
      </div>

      {/* Input */}
      <input
        type="text"
        placeholder={`Ask about ${documentName}...`}
        disabled={!isConnected}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && e.currentTarget.value.trim()) {
            sendMessage(e.currentTarget.value)
            e.currentTarget.value = ''
          }
        }}
      />
    </div>
  )
}

// ============================================================================
// Example 3: Quotation Chat with Context Updates
// ============================================================================

export function QuotationChatExample({ quotationId, customerName }: {
  quotationId: string
  customerName: string
}) {
  const {
    isConnected,
    messages,
    sendMessage,
    updateContext,
    connectionState,
  } = useWebSocket({
    userId: 'sales_rep_456',
    sessionId: `quotation_${quotationId}`,
    context: {
      type: 'quotation',
      quotation_id: quotationId,
      customer: customerName,
    },
    autoConnect: true,
    reconnectInterval: 5000,
    maxReconnectAttempts: 5,
  })

  const handleSwitchToProduct = (productName: string) => {
    updateContext({
      type: 'product',
      name: productName,
    })
  }

  return (
    <div className="quotation-chat">
      <div className="header">
        <h3>Quotation for {customerName}</h3>
        <span className={`status ${connectionState}`}>
          {connectionState}
        </span>
      </div>

      <div className="messages">
        {messages.map((msg) => (
          <div key={msg.id} className={`msg-${msg.type}`}>
            <div className="content">{msg.content}</div>
            <div className="timestamp">
              {new Date(msg.timestamp).toLocaleTimeString()}
            </div>
          </div>
        ))}
      </div>

      <div className="input-container">
        <input
          type="text"
          placeholder="Ask about pricing, products, delivery..."
          disabled={!isConnected}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && e.currentTarget.value.trim()) {
              sendMessage(e.currentTarget.value)
              e.currentTarget.value = ''
            }
          }}
        />
      </div>

      {/* Quick actions */}
      <div className="quick-actions">
        <button onClick={() => sendMessage('What is the total price?')}>
          Get Total Price
        </button>
        <button onClick={() => sendMessage('What are the delivery terms?')}>
          Delivery Terms
        </button>
        <button onClick={() => handleSwitchToProduct('Product XYZ')}>
          Switch to Product View
        </button>
      </div>
    </div>
  )
}

// ============================================================================
// Example 4: Advanced Usage with Custom Handlers
// ============================================================================

export function AdvancedChatExample() {
  const {
    connectionState,
    isConnected,
    messages,
    lastMessage,
    sendMessage,
    requestHistory,
    disconnect,
    error,
  } = useWebSocket({
    userId: 'advanced_user',
    autoConnect: true,
    reconnectInterval: 3000,
    maxReconnectAttempts: 10,
    pingInterval: 30000,
    onOpen: () => {
      console.log('WebSocket connected! Requesting message history...')
    },
    onClose: () => {
      console.log('WebSocket disconnected. Will attempt to reconnect...')
    },
    onError: (event) => {
      console.error('WebSocket error:', event)
    },
    onMessage: (message) => {
      console.log('Received message:', message.type)

      // Handle specific message types
      if (message.type === 'typing') {
        // Show typing indicator
        console.log('AI is typing...')
      }

      if (message.type === 'error') {
        // Handle server errors
        console.error('Server error:', message.error)
      }
    },
  })

  useEffect(() => {
    if (isConnected) {
      // Request message history when connected
      requestHistory()
    }
  }, [isConnected, requestHistory])

  // Handle typing indicator
  const isTyping = lastMessage?.type === 'typing' && lastMessage.typing === true

  return (
    <div className="advanced-chat">
      <div className="header">
        <h3>Advanced Chat</h3>
        <div className="controls">
          <span className={`status-${connectionState}`}>
            {connectionState}
          </span>
          <button onClick={disconnect} disabled={connectionState === 'disconnected'}>
            Disconnect
          </button>
          <button onClick={requestHistory} disabled={!isConnected}>
            Load History
          </button>
        </div>
      </div>

      {error && (
        <div className="error-banner">
          Error: {error}
        </div>
      )}

      <div className="messages-container">
        {messages.map((msg) => (
          <div key={msg.id} className={`message-${msg.type}`}>
            <div className="avatar">
              {msg.type === 'user' ? '👤' : '🤖'}
            </div>
            <div className="content">
              <strong>{msg.type === 'user' ? 'You' : 'AI Assistant'}</strong>
              <p>{msg.content}</p>
              <time>{new Date(msg.timestamp).toLocaleString()}</time>
            </div>
          </div>
        ))}

        {isTyping && (
          <div className="typing-indicator">
            <div className="avatar">🤖</div>
            <div className="dots">
              <span>●</span>
              <span>●</span>
              <span>●</span>
            </div>
          </div>
        )}
      </div>

      <div className="input-area">
        <input
          type="text"
          placeholder={
            isConnected
              ? 'Type your message...'
              : 'Connecting to chat server...'
          }
          disabled={!isConnected}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && e.currentTarget.value.trim()) {
              sendMessage(e.currentTarget.value)
              e.currentTarget.value = ''
            }
          }}
        />
      </div>
    </div>
  )
}

// ============================================================================
// Example 5: Session Persistence with localStorage
// ============================================================================

export function PersistentChatExample() {
  const sessionId = typeof window !== 'undefined'
    ? localStorage.getItem('chat_session_id') || undefined
    : undefined

  const {
    isConnected,
    messages,
    sendMessage,
    lastMessage,
  } = useWebSocket({
    userId: 'persistent_user',
    sessionId,
    autoConnect: true,
  })

  // Save session ID when authenticated
  useEffect(() => {
    if (lastMessage?.type === 'auth_success' && lastMessage.session_id) {
      localStorage.setItem('chat_session_id', lastMessage.session_id)
    }
  }, [lastMessage])

  return (
    <div className="persistent-chat">
      <div className="info">
        Session ID: {sessionId || 'New session will be created'}
      </div>

      <div className="messages">
        {messages.map((msg) => (
          <div key={msg.id}>{msg.content}</div>
        ))}
      </div>

      <input
        type="text"
        disabled={!isConnected}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && e.currentTarget.value.trim()) {
            sendMessage(e.currentTarget.value)
            e.currentTarget.value = ''
          }
        }}
      />
    </div>
  )
}
