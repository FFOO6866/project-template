# Frontend Integration and E2E Testing Guide

## Overview

This directory contains comprehensive integration and end-to-end tests for the Horme POV frontend application, following the Kailash SDK's rigorous 3-tier testing strategy.

**CRITICAL: NO MOCKING in Integration/E2E Tests**

All Tier 2 (Integration) and Tier 3 (E2E) tests connect to **REAL Docker services**. No mock data, no stubbed responses, no fake implementations.

---

## Test Structure

```
frontend/tests/
├── setup/                          # Test configuration
│   ├── jest.config.js             # Jest configuration
│   ├── jest.setup.ts              # Global test setup
│   └── __mocks__/                 # Static asset mocks only
│       ├── styleMock.js
│       └── fileMock.js
├── integration/                    # Tier 2: Integration tests
│   ├── api-client.test.ts         # API client integration tests
│   └── websocket.test.ts          # WebSocket integration tests
└── e2e/                           # Tier 3: End-to-end tests
    └── chat-flow.test.ts          # Complete chat workflow tests
```

---

## 3-Tier Testing Strategy

### Tier 1: Unit Tests (NOT INCLUDED HERE)
- Fast (<1s per test)
- Mocking allowed for external dependencies
- Tests individual components in isolation
- Location: Component files with `.test.tsx` suffix

### Tier 2: Integration Tests (`tests/integration/`)
- Real Docker services (**NO MOCKING**)
- Timeout: <5s per test
- Tests component interactions with backend
- Real HTTP/WebSocket connections
- Real database operations

**Test Files:**
- `api-client.test.ts` - API authentication, CRUD operations, error handling
- `websocket.test.ts` - WebSocket connection, messaging, auto-reconnection

### Tier 3: E2E Tests (`tests/e2e/`)
- Complete real infrastructure stack
- Timeout: <10-15s per test
- Tests complete user workflows
- Real authentication → upload → chat workflows

**Test Files:**
- `chat-flow.test.ts` - Complete chat workflows from login to interaction

---

## Prerequisites

### 1. Docker Infrastructure

**Start backend services:**

```bash
# From project root
docker-compose -f docker-compose.production.yml up -d

# Verify services are healthy
docker-compose -f docker-compose.production.yml ps
```

**Required services:**
- `horme-api` - Backend API (port 8000)
- `horme-websocket` - WebSocket server (port 8001)
- `postgres` - PostgreSQL database (port 5433)
- `redis` - Redis cache (port 6380)

### 2. Test Environment Configuration

Create `.env.test.local` from `.env.test`:

```bash
cd frontend
cp .env.test .env.test.local
```

**Configure test environment variables:**

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WEBSOCKET_URL=ws://localhost:8001

# Test User Credentials
TEST_USER_EMAIL=test@horme.com
TEST_USER_PASSWORD=TestPassword123!

# Test Timeouts
TEST_API_TIMEOUT=5000
TEST_WEBSOCKET_TIMEOUT=10000
```

### 3. Test Database Setup

**Create test user in PostgreSQL:**

```bash
# Connect to PostgreSQL container
docker exec -it horme-postgres psql -U horme_user -d horme_db

# Create test user
INSERT INTO users (email, password, name, role, created_at, updated_at)
VALUES (
  'test@horme.com',
  '$2b$12$hashed_password_here',  -- Use bcrypt to hash 'TestPassword123!'
  'Test User',
  'user',
  NOW(),
  NOW()
);
```

### 4. Install Dependencies

```bash
cd frontend

# Install test dependencies
npm install --save-dev \
  @testing-library/react \
  @testing-library/jest-dom \
  @testing-library/react-hooks \
  @swc/jest \
  jest \
  jest-environment-jsdom

# Or if using package.json
npm install
```

---

## Running Tests

### Quick Start

```bash
cd frontend

# Run all integration and E2E tests
npm test

# Run specific test tier
npm test tests/integration/
npm test tests/e2e/

# Run specific test file
npm test tests/integration/api-client.test.ts
npm test tests/integration/websocket.test.ts
npm test tests/e2e/chat-flow.test.ts
```

### Detailed Commands

```bash
# Run with coverage
npm test -- --coverage

# Run in watch mode (for development)
npm test -- --watch

# Run with verbose output
npm test -- --verbose

# Run specific test suite
npm test -- --testNamePattern="Authentication"

# Run with timeout override
npm test -- --testTimeout=20000
```

### CI/CD Pipeline

```bash
# Full test suite for CI
npm run test:ci

# This runs:
# 1. Linting
# 2. Type checking
# 3. Integration tests
# 4. E2E tests
# 5. Coverage report
```

---

## Test Coverage

### Coverage Requirements

- **Branches**: 70%
- **Functions**: 70%
- **Lines**: 70%
- **Statements**: 70%

### Generate Coverage Report

```bash
npm test -- --coverage --coverageDirectory=coverage

# View HTML report
open coverage/lcov-report/index.html  # macOS
start coverage/lcov-report/index.html # Windows
```

---

## Test Files Overview

### 1. API Client Integration Tests (`integration/api-client.test.ts`)

**What it tests:**
- ✅ Health check endpoint
- ✅ User authentication (login, token management)
- ✅ Dashboard data fetching
- ✅ Customer CRUD operations
- ✅ Quotation CRUD operations
- ✅ Document upload and retrieval
- ✅ File validation (size, type)
- ✅ Error handling (404, 401, 422, 500)
- ✅ Request retry logic
- ✅ Authentication header injection

**Prerequisites:**
- Backend API running on port 8000
- PostgreSQL database with test data
- Test user credentials

**Example:**
```typescript
describe('Authentication', () => {
  it('should successfully login with valid credentials', async () => {
    const response = await client.login({
      email: TEST_USER_EMAIL,
      password: TEST_USER_PASSWORD,
    })

    expect(response.access_token).toBeDefined()
    expect(response.user.email).toBe(TEST_USER_EMAIL)
  })
})
```

### 2. WebSocket Integration Tests (`integration/websocket.test.ts`)

**What it tests:**
- ✅ WebSocket connection establishment
- ✅ Authentication flow
- ✅ Message sending/receiving
- ✅ Session management
- ✅ Context updates (document, quotation)
- ✅ Message history retrieval
- ✅ Auto-reconnection logic
- ✅ Keep-alive ping/pong
- ✅ Error handling
- ✅ Event callbacks (onOpen, onClose, onMessage)

**Prerequisites:**
- WebSocket server running on port 8001
- Redis for session storage
- Backend API for authentication

**Example:**
```typescript
describe('Message Sending', () => {
  it('should send a chat message', async () => {
    await waitForConnection(result, 'connected')

    act(() => {
      result.current.sendMessage('Hello from test')
    })

    await waitForMessage(
      result,
      (msg) => msg?.type === 'message'
    )

    expect(result.current.lastMessage?.type).toBe('message')
  })
})
```

### 3. E2E Chat Flow Tests (`e2e/chat-flow.test.ts`)

**What it tests:**
- ✅ Complete login → WebSocket → chat workflow
- ✅ Document upload → context setting → chat
- ✅ Quotation creation → context setting → chat
- ✅ Multi-document comparison workflows
- ✅ Context switching (document ↔ quotation)
- ✅ Error recovery scenarios
- ✅ Session persistence across messages
- ✅ Performance with rapid messages
- ✅ Long conversation history handling

**Prerequisites:**
- Complete Docker stack (API, WebSocket, PostgreSQL, Redis)
- All services healthy
- Test user authenticated

**Example:**
```typescript
describe('Document Upload → Chat Interaction', () => {
  it('should upload document → set context → chat about document', async () => {
    // Step 1: Upload document
    const uploadResponse = await apiClient.uploadFile({ file })

    // Step 2: Connect WebSocket with document context
    const { result } = renderHook(() =>
      useWebSocket({
        context: { type: 'document', document_id: uploadResponse.document_id }
      })
    )

    // Step 3: Chat about document
    act(() => {
      result.current.sendMessage('Analyze this document')
    })

    // Step 4: Verify AI response
    expect(result.current.lastMessage?.message?.type).toBe('ai')
  })
})
```

---

## Common Issues and Solutions

### Issue: "Connection refused" errors

**Cause:** Backend services not running

**Solution:**
```bash
# Check service status
docker-compose -f docker-compose.production.yml ps

# Restart services
docker-compose -f docker-compose.production.yml up -d

# Check logs
docker-compose -f docker-compose.production.yml logs horme-api
docker-compose -f docker-compose.production.yml logs horme-websocket
```

### Issue: "Authentication failed" in tests

**Cause:** Test user not created in database

**Solution:**
```bash
# Create test user (see Prerequisites section)
docker exec -it horme-postgres psql -U horme_user -d horme_db

# Or run database seed script
docker exec -it horme-postgres psql -U horme_user -d horme_db -f /init-scripts/seed-test-data.sql
```

### Issue: Tests timeout

**Cause:** Services slow to respond or not healthy

**Solution:**
```bash
# Check service health
docker-compose -f docker-compose.production.yml ps

# Restart unhealthy services
docker-compose -f docker-compose.production.yml restart horme-api

# Increase test timeout
npm test -- --testTimeout=30000
```

### Issue: WebSocket connection fails

**Cause:** WebSocket server not running or wrong URL

**Solution:**
```bash
# Check WebSocket server
curl -i http://localhost:8001/health

# Verify environment variable
echo $NEXT_PUBLIC_WEBSOCKET_URL

# Update .env.test.local
NEXT_PUBLIC_WEBSOCKET_URL=ws://localhost:8001
```

### Issue: File upload tests fail

**Cause:** File size limits or permission issues

**Solution:**
```bash
# Check backend upload limits
docker exec horme-api cat /app/src/core/config.py | grep MAX_UPLOAD_SIZE

# Check disk space
df -h
```

---

## Best Practices

### 1. NO MOCKING in Integration/E2E Tests

```typescript
// ❌ WRONG - Don't mock in integration tests
jest.mock('@/lib/api-client')

// ✅ CORRECT - Use real API client
import { APIClient } from '@/lib/api-client'
const client = new APIClient()
```

### 2. Always Clean Up

```typescript
// Use beforeAll/afterAll for setup/cleanup
afterAll(() => {
  apiClient.logout()
  unmount()
})
```

### 3. Use waitFor for Async Operations

```typescript
// ✅ CORRECT - Wait for async state changes
await waitFor(() => {
  expect(result.current.isConnected).toBe(true)
}, { timeout: 5000 })

// ❌ WRONG - Direct assertion on async state
expect(result.current.isConnected).toBe(true)
```

### 4. Test Real Error Scenarios

```typescript
// Test actual error responses from backend
await expect(client.getDocument(999999)).rejects.toThrow(NotFoundError)
```

### 5. Verify Real Data Flows

```typescript
// Upload real file → verify in database
const upload = await client.uploadFile({ file })
const document = await client.getDocument(upload.document_id)
expect(document.filename).toBe(file.name)
```

---

## Performance Benchmarks

### Target Performance

| Test Tier | Timeout | Avg Duration | Max Duration |
|-----------|---------|--------------|--------------|
| Integration | 5s | 1-2s | 5s |
| E2E | 15s | 5-10s | 15s |

### Performance Optimization

```bash
# Run tests in parallel
npm test -- --maxWorkers=4

# Skip slow tests in development
npm test -- --testPathIgnorePatterns=e2e

# Profile slow tests
npm test -- --verbose --detectOpenHandles
```

---

## Continuous Integration

### GitHub Actions Example

```yaml
name: Frontend Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Start Docker services
        run: docker-compose -f docker-compose.production.yml up -d

      - name: Wait for services
        run: |
          timeout 60 bash -c 'until curl -f http://localhost:8000/health; do sleep 2; done'

      - name: Install dependencies
        working-directory: ./frontend
        run: npm ci

      - name: Run integration tests
        working-directory: ./frontend
        run: npm test tests/integration/ -- --coverage

      - name: Run E2E tests
        working-directory: ./frontend
        run: npm test tests/e2e/

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## Resources

- **3-Tier Testing Strategy**: `/tests/COMPREHENSIVE_3_TIER_TESTING_STRATEGY.md`
- **API Client Documentation**: `/frontend/lib/API_CLIENT_README.md`
- **WebSocket Hook Documentation**: `/frontend/hooks/use-websocket.ts`
- **Backend API Documentation**: `/src/api/README.md`

---

## Support

For issues or questions:

1. Check Docker service logs: `docker-compose -f docker-compose.production.yml logs`
2. Verify test environment: `.env.test.local`
3. Review test output: `npm test -- --verbose`
4. Check database state: `docker exec -it horme-postgres psql -U horme_user -d horme_db`

**Remember: NO MOCKING. Real infrastructure. Real confidence.**
