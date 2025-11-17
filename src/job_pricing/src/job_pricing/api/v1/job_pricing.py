"""
Job Pricing API Router

Endpoints for creating and retrieving job pricing requests.

SECURITY: All endpoints require authentication and proper permissions.
"""

import logging
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from job_pricing.core.database import get_session
from job_pricing.repositories.job_pricing_repository import JobPricingRepository
from job_pricing.models import JobPricingRequest
from job_pricing.models.auth import User, Permission
from job_pricing.api.dependencies.auth import get_current_active_user, PermissionChecker
from job_pricing.schemas.job_pricing import (
    JobPricingRequestCreate,
    JobPricingRequestResponse,
    JobPricingResultResponse,
    JobPricingStatusResponse,
    ErrorResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# --------------------------------------------------------------------------
# Dependency Injection
# --------------------------------------------------------------------------

def get_repository(session: Session = Depends(get_session)) -> JobPricingRepository:
    """Get job pricing repository instance."""
    return JobPricingRepository(session)


# --------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------

@router.post(
    "/requests",
    response_model=JobPricingRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Job Pricing Request",
    description="Submit a new job pricing request for processing",
    responses={
        201: {"description": "Request created successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request data"},
        401: {"description": "Authentication required"},
        403: {"description": "Permission denied"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def create_job_pricing_request(
    request: JobPricingRequestCreate,
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(PermissionChecker([Permission.CREATE_JOB_PRICING])),
    repository: JobPricingRepository = Depends(get_repository),
    session: Session = Depends(get_session),
):
    """
    Create a new job pricing request.

    This endpoint accepts job details and returns a request ID that can be used
    to check the status and retrieve results.

    The request will be queued for asynchronous processing by the Celery worker.

    **Required Fields:**
    - job_title: The job title to be priced

    **Optional Fields:**
    - job_description: Full job description with responsibilities and requirements
    - location_id: ID from locations table (preferred over free text)
    - location_text: Free-text location if location_id not available
    - years_of_experience_min/max: Experience requirements
    - industry: Industry classification
    - company_size: Company size category
    - urgency: Request priority (low, normal, high, critical)
    - requestor_email: Email for notifications

    **Returns:**
    - Request ID and basic information
    - Status will initially be 'pending'
    - Use GET /requests/{request_id}/status to check processing status
    - Use GET /results/{request_id} to retrieve final results when completed
    """
    try:
        logger.info(
            f"Creating job pricing request for user {current_user.email}: "
            f"job_title='{request.job_title}'"
        )

        # Create the job pricing request model
        job_pricing_request = JobPricingRequest(
            job_title=request.job_title,
            job_description=request.job_description or "",
            location_id=request.location_id,
            location_text=request.location_text,
            years_of_experience_min=request.years_of_experience_min,
            years_of_experience_max=request.years_of_experience_max,
            industry=request.industry,
            company_size=request.company_size,
            urgency=request.urgency,
            requested_by=current_user.email,
            requestor_email=request.requestor_email or current_user.email,
            status="pending",
            # TPC-Specific Fields
            portfolio=request.portfolio,
            department=request.department,
            employment_type=request.employment_type,
            job_family=request.job_family,
            internal_grade=request.internal_grade,
            skills_required=request.skills_required,
            alternative_titles=request.alternative_titles,
            mercer_job_code=request.mercer_job_code,
            mercer_job_description=request.mercer_job_description,
        )

        # Save to database
        created_request = repository.create(job_pricing_request)
        session.commit()

        logger.info(f"Job pricing request created: id={created_request.id}")

        # Trigger Celery task for async processing
        try:
            from job_pricing.tasks import process_job_pricing_request

            task = process_job_pricing_request.delay(str(created_request.id))
            logger.info(
                f"Queued job processing task {task.id} for request {created_request.id}"
            )
        except Exception as celery_error:
            # Log error but don't fail the request
            logger.warning(
                f"Failed to queue Celery task for request {created_request.id}: {celery_error}. "
                "Request created but will need manual processing."
            )

        # Return response
        return JobPricingRequestResponse(
            id=created_request.id,
            status=created_request.status,
            job_title=created_request.job_title,
            location_text=created_request.location_text,
            urgency=created_request.urgency,
            created_at=created_request.created_at,
        )

    except ValueError as e:
        logger.error(f"Validation error creating job pricing request: {e}")
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "VALIDATION_ERROR",
                "message": "Invalid request data",
                "details": str(e),
            },
        )
    except Exception as e:
        logger.error(
            f"Failed to create job pricing request: {e}",
            exc_info=True
        )
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "CREATE_FAILED",
                "message": "Failed to create job pricing request",
                "details": "An internal error occurred",
            },
        )


@router.get(
    "/requests/{request_id}/status",
    response_model=JobPricingStatusResponse,
    summary="Get Request Status",
    description="Check the processing status of a job pricing request",
    responses={
        200: {"description": "Status retrieved successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Permission denied"},
        404: {"model": ErrorResponse, "description": "Request not found"},
    },
)
async def get_request_status(
    request_id: UUID,
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(PermissionChecker([Permission.VIEW_JOB_PRICING])),
    repository: JobPricingRepository = Depends(get_repository),
):
    """
    Get the current status of a job pricing request.

    Use this endpoint to check if a request is still pending, processing,
    completed, or failed.

    **Status Values:**
    - `pending`: Request received, waiting to be processed
    - `processing`: Currently being processed by the system
    - `completed`: Processing complete, results available via /results endpoint
    - `failed`: Processing failed, check error_message

    **Returns:**
    - Request ID
    - Current status
    - Creation timestamp
    - Completion timestamp (if completed)
    - Error message (if failed)
    """
    request = repository.get_by_id(request_id)

    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": "Job pricing request not found",
                "details": f"No request found with ID: {request_id}",
            },
        )

    return JobPricingStatusResponse(
        id=request.id,
        status=request.status,
        created_at=request.created_at,
        completed_at=request.updated_at if request.status == "completed" else None,
        error_message=request.error_message,
    )


@router.get(
    "/results/{request_id}",
    response_model=JobPricingResultResponse,
    summary="Get Pricing Results",
    description="Retrieve complete job pricing results including extracted skills and salary calculations",
    responses={
        200: {"description": "Results retrieved successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Permission denied"},
        404: {"model": ErrorResponse, "description": "Request not found"},
        425: {
            "model": ErrorResponse,
            "description": "Request still processing (too early)",
        },
    },
)
async def get_pricing_results(
    request_id: UUID,
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(PermissionChecker([Permission.VIEW_JOB_PRICING])),
    repository: JobPricingRepository = Depends(get_repository),
):
    """
    Get complete job pricing results.

    This endpoint returns the full results including:
    - Job details
    - Extracted skills with SSG TSC mappings
    - Salary pricing calculations
    - Matched job codes (Mercer, SSG)
    - Confidence scores

    **Note:** Results are only available for requests with status='completed'.
    Use GET /requests/{request_id}/status to check status first.

    **Returns:**
    - All request details
    - List of extracted skills with SSG matches
    - Pricing calculation results
    - Timestamps and metadata
    """
    # Get request with full details (all relationships loaded)
    request = repository.get_with_full_details(request_id)

    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": "Job pricing request not found",
                "details": f"No request found with ID: {request_id}",
            },
        )

    # Check if processing is complete
    if request.status == "pending":
        raise HTTPException(
            status_code=status.HTTP_425_TOO_EARLY,
            detail={
                "code": "STILL_PENDING",
                "message": "Request is still pending processing",
                "details": "Please wait for processing to start. Check status endpoint for updates.",
            },
        )

    if request.status == "processing":
        raise HTTPException(
            status_code=status.HTTP_425_TOO_EARLY,
            detail={
                "code": "STILL_PROCESSING",
                "message": "Request is currently being processed",
                "details": "Please wait for processing to complete. Check status endpoint for updates.",
            },
        )

    # Build response
    response = JobPricingResultResponse(
        # Request info
        id=request.id,
        status=request.status,
        job_title=request.job_title,
        job_description=request.job_description,
        location_text=request.location_text,
        years_of_experience_min=request.years_of_experience_min,
        years_of_experience_max=request.years_of_experience_max,
        industry=request.industry,
        company_size=request.company_size,
        urgency=request.urgency,
        # TPC-Specific Fields
        portfolio=request.portfolio,
        department=request.department,
        employment_type=request.employment_type,
        job_family=request.job_family,
        internal_grade=request.internal_grade,
        skills_required=request.skills_required,
        alternative_titles=request.alternative_titles,
        mercer_job_code=request.mercer_job_code,
        mercer_job_description=request.mercer_job_description,
        # Timing
        created_at=request.created_at,
        completed_at=request.updated_at if request.status == "completed" else None,
        # Results (will be populated by processing)
        extracted_skills=[],
        pricing_result=None,
        # Error handling
        error_message=request.error_message,
    )

    # Add extracted skills if available
    if hasattr(request, "extracted_skills") and request.extracted_skills:
        from job_pricing.schemas.job_pricing import SkillExtracted

        response.extracted_skills = [
            SkillExtracted(
                skill_name=skill.skill_name,
                skill_category=skill.skill_category,
                matched_tsc_code=skill.matched_tsc_code,
                match_confidence=float(skill.match_confidence)
                if skill.match_confidence
                else None,
                is_core_skill=skill.is_core_skill,
            )
            for skill in request.extracted_skills
        ]

    # Add pricing result if available
    if hasattr(request, "pricing_result") and request.pricing_result:
        from job_pricing.schemas.job_pricing import PricingResult

        pr = request.pricing_result
        response.pricing_result = PricingResult(
            currency=pr.currency,
            period=pr.period,
            recommended_min=float(pr.recommended_min) if pr.recommended_min else None,
            recommended_max=float(pr.recommended_max) if pr.recommended_max else None,
            target_salary=float(pr.target_salary) if pr.target_salary else None,
            p10=float(pr.p10) if pr.p10 else None,
            p25=float(pr.p25) if pr.p25 else None,
            p50=float(pr.p50) if pr.p50 else None,
            p75=float(pr.p75) if pr.p75 else None,
            p90=float(pr.p90) if pr.p90 else None,
            confidence_score=float(pr.confidence_score) if pr.confidence_score else None,
            confidence_level=pr.confidence_level,
            market_position=pr.market_position,
            summary_text=pr.summary_text,
            key_factors=pr.key_factors or [],
            considerations=pr.considerations or [],
            confidence_factors=pr.confidence_factors,
            total_data_points=pr.total_data_points,
            data_sources_used=pr.data_sources_used,
            data_consistency_score=float(pr.data_consistency_score) if pr.data_consistency_score else None,
        )

    return response


@router.get(
    "/requests",
    summary="List Job Pricing Requests",
    description="List job pricing requests with optional filters",
    response_model=list[JobPricingRequestResponse],
    responses={
        200: {"description": "Requests retrieved successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Permission denied"},
    },
)
async def list_requests(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(PermissionChecker([Permission.VIEW_JOB_PRICING])),
    repository: JobPricingRepository = Depends(get_repository),
):
    """
    List job pricing requests with pagination.

    **Query Parameters:**
    - skip: Number of records to skip (default: 0)
    - limit: Maximum number of records to return (default: 20, max: 100)
    - status: Filter by status (pending, processing, completed, failed)

    **Returns:**
    - List of job pricing requests (basic info only)
    """
    # Validate limit
    if limit > 100:
        limit = 100

    # Get all requests (basic method from BaseRepository)
    # TODO: Add filtering by status and pagination
    all_requests = repository.get_all()

    # Apply filters
    filtered = all_requests
    if status:
        filtered = [r for r in filtered if r.status == status]

    # Apply pagination
    paginated = filtered[skip : skip + limit]

    # Return response
    return [
        JobPricingRequestResponse(
            id=req.id,
            status=req.status,
            job_title=req.job_title,
            location_text=req.location_text,
            urgency=req.urgency,
            created_at=req.created_at,
        )
        for req in paginated
    ]
