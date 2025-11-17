# Database Seed Scripts

This directory contains SQL scripts for seeding the database with initial static data required for the Job Pricing Engine to function.

## 📋 Overview

Seed scripts populate reference data and configuration that doesn't change frequently and is needed for the application to operate correctly.

## 🗂️ Seed Files

### 01-locations.sql
**Purpose**: Populates the `location_index` table with Singapore location data.

**Contents**:
- 23 Singapore locations (CBD, City Areas, Regional Centers, etc.)
- Cost-of-living adjustments (0.88 - 1.30 index)
- Housing and transport indexes
- Location codes and regional groupings

**When to Run**: After initial database setup, before loading job data.

**Usage**:
```bash
# From within PostgreSQL container
docker-compose exec postgres psql -U job_pricing_user -d job_pricing_db -f /docker-entrypoint-initdb.d/seeds/01-locations.sql

# Or from host (if PostgreSQL is accessible)
psql -U job_pricing_user -h localhost -d job_pricing_db -f db/seeds/01-locations.sql
```

**Example Data**:
- **Singapore CBD - Raffles Place**: 1.15 cost-of-living index (15% premium)
- **Singapore - Remote**: 0.95 index (5% discount for work-from-home)
- **Singapore - Tuas** (Industrial): 0.93 index

---

### 02-grade-salary-bands.sql
**Purpose**: Populates the `grade_salary_bands` table with company salary structure.

**Contents**:
- **Management Track (M1-M6)**: 6 grades from Junior Manager to Senior Director/VP
- **Professional Track (P1-P6)**: 6 grades from Junior Professional to Distinguished Professional
- **Executive Track (E1-E5)**: 5 grades from VP to CEO

**Salary Philosophy**:
- All salaries at P50 (median) market position
- Aligned with Mercer career levels
- Based on Singapore market data (SGD)

**When to Run**: After initial database setup, before loading employee data or creating job pricing requests.

**Usage**:
```bash
# From within PostgreSQL container
docker-compose exec postgres psql -U job_pricing_user -d job_pricing_db -f /docker-entrypoint-initdb.d/seeds/02-grade-salary-bands.sql

# Or from host
psql -U job_pricing_user -h localhost -d job_pricing_db -f db/seeds/02-grade-salary-bands.sql
```

**Example Grades**:
- **P1** (Junior Professional): $3,000 - $4,500 SGD
- **M4** (Principal Manager): $8,000 - $12,000 SGD
- **E4** (Chief Officer): $70,000 - $120,000 SGD

**Career Progression**:
```
Professional Track: P1 → P2 → P3 → P4 → P5 → P6
Management Track:   P3 → M2 → M3 → M4 → M5 → M6
Executive Track:    M5 → E1 → E2 → E3 → E4 → E5
```

---

## 🚀 Running All Seeds

### Using Docker Compose

Add seed scripts to the `docker-compose.yml` postgres volumes:

```yaml
postgres:
  volumes:
    - ./db/init:/docker-entrypoint-initdb.d/init
    - ./db/seeds:/docker-entrypoint-initdb.d/seeds
```

Then run seeds manually after container startup:

```bash
# Run all seeds in order
docker-compose exec postgres bash -c "
  psql -U job_pricing_user -d job_pricing_db -f /docker-entrypoint-initdb.d/seeds/01-locations.sql
  psql -U job_pricing_user -d job_pricing_db -f /docker-entrypoint-initdb.d/seeds/02-grade-salary-bands.sql
"
```

### Using Python Script (Planned)

A Python seeding script will be created in Phase 3:

```python
# db/seeds/run_seeds.py
from src.job_pricing.utils.database import engine
import sqlalchemy

def run_seed_file(filename):
    with open(f"db/seeds/{filename}", "r") as f:
        sql = f.read()

    with engine.connect() as conn:
        conn.execute(sqlalchemy.text(sql))
        conn.commit()

if __name__ == "__main__":
    run_seed_file("01-locations.sql")
    run_seed_file("02-grade-salary-bands.sql")
    print("✅ All seed scripts executed successfully")
```

---

## 📊 Data Loading Strategy

### Phase 2 (Current): Static Reference Data
- ✅ Locations (01-locations.sql)
- ✅ Grade salary bands (02-grade-salary-bands.sql)
- 🔄 Currency exchange rates (manual or API)

### Phase 3 (Data Ingestion): Dynamic Business Data
- 🔜 Mercer Job Library (18,000+ jobs from Excel)
- 🔜 Mercer Market Data (compensation benchmarks)
- 🔜 SSG Skills Framework (job roles from Excel)
- 🔜 SSG TSC (technical skills & competencies from Excel)
- 🔜 SSG Job Role-TSC Mappings

### Phase 4+ (Operational Data): Scraped & Internal Data
- 🔜 MyCareersFuture job listings (web scraping)
- 🔜 Glassdoor job listings (web scraping)
- 🔜 Internal employee data (HR system integration)
- 🔜 Applicant data (ATS integration)

---

## 🔍 Verification Queries

After running seed scripts, verify the data:

### Check Locations
```sql
SELECT COUNT(*) as total_locations
FROM location_index
WHERE country_code = 'SG';
-- Expected: 23 locations

SELECT location_name, cost_of_living_index
FROM location_index
WHERE country_code = 'SG'
ORDER BY cost_of_living_index DESC
LIMIT 5;
-- Top 5 most expensive locations
```

### Check Salary Bands
```sql
SELECT COUNT(*) as total_grades
FROM grade_salary_bands;
-- Expected: 17 grades (M1-M6, P1-P6, E1-E5)

SELECT grade, grade_description, salary_min, salary_max
FROM grade_salary_bands
ORDER BY salary_min;
-- All grades ordered by salary
```

---

## ⚠️ Important Notes

### NO MOCK DATA Policy
- Seed scripts contain **real reference data structures** only
- Do NOT include mock/fake operational data (job requests, employees, etc.)
- Operational data will come from real sources in later phases

### Idempotency
- All seed scripts use `ON CONFLICT DO NOTHING` for safe re-running
- Safe to run multiple times without duplicating data
- Use `TRUNCATE` only in development, never in production

### Data Maintenance
- **Locations**: Update when new offices open or cost-of-living changes
- **Salary Bands**: Update annually during compensation review
- **Currency Rates**: Should be refreshed regularly via API (Phase 3)

---

## 📝 Adding New Seed Files

When adding new seed scripts, follow this naming convention:

```
##-descriptive-name.sql
```

Where `##` is a zero-padded number indicating execution order.

**Template**:
```sql
-- ============================================================================
-- Seed Script: [Description]
-- ============================================================================
-- Purpose and usage instructions
--
-- Run with: psql -U job_pricing_user -d job_pricing_db -f ##-name.sql
-- ============================================================================

\c job_pricing_db

INSERT INTO table_name (columns)
VALUES (values)
ON CONFLICT (unique_column) DO NOTHING;

-- ============================================================================
-- Verification Query
-- ============================================================================
-- SELECT * FROM table_name LIMIT 5;
```

---

## 🤝 Contributing

When adding or modifying seed data:

1. **Test in development** first
2. **Document the data** with comments
3. **Use real values**, not placeholders
4. **Include verification queries**
5. **Update this README**

---

## 📚 Related Documentation

- `docs/architecture/data_models.md` - Complete database schema
- `todos/active/002-phase2-database.md` - Phase 2 implementation details
- `todos/active/003-phase3-data-ingestion.md` - Data loading strategy
