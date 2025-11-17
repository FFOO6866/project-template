# External Applicants Integration - Implementation Guide

## Overview
This document outlines the complete implementation plan to replace hardcoded external applicants data with real API integration.

## ✅ Completed Work

### 1. Database Model Updates
**File:** `src/job_pricing/src/job_pricing/models/hris.py`

Updated the `Applicant` model (lines 286-482) with additional fields:
- `name`: Applicant name (nullable for privacy)
- `current_organisation`: Current employer organization
- `current_title`: Current job title at current employer
- `organisation_summary`: Summary description of current organization
- `role_scope`: Scope and responsibilities of current role
- `application_year`: Year of application (for grouping/filtering)
- `sharepoint_file_id`: SharePoint file ID if synced from SharePoint folder
- `last_updated`: Last update timestamp

Updated application status constraints to include:
- 'Applied', 'Shortlisted', 'Interview Stage 1', 'Interview Stage 2'
- 'Offered', 'Offer Extended', 'Rejected', 'Withdrawn'
- 'Declined Offer', 'Hired'

### 2. Repository Methods
**File:** `src/job_pricing/src/job_pricing/repositories/hris_repository.py`

Updated methods:
- `get_applicants_by_position()`: Now uses `applied_job_title` field
- `get_applicant_salary_statistics()`: Updated field references
- `create_applicant()`: Updated to match new model structure
- **Added:** `get_all_applicants()`: Query all applicants with optional job_family filter

## 📋 Remaining Work

### 3. Database Migration
**Location:** `alembic/versions/`

Create a new Alembic migration to add the new columns to the `applicants` table:

```bash
cd src/job_pricing
alembic revision -m "add_applicant_extended_fields"
```

**Migration content:**
```python
def upgrade():
    # Add new columns
    op.add_column('applicants', sa.Column('name', sa.String(200), nullable=True))
    op.add_column('applicants', sa.Column('current_organisation', sa.String(200), nullable=True))
    op.add_column('applicants', sa.Column('current_title', sa.String(200), nullable=True))
    op.add_column('applicants', sa.Column('organisation_summary', sa.Text(), nullable=True))
    op.add_column('applicants', sa.Column('role_scope', sa.Text(), nullable=True))
    op.add_column('applicants', sa.Column('application_year', sa.String(4), nullable=True))
    op.add_column('applicants', sa.Column('sharepoint_file_id', sa.String(255), nullable=True))
    op.add_column('applicants', sa.Column('last_updated', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False))

    # Update constraint to include new statuses
    op.drop_constraint('check_application_status', 'applicants', type_='check')
    op.create_check_constraint(
        'check_application_status',
        'applicants',
        "application_status IN ('Applied', 'Shortlisted', 'Interview Stage 1', 'Interview Stage 2', 'Offered', 'Offer Extended', 'Rejected', 'Withdrawn', 'Declined Offer', 'Hired')"
    )

    # Add indexes
    op.create_index('idx_applicants_year', 'applicants', ['application_year'])
    op.create_index('idx_applicants_organisation', 'applicants', ['current_organisation'])

    # Rename column if needed
    op.alter_column('applicants', 'position_applied_for', new_column_name='applied_job_title')

def downgrade():
    # Reverse all changes
    op.drop_index('idx_applicants_organisation', 'applicants')
    op.drop_index('idx_applicants_year', 'applicants')
    op.drop_column('applicants', 'last_updated')
    op.drop_column('applicants', 'sharepoint_file_id')
    op.drop_column('applicants', 'application_year')
    op.drop_column('applicants', 'role_scope')
    op.drop_column('applicants', 'organisation_summary')
    op.drop_column('applicants', 'current_title')
    op.drop_column('applicants', 'current_organisation')
    op.drop_column('applicants', 'name')
    op.alter_column('applicants', 'applied_job_title', new_column_name='position_applied_for')
```

Run migration:
```bash
alembic upgrade head
```

### 4. API Endpoint
**File:** `src/job_pricing/src/job_pricing/api/v1/applicants.py` (NEW)

Create a new API router for external applicants:

```python
"""
External Applicants API Router

Endpoints for accessing external applicant data for market intelligence.
Production-ready with caching, rate limiting, and comprehensive error handling.
"""

import logging
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.job_pricing.core.database import get_session
from src.job_pricing.core.config import get_settings
from src.job_pricing.core.constants import APIConfig
from src.job_pricing.repositories.hris_repository import HRISRepository

# Initialize
logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)
settings = get_settings()
router = APIRouter()


# ==============================================================================
# Pydantic Models
# ==============================================================================

class ApplicantResponse(BaseModel):
    """Single applicant data response."""
    year: str
    name: Optional[str] = None
    organisation: Optional[str] = None
    title: Optional[str] = None
    experience: Optional[int] = None
    currentSalary: Optional[float] = None
    expectedSalary: Optional[float] = None
    orgSummary: Optional[str] = None
    roleScope: Optional[str] = None
    status: str

    class Config:
        from_attributes = True


class ExternalApplicantsResponse(BaseModel):
    """Response model for external applicants endpoint."""
    applicants: List[ApplicantResponse]
    total: int
    success: bool = True
    cached: bool = False


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    details: Optional[str] = None


# ==============================================================================
# Dependency Injection
# ==============================================================================

def get_hris_repository(session: Session = Depends(get_session)) -> HRISRepository:
    """Dependency to get HRIS repository instance."""
    return HRISRepository(session)


# ==============================================================================
# Transformation Functions
# ==============================================================================

def transform_applicant(applicant) -> Optional[ApplicantResponse]:
    """Transform database Applicant model to API response model."""
    try:
        return ApplicantResponse(
            year=applicant.application_year or datetime.now().year,
            name=applicant.name if not applicant.data_anonymized else None,
            organisation=applicant.current_organisation,
            title=applicant.current_title,
            experience=applicant.years_of_experience,
            currentSalary=float(applicant.current_salary) if applicant.current_salary else None,
            expectedSalary=float(applicant.expected_salary) if applicant.expected_salary else None,
            orgSummary=applicant.organisation_summary,
            roleScope=applicant.role_scope,
            status=applicant.application_status or "Applied"
        )
    except Exception as e:
        logger.error(f"Failed to transform applicant {applicant.id}: {e}")
        return None


# ==============================================================================
# Endpoints
# ==============================================================================

@router.get(
    "/external-applicants",
    response_model=ExternalApplicantsResponse,
    summary="Get External Applicant Data",
    description="Fetch external applicant data for market intelligence and salary benchmarking",
    responses={
        200: {"description": "Successfully retrieved applicant data"},
        400: {"model": ErrorResponse, "description": "Invalid request parameters"},
        503: {"model": ErrorResponse, "description": "Database unavailable"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
        429: {"description": "Rate limit exceeded"},
    },
)
@limiter.limit(f"{APIConfig.RATE_LIMIT_PER_MINUTE}/minute")
async def get_external_applicants(
    request: Request,
    job_title: Optional[str] = Query(
        None,
        description="Job title filter (optional, case-insensitive partial match)",
        min_length=2,
        max_length=200,
        example="Total Rewards"
    ),
    job_family: Optional[str] = Query(
        None,
        description="Job family filter (optional)",
        max_length=100,
        example="HR"
    ),
    limit: int = Query(
        APIConfig.DEFAULT_PAGE_SIZE,
        description="Maximum number of results to return",
        ge=1,
        le=APIConfig.MAX_PAGE_SIZE
    ),
    repository: HRISRepository = Depends(get_hris_repository),
):
    """
    Get external applicant data for market intelligence.

    This endpoint returns applicant salary expectations and profiles
    to help with competitive salary benchmarking.

    **Query Parameters:**
    - `job_title` (optional): Filter by job title (e.g., "Director", "Manager")
    - `job_family` (optional): Filter by job family (e.g., "HR", "IT")
    - `limit` (optional): Maximum results to return (default: 20, max: 100)

    **Returns:**
    - `applicants`: Array of applicant data objects
    - `total`: Total number of applicants returned
    - `cached`: Whether response was served from cache

    **Note:** For privacy protection (PDPA compliance), personal data is anonymized
    when `data_anonymized` flag is set on applicant records.
    """
    try:
        logger.info(f"Fetching external applicants: job_title={job_title}, job_family={job_family}")

        # Query applicants
        if job_title:
            applicants = repository.get_applicants_by_position(
                position_title=job_title,
                skip=0,
                limit=limit
            )
        else:
            applicants = repository.get_all_applicants(
                skip=0,
                limit=limit,
                job_family=job_family
            )

        # Transform to response models
        transformed_applicants = [
            transform_applicant(app) for app in applicants
        ]
        valid_applicants = [app for app in transformed_applicants if app is not None]

        logger.info(f"Successfully retrieved {len(valid_applicants)} external applicants")

        return ExternalApplicantsResponse(
            applicants=valid_applicants,
            total=len(valid_applicants),
            success=True,
            cached=False
        )

    except Exception as e:
        logger.error(f"Failed to fetch external applicants: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve external applicant data"
        )
```

**Register router in main.py:**
```python
# In src/job_pricing/src/job_pricing/api/main.py
from src.job_pricing.api.v1 import applicants

app.include_router(
    applicants.router,
    prefix="/api/v1",
    tags=["External Applicants"]
)
```

### 5. React Hook
**File:** `frontend/hooks/useExternalApplicants.ts` (NEW)

```typescript
import { useState, useEffect, useCallback, useRef } from 'react'
import { externalApplicantsApi } from '@/lib/api/externalApplicantsApi'

export interface ExternalApplicant {
  year: string
  name?: string
  organisation?: string
  title?: string
  experience?: number
  currentSalary?: number
  expectedSalary?: number
  orgSummary?: string
  roleScope?: string
  status: string
}

export interface UseExternalApplicantsOptions {
  jobTitle?: string
  jobFamily?: string
  enabled?: boolean
}

export interface UseExternalApplicantsReturn {
  data: ExternalApplicant[]
  loading: boolean
  error: Error | null
  refetch: () => Promise<void>
  disabled: boolean
}

const DEBOUNCE_DELAY = 500

export function useExternalApplicants(
  options: UseExternalApplicantsOptions
): UseExternalApplicantsReturn {
  const { jobTitle, jobFamily, enabled = true } = options

  const [data, setData] = useState<ExternalApplicant[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const [disabled, setDisabled] = useState(false)

  const abortControllerRef = useRef<AbortController | null>(null)
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null)

  const fetchData = useCallback(async (signal: AbortSignal) => {
    try {
      setLoading(true)
      setError(null)

      const response = await externalApplicantsApi.getExternalApplicants({
        jobTitle,
        jobFamily,
        signal,
      })

      if (response.success && response.applicants) {
        setData(response.applicants)
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        console.error('[useExternalApplicants] Error:', err)
        setError(err)
        setDisabled(true)
      }
    } finally {
      setLoading(false)
    }
  }, [jobTitle, jobFamily])

  const refetch = useCallback(async () => {
    const controller = new AbortController()
    await fetchData(controller.signal)
  }, [fetchData])

  useEffect(() => {
    if (!enabled || (!jobTitle && !jobFamily)) {
      setData([])
      return
    }

    // Cancel previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }

    // Clear previous debounce timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
    }

    // Debounce API call
    debounceTimerRef.current = setTimeout(() => {
      const controller = new AbortController()
      abortControllerRef.current = controller
      fetchData(controller.signal)
    }, DEBOUNCE_DELAY)

    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current)
      }
    }
  }, [enabled, jobTitle, jobFamily, fetchData])

  return {
    data,
    loading,
    error,
    refetch,
    disabled,
  }
}
```

### 6. API Client
**File:** `frontend/lib/api/externalApplicantsApi.ts` (NEW)

```typescript
import { config } from '@/lib/config'

export interface ExternalApplicantsRequest {
  jobTitle?: string
  jobFamily?: string
  signal?: AbortSignal
}

export interface ExternalApplicant {
  year: string
  name?: string
  organisation?: string
  title?: string
  experience?: number
  currentSalary?: number
  expectedSalary?: number
  orgSummary?: string
  roleScope?: string
  status: string
}

export interface ExternalApplicantsResponse {
  applicants: ExternalApplicant[]
  total: number
  success: boolean
  cached: boolean
}

export const externalApplicantsApi = {
  async getExternalApplicants(
    params: ExternalApplicantsRequest
  ): Promise<ExternalApplicantsResponse> {
    const queryParams = new URLSearchParams()

    if (params.jobTitle) {
      queryParams.append('job_title', params.jobTitle)
    }
    if (params.jobFamily) {
      queryParams.append('job_family', params.jobFamily)
    }

    const url = `${config.api.baseUrl}/api/v1/external-applicants?${queryParams.toString()}`

    const response = await fetch(url, {
      signal: params.signal,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return response.json()
  },
}
```

### 7. Frontend Update
**File:** `frontend/app/job-pricing/page.tsx`

**Changes needed:**

1. **Import the hook** (add at top):
```typescript
import { useExternalApplicants } from '@/hooks/useExternalApplicants'
```

2. **Add hook call** (around line 190):
```typescript
const {
  data: externalApplicantsData,
  loading: applicantsLoading,
  error: applicantsError,
  disabled: applicantsDisabled,
} = useExternalApplicants({
  jobTitle: jobData.jobTitle,
  jobFamily: jobData.jobFamily,
  enabled: !!jobData.jobTitle,
})
```

3. **Replace hardcoded array** (delete lines 277-326):
```typescript
// DELETE THIS:
const externalApplicants = [
  {
    year: "2024",
    name: "Lim Jia Wei",
    // ... all hardcoded data
  },
  // ...
]

// REPLACE WITH:
const externalApplicants = externalApplicantsData || []
```

4. **Update UI to show loading/error states** (around line 1850):
```typescript
{applicantsLoading && (
  <div className="animate-pulse space-y-3">
    <div className="h-4 bg-gray-200 rounded w-3/4"></div>
    <div className="h-4 bg-gray-200 rounded w-full"></div>
  </div>
)}

{applicantsError && (
  <Alert className="border-red-200 bg-red-50">
    <AlertCircle className="h-4 w-4 text-red-600" />
    <AlertDescription className="text-red-800">
      <strong>Error loading applicant data:</strong> {applicantsError.message}
    </AlertDescription>
  </Alert>
)}

{!applicantsLoading && !applicantsError && externalApplicants.length === 0 && (
  <Alert>
    <Info className="h-4 w-4" />
    <AlertDescription>
      No external applicant data available for this role.
    </AlertDescription>
  </Alert>
)}
```

### 8. Seed Sample Data
**File:** `src/job_pricing/seed_applicants.py` (NEW)

Create a script to populate the database with the hardcoded applicant data:

```python
"""
Seed script to populate applicants table with sample data
"""
from datetime import date
from src.job_pricing.core.database import SessionLocal
from src.job_pricing.repositories.hris_repository import HRISRepository

def seed_applicants():
    session = SessionLocal()
    repo = HRISRepository(session)

    applicants_data = [
        {
            "applicant_id": "APP-2024-001",
            "name": "Lim Jia Wei",
            "current_organisation": "CapitaLand Group",
            "current_title": "Global Rewards Director",
            "applied_job_title": "Assistant Director, Total Rewards",
            "years_of_experience": 15,
            "current_salary": 12500,
            "expected_salary": 15000,
            "organisation_summary": "Leading property development and investment company in Asia",
            "role_scope": "Strategic rewards design across global property development portfolio",
            "application_status": "Interview Stage 2",
            "application_date": date(2024, 11, 1),
            "application_year": "2024",
            "job_family": "HR",
        },
        # Add all 6 applicants from the hardcoded data
    ]

    try:
        for app_data in applicants_data:
            repo.create_applicant(**app_data)

        session.commit()
        print(f"✅ Successfully seeded {len(applicants_data)} applicants")
    except Exception as e:
        session.rollback()
        print(f"❌ Error seeding applicants: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    seed_applicants()
```

Run: `python seed_applicants.py`

## 📁 SharePoint Integration (Future Enhancement)

### Overview
External applicant data can be synced from a SharePoint folder where HR stores application documents.

### Implementation Approach

1. **SharePoint Authentication**
   - Use Microsoft Graph API with OAuth 2.0
   - Store credentials in `.env.production`

2. **Sync Script**
   - Create `sync_sharepoint_applicants.py`
   - Parse Excel files or PDFs in SharePoint folder
   - Extract applicant data using Azure Form Recognizer or OpenAI

3. **Automation**
   - Schedule sync with Celery Beat (daily at 2 AM)
   - Store `sharepoint_file_id` for deduplication

4. **Required Environment Variables**
```bash
SHAREPOINT_SITE_ID=your-site-id
SHAREPOINT_FOLDER_PATH=/HR/Applicants
MICROSOFT_CLIENT_ID=your-client-id
MICROSOFT_CLIENT_SECRET=your-client-secret
MICROSOFT_TENANT_ID=your-tenant-id
```

## 🚀 Deployment Checklist

- [ ] Run database migration
- [ ] Seed initial applicant data
- [ ] Test API endpoint with Postman/curl
- [ ] Test React hook in development
- [ ] Verify frontend displays real data
- [ ] Test error handling and loading states
- [ ] Update API documentation
- [ ] Deploy to production
- [ ] Monitor logs for errors

## 📝 Testing Commands

```bash
# Test API endpoint
curl "http://localhost:8000/api/v1/external-applicants?job_title=Director&job_family=HR"

# Test with different filters
curl "http://localhost:8000/api/v1/external-applicants?job_family=HR&limit=10"

# Run frontend in dev mode
cd frontend && npm run dev

# Check database
docker-compose exec postgres psql -U job_pricing_user -d job_pricing_db
SELECT * FROM applicants LIMIT 5;
```

## 🔗 Related Files

- Model: `src/job_pricing/src/job_pricing/models/hris.py`
- Repository: `src/job_pricing/src/job_pricing/repositories/hris_repository.py`
- API: `src/job_pricing/src/job_pricing/api/v1/applicants.py` (to be created)
- Hook: `frontend/hooks/useExternalApplicants.ts` (to be created)
- Frontend: `frontend/app/job-pricing/page.tsx` (lines 277-326, 1838-2078)
