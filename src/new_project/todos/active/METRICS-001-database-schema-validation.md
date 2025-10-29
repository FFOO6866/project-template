# METRICS-001-Database-Schema-Validation

## Description
Validate and fix database schema inconsistencies between production databases (sales_assistant.db, quotations.db, documents.db) to ensure proper business metrics data flow.

## Current Issue Analysis
- `sales_assistant.db` has customers table but schema differs from production_business_metrics_server.py expectations
- `quotations.db` exists but may not have proper quotations table structure
- `documents.db` schema needs validation for recent document tracking
- Health check showing "no such table: customers" error indicates schema mismatch

## Acceptance Criteria
- [ ] All three databases have consistent, validated schemas
- [ ] production_business_metrics_server.py can connect without errors
- [ ] Health check endpoint returns successful database connections
- [ ] All required tables exist with proper foreign key relationships
- [ ] Sample data populated for testing business metrics

## Dependencies
- Production business metrics server (running on port 3002)
- Database files: sales_assistant.db, quotations.db, documents.db

## Risk Assessment
- **HIGH**: Schema mismatches could cause complete metrics failure
- **MEDIUM**: Data migration may be needed if tables exist with different structure
- **LOW**: SQLite corruption risk minimal with proper backup strategy

## Subtasks
- [ ] Database Schema Audit (Est: 30min) - Compare actual vs. expected schemas
  - Verification: All required tables and columns identified
- [ ] Schema Migration Script (Est: 45min) - Create script to fix schema issues
  - Verification: Migration script runs without errors
- [ ] Data Validation (Est: 30min) - Ensure referential integrity and sample data
  - Verification: Foreign keys work, sample data exists for all tables
- [ ] Connection Testing (Est: 15min) - Test all database connections from metrics server
  - Verification: Health check returns "connected" for all databases

## Testing Requirements
- [ ] Unit tests: Database connection and schema validation
- [ ] Integration tests: Metrics server can query all databases successfully
- [ ] E2E tests: Full metrics API endpoints return valid business data

## Definition of Done
- [ ] All acceptance criteria met
- [ ] production_business_metrics_server.py health check succeeds
- [ ] No database connection errors in logs
- [ ] Business metrics APIs return real data from all three databases
- [ ] Database schema matches production_business_metrics_server.py expectations

## Specialist Assignment
- **dataflow-specialist**: Handle database schema design and migration
- **testing-specialist**: Create database validation tests
- **infrastructure-validation**: Verify production database connections

## Execution Commands
```bash
# 1. Schema validation
python -c "import sqlite3; [print(f'{db}: {sqlite3.connect(db).execute(\"SELECT name FROM sqlite_master WHERE type=\\\"table\\\"\").fetchall()}') for db in ['sales_assistant.db', 'quotations.db', 'documents.db']]"

# 2. Run database schema fix
python src/new_project/fix_database_schemas.py

# 3. Test metrics server connection
curl http://localhost:3002/health

# 4. Validate business metrics
curl http://localhost:3002/metrics/business
```