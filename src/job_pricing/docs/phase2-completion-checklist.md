# Phase 2 Completion Checklist

## 📋 Overview

This checklist contains the final steps to complete **Phase 2: Database & Data Models**. These tasks are currently blocked by Docker connectivity issues but are ready to execute once Docker Desktop is operational.

**Current Phase 2 Status**: 90% Complete

**Remaining Tasks**: All require Docker containers to be running

---

## ⚠️ Prerequisites

### 1. Verify Docker Desktop is Running

```bash
# Check Docker service status
docker ps

# Expected: Should show running containers or empty list (no errors)
```

If Docker Desktop is not running, follow troubleshooting steps in `docs/docker-troubleshooting.md`.

### 2. Start Docker Containers

```bash
cd C:\Users\fujif\OneDrive\Documents\GitHub\rrrr\src\job_pricing

# Start all services (PostgreSQL, Redis, API, Celery)
docker-compose up -d --build

# Verify all containers are running
docker-compose ps
```

**Expected Output**:
```
NAME                                    STATUS
job-pricing-engine-api                  Up
job-pricing-engine-celery-beat          Up
job-pricing-engine-celery-worker        Up
job-pricing-engine-postgres             Up
job-pricing-engine-redis                Up
```

### 3. Verify PostgreSQL Connection

```bash
# Test database connection
docker-compose exec postgres psql -U job_pricing_user -d job_pricing_db -c "SELECT version();"

# Expected: Should show PostgreSQL version information
```

---

## 🚀 Completion Steps

### Step 1: Generate Alembic Migration

**Purpose**: Create the initial database migration for all 19 tables.

**Command**:
```bash
docker-compose exec api alembic revision --autogenerate -m "Initial schema - 19 tables"
```

**Expected Output**:
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.autogenerate.compare] Detected added table 'location_index'
INFO  [alembic.autogenerate.compare] Detected added table 'grade_salary_bands'
... (17 more tables)
Generating C:\...\alembic\versions\<revision_id>_initial_schema_19_tables.py ... done
```

**Verification**:
```bash
# Check that migration file was created
ls alembic/versions/

# Expected: Should show a new file like "abc123_initial_schema_19_tables.py"
```

**What This Does**:
- Compares SQLAlchemy models with current database state
- Generates Python migration script with `upgrade()` and `downgrade()` functions
- Creates tables, indexes, constraints, and extensions (pgvector, pg_trgm)

---

### Step 2: Review Generated Migration

**Purpose**: Verify that the auto-generated migration is correct before applying it.

**Command**:
```bash
# Open the generated migration file
code alembic/versions/<revision_id>_initial_schema_19_tables.py
```

**What to Check**:
1. ✅ All 19 tables are included:
   - `location_index`
   - `grade_salary_bands`
   - `mercer_job_library`
   - `ssg_job_roles`
   - `ssg_tsc`
   - `ssg_job_role_tsc_mapping`
   - `job_pricing_requests`
   - `job_pricing_results`
   - `scraped_job_listings`
   - `mercer_market_data`
   - `internal_employees`
   - `internal_job_postings`
   - `applicant_profiles`
   - `applicant_applications`
   - `scraped_skills`
   - `company_profiles`
   - `salary_survey_data`
   - `job_price_audit_log`
   - `scraping_audit_log`

2. ✅ PostgreSQL extensions are created:
   ```python
   op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
   op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm";')
   op.execute('CREATE EXTENSION IF NOT EXISTS "vector";')
   ```

3. ✅ Vector columns are created with correct dimensions:
   ```python
   sa.Column('embedding', sqlalchemy.dialects.postgresql.VECTOR(1536), nullable=True)
   ```

4. ✅ Indexes are created for:
   - Foreign keys
   - Frequently queried columns
   - Full-text search columns (GIN indexes)
   - Vector similarity columns (IVFFlat or HNSW indexes)

**If Issues Found**:
- Edit the migration file manually
- Add missing indexes or constraints
- Ensure idempotency (use `IF NOT EXISTS` for extensions)

---

### Step 3: Apply Migration (Upgrade)

**Purpose**: Execute the migration to create all database objects.

**Command**:
```bash
docker-compose exec api alembic upgrade head
```

**Expected Output**:
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> abc123, Initial schema - 19 tables
```

**Verification**:
```bash
# List all tables in the database
docker-compose exec postgres psql -U job_pricing_user -d job_pricing_db -c "\dt"

# Expected: Should show all 19 tables
```

**Check Current Migration Version**:
```bash
docker-compose exec api alembic current
```

**Expected Output**:
```
abc123 (head)
```

---

### Step 4: Verify Database Schema

**Purpose**: Ensure all database objects were created correctly.

**1. Check Extensions**:
```bash
docker-compose exec postgres psql -U job_pricing_user -d job_pricing_db -c "\dx"
```

**Expected Extensions**:
- `uuid-ossp`
- `pg_trgm`
- `vector`

**2. Check Table Counts**:
```bash
docker-compose exec postgres psql -U job_pricing_user -d job_pricing_db -c "
SELECT schemaname, tablename
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
"
```

**Expected**: 19 tables + 1 `alembic_version` table = 20 total

**3. Check Indexes**:
```bash
docker-compose exec postgres psql -U job_pricing_user -d job_pricing_db -c "
SELECT tablename, indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
"
```

**Expected**: Multiple indexes per table (primary keys, foreign keys, search indexes)

**4. Check Foreign Key Constraints**:
```bash
docker-compose exec postgres psql -U job_pricing_user -d job_pricing_db -c "
SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
ORDER BY tc.table_name, kcu.column_name;
"
```

**Expected**: Foreign key relationships between related tables

---

### Step 5: Load Seed Data

**Purpose**: Populate reference tables with initial static data.

**5.1. Load Locations**:
```bash
docker-compose exec postgres psql -U job_pricing_user -d job_pricing_db \
    -f /docker-entrypoint-initdb.d/seeds/01-locations.sql
```

**Expected Output**:
```
INSERT 0 23
```

**Verification**:
```bash
docker-compose exec postgres psql -U job_pricing_user -d job_pricing_db -c "
SELECT COUNT(*) as total_locations
FROM location_index
WHERE country_code = 'SG';
"
```

**Expected**: `23 locations`

**5.2. Load Salary Bands**:
```bash
docker-compose exec postgres psql -U job_pricing_user -d job_pricing_db \
    -f /docker-entrypoint-initdb.d/seeds/02-grade-salary-bands.sql
```

**Expected Output**:
```
INSERT 0 17
```

**Verification**:
```bash
docker-compose exec postgres psql -U job_pricing_user -d job_pricing_db -c "
SELECT COUNT(*) as total_grades
FROM grade_salary_bands;
"
```

**Expected**: `17 grades` (M1-M6, P1-P6, E1-E5)

**5.3. Verify Seed Data**:
```bash
# Check location with highest cost of living
docker-compose exec postgres psql -U job_pricing_user -d job_pricing_db -c "
SELECT location_name, cost_of_living_index
FROM location_index
WHERE country_code = 'SG'
ORDER BY cost_of_living_index DESC
LIMIT 5;
"
```

**Expected**: Singapore CBD locations (1.15 index)

```bash
# Check salary band ranges
docker-compose exec postgres psql -U job_pricing_user -d job_pricing_db -c "
SELECT grade, grade_description, salary_min, salary_max, midpoint
FROM grade_salary_bands
ORDER BY salary_min;
"
```

**Expected**: Ordered list from P1 ($3,000) to E5 ($200,000)

---

### Step 6: Run Integration Tests

**Purpose**: Verify that all repository classes work correctly with the real database.

**6.1. Run All Integration Tests**:
```bash
docker-compose exec api pytest tests/integration/test_repositories.py -v
```

**Expected Output**:
```
tests/integration/test_repositories.py::TestJobPricingRepository::test_create_job_pricing_request PASSED
tests/integration/test_repositories.py::TestJobPricingRepository::test_mark_as_completed PASSED
tests/integration/test_repositories.py::TestJobPricingRepository::test_get_statistics PASSED
tests/integration/test_repositories.py::TestMercerRepository::test_create_mercer_job PASSED
tests/integration/test_repositories.py::TestMercerRepository::test_find_by_family PASSED
... (many more tests)
======================== XX passed in X.XXs ========================
```

**6.2. Run Tests with Coverage**:
```bash
docker-compose exec api pytest tests/integration/test_repositories.py --cov=src.job_pricing.repositories --cov-report=term-missing
```

**Expected Coverage**: >80% for repository modules

**6.3. If Tests Fail**:
- Check error messages for specific failures
- Verify seed data was loaded correctly
- Check database connection settings
- Review repository implementation for bugs

---

### Step 7: Test Migration Downgrade

**Purpose**: Verify that migrations can be safely rolled back.

**7.1. Downgrade One Version**:
```bash
docker-compose exec api alembic downgrade -1
```

**Expected Output**:
```
INFO  [alembic.runtime.migration] Running downgrade abc123 -> , Initial schema - 19 tables
```

**7.2. Verify Tables Are Dropped**:
```bash
docker-compose exec postgres psql -U job_pricing_user -d job_pricing_db -c "\dt"
```

**Expected**: Only `alembic_version` table should remain

**7.3. Upgrade Back to Head**:
```bash
docker-compose exec api alembic upgrade head
```

**Expected Output**:
```
INFO  [alembic.runtime.migration] Running upgrade  -> abc123, Initial schema - 19 tables
```

**7.4. Reload Seed Data**:
```bash
# Re-run seed scripts
docker-compose exec postgres psql -U job_pricing_user -d job_pricing_db \
    -f /docker-entrypoint-initdb.d/seeds/01-locations.sql

docker-compose exec postgres psql -U job_pricing_user -d job_pricing_db \
    -f /docker-entrypoint-initdb.d/seeds/02-grade-salary-bands.sql
```

**7.5. Re-run Integration Tests**:
```bash
docker-compose exec api pytest tests/integration/test_repositories.py -v
```

**Expected**: All tests should pass again

---

### Step 8: Create Database Backup

**Purpose**: Create a backup of the clean database with seed data.

**Command**:
```bash
docker-compose exec postgres pg_dump -U job_pricing_user -d job_pricing_db \
    > backups/job_pricing_db_phase2_baseline.sql
```

**Verification**:
```bash
# Check backup file was created
ls -lh backups/job_pricing_db_phase2_baseline.sql
```

**Why Important**:
- Clean baseline state for development
- Can restore if data gets corrupted
- Starting point for Phase 3 data ingestion

---

### Step 9: Update Phase 2 Documentation

**Purpose**: Mark Phase 2 as complete and document what was accomplished.

**9.1. Update Phase 2 Todo**:
```bash
code todos/active/002-phase2-database.md
```

**Changes**:
- Update progress from `90%` to `100%`
- Mark all remaining tasks as complete
- Add completion date
- Document final statistics (lines of code, number of tests, etc.)

**9.2. Add Phase 2 Summary Section**:

```markdown
## ✅ Phase 2 Complete - 2025-11-11

### Summary Statistics
- **19 Database Tables**: All models implemented with full relationships
- **6 Repository Classes**: BaseRepository + 5 domain-specific repositories
- **2,233+ Lines of Repository Code**: Production-ready CRUD operations
- **478 Lines of Integration Tests**: Comprehensive test coverage
- **40 Seed Records**: 23 locations + 17 salary bands
- **2 Alembic Migrations**: Initial schema + any fixes
- **Vector Search**: pgvector with cosine similarity for job matching
- **Fuzzy Search**: pg_trgm for skill matching
- **PDPA Compliance**: Anonymization for <5 records

### Key Achievements
✅ Complete data model with 19 tables
✅ Repository pattern with generic base class
✅ Vector similarity search for AI embeddings
✅ Fuzzy text search for skill matching
✅ Integration test infrastructure
✅ Real reference data (no mock data)
✅ Alembic migrations with upgrade/downgrade
✅ Docker Compose orchestration
✅ PDPA-compliant employee data access

### Blockers Resolved
- ✅ Docker Desktop connectivity issue (resolved by restart)
- ✅ Alembic migration generation (completed)
- ✅ Integration tests (all passing)
```

**9.3. Move Phase 2 Todo to Completed**:
```bash
# Move file to completed directory
git mv todos/active/002-phase2-database.md todos/completed/002-phase2-database.md

# Update master todo list
code todos/000-master.md
```

---

## 🎯 Completion Criteria

Phase 2 is considered **100% complete** when:

- ✅ Docker containers are running successfully
- ✅ Alembic migration generated and applied
- ✅ All 19 tables created in PostgreSQL
- ✅ PostgreSQL extensions installed (uuid-ossp, pg_trgm, vector)
- ✅ Seed data loaded (23 locations, 17 salary bands)
- ✅ All integration tests passing
- ✅ Migration downgrade/upgrade tested
- ✅ Database backup created
- ✅ Phase 2 todo moved to completed directory

---

## 📊 Time Estimates

Assuming Docker is operational:

| Step | Estimated Time | Complexity |
|------|---------------|------------|
| 1. Generate migration | 1 minute | Low |
| 2. Review migration | 5 minutes | Medium |
| 3. Apply migration | 1 minute | Low |
| 4. Verify schema | 5 minutes | Low |
| 5. Load seed data | 2 minutes | Low |
| 6. Run integration tests | 5-10 minutes | Medium |
| 7. Test downgrade/upgrade | 5 minutes | Medium |
| 8. Create backup | 2 minutes | Low |
| 9. Update documentation | 10 minutes | Low |
| **Total** | **36-41 minutes** | **Medium** |

---

## ⚠️ Troubleshooting

### Issue: Alembic Migration Fails

**Symptoms**:
```
alembic.util.exc.CommandError: Can't locate revision identified by 'abc123'
```

**Solution**:
```bash
# Check alembic version table
docker-compose exec postgres psql -U job_pricing_user -d job_pricing_db -c "SELECT * FROM alembic_version;"

# Reset if needed
docker-compose exec api alembic stamp head
```

---

### Issue: Seed Scripts Insert 0 Rows

**Symptoms**:
```
INSERT 0 0
```

**Solution**:
- Data may already exist (ON CONFLICT DO NOTHING)
- Check if records exist:
```bash
docker-compose exec postgres psql -U job_pricing_user -d job_pricing_db -c "SELECT COUNT(*) FROM location_index;"
```

---

### Issue: Integration Tests Fail with Connection Error

**Symptoms**:
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solution**:
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check DATABASE_URL in .env
cat .env | grep DATABASE_URL

# Restart PostgreSQL container
docker-compose restart postgres
```

---

### Issue: pgvector Extension Not Found

**Symptoms**:
```
ERROR: type "vector" does not exist
```

**Solution**:
```bash
# Install pgvector extension manually
docker-compose exec postgres psql -U job_pricing_user -d job_pricing_db -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Verify installation
docker-compose exec postgres psql -U job_pricing_user -d job_pricing_db -c "\dx vector"
```

---

## 📚 Related Documentation

- `db/init/01-init-database.sql` - Initial database setup
- `db/seeds/README.md` - Seed data documentation
- `alembic/README` - Alembic configuration and usage
- `tests/integration/conftest.py` - Test fixtures and configuration
- `docs/architecture/data_models.md` - Database schema documentation
- `todos/active/002-phase2-database.md` - Phase 2 implementation details

---

## 🎓 Learning Resources

### Alembic Migrations
- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [Auto Generating Migrations](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)

### PostgreSQL Extensions
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [pg_trgm Documentation](https://www.postgresql.org/docs/current/pgtrgm.html)

### Testing with SQLAlchemy
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/14/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)
- [Pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)

---

## ✅ Quick Reference Commands

```bash
# Start Docker containers
cd C:\Users\fujif\OneDrive\Documents\GitHub\rrrr\src\job_pricing
docker-compose up -d --build

# Generate and apply migration
docker-compose exec api alembic revision --autogenerate -m "Initial schema - 19 tables"
docker-compose exec api alembic upgrade head

# Load seed data
docker-compose exec postgres psql -U job_pricing_user -d job_pricing_db -f /docker-entrypoint-initdb.d/seeds/01-locations.sql
docker-compose exec postgres psql -U job_pricing_user -d job_pricing_db -f /docker-entrypoint-initdb.d/seeds/02-grade-salary-bands.sql

# Run integration tests
docker-compose exec api pytest tests/integration/test_repositories.py -v

# Test migration rollback
docker-compose exec api alembic downgrade -1
docker-compose exec api alembic upgrade head

# Create backup
docker-compose exec postgres pg_dump -U job_pricing_user -d job_pricing_db > backups/job_pricing_db_phase2_baseline.sql

# Check status
docker-compose ps
docker-compose exec api alembic current
docker-compose exec postgres psql -U job_pricing_user -d job_pricing_db -c "\dt"
```

---

## 🚀 Next Phase

Once Phase 2 is complete, proceed to:
- **Phase 3: Data Ingestion** (`todos/active/003-phase3-data-ingestion.md`)
  - Load Mercer Job Library (18,000+ jobs)
  - Load SSG Skills Framework
  - Generate embeddings for vector search
  - Load Mercer market data
  - Set up scraping infrastructure

---

*Last Updated: 2025-11-11*
*Phase 2 Progress: 90% → Awaiting Docker Resolution → 100% (after checklist execution)*
