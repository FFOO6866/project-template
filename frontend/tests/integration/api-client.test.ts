/**
 * Integration Tests for API Client
 * =================================
 *
 * Tests the production API client against REAL backend services.
 *
 * TIER 2: INTEGRATION TESTS
 * - NO MOCKING - All requests go to real Docker backend
 * - Real PostgreSQL database operations
 * - Real authentication flows
 * - Real file upload validation
 *
 * Prerequisites:
 * - Backend API running on localhost:8000 (or NEXT_PUBLIC_API_URL)
 * - PostgreSQL database with test data
 * - Test user credentials configured
 *
 * Run: npm test tests/integration/api-client.test.ts
 */

import { APIClient, apiClient } from '@/lib/api-client'
import {
  AuthenticationError,
  ValidationError,
  NetworkError,
  NotFoundError,
  ServerError,
} from '@/lib/api-errors'
import type {
  LoginRequest,
  DocumentUploadRequest,
  QuotationCreateRequest,
  CustomerCreateRequest,
} from '@/lib/api-types'

// Test configuration from environment
const TEST_API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const TEST_USER_EMAIL = process.env.TEST_USER_EMAIL || 'test@horme.com'
const TEST_USER_PASSWORD = process.env.TEST_USER_PASSWORD || 'TestPassword123!'
const TEST_TIMEOUT = parseInt(process.env.TEST_API_TIMEOUT || '5000', 10)

describe('API Client Integration Tests', () => {
  let client: APIClient
  let authToken: string | null = null

  beforeAll(() => {
    // Create fresh client instance for tests
    client = new APIClient({
      baseUrl: TEST_API_URL,
      timeout: TEST_TIMEOUT,
      maxRetries: 2,
    })
  })

  afterAll(() => {
    // Cleanup: logout
    client.logout()
  })

  // ============================================================================
  // Health Check Tests
  // ============================================================================

  describe('Health Check', () => {
    it('should successfully check API health', async () => {
      const response = await client.healthCheck()

      expect(response).toBeDefined()
      expect(response.status).toBe('healthy')
      expect(response.timestamp).toBeDefined()
    }, TEST_TIMEOUT)

    it('should include service status in health check', async () => {
      const response = await client.healthCheck()

      expect(response.services).toBeDefined()
      if (response.services) {
        // At minimum, database should be up
        expect(['up', 'down']).toContain(response.services.database)
      }
    }, TEST_TIMEOUT)
  })

  // ============================================================================
  // Authentication Tests
  // ============================================================================

  describe('Authentication', () => {
    it('should successfully login with valid credentials', async () => {
      const credentials: LoginRequest = {
        email: TEST_USER_EMAIL,
        password: TEST_USER_PASSWORD,
      }

      const response = await client.login(credentials)

      expect(response).toBeDefined()
      expect(response.access_token).toBeDefined()
      expect(response.token_type).toBe('bearer')
      expect(response.user).toBeDefined()
      expect(response.user.email).toBe(TEST_USER_EMAIL)

      // Store token for subsequent tests
      authToken = response.access_token
    }, TEST_TIMEOUT)

    it('should fail login with invalid email format', async () => {
      const credentials: LoginRequest = {
        email: 'invalid-email',
        password: TEST_USER_PASSWORD,
      }

      await expect(client.login(credentials)).rejects.toThrow(ValidationError)
    }, TEST_TIMEOUT)

    it('should fail login with missing password', async () => {
      const credentials: LoginRequest = {
        email: TEST_USER_EMAIL,
        password: '',
      }

      await expect(client.login(credentials)).rejects.toThrow(ValidationError)
    }, TEST_TIMEOUT)

    it('should fail login with incorrect credentials', async () => {
      const credentials: LoginRequest = {
        email: TEST_USER_EMAIL,
        password: 'WrongPassword123!',
      }

      await expect(client.login(credentials)).rejects.toThrow(AuthenticationError)
    }, TEST_TIMEOUT)

    it('should store and retrieve auth token', async () => {
      expect(authToken).toBeTruthy()

      client.setAuthToken(authToken!)

      const retrievedToken = client.getAuthToken()
      expect(retrievedToken).toBe(authToken)
    })

    it('should detect token expiry correctly', () => {
      // This test verifies the token is NOT expired immediately after login
      expect(client.isTokenExpired()).toBe(false)
    })

    it('should clear auth token on logout', () => {
      client.setAuthToken(authToken!)
      expect(client.getAuthToken()).toBe(authToken)

      client.logout()
      expect(client.getAuthToken()).toBeNull()

      // Re-authenticate for other tests
      client.setAuthToken(authToken!)
    })
  })

  // ============================================================================
  // Request Interceptor Tests
  // ============================================================================

  describe('Request Interceptors', () => {
    it('should add authentication headers to requests', async () => {
      client.setAuthToken(authToken!)

      // Make an authenticated request
      const response = await client.getDashboardData()

      expect(response).toBeDefined()
      // If request succeeds, authentication header was properly added
    }, TEST_TIMEOUT)

    it('should handle requests without authentication', async () => {
      // Temporarily clear token
      const tempToken = client.getAuthToken()
      client.logout()

      // Health check doesn't require auth
      const response = await client.healthCheck()
      expect(response).toBeDefined()

      // Restore token
      if (tempToken) {
        client.setAuthToken(tempToken)
      }
    }, TEST_TIMEOUT)
  })

  // ============================================================================
  // Error Handling Tests
  // ============================================================================

  describe('Error Handling', () => {
    it('should throw NotFoundError for non-existent resources', async () => {
      client.setAuthToken(authToken!)

      await expect(client.getDocument(999999)).rejects.toThrow(NotFoundError)
    }, TEST_TIMEOUT)

    it('should throw AuthenticationError for missing token', async () => {
      // Temporarily clear token
      const tempToken = client.getAuthToken()
      client.logout()

      await expect(client.getDashboardData()).rejects.toThrow(AuthenticationError)

      // Restore token
      if (tempToken) {
        client.setAuthToken(tempToken)
      }
    }, TEST_TIMEOUT)

    it('should retry on network errors', async () => {
      // Create client with invalid URL to trigger retries
      const failingClient = new APIClient({
        baseUrl: 'http://invalid-url-that-does-not-exist:9999',
        timeout: 1000,
        maxRetries: 2,
      })

      await expect(failingClient.healthCheck()).rejects.toThrow(NetworkError)
    }, 10000) // Longer timeout for retries
  })

  // ============================================================================
  // Dashboard API Tests
  // ============================================================================

  describe('Dashboard API', () => {
    beforeEach(() => {
      client.setAuthToken(authToken!)
    })

    it('should fetch dashboard data', async () => {
      const dashboard = await client.getDashboardData()

      expect(dashboard).toBeDefined()
      expect(typeof dashboard.total_documents).toBe('number')
      expect(typeof dashboard.total_quotations).toBe('number')
      expect(typeof dashboard.total_customers).toBe('number')
    }, TEST_TIMEOUT)

    it('should include recent documents in dashboard', async () => {
      const dashboard = await client.getDashboardData()

      if (dashboard.recent_documents) {
        expect(Array.isArray(dashboard.recent_documents)).toBe(true)
        dashboard.recent_documents.forEach((doc) => {
          expect(doc.id).toBeDefined()
          expect(doc.filename).toBeDefined()
        })
      }
    }, TEST_TIMEOUT)
  })

  // ============================================================================
  // Customer API Tests
  // ============================================================================

  describe('Customer API', () => {
    let createdCustomerId: number | null = null

    beforeEach(() => {
      client.setAuthToken(authToken!)
    })

    it('should create a new customer', async () => {
      const customerData: CustomerCreateRequest = {
        name: `Test Customer ${Date.now()}`,
        email: `test-${Date.now()}@example.com`,
        phone: '+1234567890',
        company: 'Test Company',
      }

      const customer = await client.createCustomer(customerData)

      expect(customer).toBeDefined()
      expect(customer.id).toBeDefined()
      expect(customer.name).toBe(customerData.name)
      expect(customer.email).toBe(customerData.email)

      createdCustomerId = customer.id
    }, TEST_TIMEOUT)

    it('should fetch list of customers', async () => {
      const customers = await client.getCustomers({ limit: 10 })

      expect(Array.isArray(customers)).toBe(true)
      if (customers.length > 0) {
        expect(customers[0].id).toBeDefined()
        expect(customers[0].name).toBeDefined()
      }
    }, TEST_TIMEOUT)

    it('should fetch specific customer', async () => {
      if (!createdCustomerId) {
        // Create a customer first
        const customerData: CustomerCreateRequest = {
          name: `Test Customer ${Date.now()}`,
          email: `test-${Date.now()}@example.com`,
        }
        const created = await client.createCustomer(customerData)
        createdCustomerId = created.id
      }

      const customer = await client.getCustomer(createdCustomerId)

      expect(customer).toBeDefined()
      expect(customer.id).toBe(createdCustomerId)
    }, TEST_TIMEOUT)

    it('should update customer information', async () => {
      if (!createdCustomerId) {
        const customerData: CustomerCreateRequest = {
          name: `Test Customer ${Date.now()}`,
          email: `test-${Date.now()}@example.com`,
        }
        const created = await client.createCustomer(customerData)
        createdCustomerId = created.id
      }

      const updatedData = {
        name: `Updated Customer ${Date.now()}`,
      }

      const updated = await client.updateCustomer(createdCustomerId, updatedData)

      expect(updated).toBeDefined()
      expect(updated.id).toBe(createdCustomerId)
      expect(updated.name).toBe(updatedData.name)
    }, TEST_TIMEOUT)
  })

  // ============================================================================
  // Quotation API Tests
  // ============================================================================

  describe('Quotation API', () => {
    let createdQuoteId: number | null = null

    beforeEach(() => {
      client.setAuthToken(authToken!)
    })

    it('should create a new quotation', async () => {
      const quoteData: QuotationCreateRequest = {
        items: [
          {
            description: 'Test Product 1',
            quantity: 2,
            unit_price: 100.0,
            total_price: 200.0,
          },
          {
            description: 'Test Product 2',
            quantity: 1,
            unit_price: 50.0,
            total_price: 50.0,
          },
        ],
        notes: 'Test quotation',
      }

      const quote = await client.createQuotation(quoteData)

      expect(quote).toBeDefined()
      expect(quote.id).toBeDefined()
      expect(quote.quote_number).toBeDefined()
      expect(quote.total_amount).toBeGreaterThan(0)

      createdQuoteId = quote.id
    }, TEST_TIMEOUT)

    it('should fetch list of quotations', async () => {
      const quotes = await client.getQuotations({ limit: 10 })

      expect(Array.isArray(quotes)).toBe(true)
      if (quotes.length > 0) {
        expect(quotes[0].id).toBeDefined()
        expect(quotes[0].quote_number).toBeDefined()
      }
    }, TEST_TIMEOUT)

    it('should fetch specific quotation', async () => {
      if (!createdQuoteId) {
        const quoteData: QuotationCreateRequest = {
          items: [
            {
              description: 'Test Product',
              quantity: 1,
              unit_price: 100.0,
              total_price: 100.0,
            },
          ],
        }
        const created = await client.createQuotation(quoteData)
        createdQuoteId = created.id
      }

      const quote = await client.getQuotation(createdQuoteId)

      expect(quote).toBeDefined()
      expect(quote.id).toBe(createdQuoteId)
    }, TEST_TIMEOUT)

    it('should update quotation status', async () => {
      if (!createdQuoteId) {
        const quoteData: QuotationCreateRequest = {
          items: [
            {
              description: 'Test Product',
              quantity: 1,
              unit_price: 100.0,
              total_price: 100.0,
            },
          ],
        }
        const created = await client.createQuotation(quoteData)
        createdQuoteId = created.id
      }

      const updated = await client.updateQuotationStatus(createdQuoteId, {
        status: 'pending',
      })

      expect(updated).toBeDefined()
      expect(updated.id).toBe(createdQuoteId)
      expect(updated.status).toBe('pending')
    }, TEST_TIMEOUT)
  })

  // ============================================================================
  // File Upload Tests
  // ============================================================================

  describe('File Upload', () => {
    beforeEach(() => {
      client.setAuthToken(authToken!)
    })

    it('should upload a valid PDF file', async () => {
      // Create a test PDF file
      const pdfContent = '%PDF-1.4\n%Test PDF content'
      const blob = new Blob([pdfContent], { type: 'application/pdf' })
      const file = new File([blob], 'test-document.pdf', {
        type: 'application/pdf',
      })

      const uploadRequest: DocumentUploadRequest = {
        file,
        document_type: 'pdf',
        metadata: {
          title: 'Test Document',
          description: 'Integration test upload',
        },
      }

      const response = await client.uploadFile(uploadRequest)

      expect(response).toBeDefined()
      expect(response.document_id).toBeDefined()
      expect(response.filename).toBeDefined()
      expect(response.status).toBe('success')
    }, TEST_TIMEOUT)

    it('should reject file upload without file', async () => {
      const uploadRequest: DocumentUploadRequest = {
        file: null as any,
      }

      await expect(client.uploadFile(uploadRequest)).rejects.toThrow(ValidationError)
    })

    it('should reject oversized files', async () => {
      // Create a file larger than 50MB
      const largeContent = new Array(51 * 1024 * 1024).fill('a').join('')
      const blob = new Blob([largeContent], { type: 'application/pdf' })
      const file = new File([blob], 'large-file.pdf', {
        type: 'application/pdf',
      })

      const uploadRequest: DocumentUploadRequest = {
        file,
      }

      await expect(client.uploadFile(uploadRequest)).rejects.toThrow(ValidationError)
    })

    it('should reject invalid file types', async () => {
      const content = 'executable content'
      const blob = new Blob([content], { type: 'application/x-executable' })
      const file = new File([blob], 'malicious.exe', {
        type: 'application/x-executable',
      })

      const uploadRequest: DocumentUploadRequest = {
        file,
      }

      await expect(client.uploadFile(uploadRequest)).rejects.toThrow(ValidationError)
    })
  })

  // ============================================================================
  // Document API Tests
  // ============================================================================

  describe('Document API', () => {
    beforeEach(() => {
      client.setAuthToken(authToken!)
    })

    it('should fetch list of documents', async () => {
      const documents = await client.getDocuments({ limit: 10 })

      expect(Array.isArray(documents)).toBe(true)
      if (documents.length > 0) {
        expect(documents[0].id).toBeDefined()
        expect(documents[0].filename).toBeDefined()
      }
    }, TEST_TIMEOUT)

    it('should filter documents by type', async () => {
      const documents = await client.getDocuments({
        document_type: 'pdf',
        limit: 5,
      })

      expect(Array.isArray(documents)).toBe(true)
      documents.forEach((doc) => {
        if (doc.document_type) {
          expect(doc.document_type).toBe('pdf')
        }
      })
    }, TEST_TIMEOUT)

    it('should paginate document results', async () => {
      const page1 = await client.getDocuments({ limit: 5, skip: 0 })
      const page2 = await client.getDocuments({ limit: 5, skip: 5 })

      expect(Array.isArray(page1)).toBe(true)
      expect(Array.isArray(page2)).toBe(true)

      // If there are enough documents, pages should be different
      if (page1.length === 5 && page2.length > 0) {
        expect(page1[0].id).not.toBe(page2[0].id)
      }
    }, TEST_TIMEOUT)
  })

  // ============================================================================
  // Chat API Tests
  // ============================================================================

  describe('Chat API', () => {
    beforeEach(() => {
      client.setAuthToken(authToken!)
    })

    it('should send a chat message', async () => {
      const chatRequest = {
        message: 'Hello, this is a test message',
        context: ['test-context'],
      }

      const response = await client.sendChatMessage(chatRequest)

      expect(response).toBeDefined()
      expect(response.id).toBeDefined()
      expect(response.message).toBeDefined()
      expect(response.role).toBe('assistant')
      expect(response.session_id).toBeDefined()
    }, TEST_TIMEOUT)

    it('should maintain session across multiple messages', async () => {
      const message1 = await client.sendChatMessage({
        message: 'First message',
      })

      const sessionId = message1.session_id

      const message2 = await client.sendChatMessage({
        message: 'Second message',
        session_id: sessionId,
      })

      expect(message2.session_id).toBe(sessionId)
    }, TEST_TIMEOUT)
  })

  // ============================================================================
  // Singleton Instance Tests
  // ============================================================================

  describe('Singleton API Client', () => {
    it('should export a singleton instance', () => {
      expect(apiClient).toBeDefined()
      expect(apiClient).toBeInstanceOf(APIClient)
    })

    it('should share state across singleton instance', () => {
      apiClient.setAuthToken('test-token-singleton')

      const token = apiClient.getAuthToken()
      expect(token).toBe('test-token-singleton')

      apiClient.logout()
    })
  })
})
