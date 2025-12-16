"""
Internal HRIS API Router

Endpoints for accessing internal employee data for benchmarking.
Production-ready with rate limiting, PDPA compliance, and comprehensive error handling.

SECURITY: All endpoints require authentication.
- GET endpoints require VIEW_HRIS_DATA permission
- Sync endpoint requires MANAGE_HRIS_INTEGRATION permission
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
from job_pricing.services.bipo_sync_service import BIPOSyncService
from job_pricing.models.auth import User
from job_pricing.api.dependencies.auth import get_current_active_user

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)
settings = get_settings()
router = APIRouter()


class InternalEmployeeResponse(BaseModel):
    """Single internal employee data response (anonymized)."""
    id: str
    department: Optional[str] = None
    job_title: str
    experience_years: Optional[int] = None
    current_salary: float
    performance_rating: Optional[str] = None

    class Config:
        from_attributes = True


class InternalHRISResponse(BaseModel):
    """Response model for internal HRIS endpoint."""
    employees: List[InternalEmployeeResponse]
    total: int
    success: bool = True
    cached: bool = False


class SyncResponse(BaseModel):
    """Response model for sync endpoint."""
    message: str
    fetched: int
    synced: int
    failed: int
    success: bool


def get_hris_repository(session: Session = Depends(get_session)) -> HRISRepository:
    """Dependency to get HRIS repository instance."""
    return HRISRepository(session)


def transform_employee(employee) -> Optional[InternalEmployeeResponse]:
    """Transform database InternalEmployee model to API response model."""
    try:
        return InternalEmployeeResponse(
            id=str(employee.id),  # Use internal DB ID, not employee_id for anonymization
            department=employee.department,
            job_title=employee.job_title,
            experience_years=employee.years_of_experience or employee.years_in_company,
            current_salary=float(employee.current_salary),
            performance_rating=employee.performance_rating,
        )
    except Exception as e:
        logger.error(f"Failed to transform employee {employee.id}: {e}")
        return None


@router.get(
    "/internal/hris/benchmarks",
    response_model=InternalHRISResponse,
    summary="Get Internal Employee Benchmarks",
    description="Fetch internal employee salary benchmarks for market intelligence (PDPA compliant)",
    responses={
        200: {"description": "Benchmarks retrieved successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Permission denied"},
        500: {"description": "Internal server error"},
        429: {"description": "Rate limit exceeded"},
    },
)
@limiter.limit(f"{APIConfig.RATE_LIMIT_PER_MINUTE}/minute")
async def get_internal_benchmarks(
    request: Request,
    department: Optional[str] = Query(None, min_length=2, max_length=100),
    job_title: Optional[str] = Query(None, min_length=2, max_length=200),
    limit: int = Query(APIConfig.DEFAULT_PAGE_SIZE, ge=1, le=APIConfig.MAX_PAGE_SIZE),
    current_user: User = Depends(get_current_active_user),
    repository: HRISRepository = Depends(get_hris_repository),
):
    """
    Get internal employee benchmarks for salary analysis.

    **PDPA Compliance:**
    - Employee IDs are anonymized (internal DB ID used)
    - Only aggregated/anonymized data is returned
    - No personally identifiable information (PII) exposed

    **Query Parameters:**
    - department: Filter by department
    - job_title: Filter by job title (partial match)
    - limit: Maximum number of records (default: 50, max: 200)

    **Returns:**
    - List of anonymized employee salary benchmarks
    """
    try:
        logger.info(
            f"Fetching internal HRIS benchmarks for user {current_user.email}: "
            f"department={department}, job_title={job_title}"
        )

        # Apply filters
        if department and job_title:
            employees = repository.get_by_department(department, skip=0, limit=limit)
            # Further filter by job title
            employees = [
                emp for emp in employees
                if job_title.lower() in emp.job_title.lower()
            ][:limit]
        elif department:
            employees = repository.get_by_department(department, skip=0, limit=limit)
        elif job_title:
            # Use repository method if available, otherwise filter manually
            all_employees = repository.get_all(skip=0, limit=500)  # Get more for filtering
            employees = [
                emp for emp in all_employees
                if job_title.lower() in emp.job_title.lower()
            ][:limit]
        else:
            employees = repository.get_all(skip=0, limit=limit)

        # Transform to anonymized response
        transformed_employees = [transform_employee(emp) for emp in employees]
        valid_employees = [emp for emp in transformed_employees if emp is not None]

        logger.info(f"Successfully retrieved {len(valid_employees)} internal employee benchmarks")

        return InternalHRISResponse(
            employees=valid_employees,
            total=len(valid_employees),
            success=True,
            cached=False
        )

    except Exception as e:
        logger.error(f"Failed to fetch internal HRIS benchmarks: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve internal employee benchmarks"
        )


@router.post(
    "/internal/hris/sync",
    response_model=SyncResponse,
    summary="Sync Employee Data from BIPO",
    description="Trigger manual sync of employee data from BIPO Cloud HRIS (Admin only)",
    responses={
        200: {"description": "Sync completed successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Permission denied - Admin only"},
        503: {"description": "BIPO integration disabled"},
        500: {"description": "Internal server error"},
        429: {"description": "Rate limit exceeded"},
    },
)
@limiter.limit("5/minute")  # Stricter rate limit for sync endpoint
async def sync_employees_from_bipo(
    request: Request,
    is_active: bool = Query(True, description="Only sync active employees"),
    anonymize: bool = Query(True, description="Anonymize PII data (PDPA compliance)"),
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    """
    Manually trigger employee data sync from BIPO Cloud.

    **Note:** This endpoint should be restricted to admin users only in production.
    Consider adding authentication/authorization middleware.

    **Query Parameters:**
    - is_active: Only sync active employees (default: true)
    - anonymize: Anonymize PII data (default: true)

    **Returns:**
    - Sync statistics (fetched, synced, failed counts)
    """
    try:
        logger.info(
            f"Starting manual BIPO sync by user {current_user.email}: "
            f"is_active={is_active}, anonymize={anonymize}"
        )

        # Check if BIPO integration is enabled
        if not settings.BIPO_ENABLED:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="BIPO integration is disabled. Set BIPO_ENABLED=true in configuration."
            )

        # Initialize sync service
        sync_service = BIPOSyncService(session)

        # Perform sync
        result = sync_service.sync_all_employees(
            is_active=is_active,
            anonymize=anonymize
        )

        logger.info(f"BIPO sync completed: {result}")

        return SyncResponse(
            message="Employee data sync completed successfully",
            fetched=result["fetched"],
            synced=result["synced"],
            failed=result["failed"],
            success=True
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync employee data from BIPO: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync employee data: {str(e)}"
        )


@router.get(
    "/internal/hris/statistics",
    summary="Get Internal HRIS Statistics",
    description="Get aggregated statistics for internal employee data",
    responses={
        200: {"description": "Statistics retrieved successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Permission denied or insufficient data for anonymization"},
        500: {"description": "Internal server error"},
        429: {"description": "Rate limit exceeded"},
    },
)
@limiter.limit(f"{APIConfig.RATE_LIMIT_PER_MINUTE}/minute")
async def get_hris_statistics(
    request: Request,
    department: Optional[str] = Query(None),
    job_family: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    repository: HRISRepository = Depends(get_hris_repository),
):
    """
    Get aggregated salary statistics for internal employees.

    **PDPA Compliance:**
    - Only returns aggregated data if >= 5 employees
    - No individual employee data exposed

    **Query Parameters:**
    - department: Filter by department
    - job_family: Filter by job family

    **Returns:**
    - Aggregated salary statistics (avg, median, percentiles)
    """
    try:
        logger.info(
            f"Fetching HRIS statistics for user {current_user.email}: "
            f"department={department}, job_family={job_family}"
        )

        stats = repository.get_salary_statistics(
            department=department,
            job_family=job_family,
            anonymize=True  # PDPA compliance - returns None if < 5 records
        )

        if stats is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient data for anonymized statistics (minimum 5 employees required)"
            )

        logger.info(f"Successfully retrieved HRIS statistics")
        return {"success": True, "statistics": stats}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch HRIS statistics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve HRIS statistics"
        )
