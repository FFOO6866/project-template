"""
External Applicants API Router

Endpoints for accessing external applicant data for market intelligence.
Production-ready with rate limiting and comprehensive error handling.

SECURITY: All endpoints require authentication.
- GET endpoint requires VIEW_APPLICANTS permission
"""

import logging
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from job_pricing.core.database import get_session
from job_pricing.core.config import get_settings
from job_pricing.core.constants import APIConfig
from job_pricing.repositories.hris_repository import HRISRepository
from job_pricing.models.auth import User, Permission
from job_pricing.api.dependencies.auth import get_current_active_user, PermissionChecker

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Get settings
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
            year=applicant.application_year or str(datetime.now().year),
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
        401: {"description": "Authentication required"},
        403: {"description": "Permission denied"},
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
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(PermissionChecker([Permission.VIEW_APPLICANTS])),
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
    - `success`: Request success status
    - `cached`: Whether response was served from cache

    **Note:** For privacy protection (PDPA compliance), personal data is anonymized
    when `data_anonymized` flag is set on applicant records.
    """
    try:
        logger.info(
            f"Fetching external applicants for user {current_user.email}: "
            f"job_title={job_title}, job_family={job_family}"
        )

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
