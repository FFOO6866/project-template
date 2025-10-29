# Frontend Testing Quick Start Guide

## 5-Minute Setup

### 1. Start Docker Services (2 minutes)

```bash
# From project root
cd /c/Users/fujif/OneDrive/Documents/GitHub/horme-pov

# Start all backend services
docker-compose -f docker-compose.production.yml up -d

# Verify services are running
docker-compose -f docker-compose.production.yml ps
```

**Expected output:**
```
NAME                STATUS              PORTS
horme-api           Up (healthy)        0.0.0.0:8000->8000/tcp
horme-websocket     Up (healthy)        0.0.0.0:8001->8001/tcp
postgres            Up (healthy)        0.0.0.0:5433->5432/tcp
redis               Up (healthy)        0.0.0.0:6380->6379/tcp
```

### 2. Configure Test Environment (1 minute)

```bash
cd frontend

# Copy environment template
cp .env.test .env.test.local

# Verify configuration (should work with defaults)
cat .env.test.local
```

### 3. Install Dependencies (1 minute)

```bash
# Install frontend dependencies (if not already installed)
npm install
```

### 4. Run Tests (1 minute)

```bash
# Run all tests
npm test

# Or run specific test suites
npm test tests/integration/api-client.test.ts
npm test tests/integration/websocket.test.ts
npm test tests/e2e/chat-flow.test.ts
```

---

## Verify Everything Works

### Test 1: API Health Check

```bash
curl http://localhost:8000/health
```

**Expected:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-21T...",
  "services": {
    "database": "up",
    "redis": "up"
  }
}
```

### Test 2: WebSocket Connection

```bash
# Test WebSocket health (should return 426 Upgrade Required for HTTP)
curl -i http://localhost:8001/
```

**Expected:**
```
HTTP/1.1 426 Upgrade Required
```

### Test 3: Run Single Integration Test

```bash
npm test -- tests/integration/api-client.test.ts --testNamePattern="Health Check"
```

**Expected:**
```
PASS  tests/integration/api-client.test.ts
  API Client Integration Tests
    Health Check
      ✓ should successfully check API health (XXXms)
```

---

## Common Quick Fixes

### Services Not Running

```bash
# Restart all services
docker-compose -f docker-compose.production.yml restart

# Or rebuild and restart
docker-compose -f docker-compose.production.yml up -d --build
```

### Test User Missing

```bash
# Create test user in database
docker exec -it horme-postgres psql -U horme_user -d horme_db -c "
INSERT INTO users (email, password, name, role, created_at, updated_at)
VALUES (
  'test@horme.com',
  '\$2b\$12\$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYL3ZL5uJke',
  'Test User',
  'user',
  NOW(),
  NOW()
) ON CONFLICT (email) DO NOTHING;
"
```

### Port Conflicts

```bash
# Check what's using ports
netstat -ano | findstr "8000"
netstat -ano | findstr "8001"

# Kill process or change ports in .env.production
```

---

## Test Commands Cheat Sheet

```bash
# Run all tests
npm test

# Run integration tests only
npm test tests/integration/

# Run E2E tests only
npm test tests/e2e/

# Run with coverage
npm test -- --coverage

# Run in watch mode
npm test -- --watch

# Run specific test file
npm test tests/integration/api-client.test.ts

# Run specific test suite
npm test -- --testNamePattern="Authentication"

# Verbose output
npm test -- --verbose

# Debug mode
npm test -- --detectOpenHandles --verbose
```

---

## Troubleshooting in 30 Seconds

### Problem: Tests fail with "Connection refused"

```bash
# Check services
docker-compose -f docker-compose.production.yml ps

# Restart if needed
docker-compose -f docker-compose.production.yml restart
```

### Problem: Tests timeout

```bash
# Increase timeout
npm test -- --testTimeout=30000

# Or check service logs
docker-compose -f docker-compose.production.yml logs horme-api
```

### Problem: Authentication fails

```bash
# Verify test user exists
docker exec -it horme-postgres psql -U horme_user -d horme_db -c "SELECT email FROM users WHERE email='test@horme.com';"

# Create if missing (see "Test User Missing" above)
```

---

## What Gets Tested

### Integration Tests (Tier 2)

✅ **API Client** (`tests/integration/api-client.test.ts`)
- Authentication (login, token management)
- Dashboard data fetching
- Customer CRUD operations
- Quotation CRUD operations
- Document upload/download
- Error handling (404, 401, 422, 500)

✅ **WebSocket** (`tests/integration/websocket.test.ts`)
- Connection management
- Message sending/receiving
- Session management
- Context updates
- Auto-reconnection
- Keep-alive ping/pong

### E2E Tests (Tier 3)

✅ **Complete Workflows** (`tests/e2e/chat-flow.test.ts`)
- Login → WebSocket → Chat
- Document Upload → Chat
- Quotation Creation → Chat
- Context Switching
- Error Recovery
- Performance Tests

---

## Expected Test Duration

| Test Suite | Tests | Duration |
|------------|-------|----------|
| API Client Integration | ~40 tests | 30-60s |
| WebSocket Integration | ~30 tests | 30-60s |
| E2E Chat Flow | ~15 tests | 60-120s |
| **Total** | **~85 tests** | **2-4 minutes** |

---

## Next Steps

1. ✅ Run tests to verify setup
2. 📖 Read `/frontend/tests/README.md` for detailed documentation
3. 🔍 Explore test files to understand patterns
4. ✍️ Write your own tests following the same structure
5. 🚀 Integrate into CI/CD pipeline

---

## Getting Help

- **Full Documentation**: `/frontend/tests/README.md`
- **API Client Guide**: `/frontend/lib/API_CLIENT_README.md`
- **3-Tier Strategy**: `/tests/COMPREHENSIVE_3_TIER_TESTING_STRATEGY.md`

**Remember: NO MOCKING. Real infrastructure. Real confidence.**
