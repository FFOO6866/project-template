# Production Readiness Audit Report

**Date**: 2025-11-13
**System**: Job Pricing Engine (MVP)
**Audit Scope**: Complete system review for hardcoded values, mock data, simulated data, and fallback data

---

## Executive Summary

**Production Readiness Status**: ❌ **NOT READY**

The system has **CRITICAL PRODUCTION BLOCKERS** that must be resolved before deployment:

- **Frontend**: Extensive hardcoded mock data actively displayed to users
- **Backend**: Multiple hardcoded calculation parameters that should be configurable
- **Configuration**: ✅ Excellent - all externalized to environment variables
- **Data Sources**: ✅ Good - using real PostgreSQL data, but with hardcoded fallbacks

---

## Severity Classification

- **CRITICAL**: Blocks production deployment - immediate fix required
- **MAJOR**: Significant issue - must fix before production
- **MINOR**: Best practice violation - should fix but not blocking

---

## CRITICAL Issues (Production Blockers)

### 1. Frontend Mock Data - ACTIVELY DISPLAYED TO USERS

**File**: `frontend/app/job-pricing/page.tsx`
**Lines**: 227-476+
**Severity**: 🔴 **CRITICAL**

#### Mock Data Arrays Found:

1. **Mercer Benchmark Data** (Lines 227-268)
   - 5 hardcoded benchmark entries
   - Mock sample sizes, percentiles (p25/p50/p75)
   - Example: `{ category: "By Job", p25: 135600, p50: 148200, p75: 158400, sampleSize: 87 }`

2. **MyCareersFuture Job Listings** (Lines 271-332)
   - 6 hardcoded job postings
   - Fake companies: CapitaLand Group, DBS Bank, Grab Holdings, etc.
   - Mock salaries, dates, skill matches
   - Example: `{ company: "CapitaLand Group", salaryRange: "SGD 13,000 - 15,000", skillsMatch: "92%" }`

3. **Glassdoor Salary Data** (Lines 335-386)
   - 5 hardcoded Glassdoor entries
   - Fake review counts, company ratings, reliability scores
   - Example: `{ company: "CapitaLand Group", reviewCount: 45, companyRating: 4.2 }`

4. **Internal Employee Salary Data** (Lines 389-455)
   - 5 hardcoded employee records
   - Real-looking employee names, grades, salaries
   - Example: `{ name: "Wong Mei Ling", title: "Chief People Officer", monthlySalary: 22500 }`

5. **Other Department Salary Data** (Lines 458+)
   - Multiple hardcoded cross-department comparisons
   - Fake employee data for benchmarking
   - Example: `{ name: "Zhang Wei Jie", dept: "Finance", monthlySalary: 14200 }`

#### Usage Confirmed:

The mock data is actively used in the UI:
- **Line 192**: `myCareersFutureData.filter(...)` - filtering mock jobs
- **Line 206**: `glassdoorData.filter(...)` - filtering mock Glassdoor data
- **Line 217**: `mercerBenchmarkData.filter(...)` - filtering mock benchmarks
- **Lines 1903, 1960**: Table rendering with `internalData.map(...)` and `otherDepartmentData.map(...)`
- **Lines 1992-1999**: Salary range calculations using hardcoded mock data

#### Impact:

❌ Users see **100% fake data** for:
- Market benchmarks (Mercer comparisons)
- External job postings (MyCareersFuture)
- Glassdoor salary insights
- Internal salary comparisons
- Cross-department benchmarking

**This is a CRITICAL production blocker** - the entire frontend displays mock data instead of calling real APIs.

#### Required Fix:

Replace all hardcoded arrays with actual API calls:
1. Create API clients for MyCareersFuture integration
2. Create API clients for Glassdoor integration (or remove if not licensed)
3. Query real Mercer data from backend `/api/v1/salary/recommend` endpoint
4. Query real internal employee data from HRIS system (if `FEATURE_INTERNAL_HRIS` enabled)
5. Remove all hardcoded mock arrays

---

### 2. Backend Hardcoded Pricing Parameters

**File**: `src/job_pricing/services/pricing_calculation_service.py`
**Severity**: 🔴 **CRITICAL**

#### Hardcoded Calculation Values:

1. **Base Salary Ranges by Experience** (Lines 70-76)
```python
BASE_SALARY_BY_EXPERIENCE = {
    "entry": (45000, 65000),    # 0-2 years - HARDCODED
    "junior": (60000, 85000),   # 2-4 years - HARDCODED
    "mid": (85000, 120000),     # 4-7 years - HARDCODED
    "senior": (120000, 170000), # 7-10 years - HARDCODED
    "lead": (170000, 250000),   # 10+ years - HARDCODED
}
```

2. **Industry Adjustment Factors** (Lines 79-89)
```python
INDUSTRY_FACTORS = {
    "Technology": 1.15,   # HARDCODED +15%
    "Finance": 1.20,      # HARDCODED +20%
    "Healthcare": 1.05,   # HARDCODED +5%
    "Education": 0.90,    # HARDCODED -10%
    "Retail": 0.95,       # HARDCODED -5%
    "Manufacturing": 1.00,
    "Consulting": 1.10,   # HARDCODED +10%
    "Government": 0.95,   # HARDCODED -5%
    "default": 1.00,
}
```

3. **Company Size Multipliers** (Lines 92-100)
```python
COMPANY_SIZE_FACTORS = {
    "1-10": 0.85,      # HARDCODED -15%
    "11-50": 0.90,     # HARDCODED -10%
    "51-200": 1.00,
    "201-500": 1.10,   # HARDCODED +10%
    "501-1000": 1.15,  # HARDCODED +15%
    "1000+": 1.20,     # HARDCODED +20%
    "default": 1.00,
}
```

4. **High-Value Skills Premium** (Lines 302-310)
```python
# High-value skills (placeholder - would come from market data)
high_value_skills = {
    "python", "aws", "kubernetes", "machine learning",
    "react", "typescript", "terraform",
}
# 2% premium per high-value skill, max 20% - HARDCODED
return min(matched_high_value * 0.02, 0.20)
```

#### Impact:

❌ All salary calculations use hardcoded multipliers instead of:
- Market-driven salary data
- Dynamically updated industry trends
- Real-time company size adjustments
- Skills demand analysis from job market data

#### Required Fix:

1. Move all calculation parameters to **database tables**:
   - `salary_bands` table (by experience level, updated quarterly)
   - `industry_adjustments` table (by industry, updated monthly)
   - `company_size_factors` table (by size category, updated annually)
   - `skill_premiums` table (by skill, updated from market demand)

2. Create **admin API endpoints** to update these parameters

3. Add **data versioning** to track when parameters change

4. Implement **A/B testing framework** to validate parameter changes

---

## MAJOR Issues (Must Fix Before Production)

### 3. Location Cost-of-Living Fallback

**File**: `src/job_pricing/services/salary_recommendation_service.py`
**Line**: 202
**Severity**: 🟠 **MAJOR**

```python
def _get_location_index(self, location: str) -> float:
    """Get cost-of-living index for location."""
    # ... query database ...

    if result:
        return float(result.cost_of_living_index)

    # Default index if location not found
    return 0.90  # HARDCODED FALLBACK - Conservative estimate
```

#### Impact:

If location not found in database, uses hardcoded `0.90` multiplier (10% reduction).

#### Required Fix:

**Option 1 (Recommended)**: Fail fast - require valid location
```python
if not result:
    raise ValueError(f"Location '{location}' not found in database. Please use a valid Singapore location.")
```

**Option 2**: Use Central Business District as fallback
```python
if not result:
    logger.warning(f"Location '{location}' not found, using CBD baseline")
    return 1.0  # CBD baseline
```

---

### 4. Location Multiplier Placeholder

**File**: `src/job_pricing/services/pricing_calculation_service.py`
**Line**: 293
**Severity**: 🟠 **MAJOR**

```python
def _get_location_multiplier(self, location_text: Optional[str]) -> float:
    # ... try database lookup ...

    # Default Singapore multiplier
    if "singapore" in location_text.lower():
        return 1.0

    # Other locations (placeholder) - HARDCODED
    return 1.0
```

#### Impact:

Non-Singapore locations default to `1.0` multiplier instead of real cost-of-living data.

#### Required Fix:

1. Expand `location_index` table to cover all required countries/cities
2. Remove placeholder fallback
3. Require location to be in database (fail-fast approach)

---

## MINOR Issues (Best Practice Violations)

### 5. Fallback Match Type in Validator

**File**: `src/job_pricing/data/validation/mercer_validator.py`
**Line**: 287
**Severity**: 🟡 **MINOR**

```python
self.add_rule(enum_check("match_type", [
    "exact", "high_confidence", "medium_confidence",
    "low_confidence", "manual", "fallback"  # "fallback" suggests mock matching
]))
```

#### Impact:

The system supports a `"fallback"` match type, which suggests mock/placeholder job matching is allowed.

#### Recommendation:

Review if `"fallback"` matches should be allowed in production, or if they should be rejected during validation.

---

## ✅ EXCELLENT: Configuration Management

**File**: `src/job_pricing/src/job_pricing/core/config.py`
**Status**: ✅ **PRODUCTION READY**

### Strengths:

1. **ALL configuration from environment variables** - no hardcoded secrets
2. **Pydantic validation** - type checking and validation on all settings
3. **Required fields enforced** - `Field(...)` ensures critical values are set
4. **Validation rules** - custom validators for OpenAI keys, environment, log levels
5. **Clear documentation** - every field has description
6. **Feature flags** - enable/disable features via config
7. **Environment-aware** - supports development/staging/production modes

### Example Excellence:

```python
# CRITICAL: NO HARDCODED VALUES
OPENAI_API_KEY: str = Field(..., description="OpenAI API key - REQUIRED")
DATABASE_URL: str = Field(..., description="PostgreSQL connection string")
JWT_SECRET_KEY: str = Field(..., description="JWT secret key")

# Validation
@field_validator("OPENAI_API_KEY")
@classmethod
def validate_openai_key(cls, v: str) -> str:
    if not v.startswith("sk-"):
        raise ValueError("OpenAI API key must start with 'sk-'")
    return v
```

**No changes needed** - this is a best-practice implementation.

---

## ✅ GOOD: Data Sources

**Status**: ✅ **MOSTLY PRODUCTION READY**

### Strengths:

1. **Real PostgreSQL database** - all data persisted properly
2. **Real OpenAI API** - embeddings and AI features use live API
3. **Real Mercer job library** - 174 jobs with 100% embedding coverage
4. **Real salary data** - 37 jobs with market salary percentiles (P25/P50/P75)
5. **Real location data** - 24 Singapore locations with cost-of-living indices
6. **No mock database data** - all seed data is real

### Weaknesses:

- Backend has fallback values (see MAJOR issues above)
- Frontend doesn't use backend APIs (see CRITICAL issues above)

---

## Summary by Component

| Component | Status | Issues | Severity |
|-----------|--------|--------|----------|
| **Frontend Data Display** | ❌ NOT READY | Extensive hardcoded mock data | CRITICAL |
| **Backend Pricing Logic** | ❌ NOT READY | Hardcoded calculation parameters | CRITICAL |
| **Backend Location Handling** | ⚠️ NEEDS WORK | Hardcoded fallback values | MAJOR |
| **Configuration Management** | ✅ READY | None | N/A |
| **Database & Data Sources** | ✅ READY | None | N/A |
| **API Endpoints** | ✅ READY | None | N/A |

---

## Production Readiness Checklist

### CRITICAL (Must Fix)

- [ ] **Remove all hardcoded mock data arrays from frontend** (`page.tsx:227-476+`)
  - [ ] Replace `mercerBenchmarkData` with API call to `/api/v1/salary/recommend`
  - [ ] Replace `myCareersFutureData` with real MyCareersFuture API integration
  - [ ] Replace `glassdoorData` with real Glassdoor API (or remove if not licensed)
  - [ ] Replace `internalData` with real HRIS integration (if `FEATURE_INTERNAL_HRIS` enabled)
  - [ ] Replace `otherDepartmentData` with real HRIS queries

- [ ] **Move backend pricing parameters to database**
  - [ ] Create `salary_bands` table for experience-based ranges
  - [ ] Create `industry_adjustments` table for industry multipliers
  - [ ] Create `company_size_factors` table for size-based adjustments
  - [ ] Create `skill_premiums` table for skill-based premiums
  - [ ] Create admin API to manage these parameters
  - [ ] Seed initial values from current hardcoded constants

### MAJOR (Should Fix)

- [ ] **Remove location fallback values**
  - [ ] Update `_get_location_index()` to fail-fast on invalid location
  - [ ] Update `_get_location_multiplier()` to fail-fast on invalid location
  - [ ] Add comprehensive location data for all required countries/cities

### MINOR (Nice to Have)

- [ ] Review `"fallback"` match type in Mercer validator
- [ ] Add monitoring/alerts when fallback values are used
- [ ] Create data quality dashboard showing parameter freshness

---

## GO/NO-GO Recommendation

**Recommendation**: 🔴 **NO-GO for Production**

### Justification:

1. **Frontend displays 100% mock data** - users cannot trust any information shown
2. **Backend uses arbitrary calculation parameters** - recommendations not based on real market data
3. **No external data integrations** - MyCareersFuture, Glassdoor, HRIS all mocked

### Estimated Effort to Fix:

| Task | Effort | Priority |
|------|--------|----------|
| Remove frontend mock data + wire APIs | 3-5 days | CRITICAL |
| Database schema for pricing parameters | 2 days | CRITICAL |
| Migrate hardcoded params to DB | 1 day | CRITICAL |
| Admin API for parameter management | 2-3 days | CRITICAL |
| MyCareersFuture integration | 5-7 days | CRITICAL |
| Glassdoor integration | 5-7 days | CRITICAL (or remove feature) |
| HRIS integration | 7-10 days | CRITICAL (or disable feature) |
| Location fallback fixes | 1 day | MAJOR |
| **Total Estimated Effort** | **26-40 days** | |

### Recommended Phased Approach:

**Phase 1 - Quick Wins (1 week)**
1. Remove frontend mock data arrays
2. Wire frontend to existing backend `/api/v1/salary/recommend` endpoint
3. Disable/hide features that don't have real integrations yet
4. Fix location fallback issues

**Phase 2 - Core Pricing (1 week)**
1. Move pricing parameters to database
2. Create admin API for parameter management
3. Seed database with validated market data

**Phase 3 - External Integrations (2-4 weeks)**
1. Implement MyCareersFuture integration (if API available)
2. Implement Glassdoor integration (if licensed)
3. Implement HRIS integration (if required)

---

## Conclusion

The Job Pricing Engine has a **solid technical foundation** with excellent configuration management, real database architecture, and working AI-powered semantic search. However, the **frontend displays extensive mock data** and the **backend uses hardcoded calculation parameters**, making the system **NOT READY for production deployment**.

**Priority Actions:**
1. Remove all frontend mock data (CRITICAL)
2. Move backend parameters to database (CRITICAL)
3. Implement real external API integrations or disable those features (CRITICAL)

Once these critical issues are resolved, the system will be production-ready for deployment.

---

**Auditor**: Claude Code
**Date**: 2025-11-13
**Report Version**: 1.0
