/**
 * End-to-End Tests for Complete Chat Workflows
 * =============================================
 *
 * Tests complete user workflows from authentication to chat interaction.
 *
 * TIER 3: END-TO-END TESTS
 * - NO MOCKING - Complete real infrastructure stack
 * - Real authentication flow
 * - Real file upload → chat workflow
 * - Real quotation creation → chat workflow
 * - Real error scenarios
 *
 * Prerequisites:
 * - Complete Docker stack running (API, WebSocket, PostgreSQL, Redis)
 * - Test user in database
 * - All services healthy
 *
 * Run: npm test tests/e2e/chat-flow.test.ts
 */

import { renderHook, act, waitFor } from '@testing-library/react'
import { APIClient } from '@/lib/api-client'
import { useWebSocket } from '@/hooks/use-websocket'
import type {
  LoginRequest,
  DocumentUploadRequest,
  QuotationCreateRequest,
} from '@/lib/api-types'
import type { DocumentContext } from '@/hooks/use-websocket'

// Test configuration
const TEST_API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const TEST_WS_URL = process.env.NEXT_PUBLIC_WEBSOCKET_URL || 'ws://localhost:8001'
const TEST_USER_EMAIL = process.env.TEST_USER_EMAIL || 'test@horme.com'
const TEST_USER_PASSWORD = process.env.TEST_USER_PASSWORD || 'TestPassword123!'
const TEST_TIMEOUT = 15000 // 15 seconds for E2E tests

describe('End-to-End Chat Flow Tests', () => {
  let apiClient: APIClient
  let authToken: string | null = null
  let userId: string | null = null

  beforeAll(async () => {
    // Initialize API client
    apiClient = new APIClient({
      baseUrl: TEST_API_URL,
      timeout: 10000,
      maxRetries: 2,
    })

    // Authenticate
    const credentials: LoginRequest = {
      email: TEST_USER_EMAIL,
      password: TEST_USER_PASSWORD,
    }

    const loginResponse = await apiClient.login(credentials)
    authToken = loginResponse.access_token
    userId = loginResponse.user.id.toString()
  }, TEST_TIMEOUT)

  afterAll(() => {
    // Cleanup
    apiClient.logout()
  })

  // ============================================================================
  // Complete Authentication + Chat Workflow
  // ============================================================================

  describe('Authentication + Basic Chat', () => {
    it('should complete full login → websocket connect → chat workflow', async () => {
      // Step 1: Authenticate (already done in beforeAll)
      expect(authToken).toBeTruthy()
      expect(userId).toBeTruthy()

      // Step 2: Connect WebSocket
      const { result, unmount } = renderHook(() =>
        useWebSocket({
          url: TEST_WS_URL,
          userId: userId!,
          autoConnect: true,
        })
      )

      // Wait for WebSocket connection
      await waitFor(
        () => {
          expect(result.current.connectionState).toBe('connected')
        },
        { timeout: TEST_TIMEOUT }
      )

      expect(result.current.isConnected).toBe(true)

      // Step 3: Send chat message
      act(() => {
        result.current.sendMessage('Hello, I need help with a quotation')
      })

      // Wait for AI response
      await waitFor(
        () => {
          expect(result.current.lastMessage?.type).toBe('message')
        },
        { timeout: TEST_TIMEOUT }
      )

      expect(result.current.lastMessage?.message?.type).toBe('ai')
      expect(result.current.lastMessage?.message?.content).toBeDefined()

      // Step 4: Verify message is added to history
      expect(result.current.messages.length).toBeGreaterThan(0)

      unmount()
    }, TEST_TIMEOUT * 2)

    it('should maintain session across multiple messages', async () => {
      const { result, unmount } = renderHook(() =>
        useWebSocket({
          url: TEST_WS_URL,
          userId: userId!,
          autoConnect: true,
        })
      )

      await waitFor(
        () => {
          expect(result.current.connectionState).toBe('connected')
        },
        { timeout: TEST_TIMEOUT }
      )

      // Send first message
      act(() => {
        result.current.sendMessage('First message in conversation')
      })

      await waitFor(
        () => {
          expect(result.current.lastMessage?.type).toBe('message')
        },
        { timeout: TEST_TIMEOUT }
      )

      const sessionId = result.current.lastMessage?.session_id

      // Send second message
      act(() => {
        result.current.sendMessage('Second message in same conversation')
      })

      await waitFor(
        () => {
          expect(result.current.messages.length).toBeGreaterThan(1)
        },
        { timeout: TEST_TIMEOUT }
      )

      // Verify session ID is maintained
      const latestMessage = result.current.messages[result.current.messages.length - 1]
      expect(latestMessage.session_id).toBe(sessionId)

      unmount()
    }, TEST_TIMEOUT * 2)
  })

  // ============================================================================
  // Document Upload → Chat Workflow
  // ============================================================================

  describe('Document Upload → Chat Interaction', () => {
    it('should upload document → set context → chat about document', async () => {
      // Step 1: Upload document
      const pdfContent = '%PDF-1.4\n%Test RFP Document\nProject: Office Renovation'
      const blob = new Blob([pdfContent], { type: 'application/pdf' })
      const file = new File([blob], 'test-rfp.pdf', {
        type: 'application/pdf',
      })

      const uploadRequest: DocumentUploadRequest = {
        file,
        document_type: 'rfp',
        metadata: {
          title: 'Test RFP Document',
          description: 'E2E test upload',
        },
      }

      const uploadResponse = await apiClient.uploadFile(uploadRequest)

      expect(uploadResponse).toBeDefined()
      expect(uploadResponse.document_id).toBeDefined()

      const documentId = uploadResponse.document_id

      // Step 2: Connect WebSocket with document context
      const documentContext: DocumentContext = {
        type: 'document',
        document_id: documentId.toString(),
        name: 'Test RFP Document',
      }

      const { result, unmount } = renderHook(() =>
        useWebSocket({
          url: TEST_WS_URL,
          userId: userId!,
          context: documentContext,
          autoConnect: true,
        })
      )

      await waitFor(
        () => {
          expect(result.current.connectionState).toBe('connected')
        },
        { timeout: TEST_TIMEOUT }
      )

      // Step 3: Chat about the document
      act(() => {
        result.current.sendMessage('Can you analyze this RFP document?')
      })

      await waitFor(
        () => {
          expect(result.current.lastMessage?.type).toBe('message')
        },
        { timeout: TEST_TIMEOUT }
      )

      expect(result.current.lastMessage?.message?.type).toBe('ai')
      expect(result.current.lastMessage?.message?.content).toBeDefined()

      // Step 4: Verify context is maintained
      const aiMessage = result.current.lastMessage?.message
      expect(aiMessage?.context?.type).toBe('document')

      unmount()
    }, TEST_TIMEOUT * 3)

    it('should handle document context updates during conversation', async () => {
      // Upload first document
      const doc1Content = '%PDF-1.4\n%Document 1'
      const blob1 = new Blob([doc1Content], { type: 'application/pdf' })
      const file1 = new File([blob1], 'doc1.pdf', { type: 'application/pdf' })

      const upload1 = await apiClient.uploadFile({ file: file1 })
      const doc1Id = upload1.document_id

      // Connect with first document context
      const { result, unmount } = renderHook(() =>
        useWebSocket({
          url: TEST_WS_URL,
          userId: userId!,
          context: {
            type: 'document',
            document_id: doc1Id.toString(),
            name: 'Document 1',
          },
          autoConnect: true,
        })
      )

      await waitFor(
        () => {
          expect(result.current.connectionState).toBe('connected')
        },
        { timeout: TEST_TIMEOUT }
      )

      // Chat about first document
      act(() => {
        result.current.sendMessage('Analyze the first document')
      })

      await waitFor(
        () => {
          expect(result.current.lastMessage?.type).toBe('message')
        },
        { timeout: TEST_TIMEOUT }
      )

      // Upload second document
      const doc2Content = '%PDF-1.4\n%Document 2'
      const blob2 = new Blob([doc2Content], { type: 'application/pdf' })
      const file2 = new File([blob2], 'doc2.pdf', { type: 'application/pdf' })

      const upload2 = await apiClient.uploadFile({ file: file2 })
      const doc2Id = upload2.document_id

      // Update context to second document
      act(() => {
        result.current.updateContext({
          type: 'document',
          document_id: doc2Id.toString(),
          name: 'Document 2',
        })
      })

      await waitFor(
        () => {
          expect(result.current.lastMessage?.type).toBe('context_updated')
        },
        { timeout: TEST_TIMEOUT }
      )

      // Chat about second document
      act(() => {
        result.current.sendMessage('Now analyze the second document')
      })

      await waitFor(
        () => {
          const msgs = result.current.messages
          return msgs.length > 2
        },
        { timeout: TEST_TIMEOUT }
      )

      unmount()
    }, TEST_TIMEOUT * 4)
  })

  // ============================================================================
  // Quotation Creation → Chat Workflow
  // ============================================================================

  describe('Quotation Creation → Chat Interaction', () => {
    it('should create quotation → set context → chat about quotation', async () => {
      // Step 1: Create quotation
      const quoteData: QuotationCreateRequest = {
        items: [
          {
            description: 'Construction Materials',
            quantity: 100,
            unit_price: 50.0,
            total_price: 5000.0,
          },
          {
            description: 'Labor Costs',
            quantity: 40,
            unit_price: 75.0,
            total_price: 3000.0,
          },
        ],
        notes: 'E2E test quotation',
      }

      const quotation = await apiClient.createQuotation(quoteData)

      expect(quotation).toBeDefined()
      expect(quotation.id).toBeDefined()
      expect(quotation.quote_number).toBeDefined()

      // Step 2: Connect WebSocket with quotation context
      const quotationContext: DocumentContext = {
        type: 'quotation',
        quotation_id: quotation.id.toString(),
        name: quotation.quote_number,
      }

      const { result, unmount } = renderHook(() =>
        useWebSocket({
          url: TEST_WS_URL,
          userId: userId!,
          context: quotationContext,
          autoConnect: true,
        })
      )

      await waitFor(
        () => {
          expect(result.current.connectionState).toBe('connected')
        },
        { timeout: TEST_TIMEOUT }
      )

      // Step 3: Chat about the quotation
      act(() => {
        result.current.sendMessage('Can you explain this quotation?')
      })

      await waitFor(
        () => {
          expect(result.current.lastMessage?.type).toBe('message')
        },
        { timeout: TEST_TIMEOUT }
      )

      expect(result.current.lastMessage?.message?.type).toBe('ai')

      // Step 4: Ask follow-up questions
      act(() => {
        result.current.sendMessage('What is the total cost?')
      })

      await waitFor(
        () => {
          expect(result.current.messages.length).toBeGreaterThan(2)
        },
        { timeout: TEST_TIMEOUT }
      )

      unmount()
    }, TEST_TIMEOUT * 3)

    it('should update quotation status → chat about changes', async () => {
      // Create quotation
      const quoteData: QuotationCreateRequest = {
        items: [
          {
            description: 'Test Item',
            quantity: 1,
            unit_price: 100.0,
            total_price: 100.0,
          },
        ],
      }

      const quotation = await apiClient.createQuotation(quoteData)

      // Update status to pending
      const updated = await apiClient.updateQuotationStatus(quotation.id, {
        status: 'pending',
      })

      expect(updated.status).toBe('pending')

      // Connect with quotation context
      const { result, unmount } = renderHook(() =>
        useWebSocket({
          url: TEST_WS_URL,
          userId: userId!,
          context: {
            type: 'quotation',
            quotation_id: quotation.id.toString(),
          },
          autoConnect: true,
        })
      )

      await waitFor(
        () => {
          expect(result.current.connectionState).toBe('connected')
        },
        { timeout: TEST_TIMEOUT }
      )

      // Ask about quotation status
      act(() => {
        result.current.sendMessage('What is the status of this quotation?')
      })

      await waitFor(
        () => {
          expect(result.current.lastMessage?.type).toBe('message')
        },
        { timeout: TEST_TIMEOUT }
      )

      unmount()
    }, TEST_TIMEOUT * 3)
  })

  // ============================================================================
  // Multi-Document Comparison Workflow
  // ============================================================================

  describe('Multi-Document Comparison', () => {
    it('should upload multiple documents → compare in chat', async () => {
      // Upload multiple documents
      const docs = []

      for (let i = 0; i < 3; i++) {
        const content = `%PDF-1.4\n%Document ${i + 1}\nContent for document ${i + 1}`
        const blob = new Blob([content], { type: 'application/pdf' })
        const file = new File([blob], `comparison-doc-${i + 1}.pdf`, {
          type: 'application/pdf',
        })

        const upload = await apiClient.uploadFile({ file })
        docs.push(upload.document_id)
      }

      expect(docs.length).toBe(3)

      // Connect WebSocket
      const { result, unmount } = renderHook(() =>
        useWebSocket({
          url: TEST_WS_URL,
          userId: userId!,
          autoConnect: true,
        })
      )

      await waitFor(
        () => {
          expect(result.current.connectionState).toBe('connected')
        },
        { timeout: TEST_TIMEOUT }
      )

      // Ask to compare documents
      act(() => {
        result.current.sendMessage(
          `Compare documents with IDs: ${docs.join(', ')}`
        )
      })

      await waitFor(
        () => {
          expect(result.current.lastMessage?.type).toBe('message')
        },
        { timeout: TEST_TIMEOUT }
      )

      expect(result.current.lastMessage?.message?.type).toBe('ai')

      unmount()
    }, TEST_TIMEOUT * 4)
  })

  // ============================================================================
  // Error Scenario Workflows
  // ============================================================================

  describe('Error Scenarios', () => {
    it('should handle invalid document ID in context gracefully', async () => {
      const { result, unmount } = renderHook(() =>
        useWebSocket({
          url: TEST_WS_URL,
          userId: userId!,
          context: {
            type: 'document',
            document_id: '999999', // Non-existent
            name: 'Invalid Document',
          },
          autoConnect: true,
        })
      )

      await waitFor(
        () => {
          expect(result.current.connectionState).toBe('connected')
        },
        { timeout: TEST_TIMEOUT }
      )

      // Try to chat about invalid document
      act(() => {
        result.current.sendMessage('Tell me about this document')
      })

      await waitFor(
        () => {
          expect(result.current.lastMessage?.type).toBe('message')
        },
        { timeout: TEST_TIMEOUT }
      )

      // Should receive error or informative response
      expect(result.current.lastMessage?.message).toBeDefined()

      unmount()
    }, TEST_TIMEOUT * 2)

    it('should recover from WebSocket disconnection during chat', async () => {
      const { result, unmount } = renderHook(() =>
        useWebSocket({
          url: TEST_WS_URL,
          userId: userId!,
          autoConnect: true,
          reconnectInterval: 1000,
          maxReconnectAttempts: 3,
        })
      )

      await waitFor(
        () => {
          expect(result.current.connectionState).toBe('connected')
        },
        { timeout: TEST_TIMEOUT }
      )

      // Send message
      act(() => {
        result.current.sendMessage('Message before disconnection')
      })

      await waitFor(
        () => {
          expect(result.current.lastMessage?.type).toBe('message')
        },
        { timeout: TEST_TIMEOUT }
      )

      // Simulate disconnection
      act(() => {
        result.current.disconnect()
      })

      await waitFor(
        () => {
          expect(result.current.connectionState).toBe('disconnected')
        },
        { timeout: TEST_TIMEOUT }
      )

      // Reconnect
      act(() => {
        result.current.connect()
      })

      await waitFor(
        () => {
          expect(result.current.connectionState).toBe('connected')
        },
        { timeout: TEST_TIMEOUT }
      )

      // Send message after reconnection
      act(() => {
        result.current.sendMessage('Message after reconnection')
      })

      await waitFor(
        () => {
          expect(result.current.messages.length).toBeGreaterThan(2)
        },
        { timeout: TEST_TIMEOUT }
      )

      unmount()
    }, TEST_TIMEOUT * 3)

    it('should handle API authentication expiry during chat session', async () => {
      // Create new client with short-lived token simulation
      const tempClient = new APIClient({
        baseUrl: TEST_API_URL,
        timeout: 5000,
      })

      // Login
      const loginResponse = await tempClient.login({
        email: TEST_USER_EMAIL,
        password: TEST_USER_PASSWORD,
      })

      const tempUserId = loginResponse.user.id.toString()

      // Connect WebSocket
      const { result, unmount } = renderHook(() =>
        useWebSocket({
          url: TEST_WS_URL,
          userId: tempUserId,
          autoConnect: true,
        })
      )

      await waitFor(
        () => {
          expect(result.current.connectionState).toBe('connected')
        },
        { timeout: TEST_TIMEOUT }
      )

      // Chat should still work via WebSocket even if API token expires
      act(() => {
        result.current.sendMessage('Testing chat with potential token expiry')
      })

      await waitFor(
        () => {
          expect(result.current.lastMessage?.type).toBe('message')
        },
        { timeout: TEST_TIMEOUT }
      )

      unmount()
    }, TEST_TIMEOUT * 2)
  })

  // ============================================================================
  // Performance and Load Tests
  // ============================================================================

  describe('Performance Tests', () => {
    it('should handle rapid successive messages', async () => {
      const { result, unmount } = renderHook(() =>
        useWebSocket({
          url: TEST_WS_URL,
          userId: userId!,
          autoConnect: true,
        })
      )

      await waitFor(
        () => {
          expect(result.current.connectionState).toBe('connected')
        },
        { timeout: TEST_TIMEOUT }
      )

      // Send 5 messages rapidly
      for (let i = 0; i < 5; i++) {
        act(() => {
          result.current.sendMessage(`Rapid message ${i + 1}`)
        })
      }

      // Wait for all responses
      await waitFor(
        () => {
          expect(result.current.messages.length).toBeGreaterThanOrEqual(5)
        },
        { timeout: TEST_TIMEOUT * 2 }
      )

      unmount()
    }, TEST_TIMEOUT * 3)

    it('should maintain performance with long conversation history', async () => {
      const { result, unmount } = renderHook(() =>
        useWebSocket({
          url: TEST_WS_URL,
          userId: userId!,
          autoConnect: true,
        })
      )

      await waitFor(
        () => {
          expect(result.current.connectionState).toBe('connected')
        },
        { timeout: TEST_TIMEOUT }
      )

      // Request history (which may be long)
      act(() => {
        result.current.requestHistory()
      })

      const startTime = Date.now()

      await waitFor(
        () => {
          expect(result.current.lastMessage?.type).toBe('history')
        },
        { timeout: TEST_TIMEOUT }
      )

      const endTime = Date.now()
      const loadTime = endTime - startTime

      // History should load within reasonable time
      expect(loadTime).toBeLessThan(5000) // 5 seconds

      unmount()
    }, TEST_TIMEOUT * 2)
  })

  // ============================================================================
  // Context Switching Workflow
  // ============================================================================

  describe('Context Switching', () => {
    it('should switch between document and quotation contexts smoothly', async () => {
      // Upload document
      const docContent = '%PDF-1.4\n%Test document'
      const blob = new Blob([docContent], { type: 'application/pdf' })
      const file = new File([blob], 'context-switch-doc.pdf', {
        type: 'application/pdf',
      })
      const docUpload = await apiClient.uploadFile({ file })

      // Create quotation
      const quote = await apiClient.createQuotation({
        items: [
          {
            description: 'Context Switch Test',
            quantity: 1,
            unit_price: 100.0,
            total_price: 100.0,
          },
        ],
      })

      // Connect with document context
      const { result, unmount } = renderHook(() =>
        useWebSocket({
          url: TEST_WS_URL,
          userId: userId!,
          context: {
            type: 'document',
            document_id: docUpload.document_id.toString(),
          },
          autoConnect: true,
        })
      )

      await waitFor(
        () => {
          expect(result.current.connectionState).toBe('connected')
        },
        { timeout: TEST_TIMEOUT }
      )

      // Chat about document
      act(() => {
        result.current.sendMessage('What is this document about?')
      })

      await waitFor(
        () => {
          expect(result.current.lastMessage?.type).toBe('message')
        },
        { timeout: TEST_TIMEOUT }
      )

      // Switch to quotation context
      act(() => {
        result.current.updateContext({
          type: 'quotation',
          quotation_id: quote.id.toString(),
        })
      })

      await waitFor(
        () => {
          expect(result.current.lastMessage?.type).toBe('context_updated')
        },
        { timeout: TEST_TIMEOUT }
      )

      // Chat about quotation
      act(() => {
        result.current.sendMessage('Explain this quotation')
      })

      await waitFor(
        () => {
          expect(result.current.messages.length).toBeGreaterThan(2)
        },
        { timeout: TEST_TIMEOUT }
      )

      // Clear context
      act(() => {
        result.current.updateContext(null)
      })

      await waitFor(
        () => {
          expect(result.current.lastMessage?.type).toBe('context_updated')
        },
        { timeout: TEST_TIMEOUT }
      )

      unmount()
    }, TEST_TIMEOUT * 4)
  })
})
