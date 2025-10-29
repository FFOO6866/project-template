#!/bin/bash
# Docker Test Migration Validation Script
# Verifies that all tests are properly configured for Docker-only execution

echo "=========================================="
echo "Docker Test Migration Validation"
echo "=========================================="
echo ""

PASSED=0
FAILED=0

# Function to check test
check() {
    if [ $1 -eq 0 ]; then
        echo "✅ PASS: $2"
        PASSED=$((PASSED + 1))
    else
        echo "❌ FAIL: $2"
        FAILED=$((FAILED + 1))
    fi
}

# 1. Verify no test files in root
echo "1. Checking for test files in project root..."
TEST_COUNT=$(find . -maxdepth 1 -name "test_*.py" 2>/dev/null | wc -l)
if [ "$TEST_COUNT" -eq 0 ]; then
    check 0 "No test files in project root"
else
    check 1 "Found $TEST_COUNT test files in root (should be 0)"
    find . -maxdepth 1 -name "test_*.py"
fi
echo ""

# 2. Verify tests in proper directories
echo "2. Checking for tests in proper directories..."
INTEGRATION_COUNT=$(find tests/integration -name "test_*.py" 2>/dev/null | wc -l)
E2E_COUNT=$(find tests/e2e -name "test_*.py" 2>/dev/null | wc -l)

if [ "$INTEGRATION_COUNT" -ge 7 ]; then
    check 0 "Found $INTEGRATION_COUNT integration tests"
else
    check 1 "Found $INTEGRATION_COUNT integration tests (expected >= 7)"
fi

if [ "$E2E_COUNT" -ge 1 ]; then
    check 0 "Found $E2E_COUNT E2E tests"
else
    check 1 "Found $E2E_COUNT E2E tests (expected >= 1)"
fi
echo ""

# 3. Verify docker-compose.test.yml exists
echo "3. Checking for docker-compose.test.yml..."
if [ -f "docker-compose.test.yml" ]; then
    check 0 "docker-compose.test.yml exists"
    
    # Check for required services
    if grep -q "test-runner:" docker-compose.test.yml; then
        check 0 "test-runner service defined"
    else
        check 1 "test-runner service not found"
    fi
    
    if grep -q "postgres:" docker-compose.test.yml; then
        check 0 "postgres service defined"
    else
        check 1 "postgres service not found"
    fi
    
    if grep -q "redis:" docker-compose.test.yml; then
        check 0 "redis service defined"
    else
        check 1 "redis service not found"
    fi
else
    check 1 "docker-compose.test.yml not found"
fi
echo ""

# 4. Verify conftest.py exists
echo "4. Checking for tests/conftest.py..."
if [ -f "tests/conftest.py" ]; then
    check 0 "tests/conftest.py exists"
    
    # Check for required fixtures
    if grep -q "def configure_docker_environment" tests/conftest.py; then
        check 0 "configure_docker_environment fixture defined"
    else
        check 1 "configure_docker_environment fixture not found"
    fi
    
    if grep -q "def postgres_connection" tests/conftest.py; then
        check 0 "postgres_connection fixture defined"
    else
        check 1 "postgres_connection fixture not found"
    fi
    
    if grep -q "def redis_client" tests/conftest.py; then
        check 0 "redis_client fixture defined"
    else
        check 1 "redis_client fixture not found"
    fi
else
    check 1 "tests/conftest.py not found"
fi
echo ""

# 5. Verify tests/README.md updated
echo "5. Checking for tests/README.md..."
if [ -f "tests/README.md" ]; then
    check 0 "tests/README.md exists"
    
    if grep -q "Docker-Only Test Execution" tests/README.md; then
        check 0 "Docker-only policy documented"
    else
        check 1 "Docker-only policy not documented"
    fi
    
    if grep -q "docker-compose.test.yml" tests/README.md; then
        check 0 "Docker-compose usage documented"
    else
        check 1 "Docker-compose usage not documented"
    fi
else
    check 1 "tests/README.md not found"
fi
echo ""

# 6. Verify migrated test files
echo "6. Checking for migrated test files..."
MIGRATED_FILES=(
    "tests/integration/test_neo4j_integration.py"
    "tests/integration/test_classification_system.py"
    "tests/integration/test_hybrid_recommendations.py"
    "tests/integration/test_safety_compliance.py"
    "tests/integration/test_multilingual_support.py"
    "tests/integration/test_websocket_chat.py"
    "tests/e2e/test_frontend_integration.py"
)

for file in "${MIGRATED_FILES[@]}"; do
    if [ -f "$file" ]; then
        check 0 "$(basename $file) migrated correctly"
    else
        check 1 "$(basename $file) not found in expected location"
    fi
done
echo ""

# Summary
echo "=========================================="
echo "Validation Summary"
echo "=========================================="
echo "✅ Passed: $PASSED"
echo "❌ Failed: $FAILED"
echo "Total:   $((PASSED + FAILED))"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "🎉 ALL VALIDATIONS PASSED!"
    echo "Docker test migration is complete and verified."
    exit 0
else
    echo "⚠️  SOME VALIDATIONS FAILED"
    echo "Please review the failures above."
    exit 1
fi
