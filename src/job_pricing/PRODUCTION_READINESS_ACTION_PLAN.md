# Production Readiness Action Plan
**Current Status:** 25% Ready
**Target:** 100% Production-Ready
**Timeline:** 3 weeks (3-5 days per phase)

---

## Critical Findings Summary

After thorough analysis, the system has **critical gaps** that must be addressed:

1. ❌ **Mercer matching: 0 candidates found** (40% of functionality)
2. ❌ **Results not persisted to database** (no audit trail)
3. ❌ **Glassdoor broken** (datetime bug, 15% of functionality)
4. ❌ **HRIS not implemented** (15% of functionality)
5. ❌ **Applicants not implemented** (5% of functionality)
6. ❌ **No API server deployed** (just templates)
7. ⚠️ **Tests weakened to pass with fallback data**

**Evidence:**
- Benchmark shows: `"candidates_found": 0.0` (Mercer finds nothing)
- Benchmark shows: `"sources_used": 1.0` (only MCF working)
- Test logs show: "LLM determined no good match"
- Error logs show: "can't subtract offset-naive and offset-aware datetimes"

---

## Three-Phase Recovery Plan

### Phase 1: Fix Critical Blockers (Week 1)
**Goal:** Get core multi-source pricing working
**Effort:** 3-5 days

### Phase 2: Implement Missing Features (Week 2)
**Goal:** Complete all 5 data sources
**Effort:** 3-4 days

### Phase 3: Production Hardening (Week 3)
**Goal:** Deploy, secure, and validate
**Effort:** 3-4 days

---

## PHASE 1: Fix Critical Blockers (Week 1)

### Task 1.1: Fix Glassdoor Datetime Bug (30 min)
**Priority:** P1 - Quick Win
**Impact:** Restores 15% of functionality

**Problem:**
```python
# Current (broken):
recency_days = (datetime.now() - job.posted_date).days
# Error: can't subtract offset-naive and offset-aware datetimes
```

**Fix:**
```python
# File: pricing_calculation_service_v3.py, line ~227
from datetime import timezone

def _get_glassdoor_data(self, request: JobPricingRequest):
    # ... existing code ...

    # Fix datetime comparison:
    now = datetime.now(timezone.utc)
    posted_datetime = datetime.combine(
        job.posted_date,
        datetime.min.time(),
        tzinfo=timezone.utc
    )
    recency_days = (now - posted_datetime).days
```

**Validation:**
```bash
python test_glassdoor_integration.py
# Should show: "Glassdoor data retrieved successfully"
```

---

### Task 1.2: Implement Result Persistence (1-2 hours)
**Priority:** P1 - Critical
**Impact:** Enables audit trail and historical analysis

**Problem:**
- `PricingCalculationServiceV3.calculate_pricing()` creates result but doesn't save it
- Only requests are persisted, not results

**Fix:**
```python
# File: pricing_calculation_service_v3.py

def calculate_pricing(self, request: JobPricingRequest) -> PricingResult:
    # ... existing calculation logic ...

    # Create result object
    result = PricingResult(...)

    # NEW: Save result to database
    try:
        # Convert to database model
        from src.job_pricing.models import JobPricingResult

        db_result = JobPricingResult(
            request_id=request.id,
            currency='SGD',
            period='annual',
            recommended_min=result.recommended_min,
            recommended_max=result.recommended_max,
            target_salary=result.target_salary,
            p10=result.p10,
            p25=result.p25,
            p50=result.p50,
            p75=result.p75,
            p90=result.p90,
            confidence_score=result.confidence_score,
            confidence_level=self._get_confidence_level(result.confidence_score),
            summary_text=result.explanation,
            alternative_scenarios=result.alternative_scenarios,
            calculation_metadata={
                'algorithm_version': 'v3',
                'sources_used': len(result.source_contributions),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        )

        self.session.add(db_result)
        self.session.flush()  # Get ID without committing

        logger.info(f"Saved pricing result (ID: {db_result.id}) for request {request.id}")

    except Exception as e:
        logger.error(f"Failed to persist result: {e}")
        # Don't fail the whole request if persistence fails

    return result

def _get_confidence_level(self, score: float) -> str:
    if score >= 75:
        return 'high'
    elif score >= 50:
        return 'medium'
    else:
        return 'low'
```

**Also save data source contributions:**
```python
# After saving JobPricingResult:
for contrib in result.source_contributions:
    db_contrib = DataSourceContribution(
        result_id=db_result.id,
        source_name=contrib.source_name,
        weight_applied=contrib.weight,
        sample_size=contrib.sample_size,
        # ... other fields
    )
    self.session.add(db_contrib)
```

**Validation:**
```python
# Test that results are persisted:
session = get_session()
result = session.query(JobPricingResult).filter_by(request_id=test_request.id).first()
assert result is not None
assert result.target_salary > 0
```

---

### Task 1.3: Debug Mercer Vector Search (2-4 hours)
**Priority:** P1 - Most Critical
**Impact:** Restores 40% of functionality

**Problem:**
- Vector search returns 0 candidates
- Benchmark shows: `"candidates_found": 0.0`

**Investigation Steps:**

**Step 1: Verify Mercer data actually in database**
```python
# File: debug_mercer_matching.py
from src.job_pricing.core.database import get_session
from src.job_pricing.models import MercerJobLibrary

session = get_session()

# Check total jobs
total = session.query(MercerJobLibrary).count()
print(f"Total Mercer jobs: {total}")

# Check jobs with embeddings
with_embeddings = session.query(MercerJobLibrary).filter(
    MercerJobLibrary.embedding.isnot(None)
).count()
print(f"Jobs with embeddings: {with_embeddings}")

# Sample a few jobs
samples = session.query(MercerJobLibrary).limit(5).all()
for job in samples:
    print(f"\n{job.job_code}: {job.job_title}")
    print(f"  Description: {job.job_description[:100] if job.job_description else 'None'}...")
    print(f"  Embedding dimensions: {len(job.embedding) if job.embedding else 0}")
```

**Step 2: Test embedding similarity search manually**
```python
# Check if vector search query is working
from pgvector.sqlalchemy import Vector

query_embedding = matching_service.generate_query_embedding("Software Engineer")

# Raw SQL test
raw_query = """
SELECT job_code, job_title,
       1 - (embedding <=> :query_embedding::vector) as similarity
FROM mercer_job_library
WHERE embedding IS NOT NULL
ORDER BY embedding <=> :query_embedding::vector
LIMIT 5
"""

results = session.execute(raw_query, {'query_embedding': query_embedding})
for row in results:
    print(f"{row.job_code}: {row.job_title} - {row.similarity:.2%}")
```

**Step 3: Check JobMatchingService.find_similar_jobs()**
```python
# File: services/job_matching_service.py
# Add debugging:

def find_similar_jobs(self, job_title: str, job_description: str = "", ...):
    query_text = f"{job_title}. {job_description}".strip()
    query_embedding = self.generate_query_embedding(query_text)

    # DEBUG: Log query info
    logger.info(f"Searching for: {query_text}")
    logger.info(f"Embedding dimensions: {len(query_embedding)}")

    # Build query
    similarity_expr = 1 - MercerJobLibrary.embedding.cosine_distance(query_embedding)

    query = self.session.query(MercerJobLibrary, similarity_expr.label('similarity'))
    query = query.filter(MercerJobLibrary.embedding.isnot(None))

    # DEBUG: Check query before filters
    total_count = query.count()
    logger.info(f"Total jobs with embeddings: {total_count}")

    if job_family:
        query = query.filter(MercerJobLibrary.family == job_family)
    if career_level:
        query = query.filter(MercerJobLibrary.career_level == career_level)

    query = query.order_by(similarity_expr.desc()).limit(top_k)

    results = query.all()

    # DEBUG: Log results
    logger.info(f"Found {len(results)} candidates")
    for job, sim in results:
        logger.info(f"  {job.job_code}: {job.job_title} - {sim:.2%}")

    # ... rest of method
```

**Possible Root Causes:**
1. **Embedding column is NULL** - Check data loader
2. **Query filters too restrictive** - job_family or career_level filtering out all results
3. **Vector distance calculation failing** - pgvector not properly configured
4. **Wrong embedding dimensions** - Mismatch between query and stored embeddings

**Fix Once Root Cause Found:**
- If data issue: Re-run Mercer loader with proper embedding generation
- If query issue: Adjust filtering logic
- If pgvector issue: Reinstall extension or check database setup

---

### Task 1.4: Strengthen Integration Tests (2-3 hours)
**Priority:** P1 - Prevent Regression
**Impact:** Ensures real functionality is tested

**Problem:**
- Tests accept fallback calculations
- Tests pass even when Mercer returns 0 matches
- False confidence in system quality

**Fix:**
```python
# File: test_api_integration.py

def test_mercer_integration_required(self) -> bool:
    """Test that Mercer integration is actually working."""
    try:
        from src.job_pricing.services.job_matching_service import JobMatchingService

        matching_service = JobMatchingService(self.session)

        # Test with a job that SHOULD match in Mercer library
        test_jobs = [
            'Software Engineer',
            'Data Scientist',
            'Product Manager',
            'HR Business Partner'
        ]

        matches_found = 0
        for job_title in test_jobs:
            match = matching_service.find_best_match(
                job_title=job_title,
                job_description=f'{job_title} with relevant experience',
                use_llm_reasoning=True
            )

            if match and match.get('job_code'):
                matches_found += 1
                logger.info(f"✓ Mercer matched: {job_title} -> {match['job_code']}")

        # REQUIRE at least 50% match rate
        match_rate = matches_found / len(test_jobs)

        assert match_rate >= 0.5, f"Mercer matching too low: {match_rate:.0%} (expected >=50%)"

        self.log_test(
            "Mercer Integration Required",
            True,
            f"Matched {matches_found}/{len(test_jobs)} jobs ({match_rate:.0%})"
        )
        return True

    except AssertionError as e:
        self.log_test("Mercer Integration Required", False, str(e))
        return False

def test_multi_source_required(self) -> bool:
    """Require at least 2 data sources for common jobs."""
    try:
        request = JobPricingRequest(
            job_title='Software Engineer',
            job_description='Python developer with backend experience',
            location_text='Singapore',
            requested_by='test',
            requestor_email='test@example.com',
            status='pending',
            urgency='normal'
        )
        self.session.add(request)
        self.session.flush()

        pricing_service = PricingCalculationServiceV3(self.session)
        result = pricing_service.calculate_pricing(request)

        num_sources = len(result.source_contributions)

        # REQUIRE multiple sources (not fallback)
        assert num_sources >= 2, f"Only {num_sources} source(s) - need at least 2"
        assert result.confidence_score >= 60, f"Confidence too low: {result.confidence_score}"

        self.log_test(
            "Multi-Source Required",
            True,
            f"{num_sources} sources, {result.confidence_score:.0f}% confidence"
        )
        return True

    except AssertionError as e:
        self.log_test("Multi-Source Required", False, str(e))
        return False
```

**Impact:** Tests will now **fail** if system is broken, not pass with fallback.

---

## PHASE 2: Implement Missing Features (Week 2)

### Task 2.1: Implement HRIS Integration (4-8 hours)
**Priority:** P2
**Impact:** Adds 15% functionality

**Current State:**
```python
def _get_hris_data(self, request: JobPricingRequest):
    return None  # Placeholder
```

**Implementation:**
```python
def _get_hris_data(
    self,
    request: JobPricingRequest
) -> Optional[DataSourceContribution]:
    """Get salary data from internal HRIS system."""
    try:
        from src.job_pricing.models import InternalEmployee

        # Find similar employees by job title matching
        similar_employees = self.session.query(InternalEmployee).filter(
            InternalEmployee.job_title.ilike(f'%{request.job_title}%'),
            InternalEmployee.current_salary.isnot(None),
            InternalEmployee.is_active == True
        ).all()

        if len(similar_employees) < 3:
            logger.info(f"Insufficient HRIS data: {len(similar_employees)} employees")
            return None

        # Extract salary data
        salaries = [emp.current_salary for emp in similar_employees]

        # Calculate percentiles
        data_points = salaries
        p10, p25, p50, p75, p90 = np.percentile(salaries, [10, 25, 50, 75, 90])

        # Calculate recency (average tenure)
        now = datetime.now(timezone.utc)
        avg_data_age_days = int(np.mean([
            (now - datetime.combine(emp.hire_date, datetime.min.time(), tzinfo=timezone.utc)).days
            for emp in similar_employees
            if emp.hire_date
        ]))

        return DataSourceContribution(
            source_name="hris",
            weight=self.WEIGHTS["hris"],
            sample_size=len(similar_employees),
            data_points=data_points,
            p10=p10,
            p25=p25,
            p50=p50,
            p75=p75,
            p90=p90,
            recency_days=avg_data_age_days,
            match_quality=0.8,  # High quality - exact company context
        )

    except Exception as e:
        logger.error(f"Error querying HRIS data: {e}")
        return None
```

**Data Requirements:**
- Need actual HRIS data or sample data
- Schema: InternalEmployee table with job_title, current_salary, hire_date

---

### Task 2.2: Implement Applicant Data Integration (2-4 hours)
**Priority:** P2
**Impact:** Adds 5% functionality

**Implementation:**
```python
def _get_applicant_data(
    self,
    request: JobPricingRequest
) -> Optional[DataSourceContribution]:
    """Get salary data from applicant/candidate records."""
    try:
        from src.job_pricing.models import Applicant

        # Find applicants for similar positions
        similar_applicants = self.session.query(Applicant).filter(
            Applicant.applied_position.ilike(f'%{request.job_title}%'),
            Applicant.expected_salary.isnot(None),
            Applicant.application_date >= datetime.now() - timedelta(days=365)
        ).all()

        if len(similar_applicants) < 5:
            return None

        # Extract salary expectations
        salaries = [app.expected_salary for app in similar_applicants]

        # Calculate percentiles
        p10, p25, p50, p75, p90 = np.percentile(salaries, [10, 25, 50, 75, 90])

        # Calculate average recency
        now = datetime.now(timezone.utc)
        avg_recency = int(np.mean([
            (now - datetime.combine(app.application_date, datetime.min.time(), tzinfo=timezone.utc)).days
            for app in similar_applicants
        ]))

        return DataSourceContribution(
            source_name="applicants",
            weight=self.WEIGHTS["applicants"],
            sample_size=len(similar_applicants),
            data_points=salaries,
            p10=p10,
            p25=p25,
            p50=p50,
            p75=p75,
            p90=p90,
            recency_days=avg_recency,
            match_quality=0.7,  # Moderate - self-reported expectations
        )

    except Exception as e:
        logger.error(f"Error querying applicant data: {e}")
        return None
```

---

### Task 2.3: Validate Mercer Job Library Data Quality (2-4 hours)
**Priority:** P2
**Impact:** Ensures accurate matching

**Investigation:**
```python
# Check what's actually in the Mercer library
session = get_session()

# Sample jobs with descriptions
jobs = session.query(MercerJobLibrary).limit(50).all()

for job in jobs:
    print(f"\nJob: {job.job_code}")
    print(f"Title: {job.job_title}")
    print(f"Description: {job.job_description[:200] if job.job_description else 'MISSING'}...")

    # Check if description makes sense for title
    if job.job_description:
        if 'technical recruiting' in job.job_description.lower() and 'recruiting' not in job.job_title.lower():
            print("⚠️ WARNING: Description mismatch!")
```

**If Data Issues Found:**
- Re-run Mercer loader with correct source file
- Validate CSV/data source has correct columns
- Check for data corruption during load

---

## PHASE 3: Production Hardening (Week 3)

### Task 3.1: Deploy API Server (2-4 hours)

**Build API:**
```python
# File: api_server.py (provided in deployment guide)
# Test locally:
python src/job_pricing/api_server.py

# In another terminal:
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/v1/pricing \
  -H "Content-Type: application/json" \
  -d '{"job_title": "Software Engineer", "location_text": "Singapore", ...}'
```

---

### Task 3.2: Test Docker Deployment (2-4 hours)

```bash
cd src/job_pricing

# Build containers
docker-compose build

# Start services
docker-compose up -d

# Check health
docker-compose logs app
curl http://localhost:8000/health

# Run integration tests against Docker deployment
docker-compose exec app python test_api_integration.py
```

---

### Task 3.3: Implement Authentication (2-4 hours)

```python
# Add JWT authentication to API
from flask_jwt_extended import JWTManager, jwt_required

app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
jwt = JWTManager(app)

@app.route('/api/v1/pricing', methods=['POST'])
@jwt_required()
def calculate_pricing():
    # Protected endpoint
    pass
```

---

## Success Criteria (End of 3 Weeks)

### Functional Requirements
- [ ] **All 5 data sources operational**
  - [ ] Mercer: Finding matches (>50% match rate)
  - [ ] MCF: Working (already ✓)
  - [ ] Glassdoor: Fixed datetime bug
  - [ ] HRIS: Implemented and tested
  - [ ] Applicants: Implemented and tested

- [ ] **Multi-source aggregation working**
  - [ ] Common jobs use 2-3 sources
  - [ ] Confidence scores >60%
  - [ ] Weighted aggregation validated

- [ ] **Database persistence complete**
  - [ ] Results saved to JobPricingResult
  - [ ] Data source contributions tracked
  - [ ] Historical data queryable

### API & Deployment
- [ ] **API server deployed and tested**
  - [ ] Health check responding
  - [ ] Pricing endpoint working
  - [ ] Error handling validated

- [ ] **Docker deployment working**
  - [ ] Containers build successfully
  - [ ] Services start and communicate
  - [ ] Integration tests pass in Docker

- [ ] **Security implemented**
  - [ ] JWT authentication working
  - [ ] Rate limiting configured
  - [ ] Input validation comprehensive

### Testing & Validation
- [ ] **Integration tests strengthened**
  - [ ] Tests require real data sources
  - [ ] Tests fail if Mercer not working
  - [ ] All 11 tests passing with real data

- [ ] **Performance validated**
  - [ ] Real performance benchmarks (with 5 sources)
  - [ ] Response time <5 seconds
  - [ ] Throughput >15 req/min

- [ ] **Load testing complete**
  - [ ] 50+ concurrent requests tested
  - [ ] System stable under load
  - [ ] Error rate <1%

---

## Tracking Progress

**Weekly Checkpoints:**

**End of Week 1:**
- [ ] Glassdoor fixed
- [ ] Results persisted to database
- [ ] Mercer vector search debugged and fixed
- [ ] Integration tests strengthened
- **Target:** 60% production-ready

**End of Week 2:**
- [ ] HRIS integrated
- [ ] Applicants integrated
- [ ] Mercer data quality validated
- [ ] All 5 sources working
- **Target:** 85% production-ready

**End of Week 3:**
- [ ] API deployed
- [ ] Docker tested
- [ ] Authentication implemented
- [ ] Load testing complete
- **Target:** 100% production-ready

---

## Risk Mitigation

**Risk 1: Mercer vector search can't be fixed quickly**
- **Mitigation:** Focus on other sources first, come back with more time
- **Fallback:** Launch with 4 sources, add Mercer later

**Risk 2: HRIS/Applicant data not available**
- **Mitigation:** Create sample data for testing
- **Fallback:** Launch with 3 sources (MCF, Glassdoor, Mercer), add HRIS later

**Risk 3: Docker deployment issues**
- **Mitigation:** Test locally first, gradual deployment
- **Fallback:** Direct Python deployment, add Docker later

---

**Plan Created:** November 17, 2025
**Estimated Timeline:** 3 weeks (15-20 working days)
**Current Status:** 25% ready
**Target Status:** 100% production-ready
