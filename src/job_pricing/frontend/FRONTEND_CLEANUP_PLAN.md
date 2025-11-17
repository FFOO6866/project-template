# Frontend Mock Data Cleanup Plan

**Objective**: Remove ALL hardcoded mock data and wire to real backend APIs

**Impact**: CRITICAL - Users currently see 100% fake data

---

## Mock Data Arrays to Remove

### 1. Mercer Benchmark Data (Lines 227-268)
```typescript
const mercerBenchmarkData: MercerBenchmarkData[] = [
  // 5 hardcoded entries with fake p25/p50/p75 values
]
```

**Current Usage**:
- Line 217: `mercerBenchmarkData.filter(...)`
- Displayed in UI tables showing salary benchmarks

**Replacement**:
- Call `/api/v1/salary/recommend` endpoint
- Use real Mercer data from database
- Extract percentiles from `pricing_result`

---

### 2. MyCareersFuture Job Listings (Lines 271-332)
```typescript
const myCareersFutureData = [
  // 6 hardcoded job listings with fake companies, salaries, dates
]
```

**Current Usage**:
- Line 192: `myCareersFutureData.filter(...)`
- Displayed as external job market comparisons

**Replacement Options**:
- **Option A**: Integrate real MyCareersFuture API (if available)
- **Option B**: Feature flag to disable this section
- **Option C**: Scrape data periodically and store in database

**Recommendation**: Option B (disable feature) - fastest path to production

---

### 3. Glassdoor Salary Data (Lines 335-386)
```typescript
const glassdoorData = [
  // 5 hardcoded Glassdoor entries with fake reviews, ratings
]
```

**Current Usage**:
- Line 206: `glassdoorData.filter(...)`
- Displayed as external salary insights

**Replacement Options**:
- **Option A**: License Glassdoor API (expensive, requires partnership)
- **Option B**: Feature flag to disable this section
- **Option C**: Remove completely

**Recommendation**: Option B (disable feature) - Glassdoor API requires paid license

---

### 4. Internal Employee Data (Lines 389-455)
```typescript
const internalData = [
  // 5 hardcoded employee records with fake names, salaries
]
```

**Current Usage**:
- Lines 1903, 1960: `internalData.map(...)` in table rendering
- Lines 1992-1999: Salary range calculations

**Replacement Options**:
- **Option A**: Integrate with HRIS system API
- **Option B**: Feature flag to disable (requires FEATURE_INTERNAL_HRIS=true)
- **Option C**: Manual CSV upload feature

**Recommendation**: Option B (disable if no HRIS integration)

---

### 5. Other Department Data (Lines 458+)
```typescript
const otherDepartmentData = [
  // Multiple hardcoded cross-department salary comparisons
]
```

**Current Usage**:
- Lines 2830, 2887: `otherDepartmentData.map(...)` in table rendering
- Lines 2919-2926: Salary range calculations

**Replacement**:
- Same as Internal Employee Data
- Disable if HRIS not integrated

---

## Implementation Strategy

### Phase 4.1: Create Feature Flags (30 minutes)

**File**: `frontend/.env.local`
```bash
# External Data Sources
NEXT_PUBLIC_FEATURE_MYCAREERSFUTURE=false
NEXT_PUBLIC_FEATURE_GLASSDOOR=false
NEXT_PUBLIC_FEATURE_INTERNAL_HRIS=false

# Backend API
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

**File**: `frontend/lib/config.ts` (NEW)
```typescript
export const config = {
  features: {
    myCareersFuture: process.env.NEXT_PUBLIC_FEATURE_MYCAREERSFUTURE === 'true',
    glassdoor: process.env.NEXT_PUBLIC_FEATURE_GLASSDOOR === 'true',
    internalHRIS: process.env.NEXT_PUBLIC_FEATURE_INTERNAL_HRIS === 'true',
  },
  api: {
    baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
  },
}
```

### Phase 4.2: Remove Mock Data Arrays (1 hour)

**Delete Lines**:
- Lines 227-268: `mercerBenchmarkData` array
- Lines 271-332: `myCareersFutureData` array
- Lines 335-386: `glassdoorData` array
- Lines 389-455: `internalData` array
- Lines 458+: `otherDepartmentData` array

### Phase 4.3: Create React Hooks for Data Fetching (2-3 hours)

**File**: `frontend/hooks/useSalaryRecommendation.ts` (NEW)
```typescript
import { useState, useEffect } from 'react'
import { salaryRecommendationApi } from '@/lib/api'

export function useSalaryRecommendation(jobTitle: string, location: string) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!jobTitle) return

    const fetchData = async () => {
      setLoading(true)
      try {
        const result = await salaryRecommendationApi.recommendSalary({
          job_title: jobTitle,
          location: location || 'Central Business District',
        })
        setData(result)
      } catch (err) {
        setError(err)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [jobTitle, location])

  return { data, loading, error }
}
```

**File**: `frontend/hooks/useMyCareersFutureJobs.ts` (NEW)
```typescript
// Placeholder hook - disabled by feature flag
export function useMyCareersFutureJobs(jobTitle: string) {
  return { data: [], loading: false, error: null, disabled: true }
}
```

**File**: `frontend/hooks/useGlassdoorData.ts` (NEW)
```typescript
// Placeholder hook - disabled by feature flag
export function useGlassdoorData(jobTitle: string) {
  return { data: [], loading: false, error: null, disabled: true }
}
```

**File**: `frontend/hooks/useInternalHRIS.ts` (NEW)
```typescript
// Placeholder hook - disabled by feature flag
export function useInternalHRIS(department: string) {
  return { data: [], loading: false, error: null, disabled: true }
}
```

### Phase 4.4: Update Components to Use Hooks (3-4 hours)

**In `page.tsx`**:

Replace:
```typescript
const mercerBenchmarkData = [...]
```

With:
```typescript
const {
  data: salaryData,
  loading: salaryLoading,
  error: salaryError
} = useSalaryRecommendation(jobData.jobTitle, jobData.location)

// Extract Mercer benchmarks from salaryData
const mercerBenchmarks = salaryData?.matched_jobs?.map(job => ({
  category: 'By Job',
  description: job.job_title,
  p25: salaryData.percentiles.p25,
  p50: salaryData.percentiles.p50,
  p75: salaryData.percentiles.p75,
  sampleSize: salaryData.data_sources.mercer_market_data.total_sample_size,
})) || []
```

Replace:
```typescript
const myCareersFutureData = [...]
```

With:
```typescript
const {
  data: mcfJobs,
  loading: mcfLoading,
  disabled: mcfDisabled
} = useMyCareersFutureJobs(jobData.jobTitle)
```

### Phase 4.5: Add Loading States (1 hour)

**Add loading skeletons**:
```typescript
{salaryLoading ? (
  <div className="animate-pulse">
    <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
    <div className="h-4 bg-gray-200 rounded w-1/2"></div>
  </div>
) : salaryError ? (
  <div className="text-red-600">
    Failed to load salary data: {salaryError.message}
  </div>
) : (
  <SalaryDataTable data={mercerBenchmarks} />
)}
```

### Phase 4.6: Conditional Rendering Based on Feature Flags (1 hour)

```typescript
import { config } from '@/lib/config'

// ...

{config.features.myCareersFuture && (
  <MyCareersFutureSection data={mcfJobs} loading={mcfLoading} />
)}

{config.features.glassdoor && (
  <GlassdoorSection data={glassdoorData} loading={glassdoorLoading} />
)}

{config.features.internalHRIS && (
  <InternalBenchmarkSection data={internalData} loading={internalLoading} />
)}
```

---

## Testing Plan

### 1. Backend API Testing
```bash
# Test salary recommendation endpoint
curl http://localhost:8000/api/v1/salary/recommend \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "job_title": "HR Director",
    "location": "Central Business District"
  }'

# Verify returns real data (not mock)
```

### 2. Frontend Testing
- Load page with all features disabled
- Verify no mock data displayed
- Check API calls in Network tab
- Verify loading states work
- Test error handling

### 3. Feature Flag Testing
- Enable FEATURE_MYCAREERSFUTURE → section should show (empty for now)
- Disable → section should hide
- Same for Glassdoor and HRIS

---

## Success Criteria

✅ **ZERO hardcoded mock data arrays in page.tsx**
✅ **All data from backend APIs or feature-flagged**
✅ **Loading states for all async operations**
✅ **Error handling for API failures**
✅ **Feature flags working correctly**
✅ **No console errors**
✅ **Real Mercer data displayed from backend**

---

## Estimated Timeline

| Task | Time |
|------|------|
| Create feature flags config | 30 min |
| Remove mock data arrays | 1 hour |
| Create React hooks | 2-3 hours |
| Update component logic | 3-4 hours |
| Add loading/error states | 1 hour |
| Feature flag integration | 1 hour |
| Testing | 1 hour |
| **Total** | **9-11 hours (1.5 days)** |

---

## Files to Create

1. `frontend/lib/config.ts` - Feature flag configuration
2. `frontend/hooks/useSalaryRecommendation.ts` - Real salary data
3. `frontend/hooks/useMyCareersFutureJobs.ts` - Placeholder (disabled)
4. `frontend/hooks/useGlassdoorData.ts` - Placeholder (disabled)
5. `frontend/hooks/useInternalHRIS.ts` - Placeholder (disabled)
6. `frontend/.env.local` - Environment variables

## Files to Modify

1. `frontend/app/job-pricing/page.tsx` - Remove mock data, add hooks
2. `frontend/lib/api.ts` - Already has salaryRecommendationApi (no changes needed)

---

## Next Steps After This Phase

1. ✅ Frontend displays real backend data
2. ✅ Mock data completely eliminated
3. ✅ Feature flags allow progressive enhancement
4. → **Phase 5**: Implement external API integrations (optional)
5. → **Phase 6**: Admin UI for parameter management
6. → **Production deployment**

---

**Priority**: HIGH - This is blocking production deployment
**Complexity**: MEDIUM - Mostly refactoring, no new logic
**Risk**: LOW - Feature flags provide safety net
