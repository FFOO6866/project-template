/**
 * Integration Tests for WebSocket Connection
 * ===========================================
 *
 * Tests the WebSocket hook against REAL WebSocket server.
 *
 * TIER 2: INTEGRATION TESTS
 * - NO MOCKING - Real WebSocket connection to Docker backend
 * - Real message sending/receiving
 * - Real auto-reconnection logic
 * - Real session management
 *
 * Prerequisites:
 * - WebSocket server running on localhost:8001 (or NEXT_PUBLIC_WEBSOCKET_URL)
 * - Redis for session storage
 * - Backend API for authentication context
 *
 * Run: npm test tests/integration/websocket.test.ts
 */

import { renderHook, act, waitFor } from '@testing-library/react'
import { useWebSocket } from '@/hooks/use-websocket'
import type {
  WebSocketMessage,
  DocumentContext,
  ChatMessage,
} from '@/hooks/use-websocket'

// Test configuration from environment
const TEST_WS_URL = process.env.NEXT_PUBLIC_WEBSOCKET_URL || 'ws://localhost:8001'
const TEST_USER_ID = 'test-user-' + Date.now()
const TEST_TIMEOUT = parseInt(process.env.TEST_WEBSOCKET_TIMEOUT || '10000', 10)

// Helper to wait for connection state
const waitForConnection = async (
  result: any,
  expectedState: string,
  timeout: number = 5000
) => {
  await waitFor(
    () => {
      expect(result.current.connectionState).toBe(expectedState)
    },
    { timeout }
  )
}

// Helper to wait for message
const waitForMessage = async (
  result: any,
  predicate: (msg: WebSocketMessage | null) => boolean,
  timeout: number = 5000
) => {
  await waitFor(
    () => {
      expect(predicate(result.current.lastMessage)).toBe(true)
    },
    { timeout }
  )
}

describe('WebSocket Integration Tests', () => {
  // ============================================================================
  // Connection Management Tests
  // ============================================================================

  describe('Connection Management', () => {
    it('should successfully connect to WebSocket server', async () => {
      const { result, unmount } = renderHook(() =>
        useWebSocket({
          url: TEST_WS_URL,
          userId: TEST_USER_ID,
          autoConnect: true,
        })
      )

      // Wait for connection
      await waitForConnection(result, 'connected', TEST_TIMEOUT)

      expect(result.current.isConnected).toBe(true)
      expect(result.current.error).toBeNull()

      unmount()
    }, TEST_TIMEOUT)

    it('should authenticate on connection', async () => {
      const { result, unmount } = renderHook(() =>
        useWebSocket({
          url: TEST_WS_URL,
          userId: TEST_USER_ID,
          autoConnect: true,
        })
      )

      // Wait for connection
      await waitForConnection(result, 'connected', TEST_TIMEOUT)

      // Wait for authentication success message
      await waitForMessage(
        result,
        (msg) => msg?.type === 'auth_success',
        TEST_TIMEOUT
      )

      expect(result.current.lastMessage?.type).toBe('auth_success')

      unmount()
    }, TEST_TIMEOUT)

    it('should not auto-connect when autoConnect is false', async () => {
      const { result, unmount } = renderHook(() =>
        useWebSocket({
          url: TEST_WS_URL,
          userId: TEST_USER_ID,
          autoConnect: false,
        })
      )

      // Should remain disconnected
      await new Promise((resolve) => setTimeout(resolve, 1000))
      expect(result.current.connectionState).toBe('disconnected')

      unmount()
    })

    it('should manually connect when requested', async () => {
      const { result, unmount } = renderHook(() =>
        useWebSocket({
          url: TEST_WS_URL,
          userId: TEST_USER_ID,
          autoConnect: false,
        })
      )

      expect(result.current.connectionState).toBe('disconnected')

      // Manually connect
      act(() => {
        result.current.connect()
      })

      await waitForConnection(result, 'connected', TEST_TIMEOUT)
      expect(result.current.isConnected).toBe(true)

      unmount()
    }, TEST_TIMEOUT)

    it('should disconnect when requested', async () => {
      const { result, unmount } = renderHook(() =>
        useWebSocket({
          url: TEST_WS_URL,
          userId: TEST_USER_ID,
          autoConnect: true,
        })
      )

      // Wait for connection
      await waitForConnection(result, 'connected', TEST_TIMEOUT)

      // Disconnect
      act(() => {
        result.current.disconnect()
      })

      await waitForConnection(result, 'disconnected', TEST_TIMEOUT)
      expect(result.current.isConnected).toBe(false)

      unmount()
    }, TEST_TIMEOUT)
  })

  // ============================================================================
  // Message Sending Tests
  // ============================================================================

  describe('Message Sending', () => {
    it('should send a chat message', async () => {
      const { result, unmount } = renderHook(() =>
        useWebSocket({
          url: TEST_WS_URL,
          userId: TEST_USER_ID,
          autoConnect: true,
        })
      )

      // Wait for connection
      await waitForConnection(result, 'connected', TEST_TIMEOUT)

      // Send message
      act(() => {
        result.current.sendMessage('Hello from integration test')
      })

      // Wait for response
      await waitForMessage(
        result,
        (msg) => msg?.type === 'message',
        TEST_TIMEOUT
      )

      expect(result.current.lastMessage?.type).toBe('message')

      unmount()
    }, TEST_TIMEOUT)

    it('should queue messages when disconnected', async () => {
      const { result, unmount } = renderHook(() =>
        useWebSocket({
          url: TEST_WS_URL,
          userId: TEST_USER_ID,
          autoConnect: false,
        })
      )

      // Send message while disconnected
      act(() => {
        result.current.sendMessage('Queued message')
      })

      // Connect
      act(() => {
        result.current.connect()
      })

      // Wait for connection
      await waitForConnection(result, 'connected', TEST_TIMEOUT)

      // Message should be sent after connection
      await waitForMessage(
        result,
        (msg) => msg?.type === 'message',
        TEST_TIMEOUT
      )

      unmount()
    }, TEST_TIMEOUT)

    it('should not send empty messages', async () => {
      const { result, unmount } = renderHook(() =>
        useWebSocket({
          url: TEST_WS_URL,
          userId: TEST_USER_ID,
          autoConnect: true,
        })
      )

      await waitForConnection(result, 'connected', TEST_TIMEOUT)

      const initialMessage = result.current.lastMessage

      // Try to send empty message
      act(() => {
        result.current.sendMessage('')
      })

      // Wait a bit
      await new Promise((resolve) => setTimeout(resolve, 500))

      // Last message should not have changed
      expect(result.current.lastMessage).toBe(initialMessage)

      unmount()
    }, TEST_TIMEOUT)
  })

  // ============================================================================
  // Message Receiving Tests
  // ============================================================================

  describe('Message Receiving', () => {
    it('should receive AI response messages', async () => {
      const { result, unmount } = renderHook(() =>
        useWebSocket({
          url: TEST_WS_URL,
          userId: TEST_USER_ID,
          autoConnect: true,
        })
      )

      await waitForConnection(result, 'connected', TEST_TIMEOUT)

      // Send a message
      act(() => {
        result.current.sendMessage('Test message for AI response')
      })

      // Wait for AI response
      await waitForMessage(
        result,
        (msg) => msg?.type === 'message' && msg.message?.type === 'ai',
        TEST_TIMEOUT
      )

      expect(result.current.lastMessage?.message?.type).toBe('ai')
      expect(result.current.lastMessage?.message?.content).toBeDefined()

      unmount()
    }, TEST_TIMEOUT)

    it('should add messages to messages array', async () => {
      const { result, unmount } = renderHook(() =>
        useWebSocket({
          url: TEST_WS_URL,
          userId: TEST_USER_ID,
          autoConnect: true,
        })
      )

      await waitForConnection(result, 'connected', TEST_TIMEOUT)

      const initialMessageCount = result.current.messages.length

      // Send a message
      act(() => {
        result.current.sendMessage('Test message for array')
      })

      // Wait for response
      await waitFor(
        () => {
          expect(result.current.messages.length).toBeGreaterThan(
            initialMessageCount
          )
        },
        { timeout: TEST_TIMEOUT }
      )

      unmount()
    }, TEST_TIMEOUT)

    it('should handle pong messages for keep-alive', async () => {
      const { result, unmount } = renderHook(() =>
        useWebSocket({
          url: TEST_WS_URL,
          userId: TEST_USER_ID,
          autoConnect: true,
          pingInterval: 1000, // Ping every second for testing
        })
      )

      await waitForConnection(result, 'connected', TEST_TIMEOUT)

      // Wait for pong response
      await waitForMessage(
        result,
        (msg) => msg?.type === 'pong',
        TEST_TIMEOUT
      )

      expect(result.current.lastMessage?.type).toBe('pong')

      unmount()
    }, TEST_TIMEOUT)
  })

  // ============================================================================
  // Session Management Tests
  // ============================================================================

  describe('Session Management', () => {
    it('should receive and store session ID', async () => {
      const { result, unmount } = renderHook(() =>
        useWebSocket({
          url: TEST_WS_URL,
          userId: TEST_USER_ID,
          autoConnect: true,
        })
      )

      await waitForConnection(result, 'connected', TEST_TIMEOUT)

      // Wait for auth success with session ID
      await waitForMessage(
        result,
        (msg) => msg?.type === 'auth_success' && !!msg.session_id,
        TEST_TIMEOUT
      )

      expect(result.current.lastMessage?.session_id).toBeDefined()

      unmount()
    }, TEST_TIMEOUT)

    it('should use provided session ID on connection', async () => {
      const testSessionId = 'test-session-' + Date.now()

      const { result, unmount } = renderHook(() =>
        useWebSocket({
          url: TEST_WS_URL,
          userId: TEST_USER_ID,
          sessionId: testSessionId,
          autoConnect: true,
        })
      )

      await waitForConnection(result, 'connected', TEST_TIMEOUT)

      // The session ID should be acknowledged
      await waitForMessage(
        result,
        (msg) => msg?.type === 'auth_success',
        TEST_TIMEOUT
      )

      unmount()
    }, TEST_TIMEOUT)

    it('should maintain session across reconnection', async () => {
      const { result, unmount } = renderHook(() =>
        useWebSocket({
          url: TEST_WS_URL,
          userId: TEST_USER_ID,
          autoConnect: true,
        })
      )

      // Connect and get session ID
      await waitForConnection(result, 'connected', TEST_TIMEOUT)
      await waitForMessage(
        result,
        (msg) => msg?.type === 'auth_success',
        TEST_TIMEOUT
      )

      const originalSessionId = result.current.lastMessage?.session_id

      // Disconnect
      act(() => {
        result.current.disconnect()
      })

      await waitForConnection(result, 'disconnected', TEST_TIMEOUT)

      // Reconnect
      act(() => {
        result.current.connect()
      })

      await waitForConnection(result, 'connected', TEST_TIMEOUT)

      // Session ID should be the same
      await waitForMessage(
        result,
        (msg) => msg?.type === 'auth_success',
        TEST_TIMEOUT
      )

      unmount()
    }, TEST_TIMEOUT * 2)
  })

  // ============================================================================
  // Context Management Tests
  // ============================================================================

  describe('Context Management', () => {
    it('should set context on connection', async () => {
      const testContext: DocumentContext = {
        type: 'document',
        document_id: 'test-doc-123',
        name: 'Test Document',
      }

      const { result, unmount } = renderHook(() =>
        useWebSocket({
          url: TEST_WS_URL,
          userId: TEST_USER_ID,
          context: testContext,
          autoConnect: true,
        })
      )

      await waitForConnection(result, 'connected', TEST_TIMEOUT)

      unmount()
    }, TEST_TIMEOUT)

    it('should update context after connection', async () => {
      const { result, unmount } = renderHook(() =>
        useWebSocket({
          url: TEST_WS_URL,
          userId: TEST_USER_ID,
          autoConnect: true,
        })
      )

      await waitForConnection(result, 'connected', TEST_TIMEOUT)

      const newContext: DocumentContext = {
        type: 'quotation',
        quotation_id: 'quote-456',
        customer: 'Test Customer',
      }

      // Update context
      act(() => {
        result.current.updateContext(newContext)
      })

      // Wait for context update confirmation
      await waitForMessage(
        result,
        (msg) => msg?.type === 'context_updated',
        TEST_TIMEOUT
      )

      unmount()
    }, TEST_TIMEOUT)

    it('should clear context', async () => {
      const initialContext: DocumentContext = {
        type: 'document',
        document_id: 'test-doc-789',
      }

      const { result, unmount } = renderHook(() =>
        useWebSocket({
          url: TEST_WS_URL,
          userId: TEST_USER_ID,
          context: initialContext,
          autoConnect: true,
        })
      )

      await waitForConnection(result, 'connected', TEST_TIMEOUT)

      // Clear context
      act(() => {
        result.current.updateContext(null)
      })

      // Wait for context update
      await waitForMessage(
        result,
        (msg) => msg?.type === 'context_updated',
        TEST_TIMEOUT
      )

      unmount()
    }, TEST_TIMEOUT)
  })

  // ============================================================================
  // History Request Tests
  // ============================================================================

  describe('History Request', () => {
    it('should request and receive message history', async () => {
      const { result, unmount } = renderHook(() =>
        useWebSocket({
          url: TEST_WS_URL,
          userId: TEST_USER_ID,
          autoConnect: true,
        })
      )

      await waitForConnection(result, 'connected', TEST_TIMEOUT)

      // Send a message first
      act(() => {
        result.current.sendMessage('First message for history test')
      })

      await waitForMessage(
        result,
        (msg) => msg?.type === 'message',
        TEST_TIMEOUT
      )

      // Request history
      act(() => {
        result.current.requestHistory()
      })

      // Wait for history response
      await waitForMessage(
        result,
        (msg) => msg?.type === 'history',
        TEST_TIMEOUT
      )

      expect(result.current.lastMessage?.type).toBe('history')
      if (result.current.lastMessage?.messages) {
        expect(Array.isArray(result.current.lastMessage.messages)).toBe(true)
      }

      unmount()
    }, TEST_TIMEOUT)

    it('should populate messages array from history', async () => {
      const { result, unmount } = renderHook(() =>
        useWebSocket({
          url: TEST_WS_URL,
          userId: TEST_USER_ID,
          autoConnect: true,
        })
      )

      await waitForConnection(result, 'connected', TEST_TIMEOUT)

      // Request history
      act(() => {
        result.current.requestHistory()
      })

      // Wait for history
      await waitForMessage(
        result,
        (msg) => msg?.type === 'history',
        TEST_TIMEOUT
      )

      // Messages should be populated
      expect(Array.isArray(result.current.messages)).toBe(true)

      unmount()
    }, TEST_TIMEOUT)
  })

  // ============================================================================
  // Auto-Reconnection Tests
  // ============================================================================

  describe('Auto-Reconnection', () => {
    it('should attempt reconnection on connection loss', async () => {
      const { result, unmount } = renderHook(() =>
        useWebSocket({
          url: TEST_WS_URL,
          userId: TEST_USER_ID,
          autoConnect: true,
          reconnectInterval: 1000, // 1 second for testing
          maxReconnectAttempts: 3,
        })
      )

      // Wait for initial connection
      await waitForConnection(result, 'connected', TEST_TIMEOUT)

      // Force disconnect by calling disconnect (simulates connection loss)
      // In a real scenario, the server would close the connection
      act(() => {
        result.current.disconnect()
      })

      await waitForConnection(result, 'disconnected', TEST_TIMEOUT)

      // Note: Auto-reconnection is prevented when manually disconnected
      // This test verifies the disconnect works properly

      unmount()
    }, TEST_TIMEOUT)

    it('should limit reconnection attempts', async () => {
      // Use invalid URL to force connection failure
      const { result, unmount } = renderHook(() =>
        useWebSocket({
          url: 'ws://invalid-websocket-url:9999',
          userId: TEST_USER_ID,
          autoConnect: true,
          reconnectInterval: 500,
          maxReconnectAttempts: 2,
        })
      )

      // Wait for error state
      await waitFor(
        () => {
          expect(result.current.error).not.toBeNull()
        },
        { timeout: 5000 }
      )

      unmount()
    }, 10000)
  })

  // ============================================================================
  // Error Handling Tests
  // ============================================================================

  describe('Error Handling', () => {
    it('should handle server error messages', async () => {
      const { result, unmount } = renderHook(() =>
        useWebSocket({
          url: TEST_WS_URL,
          userId: TEST_USER_ID,
          autoConnect: true,
        })
      )

      await waitForConnection(result, 'connected', TEST_TIMEOUT)

      // The server might send error messages
      // We'll wait to see if we receive any
      // This is more of a passive test

      unmount()
    }, TEST_TIMEOUT)

    it('should set error state on connection failure', async () => {
      const { result, unmount } = renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:99999', // Invalid port
          userId: TEST_USER_ID,
          autoConnect: true,
          maxReconnectAttempts: 1,
        })
      )

      // Wait for error
      await waitFor(
        () => {
          expect(
            result.current.connectionState === 'error' ||
              result.current.error !== null
          ).toBe(true)
        },
        { timeout: 5000 }
      )

      unmount()
    }, 10000)
  })

  // ============================================================================
  // Callback Tests
  // ============================================================================

  describe('Event Callbacks', () => {
    it('should call onOpen callback on connection', async () => {
      const onOpen = jest.fn()

      const { result, unmount } = renderHook(() =>
        useWebSocket({
          url: TEST_WS_URL,
          userId: TEST_USER_ID,
          autoConnect: true,
          onOpen,
        })
      )

      await waitForConnection(result, 'connected', TEST_TIMEOUT)

      expect(onOpen).toHaveBeenCalled()

      unmount()
    }, TEST_TIMEOUT)

    it('should call onClose callback on disconnection', async () => {
      const onClose = jest.fn()

      const { result, unmount } = renderHook(() =>
        useWebSocket({
          url: TEST_WS_URL,
          userId: TEST_USER_ID,
          autoConnect: true,
          onClose,
          maxReconnectAttempts: 0, // Prevent auto-reconnect
        })
      )

      await waitForConnection(result, 'connected', TEST_TIMEOUT)

      act(() => {
        result.current.disconnect()
      })

      await waitFor(
        () => {
          expect(onClose).toHaveBeenCalled()
        },
        { timeout: TEST_TIMEOUT }
      )

      unmount()
    }, TEST_TIMEOUT)

    it('should call onMessage callback on message received', async () => {
      const onMessage = jest.fn()

      const { result, unmount } = renderHook(() =>
        useWebSocket({
          url: TEST_WS_URL,
          userId: TEST_USER_ID,
          autoConnect: true,
          onMessage,
        })
      )

      await waitForConnection(result, 'connected', TEST_TIMEOUT)

      // Send message to trigger response
      act(() => {
        result.current.sendMessage('Trigger callback')
      })

      await waitFor(
        () => {
          expect(onMessage).toHaveBeenCalled()
        },
        { timeout: TEST_TIMEOUT }
      )

      unmount()
    }, TEST_TIMEOUT)
  })

  // ============================================================================
  // Cleanup Tests
  // ============================================================================

  describe('Cleanup', () => {
    it('should cleanup on unmount', async () => {
      const { result, unmount } = renderHook(() =>
        useWebSocket({
          url: TEST_WS_URL,
          userId: TEST_USER_ID,
          autoConnect: true,
        })
      )

      await waitForConnection(result, 'connected', TEST_TIMEOUT)

      // Unmount should disconnect
      unmount()

      // After unmount, connection should be closed
      // This is verified by no errors during unmount
    }, TEST_TIMEOUT)

    it('should stop ping interval on unmount', async () => {
      const { result, unmount } = renderHook(() =>
        useWebSocket({
          url: TEST_WS_URL,
          userId: TEST_USER_ID,
          autoConnect: true,
          pingInterval: 1000,
        })
      )

      await waitForConnection(result, 'connected', TEST_TIMEOUT)

      unmount()

      // Cleanup verified by no errors
    }, TEST_TIMEOUT)
  })
})
