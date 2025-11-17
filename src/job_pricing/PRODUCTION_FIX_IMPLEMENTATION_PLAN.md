# Production Fix Implementation Plan

**Objective**: Make Job Pricing Engine 100% production-ready with no mock data, no hardcoded values, no simulated data, and no fallback data.

**Based on**: PRODUCTION_READINESS_AUDIT.md findings
**Estimated Total Effort**: 26-40 days
**Start Date**: 2025-11-13

---

## Implementation Phases

### Phase 1: Backend Database Schema (Days 1-3)

**Objective**: Move all hardcoded pricing parameters to database tables

#### 1.1 Database Schema Design

**New Tables**:

```sql
-- Salary bands by experience level
CREATE TABLE salary_bands (
    id SERIAL PRIMARY KEY,
    experience_level VARCHAR(50) NOT NULL UNIQUE,  -- 'entry', 'junior', 'mid', 'senior', 'lead'
    min_years INTEGER NOT NULL,
    max_years INTEGER,
    salary_min_sgd DECIMAL(12,2) NOT NULL,
    salary_max_sgd DECIMAL(12,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'SGD',
    effective_from DATE NOT NULL,
    effective_to DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(255),
    notes TEXT
);

-- Industry adjustment factors
CREATE TABLE industry_adjustments (
    id SERIAL PRIMARY KEY,
    industry_name VARCHAR(100) NOT NULL,
    adjustment_factor DECIMAL(5,4) NOT NULL,  -- 1.15 = +15%, 0.90 = -10%
    effective_from DATE NOT NULL,
    effective_to DATE,
    is_active BOOLEAN DEFAULT TRUE,
    data_source VARCHAR(255),  -- 'Market Survey 2024', 'Internal Analysis'
    sample_size INTEGER,
    confidence_level VARCHAR(20),  -- 'High', 'Medium', 'Low'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(255),
    notes TEXT
);

-- Company size factors
CREATE TABLE company_size_factors (
    id SERIAL PRIMARY KEY,
    size_category VARCHAR(50) NOT NULL UNIQUE,  -- '1-10', '11-50', etc.
    employee_min INTEGER NOT NULL,
    employee_max INTEGER,
    adjustment_factor DECIMAL(5,4) NOT NULL,
    effective_from DATE NOT NULL,
    effective_to DATE,
    is_active BOOLEAN DEFAULT TRUE,
    data_source VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(255),
    notes TEXT
);

-- Skill premiums (market demand-based)
CREATE TABLE skill_premiums (
    id SERIAL PRIMARY KEY,
    skill_name VARCHAR(255) NOT NULL,
    skill_category VARCHAR(100),  -- 'Technical', 'Leadership', 'Domain'
    premium_percentage DECIMAL(5,4) NOT NULL,  -- 0.02 = 2% premium
    demand_level VARCHAR(20),  -- 'Critical', 'High', 'Medium', 'Low'
    effective_from DATE NOT NULL,
    effective_to DATE,
    is_active BOOLEAN DEFAULT TRUE,
    data_source VARCHAR(255),
    market_demand_score DECIMAL(5,2),  -- 0-100 score
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(255),
    notes TEXT
);

-- Parameter change history (audit trail)
CREATE TABLE parameter_change_history (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    record_id INTEGER NOT NULL,
    field_name VARCHAR(100) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_by VARCHAR(255) NOT NULL,
    changed_at TIMESTAMP DEFAULT NOW(),
    change_reason TEXT,
    approved_by VARCHAR(255),
    approved_at TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_salary_bands_active ON salary_bands(is_active, effective_from, effective_to);
CREATE INDEX idx_industry_adjustments_active ON industry_adjustments(is_active, industry_name);
CREATE INDEX idx_company_size_factors_active ON company_size_factors(is_active, size_category);
CREATE INDEX idx_skill_premiums_active ON skill_premiums(is_active, skill_name);
CREATE INDEX idx_parameter_history_table ON parameter_change_history(table_name, record_id);
```

#### 1.2 Migration Script

Create Alembic migration: `migrations/versions/xxx_add_pricing_parameter_tables.py`

#### 1.3 Seed Data

Create seed script to populate tables with current hardcoded values as initial data:
- `data/seeds/seed_salary_bands.sql`
- `data/seeds/seed_industry_adjustments.sql`
- `data/seeds/seed_company_size_factors.sql`
- `data/seeds/seed_skill_premiums.sql`

---

### Phase 2: Backend Service Updates (Days 4-6)

**Objective**: Update services to query database instead of using hardcoded values

#### 2.1 New Repository Classes

Create repositories for new tables:
- `repositories/salary_bands_repository.py`
- `repositories/industry_adjustments_repository.py`
- `repositories/company_size_factors_repository.py`
- `repositories/skill_premiums_repository.py`

#### 2.2 Update PricingCalculationService

**File**: `services/pricing_calculation_service.py`

Changes:
- Remove hardcoded dictionaries (lines 70-100, 302-310)
- Add repository injections in `__init__()`
- Update methods to query database:
  - `_get_base_salary_range()` → query `salary_bands` table
  - `_get_industry_adjustment()` → query `industry_adjustments` table
  - `_get_company_size_factor()` → query `company_size_factors` table
  - `_calculate_skill_premium()` → query `skill_premiums` table
- Add caching layer (Redis) to avoid repeated DB queries
- Add validation for missing parameters

#### 2.3 Fix Location Fallbacks

**Files**:
- `services/salary_recommendation_service.py:202`
- `services/pricing_calculation_service.py:293`

Changes:
- Remove hardcoded fallback values
- Implement fail-fast approach: raise `ValueError` if location not found
- Add comprehensive location data to `location_index` table

#### 2.4 Add Caching Layer

Implement Redis caching for pricing parameters:
- Cache TTL: 1 hour (configurable via `CACHE_TTL_MEDIUM`)
- Cache invalidation on parameter updates
- Cache warming on application startup

---

### Phase 3: Admin API for Parameter Management (Days 7-9)

**Objective**: Create admin endpoints to manage pricing parameters

#### 3.1 New API Router

Create: `api/v1/admin/pricing_parameters.py`

**Endpoints**:

```python
# Salary Bands
GET    /api/v1/admin/salary-bands                 # List all
GET    /api/v1/admin/salary-bands/{id}            # Get one
POST   /api/v1/admin/salary-bands                 # Create
PUT    /api/v1/admin/salary-bands/{id}            # Update
DELETE /api/v1/admin/salary-bands/{id}            # Soft delete
GET    /api/v1/admin/salary-bands/history/{id}    # Get change history

# Industry Adjustments
GET    /api/v1/admin/industry-adjustments
POST   /api/v1/admin/industry-adjustments
PUT    /api/v1/admin/industry-adjustments/{id}
DELETE /api/v1/admin/industry-adjustments/{id}

# Company Size Factors
GET    /api/v1/admin/company-size-factors
POST   /api/v1/admin/company-size-factors
PUT    /api/v1/admin/company-size-factors/{id}
DELETE /api/v1/admin/company-size-factors/{id}

# Skill Premiums
GET    /api/v1/admin/skill-premiums
POST   /api/v1/admin/skill-premiums
PUT    /api/v1/admin/skill-premiums/{id}
DELETE /api/v1/admin/skill-premiums/{id}
POST   /api/v1/admin/skill-premiums/bulk-update    # Bulk import from CSV

# Cache Management
POST   /api/v1/admin/cache/invalidate               # Clear parameter cache
POST   /api/v1/admin/cache/warm                     # Warm cache
```

#### 3.2 Authentication & Authorization

- Require JWT authentication for all admin endpoints
- Add role-based access control (RBAC):
  - `admin` role: full access
  - `pricing_manager` role: read + update
  - `analyst` role: read-only
- Audit all parameter changes to `parameter_change_history` table

#### 3.3 Pydantic Schemas

Create schemas for request/response validation:
- `schemas/admin/salary_band.py`
- `schemas/admin/industry_adjustment.py`
- `schemas/admin/company_size_factor.py`
- `schemas/admin/skill_premium.py`

---

### Phase 4: Frontend Mock Data Removal (Days 10-12)

**Objective**: Remove all hardcoded mock data arrays from frontend

#### 4.1 Remove Mock Data Arrays

**File**: `frontend/app/job-pricing/page.tsx`

**Delete lines 227-476+**:
- Remove `mercerBenchmarkData` array
- Remove `myCareersFutureData` array
- Remove `glassdoorData` array
- Remove `internalData` array
- Remove `otherDepartmentData` array

#### 4.2 Update State Management

Replace mock data with API-driven state:

```typescript
// Before (REMOVE)
const mercerBenchmarkData = [...]

// After (ADD)
const [mercerBenchmarks, setMercerBenchmarks] = useState<MercerBenchmark[]>([])
const [isLoadingMercer, setIsLoadingMercer] = useState(false)
const [mercerError, setMercerError] = useState<string | null>(null)
```

#### 4.3 Create API Integration Hooks

Create custom React hooks:
- `hooks/useMercerBenchmarks.ts` → Fetch from `/api/v1/salary/recommend`
- `hooks/useMyCareersFutureJobs.ts` → Fetch from MyCareersFuture API
- `hooks/useGlassdoorData.ts` → Fetch from Glassdoor API (or disable)
- `hooks/useInternalSalaries.ts` → Fetch from HRIS API (if enabled)

---

### Phase 5: External API Integrations (Days 13-25)

**Objective**: Implement real external data source integrations

#### 5.1 MyCareersFuture Integration (Days 13-17)

**Research**:
- Check if MyCareersFuture provides public API
- Alternative: Web scraping with proper rate limiting and robots.txt compliance

**Implementation**:
- Create `services/mycareersfuture_service.py`
- Create `api/v1/external/mycareersfuture.py` router
- Implement job search, filtering, caching
- Handle rate limiting, retries, error handling
- Add to Celery for background updates

**Endpoints**:
```python
GET /api/v1/external/mycareersfuture/jobs?title={title}&location={location}
GET /api/v1/external/mycareersfuture/job/{id}
```

#### 5.2 Glassdoor Integration (Days 18-22)

**Research**:
- Verify Glassdoor API license/partnership required
- Check pricing and legal requirements
- Alternative: Consider removing feature if not licensed

**Implementation** (if licensed):
- Create `services/glassdoor_service.py`
- Create `api/v1/external/glassdoor.py` router
- Implement salary search, company reviews
- Handle authentication, rate limiting
- Cache results (24-hour TTL)

**Endpoints**:
```python
GET /api/v1/external/glassdoor/salaries?title={title}&location={location}
GET /api/v1/external/glassdoor/company/{id}
```

**Alternative** (if not licensed):
- Remove Glassdoor feature from frontend
- Add placeholder: "Premium Feature - Contact Sales"

#### 5.3 Internal HRIS Integration (Days 23-25)

**Requirements Gathering**:
- Identify internal HRIS system (Workday, SAP SuccessFactors, Oracle HCM, etc.)
- Get API documentation and credentials
- Understand data access permissions and compliance (GDPR, data privacy)

**Implementation** (if `FEATURE_INTERNAL_HRIS=true`):
- Create `services/hris_service.py`
- Create `api/v1/internal/hris.py` router
- Implement anonymized salary queries
- Add role-based access control
- Implement data masking for privacy
- Add audit logging

**Endpoints**:
```python
GET /api/v1/internal/hris/salaries/department/{dept}?anonymized=true
GET /api/v1/internal/hris/salaries/grade/{grade}
```

**Alternative** (if not available):
- Disable feature via `FEATURE_INTERNAL_HRIS=false`
- Remove from frontend

---

### Phase 6: Frontend Integration (Days 26-30)

**Objective**: Wire frontend to backend APIs

#### 6.1 Update API Client

**File**: `frontend/lib/api.ts`

Add new endpoints:
```typescript
export const externalDataApi = {
  async getMyCareersFutureJobs(params: { title: string; location?: string }) {
    return fetchApi(`/api/v1/external/mycareersfuture/jobs`, { params })
  },

  async getGlassdoorSalaries(params: { title: string; location?: string }) {
    return fetchApi(`/api/v1/external/glassdoor/salaries`, { params })
  },

  async getInternalSalaries(params: { department: string; anonymized: boolean }) {
    return fetchApi(`/api/v1/internal/hris/salaries/department/${params.department}`, { params })
  }
}
```

#### 6.2 Update Components

**File**: `frontend/app/job-pricing/page.tsx`

Replace hardcoded data usage:

```typescript
// Before (REMOVE)
const relevantListings = myCareersFutureData.filter(...)

// After (ADD)
useEffect(() => {
  if (jobTitle) {
    fetchMyCareersFutureJobs(jobTitle, location)
  }
}, [jobTitle, location])

const relevantListings = myCareersFutureJobs.filter(...)
```

#### 6.3 Add Loading States

Implement proper loading, error, and empty states:
- Show skeleton loaders while fetching data
- Display error messages when API calls fail
- Show "No data available" when results are empty
- Add retry buttons for failed requests

#### 6.4 Feature Flags

Conditionally render features based on availability:
```typescript
{process.env.NEXT_PUBLIC_FEATURE_GLASSDOOR === 'true' && (
  <GlassdoorSection data={glassdoorData} />
)}

{process.env.NEXT_PUBLIC_FEATURE_INTERNAL_HRIS === 'true' && (
  <InternalBenchmarkSection data={internalData} />
)}
```

---

### Phase 7: Testing & Validation (Days 31-35)

**Objective**: Comprehensive testing with real data

#### 7.1 Backend Testing

**Unit Tests**:
- Test new repositories (CRUD operations)
- Test service methods with database parameters
- Test cache invalidation
- Test location fallback removal (should fail-fast)

**Integration Tests**:
- Test admin API endpoints (create, update, delete parameters)
- Test pricing calculation with database parameters
- Test external API integrations (with mocking for rate limits)
- Test HRIS integration (with test data)

**Performance Tests**:
- Load test salary recommendation endpoint
- Test Redis cache hit rates
- Test database query performance with indexes

#### 7.2 Frontend Testing

**Component Tests**:
- Test API integration hooks
- Test loading/error states
- Test data rendering with real API responses

**E2E Tests**:
- Test complete job pricing workflow
- Test parameter management workflow (admin)
- Test external data fetching
- Test graceful degradation when APIs fail

#### 7.3 Data Validation

- Verify all mock data removed (grep for hardcoded arrays)
- Verify all pricing parameters come from database
- Verify all external data comes from real APIs
- Verify proper error handling for missing data

---

### Phase 8: Deployment & Monitoring (Days 36-40)

**Objective**: Production deployment and monitoring setup

#### 8.1 Database Migration

- Run Alembic migrations on production database
- Load seed data for pricing parameters
- Verify location data completeness
- Backup database before migration

#### 8.2 Configuration

Update production `.env`:
```bash
# External API Keys
MYCAREERSFUTURE_API_KEY=xxx
GLASSDOOR_API_KEY=xxx (if licensed)
HRIS_API_URL=xxx
HRIS_API_KEY=xxx

# Feature Flags
FEATURE_MYCAREERSFUTURE=true
FEATURE_GLASSDOOR=false  # Disable if not licensed
FEATURE_INTERNAL_HRIS=true

# Cache Configuration
CACHE_TTL_PRICING_PARAMETERS=3600  # 1 hour
```

#### 8.3 Monitoring & Alerts

Set up monitoring:
- Application logs (ELK stack or CloudWatch)
- API performance metrics (response times, error rates)
- External API health checks
- Database query performance
- Cache hit rates

Alerts:
- External API failures (MyCareersFuture, Glassdoor, HRIS)
- Database parameter table empty (critical)
- Cache failures
- High error rates on salary recommendation endpoint

#### 8.4 Documentation

Update documentation:
- Admin guide for managing pricing parameters
- API documentation for new endpoints
- Runbook for troubleshooting external API issues
- Data refresh procedures (quarterly parameter updates)

---

## Success Criteria

### Must Have (Production Blockers)
- [ ] Zero hardcoded mock data arrays in frontend
- [ ] All pricing parameters from database (not hardcoded)
- [ ] Location fallbacks removed (fail-fast on invalid location)
- [ ] Admin API functional for parameter management
- [ ] Real Mercer benchmarks displayed (from backend API)

### Should Have (Important)
- [ ] MyCareersFuture integration working (or feature disabled)
- [ ] Glassdoor integration working (or feature removed)
- [ ] Internal HRIS integration working (or feature disabled)
- [ ] Comprehensive test coverage (>80%)
- [ ] Monitoring and alerts configured

### Nice to Have (Optional)
- [ ] Parameter change approval workflow
- [ ] A/B testing framework for parameter changes
- [ ] Data quality dashboard
- [ ] Automated parameter updates from market surveys

---

## Risk Mitigation

### High-Risk Items

1. **External API Availability**
   - Risk: MyCareersFuture or Glassdoor APIs may not be publicly available
   - Mitigation: Feature flags to disable unavailable integrations

2. **HRIS Access**
   - Risk: HRIS system may have strict access controls
   - Mitigation: Work with IT/Security to get proper API access

3. **Data Privacy Compliance**
   - Risk: Displaying internal salary data may violate privacy policies
   - Mitigation: Implement data anonymization and access controls

4. **Performance Impact**
   - Risk: Database queries may slow down salary calculations
   - Mitigation: Redis caching, database indexing, query optimization

---

## Timeline Summary

| Phase | Days | Tasks |
|-------|------|-------|
| 1. Database Schema | 1-3 | Create tables, migrations, seed data |
| 2. Backend Services | 4-6 | Update services, repositories, fix fallbacks |
| 3. Admin API | 7-9 | Create admin endpoints, RBAC |
| 4. Frontend Cleanup | 10-12 | Remove mock data, add state management |
| 5. External APIs | 13-25 | MyCareersFuture, Glassdoor, HRIS integrations |
| 6. Frontend Integration | 26-30 | Wire APIs, loading states, feature flags |
| 7. Testing | 31-35 | Unit, integration, E2E, performance tests |
| 8. Deployment | 36-40 | Migration, config, monitoring, docs |

**Total**: 40 days (8 weeks)

---

## Next Steps

1. Review and approve this plan
2. Start Phase 1: Database schema design and migration
3. Weekly progress reviews
4. Adjust timeline based on external API availability

---

**Plan Version**: 1.0
**Created**: 2025-11-13
**Owner**: Development Team
**Reviewer**: Product/Engineering Lead
