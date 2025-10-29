# WebSocket Hook - Quick Reference

## Setup

```bash
# .env.local
NEXT_PUBLIC_WEBSOCKET_URL=ws://localhost:8001

# Start WebSocket server
docker-compose up horme-websocket
```

## Basic Usage

```tsx
import { useWebSocket } from '@/hooks/use-websocket'

const {
  isConnected,
  messages,
  sendMessage,
  error
} = useWebSocket({
  userId: 'user123',
  autoConnect: true
})

// Send message
sendMessage('Hello!')

// Display messages
{messages.map(msg => <div key={msg.id}>{msg.content}</div>)}

// Show error
{error && <div>{error}</div>}
```

## Connection States

```tsx
connectionState: 'connecting' | 'connected' | 'disconnected' | 'error'
isConnected: boolean  // Convenience property
```

## Context-Aware Chat

```tsx
// Document context
const { sendMessage } = useWebSocket({
  userId: 'user123',
  context: {
    type: 'document',
    document_id: 'doc_123',
    name: 'RFP.pdf'
  }
})

// Quotation context
const { sendMessage } = useWebSocket({
  userId: 'user123',
  context: {
    type: 'quotation',
    quotation_id: 'quot_456',
    customer: 'ABC Corp'
  }
})

// Update context
updateContext({
  type: 'product',
  name: 'Safety Helmet'
})
```

## Message Types

### Outgoing (Client → Server)
- `auth` - Authentication
- `chat` - Chat message
- `context` - Update context
- `history` - Request history
- `ping` - Keep-alive

### Incoming (Server → Client)
- `system` - System message
- `message` - Chat message
- `auth_success` - Auth successful
- `context_updated` - Context updated
- `typing` - AI typing
- `history` - Message history
- `pong` - Keep-alive response
- `error` - Error

## Advanced Features

### Typing Indicator
```tsx
const isTyping = lastMessage?.type === 'typing' && lastMessage.typing === true
```

### Session Persistence
```tsx
const sessionId = localStorage.getItem('chat_session_id')

const { lastMessage } = useWebSocket({
  userId: 'user123',
  sessionId
})

useEffect(() => {
  if (lastMessage?.type === 'auth_success') {
    localStorage.setItem('chat_session_id', lastMessage.session_id!)
  }
}, [lastMessage])
```

### Message History
```tsx
const { requestHistory, isConnected } = useWebSocket({
  userId: 'user123',
  sessionId: 'existing_session'
})

useEffect(() => {
  if (isConnected) requestHistory()
}, [isConnected])
```

### Manual Control
```tsx
const { connect, disconnect, connectionState } = useWebSocket({
  userId: 'user123',
  autoConnect: false
})

// Connect manually
<button onClick={connect}>Connect</button>

// Disconnect manually
<button onClick={disconnect}>Disconnect</button>
```

### Custom Handlers
```tsx
useWebSocket({
  userId: 'user123',
  onOpen: () => console.log('Connected'),
  onClose: () => console.log('Disconnected'),
  onError: (err) => console.error(err),
  onMessage: (msg) => console.log(msg)
})
```

## Configuration Options

```tsx
interface UseWebSocketOptions {
  url?: string                    // WebSocket URL
  userId?: string                 // User ID
  sessionId?: string             // Session ID
  context?: DocumentContext      // Initial context
  autoConnect?: boolean          // Auto-connect (default: true)
  reconnectInterval?: number     // Reconnect interval (default: 3000ms)
  maxReconnectAttempts?: number  // Max attempts (default: 10)
  pingInterval?: number          // Ping interval (default: 30000ms)
  onOpen?: () => void
  onClose?: () => void
  onError?: (error: Event) => void
  onMessage?: (message: WebSocketMessage) => void
}
```

## Common Patterns

### Basic Chat
```tsx
<input
  disabled={!isConnected}
  onKeyDown={(e) => {
    if (e.key === 'Enter') {
      sendMessage(e.currentTarget.value)
      e.currentTarget.value = ''
    }
  }}
/>
```

### Connection Status Badge
```tsx
<Badge className={
  connectionState === 'connected' ? 'bg-green-100 text-green-800' :
  connectionState === 'connecting' ? 'bg-yellow-100 text-yellow-800' :
  'bg-red-100 text-red-800'
}>
  {connectionState}
</Badge>
```

### Error Display
```tsx
{error && (
  <div className="error-banner">
    <AlertCircle /> {error}
    <button onClick={() => window.location.reload()}>
      Reload
    </button>
  </div>
)}
```

### Quick Actions
```tsx
const quickActions = [
  "What is the total price?",
  "Show delivery terms",
  "Find alternatives"
]

{quickActions.map(action => (
  <button
    key={action}
    onClick={() => sendMessage(action)}
    disabled={!isConnected}
  >
    {action}
  </button>
))}
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Connection fails | Check `NEXT_PUBLIC_WEBSOCKET_URL` is set |
| Server not responding | Verify WebSocket server is running |
| Messages not sending | Check `isConnected` is `true` |
| Auto-reconnect not working | Check `maxReconnectAttempts` |
| Context not working | Verify context format matches server |

## Quick Checks

```bash
# Check environment variable
echo $NEXT_PUBLIC_WEBSOCKET_URL

# Check WebSocket server
docker-compose ps horme-websocket

# View server logs
docker-compose logs -f horme-websocket

# Test connection (browser console)
new WebSocket('ws://localhost:8001')
```

## Files

- `use-websocket.ts` - Main hook
- `use-websocket.example.tsx` - Usage examples
- `use-websocket.README.md` - Full documentation
- `INTEGRATION_GUIDE.md` - Integration steps

## Production Checklist

- [ ] Set `NEXT_PUBLIC_WEBSOCKET_URL` to `wss://` (secure)
- [ ] Configure SSL/TLS certificates
- [ ] Set up nginx reverse proxy
- [ ] Test auto-reconnection
- [ ] Test message queue
- [ ] Test context updates
- [ ] Monitor WebSocket server logs
- [ ] Set up error tracking

## Reference

Server: `src/websocket/chat_server.py`
Environment: `.env.example`
Documentation: `frontend/hooks/use-websocket.README.md`
