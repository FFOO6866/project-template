# useWebSocket Hook - Production-Ready Real-Time Chat

## Overview

The `useWebSocket` hook provides a production-ready WebSocket connection for real-time chat functionality with the Horme POV backend. It includes automatic reconnection, message queuing, authentication, and context-aware chat capabilities.

## Features

✅ **Auto-Reconnection** - Automatically reconnects on disconnect with configurable attempts
✅ **Message Queue** - Queues messages while offline and sends when reconnected
✅ **Authentication** - Integrated authentication with session management
✅ **Context-Aware** - Supports document, quotation, and product contexts
✅ **Keep-Alive** - Automatic ping/pong to maintain connection
✅ **TypeScript** - Full TypeScript types for all message formats
✅ **Connection State** - Real-time connection state tracking
✅ **Proper Cleanup** - Automatic cleanup on component unmount
❌ **NO MOCKS** - Connects to real WebSocket server
❌ **NO HARDCODED URLS** - Uses environment variables

## Installation

The hook is included in the project. No additional installation required.

## Environment Configuration

Add to your `.env.local` (for development):

```bash
# Development (local WebSocket server)
NEXT_PUBLIC_WEBSOCKET_URL=ws://localhost:8001
```

For production:

```bash
# Production (secure WebSocket)
NEXT_PUBLIC_WEBSOCKET_URL=wss://your-domain.com/ws
```

## Basic Usage

```tsx
import { useWebSocket } from '@/hooks/use-websocket'

function ChatComponent() {
  const {
    isConnected,
    messages,
    sendMessage,
    connectionState,
    error,
  } = useWebSocket({
    userId: 'user123',
    autoConnect: true,
  })

  return (
    <div>
      <div>Status: {connectionState}</div>
      {error && <div>Error: {error}</div>}

      <div>
        {messages.map((msg) => (
          <div key={msg.id}>{msg.content}</div>
        ))}
      </div>

      <input
        type="text"
        disabled={!isConnected}
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            sendMessage(e.currentTarget.value)
            e.currentTarget.value = ''
          }
        }}
      />
    </div>
  )
}
```

## API Reference

### Hook Options

```typescript
interface UseWebSocketOptions {
  url?: string                    // WebSocket URL (default: NEXT_PUBLIC_WEBSOCKET_URL)
  userId?: string                 // User ID for authentication
  sessionId?: string             // Session ID for resuming sessions
  context?: DocumentContext      // Initial document/quotation context
  autoConnect?: boolean          // Auto-connect on mount (default: true)
  reconnectInterval?: number     // Reconnect interval in ms (default: 3000)
  maxReconnectAttempts?: number  // Max reconnect attempts (default: 10)
  pingInterval?: number          // Keep-alive ping interval (default: 30000)
  onOpen?: () => void           // Callback when connection opens
  onClose?: () => void          // Callback when connection closes
  onError?: (error: Event) => void  // Callback on error
  onMessage?: (message: WebSocketMessage) => void  // Callback on message
}
```

### Hook Return Values

```typescript
interface UseWebSocketReturn {
  connectionState: ConnectionState    // Current connection state
  isConnected: boolean               // True if connected
  lastMessage: WebSocketMessage | null  // Last received message
  messages: ChatMessage[]            // All chat messages
  sendMessage: (content: string) => void  // Send chat message
  sendAuthMessage: (userId: string, sessionId?: string, context?: DocumentContext) => void
  updateContext: (context: DocumentContext | null) => void  // Update context
  requestHistory: () => void         // Request message history
  connect: () => void               // Manually connect
  disconnect: () => void            // Manually disconnect
  error: string | null              // Error message if any
}
```

### Connection States

```typescript
type ConnectionState = 'connecting' | 'connected' | 'disconnected' | 'error'
```

- **connecting** - Establishing connection to server
- **connected** - Successfully connected and authenticated
- **disconnected** - Not connected (will auto-reconnect if configured)
- **error** - Error occurred (check `error` property)

### Message Types

The hook supports the following message types compatible with the Python WebSocket server:

#### Outgoing Messages (Client → Server)

- **auth** - Authenticate and create/resume session
- **chat** - Send chat message
- **context** - Update document/quotation context
- **history** - Request message history
- **ping** - Keep-alive ping

#### Incoming Messages (Server → Client)

- **system** - System messages (welcome, notifications)
- **message** - Chat message (user or AI)
- **auth_success** - Authentication successful
- **context_updated** - Context update confirmed
- **typing** - AI typing indicator
- **history** - Message history response
- **pong** - Keep-alive response
- **error** - Server error

## Context-Aware Chat

The hook supports three context types for AI responses:

### Document Context

```typescript
const context: DocumentContext = {
  type: 'document',
  document_id: 'doc_123',
  name: 'Project Proposal.pdf'
}

const { sendMessage, updateContext } = useWebSocket({
  userId: 'user123',
  context,
})

// AI will provide document-specific responses
sendMessage('What are the key requirements?')
```

### Quotation Context

```typescript
const context: DocumentContext = {
  type: 'quotation',
  quotation_id: 'quot_456',
  customer: 'ABC Corporation'
}

const { sendMessage } = useWebSocket({
  userId: 'sales_rep',
  context,
})

// AI will provide quotation-specific responses
sendMessage('What is the total price?')
```

### Product Context

```typescript
const context: DocumentContext = {
  type: 'product',
  name: 'Industrial Safety Helmet'
}

const { sendMessage } = useWebSocket({
  userId: 'user123',
  context,
})

// AI will provide product-specific responses
sendMessage('What are the specifications?')
```

### Updating Context Dynamically

```typescript
const { updateContext } = useWebSocket({
  userId: 'user123',
  autoConnect: true,
})

// Switch to document view
updateContext({
  type: 'document',
  document_id: 'doc_789',
  name: 'RFP Document.pdf'
})

// Switch to product view
updateContext({
  type: 'product',
  name: 'Safety Gloves'
})

// Clear context
updateContext(null)
```

## Advanced Features

### Message Queue

Messages sent while disconnected are automatically queued and sent when reconnected:

```typescript
const { sendMessage, isConnected } = useWebSocket({
  userId: 'user123',
  autoConnect: true,
})

// This will be queued if not connected
sendMessage('Hello!')

// When connection is restored, queued messages are sent automatically
```

### Session Persistence

Persist session ID across page reloads:

```typescript
const [sessionId, setSessionId] = useState<string | undefined>(
  typeof window !== 'undefined'
    ? localStorage.getItem('chat_session_id') || undefined
    : undefined
)

const { lastMessage } = useWebSocket({
  userId: 'user123',
  sessionId,
  autoConnect: true,
})

// Save session ID when authenticated
useEffect(() => {
  if (lastMessage?.type === 'auth_success' && lastMessage.session_id) {
    setSessionId(lastMessage.session_id)
    localStorage.setItem('chat_session_id', lastMessage.session_id)
  }
}, [lastMessage])
```

### Custom Event Handlers

```typescript
const { connectionState } = useWebSocket({
  userId: 'user123',
  onOpen: () => {
    console.log('Connected! Ready to chat.')
  },
  onClose: () => {
    console.log('Disconnected. Reconnecting...')
  },
  onError: (error) => {
    console.error('WebSocket error:', error)
  },
  onMessage: (message) => {
    if (message.type === 'typing') {
      // Show typing indicator
    }
    if (message.type === 'error') {
      // Handle server error
    }
  },
})
```

### Manual Connection Control

```typescript
const { connect, disconnect, connectionState } = useWebSocket({
  userId: 'user123',
  autoConnect: false,  // Don't auto-connect
})

// Connect manually
<button onClick={connect}>Connect</button>

// Disconnect manually
<button onClick={disconnect}>Disconnect</button>

// Current state
<div>Status: {connectionState}</div>
```

## Error Handling

The hook provides comprehensive error handling:

```typescript
const { error, connectionState } = useWebSocket({
  userId: 'user123',
  autoConnect: true,
})

if (error) {
  // Display error to user
  return <div className="error">Connection error: {error}</div>
}

if (connectionState === 'error') {
  // Show error state
  return <div>Unable to connect to chat server</div>
}
```

Common errors:

- **"WebSocket URL not configured"** - Missing `NEXT_PUBLIC_WEBSOCKET_URL`
- **"Connection lost. Please refresh the page."** - Max reconnect attempts reached
- **"Failed to send message"** - Send failed (message will be queued)
- **Server errors** - Errors from the WebSocket server

## Message History

Request chat history for the current session:

```typescript
const { requestHistory, messages, isConnected } = useWebSocket({
  userId: 'user123',
  sessionId: 'existing_session_123',
  autoConnect: true,
})

useEffect(() => {
  if (isConnected) {
    requestHistory()
  }
}, [isConnected, requestHistory])

// Messages will be populated with history
console.log(`Loaded ${messages.length} messages`)
```

## Typing Indicator

Detect when AI is typing:

```typescript
const { lastMessage } = useWebSocket({
  userId: 'user123',
  autoConnect: true,
})

const isTyping = lastMessage?.type === 'typing' && lastMessage.typing === true

return (
  <div>
    {isTyping && <div>AI is typing...</div>}
  </div>
)
```

## Connection State Management

Monitor connection state changes:

```typescript
const { connectionState } = useWebSocket({
  userId: 'user123',
  autoConnect: true,
})

useEffect(() => {
  switch (connectionState) {
    case 'connecting':
      console.log('Establishing connection...')
      break
    case 'connected':
      console.log('Connected successfully!')
      break
    case 'disconnected':
      console.log('Disconnected. Will reconnect...')
      break
    case 'error':
      console.error('Connection error occurred')
      break
  }
}, [connectionState])
```

## Best Practices

### 1. Always Check Connection State

```typescript
// ✅ Good
<button onClick={() => sendMessage('Hello')} disabled={!isConnected}>
  Send
</button>

// ❌ Bad - doesn't check connection
<button onClick={() => sendMessage('Hello')}>
  Send
</button>
```

### 2. Handle Empty Messages

```typescript
// ✅ Good
const handleSend = () => {
  const message = input.trim()
  if (message) {
    sendMessage(message)
    setInput('')
  }
}

// ❌ Bad - sends empty message
const handleSend = () => {
  sendMessage(input)
  setInput('')
}
```

### 3. Display Errors to Users

```typescript
// ✅ Good
{error && (
  <div className="error-banner">
    {error}
    <button onClick={() => window.location.reload()}>
      Reload Page
    </button>
  </div>
)}

// ❌ Bad - silent failure
{error && console.error(error)}
```

### 4. Provide Connection Feedback

```typescript
// ✅ Good
<div className={`status-indicator status-${connectionState}`}>
  {connectionState === 'connecting' && '⏳ Connecting...'}
  {connectionState === 'connected' && '✅ Connected'}
  {connectionState === 'disconnected' && '⚠️ Reconnecting...'}
  {connectionState === 'error' && '❌ Connection error'}
</div>

// ❌ Bad - no feedback
<div>Chat</div>
```

## Testing

### Local Development

1. Start the WebSocket server:
```bash
docker-compose up horme-websocket
```

2. Configure environment:
```bash
NEXT_PUBLIC_WEBSOCKET_URL=ws://localhost:8001
```

3. Use the hook in your components

### Production

1. Configure production WebSocket URL:
```bash
NEXT_PUBLIC_WEBSOCKET_URL=wss://your-domain.com/ws
```

2. Ensure WebSocket server is running and accessible

3. Test with SSL/TLS enabled

## Troubleshooting

### Connection Fails Immediately

- Check `NEXT_PUBLIC_WEBSOCKET_URL` is set correctly
- Ensure WebSocket server is running
- Verify network connectivity
- Check browser console for errors

### Messages Not Sending

- Check `isConnected` is `true`
- Verify message is not empty
- Check browser console for WebSocket errors
- Messages should be queued if offline

### Reconnection Not Working

- Check `maxReconnectAttempts` configuration
- Verify `reconnectInterval` is reasonable
- Ensure WebSocket server is accessible
- Check server logs for connection issues

### Session Not Persisting

- Verify `sessionId` is being saved (localStorage)
- Check `sessionId` is passed to hook
- Ensure session exists on server
- Check server session expiration settings

## Performance Considerations

- **Message Queue**: Limited to prevent memory issues
- **Ping Interval**: Default 30s, adjust based on needs
- **Reconnect Attempts**: Default 10, increase for poor networks
- **Message History**: Loads last 10 messages by default

## Security Notes

- Always use `wss://` (secure WebSocket) in production
- Do not store sensitive data in localStorage
- Validate all user input before sending
- Server validates all messages and enforces authentication
- Session IDs are server-generated, not client-generated

## Example Integration

See `use-websocket.example.tsx` for complete examples including:

- Basic chat component
- Document-aware chat
- Quotation chat with context updates
- Advanced usage with custom handlers
- Session persistence with localStorage

## Support

For issues or questions:

1. Check browser console for errors
2. Verify environment configuration
3. Check WebSocket server logs
4. Review server implementation: `src/websocket/chat_server.py`

## License

Part of the Horme POV project.
