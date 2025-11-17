# End-to-End Testing Plan
**Date**: 2025-11-12
**Timeline**: 6-8 weeks
**Priorities**: A (Frontend Mocks) & B (Backend Processing)

---

## Testing Strategy

### Phase 1: Verify Current State (Week 1)
**Goal**: Understand what actually works end-to-end

#### Test 1: Browser Workflow - Happy Path
**URL**: http://localhost:3000/job-pricing

**Steps**:
1. Open browser to http://localhost:3000/job-pricing
2. Fill in Job Details form:
   - Job Title: "Senior Data Scientist"
   - Portfolio: "TPC Group Corporate Office"
   - Department: "People & Organisation"
   - Employment Type: "Permanent"
   - Internal Grade: "10"
   - Job Family: "Total Rewards"
3. Click "Analyze Job Pricing" button
4. Observe:
   - Loading spinner appears
   - Status polling happens
   - Results tab displays
   - TPC fields are reflected in results

**Expected Behavior**:
- ✅ Form submits successfully
- ✅ API request created
- ✅ Polling starts
- ✅ Results display with TPC fields
- ⚠️ Data is placeholder (known issue)

**Failure Points**:
- ❌ CORS error in console
- ❌ API timeout
- ❌ Polling never completes
- ❌ Results never display
- ❌ TPC fields missing from response

#### Test 2: AI Generation Buttons (Known to be Mocked)
**Purpose**: Document exactly what's mocked

**Test Each Button**:
1. **"AI Generate Skills"** button
   - Click button
   - Observe: setTimeout delay, hardcoded skills appear
   - Status: 🔴 MOCKED (line 757)

2. **"AI Generate Job Scope"** button
   - Click button
   - Observe: setTimeout delay, hardcoded description
   - Status: 🔴 MOCKED (line 727)

3. **"AI Map to Mercer"** button
   - Click button
   - Observe: setTimeout delay, fake Mercer code
   - Status: 🔴 MOCKED (line 784)

4. **"AI Generate Alternatives"** button
   - Click button
   - Observe: setTimeout delay, fake alternative titles
   - Status: 🔴 MOCKED (line 808)

#### Test 3: Benchmarking Tab (Known to Show Fake Data)
**Steps**:
1. Complete Test 1 to get to results
2. Click "Benchmarking" tab
3. Observe market data displayed

**Expected**:
- ⚠️ Shows hardcoded MyCareersFuture listings
- ⚠️ Shows hardcoded Glassdoor data
- ⚠️ Shows hardcoded Mercer benchmarks
- Status: 🔴 ALL FAKE DATA

#### Test 4: Validation Tests
**Purpose**: Verify TPC field validation works in browser

**Test Cases**:
```javascript
// Test 1: Invalid employment_type
{
  "job_title": "Test",
  "employment_type": "INVALID"
}
// Expected: Validation error shown in UI

// Test 2: Internal grade special characters
{
  "job_title": "Test",
  "internal_grade": "Grade@#$%"
}
// Expected: Validation error

// Test 3: Array with too many items
{
  "job_title": "Test",
  "skills_required": [...Array(51).fill("skill")]
}
// Expected: Validation error (max 50)
```

---

## Phase 2: Remove Frontend Mocks (Weeks 2-3)

### Priority Order (based on user impact):

#### Week 2: Core Form Submission
**Tasks**:
1. ✅ Keep `handleAnalyze` as-is (already connected to API)
2. Test browser form submission works
3. Add loading states
4. Add error handling UI
5. Test with various TPC field combinations

**Success Criteria**:
- User can submit form and see results
- TPC fields flow through correctly
- Error messages display properly

#### Week 3: AI Generation Buttons
**Tasks**:

**1. Remove `handleGenerateSkills` Mock** (page.tsx:757)
```typescript
// BEFORE (Mocked):
const handleGenerateSkills = async () => {
  setIsGeneratingSkills(true)
  await new Promise((resolve) => setTimeout(resolve, 1500))
  // Hardcoded skills...
}

// AFTER (Real API):
const handleGenerateSkills = async () => {
  setIsGeneratingSkills(true)
  try {
    // Call backend endpoint: POST /api/v1/ai/extract-skills
    const response = await fetch(`${API_BASE_URL}/api/v1/ai/extract-skills`, {
      method: 'POST',
      body: JSON.stringify({
        job_title: jobData.jobTitle,
        job_description: jobData.jobSummary
      })
    })
    const data = await response.json()
    setJobData({ ...jobData, skillsRequired: data.skills })
  } catch (error) {
    // Show error to user
  } finally {
    setIsGeneratingSkills(false)
  }
}
```

**2. Remove `handleGenerateJobScope` Mock** (page.tsx:727)
- Create backend endpoint: `POST /api/v1/ai/generate-job-description`
- Connect frontend button to real API
- Remove setTimeout mock

**3. Remove `handleMapMercer` Mock** (page.tsx:784)
- Create backend endpoint: `POST /api/v1/ai/map-mercer-code`
- Connect frontend button to real API
- Remove setTimeout mock

**4. Remove `handleGenerateAlternatives` Mock** (page.tsx:808)
- Create backend endpoint: `POST /api/v1/ai/generate-alternative-titles`
- Connect frontend button to real API
- Remove setTimeout mock

**Success Criteria**:
- All AI buttons call real backend
- OpenAI API generates actual results
- Loading states work correctly
- Errors handled gracefully

---

## Phase 3: Fix Backend Processing (Weeks 4-5)

### Week 4: Skills Extraction

**Current State**: Returns empty array `[]`

**Tasks**:
1. Review current skills extraction code
2. Implement OpenAI-based extraction
3. Map skills to SSG TSC codes
4. Test with various job descriptions
5. Add confidence scoring

**Backend Endpoint** (NEW):
```python
# src/job_pricing/api/v1/ai.py (create new file)

@router.post("/ai/extract-skills")
async def extract_skills(request: SkillExtractionRequest):
    """
    Extract skills from job title and description using OpenAI.

    Returns:
    - List of extracted skills
    - SSG TSC mappings
    - Confidence scores
    """
    # Use OpenAI to extract skills
    # Map to SSG taxonomy
    # Return structured response
```

**Success Criteria**:
- Skills extraction returns real results
- SSG TSC mappings populated
- Confidence scores meaningful

### Week 5: Market Data Integration

**Current State**: Returns fake data (`total_data_points: 0`)

**Tasks**:
1. **MyCareersFuture Integration**:
   - Remove hardcoded data (lines 271-332)
   - Implement real API/scraper
   - Cache results in Redis

2. **Glassdoor Integration** (if available):
   - Remove hardcoded data (lines 335+)
   - Implement scraper/API
   - Handle rate limiting

3. **Mercer Data** (if API available):
   - Remove hardcoded benchmarks (lines 227-268)
   - Integrate real Mercer API
   - Update pricing calculations

**Success Criteria**:
- `total_data_points` > 0
- Real market data displayed
- Confidence scores based on actual data
- Data sources properly attributed

---

## Phase 4: Testing & Refinement (Week 6)

### Comprehensive Testing

**1. Browser Tests** (Manual):
- Test all form field combinations
- Test all AI generation buttons
- Test error scenarios
- Test loading states
- Test validation messages

**2. API Tests** (Automated):
```bash
# Test TPC fields end-to-end
curl -X POST http://localhost:8000/api/v1/job-pricing/requests \
  -H "Content-Type: application/json" \
  -d '{
    "job_title": "Senior Data Scientist",
    "portfolio": "TPC Group Corporate Office",
    "department": "People & Organisation",
    "employment_type": "permanent",
    "job_family": "Total Rewards",
    "internal_grade": "10",
    "skills_required": ["Python", "SQL", "ML"],
    "alternative_titles": ["Data Scientist", "ML Engineer"],
    "mercer_job_code": "ICT.DS.001"
  }'

# Verify all fields stored
# Verify processing completes
# Verify results accurate
```

**3. Load Tests**:
- 10 concurrent requests
- 50 concurrent requests
- 100 concurrent requests
- Measure response times
- Check for memory leaks

**4. Edge Cases**:
- Empty optional fields
- Maximum length strings
- Special characters in fields
- Array limits (50 items)
- Invalid employment types

---

## Phase 5: Authentication & Production Prep (Weeks 7-8)

### Week 7: Authentication

**Tasks**:
1. Implement JWT authentication
2. Add user registration/login
3. Associate requests with users
4. Add API key system
5. Update frontend auth flow

**Endpoints** (NEW):
```python
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
```

### Week 8: Production Hardening

**Tasks**:
1. Add rate limiting (100 req/min per user)
2. Configure monitoring (Prometheus)
3. Set up error tracking (Sentry)
4. Add structured logging
5. Security audit
6. Performance optimization
7. Documentation update

---

## Success Metrics

### After Week 1 (Testing):
- ✅ Documented exactly what works
- ✅ Identified all mocked components
- ✅ Tested browser workflow
- ✅ Validated API integration

### After Week 3 (Frontend Mocks Removed):
- ✅ All AI buttons call real backend
- ✅ No setTimeout mocks remain
- ✅ Real OpenAI responses
- ✅ Proper error handling

### After Week 5 (Backend Processing Fixed):
- ✅ Skills extraction functional
- ✅ Real market data integrated
- ✅ `total_data_points` > 0
- ✅ Confidence scores meaningful

### After Week 8 (Production Ready):
- ✅ Authentication working
- ✅ Monitoring configured
- ✅ Security audit passed
- ✅ Load tested (100 concurrent users)
- ✅ Documentation complete

---

## Tracking Progress

### Weekly Status Reports

**Template**:
```markdown
## Week X Status Report

### Completed:
- Task 1 ✅
- Task 2 ✅

### In Progress:
- Task 3 (50%)

### Blocked:
- Task 4 (waiting for Mercer API access)

### Risks:
- OpenAI rate limiting concerns
- Database performance at scale

### Next Week:
- Focus on X
- Complete Y
```

---

## Rollback Plan

**If Issues Found**:
1. Keep current working code in `main` branch
2. Work in `feature/*` branches
3. Test thoroughly before merging
4. Can rollback to previous working state

**Critical Paths**:
- Database migrations (reversible)
- API changes (versioned)
- Frontend (can deploy separately)

---

## Contact & Support

**Questions During Implementation**:
- Database: Check logs `docker-compose logs postgres`
- API: Check logs `docker-compose logs api`
- Frontend: Check browser console + Next.js terminal

**Escalation**:
- Critical blockers: Stop and reassess
- API rate limits: Implement caching
- Performance issues: Profile and optimize

---

**Generated**: 2025-11-12
**Timeline**: 6-8 weeks
**Status**: Ready to begin Week 1 testing
