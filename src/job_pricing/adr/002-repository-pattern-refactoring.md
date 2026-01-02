# ADR-002: Repository Pattern Refactoring for PricingCalculationServiceV3

**Status:** Proposed
**Date:** 2025-12-16
**Deciders:** Engineering Team
**Consulted:** Architecture Review
**Informed:** All Developers

## Context

`PricingCalculationServiceV3` initializes three repositories (`MercerRepository`, `ScrapingRepository`, `HRISRepository`) in its constructor but **does not use them**. Instead, direct SQLAlchemy session queries are used throughout the service.

This creates technical debt:
- **Inconsistency**: API endpoints (`internal_hris.py`, `external.py`) use these repositories correctly
- **Duplication**: Same query patterns written in multiple places
- **Testability**: Cannot easily mock data access for unit testing
- **Maintainability**: Changes require updates in multiple locations

## Decision Drivers

* Repository pattern is already established in the codebase
* Repositories provide reusable, tested query methods
* API endpoints already use repositories successfully
* Need to improve unit test coverage for pricing service
* Desire for consistent architecture across services

## Considered Options

* **Option 1**: Remove unused repositories from V3 (treat as dead code)
* **Option 2**: Keep repositories, refactor V3 to use them
* **Option 3**: Keep repositories initialized but document as future work

## Decision Outcome

Chosen option: **Option 3** (Keep and document), transitioning to **Option 2** (Full refactoring) in a future sprint.

### Rationale

- Removing repositories (Option 1) would increase technical debt and diverge from established patterns
- Full refactoring now (Option 2) is risky without comprehensive test coverage
- Documenting intent (Option 3) preserves architectural vision while deferring risk

### Implementation Plan

#### Phase 1: Documentation (COMPLETED)
- [x] Document why repositories are kept but unused in code comments
- [x] Create this ADR explaining the plan
- [x] Add TODO markers in code

#### Phase 2: Test Coverage (FUTURE)
- [ ] Add unit tests for repository methods
- [ ] Add integration tests for V3 service
- [ ] Ensure test coverage >80% before refactoring

#### Phase 3: Refactoring (FUTURE)
- [ ] Replace `_get_mercer_data()` direct queries with `mercer_repo` methods
- [ ] Replace `_get_mycareersfuture_data()` direct queries with `scraping_repo` methods
- [ ] Replace `_get_glassdoor_data()` direct queries with `scraping_repo` methods
- [ ] Replace `_get_internal_hris_data()` direct queries with `hris_repo` methods
- [ ] Replace `_get_applicants_data()` direct queries with `hris_repo` methods

### Positive Consequences

* Clear documentation of architectural intent
* No breaking changes to existing functionality
* Path forward for future improvement
* Maintains consistency with rest of codebase

### Negative Consequences

* Technical debt remains until Phase 3 complete
* Unused code in constructor (minor memory overhead)
* Risk of developers not understanding why repos are there

## Repository Method Mapping

| Current Direct Query | Target Repository Method |
|---------------------|-------------------------|
| `session.query(MercerMarketData)...` | `mercer_repo.get_latest_market_data()` |
| `session.query(MercerJobLibrary)...` | `mercer_repo.get_by_job_code()` / `get_by_family()` |
| `session.query(ScrapedJobListing).filter(source='my_careers_future')...` | `scraping_repo.search_by_title()` / `get_with_salary_data()` |
| `session.query(ScrapedJobListing).filter(source='glassdoor')...` | `scraping_repo.search_by_title()` with source filter |
| `session.query(InternalEmployee)...` | `hris_repo.get_salary_statistics()` |
| `session.query(Applicant)...` | `hris_repo.get_applicant_salary_statistics()` |

## Links

* Related file: `src/job_pricing/services/pricing_calculation_service_v3.py`
* Repositories: `src/job_pricing/repositories/`
* API usage examples: `src/job_pricing/api/v1/internal_hris.py`, `external.py`

---

*This ADR is specific to the Job Pricing module and isolated from other teams' decisions.*
