#!/bin/bash
# Keyword Mapping Migration Verification Script
#
# This script verifies that the database keyword mapping migration is complete
# and ready for production deployment.
#
# Usage:
#   ./scripts/verify_keyword_migration.sh

set -e

echo "================================================================================"
echo "Database Keyword Mapping Migration Verification"
echo "================================================================================"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track results
PASSED=0
FAILED=0
WARNINGS=0

# Function to print success
success() {
    echo -e "${GREEN}✅ $1${NC}"
    ((PASSED++))
}

# Function to print failure
failure() {
    echo -e "${RED}❌ $1${NC}"
    ((FAILED++))
}

# Function to print warning
warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    ((WARNINGS++))
}

echo "Step 1: Verifying Database Schema"
echo "--------------------------------------------------------------------------------"

# Check if database is accessible
if psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "SELECT 1" > /dev/null 2>&1; then
    success "PostgreSQL database is accessible"
else
    failure "Cannot connect to PostgreSQL database"
    echo "Check POSTGRES_* environment variables"
    exit 1
fi

# Check if category_keyword_mappings table exists
if psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "\dt category_keyword_mappings" | grep -q "category_keyword_mappings"; then
    success "Table 'category_keyword_mappings' exists"
else
    failure "Table 'category_keyword_mappings' not found"
    echo "Run: psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -f init-scripts/unified-postgresql-schema.sql"
    exit 1
fi

# Check if task_keyword_mappings table exists
if psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "\dt task_keyword_mappings" | grep -q "task_keyword_mappings"; then
    success "Table 'task_keyword_mappings' exists"
else
    failure "Table 'task_keyword_mappings' not found"
    echo "Run: psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -f init-scripts/unified-postgresql-schema.sql"
    exit 1
fi

echo ""
echo "Step 2: Verifying Data Population"
echo "--------------------------------------------------------------------------------"

# Check category keyword count
CATEGORY_COUNT=$(psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -t -c "SELECT COUNT(*) FROM category_keyword_mappings")
if [ "$CATEGORY_COUNT" -gt 0 ]; then
    success "Category keyword mappings loaded: $CATEGORY_COUNT records"
else
    failure "No category keyword mappings found"
    echo "Run: python scripts/load_category_task_mappings.py"
    exit 1
fi

# Check task keyword count
TASK_COUNT=$(psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -t -c "SELECT COUNT(*) FROM task_keyword_mappings")
if [ "$TASK_COUNT" -gt 0 ]; then
    success "Task keyword mappings loaded: $TASK_COUNT records"
else
    failure "No task keyword mappings found"
    echo "Run: python scripts/load_category_task_mappings.py"
    exit 1
fi

# Check for minimum expected data
if [ "$CATEGORY_COUNT" -lt 15 ]; then
    warning "Expected at least 15 category keyword mappings, found $CATEGORY_COUNT"
fi

if [ "$TASK_COUNT" -lt 5 ]; then
    warning "Expected at least 5 task keyword mappings, found $TASK_COUNT"
fi

echo ""
echo "Step 3: Verifying Code Changes"
echo "--------------------------------------------------------------------------------"

# Check if hardcoded dictionaries are removed
if grep -q "category_keywords = {" src/ai/hybrid_recommendation_engine.py; then
    failure "Hardcoded category_keywords dictionary still exists in hybrid_recommendation_engine.py"
else
    success "Hardcoded category_keywords dictionary removed"
fi

if grep -q "'drill': 'task_drill_hole'" src/ai/hybrid_recommendation_engine.py; then
    failure "Hardcoded task_keywords dictionary still exists in hybrid_recommendation_engine.py"
else
    success "Hardcoded task_keywords dictionary removed"
fi

# Check if database loading methods exist
if grep -q "_load_category_keywords_from_db" src/ai/hybrid_recommendation_engine.py; then
    success "Database loading method '_load_category_keywords_from_db' exists"
else
    failure "Database loading method '_load_category_keywords_from_db' not found"
fi

if grep -q "_load_task_keywords_from_db" src/ai/hybrid_recommendation_engine.py; then
    success "Database loading method '_load_task_keywords_from_db' exists"
else
    failure "Database loading method '_load_task_keywords_from_db' not found"
fi

echo ""
echo "Step 4: Verifying Test Suite"
echo "--------------------------------------------------------------------------------"

# Check if test script exists
if [ -f "scripts/test_database_keyword_loading.py" ]; then
    success "Test script exists: test_database_keyword_loading.py"

    # Run tests
    if python scripts/test_database_keyword_loading.py > /tmp/keyword_test_output.log 2>&1; then
        success "Test suite passed"
        cat /tmp/keyword_test_output.log | grep -E "(PASSED|FAILED|SKIPPED)"
    else
        failure "Test suite failed"
        cat /tmp/keyword_test_output.log
        exit 1
    fi
else
    failure "Test script not found: scripts/test_database_keyword_loading.py"
fi

echo ""
echo "Step 5: Verifying Documentation"
echo "--------------------------------------------------------------------------------"

# Check if documentation exists
if [ -f "docs/DATABASE_KEYWORD_MAPPINGS.md" ]; then
    success "Documentation exists: docs/DATABASE_KEYWORD_MAPPINGS.md"
else
    warning "Documentation not found: docs/DATABASE_KEYWORD_MAPPINGS.md"
fi

if [ -f "DATABASE_KEYWORD_MIGRATION_COMPLETE.md" ]; then
    success "Migration summary exists: DATABASE_KEYWORD_MIGRATION_COMPLETE.md"
else
    warning "Migration summary not found: DATABASE_KEYWORD_MIGRATION_COMPLETE.md"
fi

echo ""
echo "Step 6: Sample Data Verification"
echo "--------------------------------------------------------------------------------"

echo "Category keyword mappings (sample):"
psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "
    SELECT category, ARRAY_AGG(keyword ORDER BY keyword) as keywords
    FROM category_keyword_mappings
    GROUP BY category
    ORDER BY category
    LIMIT 5
" | grep -v "^-" | grep -v "row"

echo ""
echo "Task keyword mappings (sample):"
psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "
    SELECT keyword, task_id
    FROM task_keyword_mappings
    ORDER BY keyword
    LIMIT 5
" | grep -v "^-" | grep -v "row"

echo ""
echo "================================================================================"
echo "Verification Summary"
echo "================================================================================"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo -e "${YELLOW}Warnings: $WARNINGS${NC}"
echo ""

if [ $FAILED -gt 0 ]; then
    echo -e "${RED}❌ VERIFICATION FAILED${NC}"
    echo "Please fix the issues above before deploying to production"
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}⚠️  VERIFICATION PASSED WITH WARNINGS${NC}"
    echo "Review warnings above, but migration is complete"
    exit 0
else
    echo -e "${GREEN}✅ VERIFICATION PASSED${NC}"
    echo "Migration is complete and ready for production deployment"
    exit 0
fi
