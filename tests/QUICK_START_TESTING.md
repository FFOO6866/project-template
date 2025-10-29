# Quick Start: Production Validation Testing

**5-Minute Guide to Running Tests**

## 🚀 Fastest Path to Testing

### Option 1: Run Unit Tests Only (No Infrastructure Required)

```bash
# Fast validation (< 20 seconds)
python tests/run_production_validation_tests.py unit
```

**When to use:** Quick validation before commits, no Docker needed

---

### Option 2: Run Complete Test Suite (Recommended)

```bash
# Complete validation (< 3 minutes)
python tests/run_production_validation_tests.py all
```

**When to use:** Before pushing to remote, pre-deployment validation

---

### Option 3: Manual Tier Execution

```bash
# Tier 1: Unit tests (<1s each)
pytest tests/unit/test_production_compliance.py -v --timeout=1

# Tier 2: Integration tests (<5s each)
# Requires Docker infrastructure
docker-compose -f tests/utils/docker-compose.test.yml up -d postgres redis
pytest tests/integration/test_real_database_queries.py -v --timeout=5 -m integration

# Tier 3: E2E tests (<10s each)
# Requires complete Docker stack
docker-compose -f docker-compose.test.yml up -d
pytest tests/e2e/test_production_workflows.py -v --timeout=10 -m e2e
```

---

## 🐳 Docker Infrastructure Setup

### Quick Start

```bash
# Start test infrastructure (PostgreSQL + Redis)
cd tests/utils
docker-compose -f docker-compose.test.yml up -d postgres redis

# Verify running
docker-compose -f docker-compose.test.yml ps

# Check health
docker ps --filter name=horme_pov_test
```

### Troubleshooting

```bash
# View logs
docker-compose -f tests/utils/docker-compose.test.yml logs postgres redis

# Restart services
docker-compose -f tests/utils/docker-compose.test.yml restart

# Stop and clean
docker-compose -f tests/utils/docker-compose.test.yml down -v
```

---

## 📊 Expected Output

### Successful Test Run

```
================================================================================
                     TIER 1: Unit Tests - Production Compliance
================================================================================

ℹ️  Speed: <1 second per test
ℹ️  Isolation: No external dependencies
ℹ️  Focus: Fail-fast validation, no mock data detection

tests/unit/test_production_compliance.py::TestProductMatchingWorkflowFailFast::test_workflow_requires_database_url PASSED
tests/unit/test_production_compliance.py::TestProductMatchingWorkflowFailFast::test_workflow_fails_on_invalid_database_url PASSED
...

✅ Tier 1 tests PASSED in 15.23s

================================================================================
                          TEST EXECUTION SUMMARY
================================================================================

Results:
  Tier 1: PASSED (15.23s)
  Tier 2: PASSED (68.45s)
  Tier 3: PASSED (95.12s)

Summary:
  Total Tests: 3 tiers
  Passed: 3
  Failed: 0
  Total Time: 178.80s

✅ ALL TESTS PASSED - PRODUCTION READY
```

---

## 🎯 What Each Tier Tests

### Tier 1: Unit Tests (tests/unit/test_production_compliance.py)

**Tests that code follows production standards:**
- ✅ Fails fast when DATABASE_URL not configured
- ✅ Fails fast when Redis not available
- ✅ Detects mock data patterns
- ✅ Detects hardcoded credentials
- ✅ Validates error messages are clear

**No infrastructure needed** - runs in seconds

---

### Tier 2: Integration Tests (tests/integration/test_real_database_queries.py)

**Tests real database operations:**
- ✅ Real PostgreSQL queries return real data
- ✅ Real Redis caching works correctly
- ✅ Product searches use database, not mocks
- ✅ Empty results return [], not fallback data

**Requires Docker** - PostgreSQL (port 5434) + Redis (port 6380)

---

### Tier 3: E2E Tests (tests/e2e/test_production_workflows.py)

**Tests complete workflows:**
- ✅ Complete RFP processing (doc → products → quotation)
- ✅ Product matching returns real SKUs from database
- ✅ API endpoints return real data or fail-fast
- ✅ Data integrity throughout workflow

**Requires complete Docker stack**

---

## ⚡ Common Commands

```bash
# Run only unit tests (fast)
python tests/run_production_validation_tests.py unit

# Run only integration tests
python tests/run_production_validation_tests.py integration

# Run only E2E tests
python tests/run_production_validation_tests.py e2e

# Run everything
python tests/run_production_validation_tests.py all

# Run specific test file
pytest tests/unit/test_production_compliance.py -v

# Run specific test class
pytest tests/unit/test_production_compliance.py::TestProductMatchingWorkflowFailFast -v

# Run specific test
pytest tests/unit/test_production_compliance.py::TestProductMatchingWorkflowFailFast::test_workflow_requires_database_url -v

# Show verbose output
pytest tests/unit/test_production_compliance.py -vv

# Show print statements
pytest tests/unit/test_production_compliance.py -s

# Stop on first failure
pytest tests/unit/test_production_compliance.py -x
```

---

## 🔧 Fixing Common Issues

### Issue: "Docker not running"

```bash
# Start Docker Desktop
# Then verify:
docker ps

# Start test infrastructure:
cd tests/utils
docker-compose -f docker-compose.test.yml up -d
```

### Issue: "Port already in use"

```bash
# PostgreSQL port 5434 or Redis port 6380 in use

# Find what's using the port:
netstat -ano | findstr :5434
netstat -ano | findstr :6380

# Stop conflicting service or change port in docker-compose.test.yml
```

### Issue: "Tests fail with 'DATABASE_URL not set'"

```bash
# For integration/E2E tests, ensure infrastructure is running:
docker-compose -f tests/utils/docker-compose.test.yml up -d postgres redis

# Verify:
docker ps --filter name=horme_pov_test_postgres
docker ps --filter name=horme_pov_test_redis
```

### Issue: "Import errors"

```bash
# Ensure in project root:
cd /c/Users/fujif/OneDrive/Documents/GitHub/horme-pov

# Install dependencies:
pip install -r requirements-test.txt
# or
uv pip install -r tests/requirements-test.txt
```

---

## 📋 Pre-Commit Checklist

Before committing code, run:

```bash
# 1. Quick unit tests (<20s)
python tests/run_production_validation_tests.py unit

# 2. If passing, commit
git add .
git commit -m "Your message"
```

---

## 📋 Pre-Push Checklist

Before pushing to remote, run:

```bash
# 1. Start infrastructure
cd tests/utils
docker-compose -f docker-compose.test.yml up -d postgres redis

# 2. Run complete test suite
cd ../..
python tests/run_production_validation_tests.py all

# 3. If all pass, push
git push origin main
```

---

## 🎓 Learn More

- **Full Documentation:** `tests/PRODUCTION_VALIDATION_TESTING_SUMMARY.md`
- **Testing Strategy:** `tests/COMPREHENSIVE_3_TIER_TESTING_STRATEGY.md`
- **Production Standards:** `CLAUDE.md` (see PRODUCTION CODE QUALITY STANDARDS)

---

**Need Help?**

Run with verbose output to see what's happening:

```bash
pytest tests/unit/test_production_compliance.py -vv -s
```

Or check the comprehensive summary:

```bash
cat tests/PRODUCTION_VALIDATION_TESTING_SUMMARY.md
```
