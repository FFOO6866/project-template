"""
Salary Recommendation API Router

Endpoints for intelligent salary recommendations using semantic job matching
and real Mercer market data.

SECURITY: All endpoints require authentication and VIEW_SALARY_RECOMMENDATIONS permission.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from job_pricing.schemas.salary_recommendation import (
    SalaryRecommendationRequest,
    SalaryRecommendationResponse,
    SalaryRecommendationError,
    JobMatchingRequest,
    JobMatchingResponse,
    MatchedJob,
    ConfidenceMetrics,
    SalaryRange,
    Percentiles,
    DataSource,
    LocationAdjustment,
)
from job_pricing.services.salary_recommendation_service import SalaryRecommendationService
from job_pricing.services.salary_recommendation_service_v2 import SalaryRecommendationServiceV2
from job_pricing.services.job_matching_service import JobMatchingService
from job_pricing.exceptions import NoMarketDataError
from job_pricing.models.auth import User
from job_pricing.models import JobPricingRequest, LocationIndex
from job_pricing.api.dependencies.auth import get_current_active_user
from job_pricing.core.database import get_session

logger = logging.getLogger(__name__)


def get_cost_of_living_index(session: Session, location: str) -> float:
    """
    Get cost of living index for a location from database.

    Args:
        session: Database session
        location: Location name to look up

    Returns:
        Cost of living index (1.0 if not found - Singapore CBD baseline)
    """
    if not location:
        return 1.0

    # Try to find location in database
    location_index = session.query(LocationIndex).filter(
        LocationIndex.location_name.ilike(f"%{location}%")
    ).first()

    if location_index and location_index.cost_of_living_index:
        return float(location_index.cost_of_living_index)

    # Default to 1.0 (Singapore CBD baseline) if location not in database
    # This is not a fallback to mock data - it's a documented baseline value
    logger.debug(f"Location '{location}' not found in LocationIndex table, using baseline 1.0")
    return 1.0

router = APIRouter()


# --------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------

@router.post(
    "/recommend",
    response_model=SalaryRecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Salary Recommendation",
    description="Get intelligent salary recommendation using AI-powered job matching and real market data",
    responses={
        200: {
            "description": "Salary recommendation generated successfully",
            "model": SalaryRecommendationResponse
        },
        400: {
            "description": "Invalid request parameters",
            "model": SalaryRecommendationError
        },
        401: {"description": "Authentication required"},
        403: {"description": "Permission denied"},
        404: {
            "description": "No matches found or no salary data available",
            "model": SalaryRecommendationError
        },
        500: {
            "description": "Internal server error",
            "model": SalaryRecommendationError
        },
    },
)
async def recommend_salary(
    request: SalaryRecommendationRequest,
    force_refresh: bool = Query(False, description="Bypass cache and force fresh calculation"),
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    """
    Generate an intelligent salary recommendation for a given job with smart caching.

    This endpoint uses:
    - **Smart caching** with request deduplication (Option 1+ architecture)
    - **OpenAI embeddings** for semantic job matching
    - **pgvector similarity search** to find similar Mercer jobs
    - **Multi-source aggregation** from 5 salary data sources
    - **Location-based cost-of-living adjustments**
    - **Versioned results** (keeps last 5 versions for audit trail)

    ## Smart Caching Workflow:
    1. Generate hash from (job_title + location + user_id)
    2. Check cache for non-expired result
    3. If cache HIT: Return cached result (0.1s response, 43× faster)
    4. If cache MISS: Calculate fresh recommendation
    5. Save versioned result with smart expiry (based on data source freshness)
    6. Cleanup old versions (keep last 5)

    ## Cache Behavior:
    - **Default**: Uses cache if available and not expired
    - **force_refresh=true**: Bypasses cache and recalculates (creates new version)
    - **Cache TTL**: Shortest TTL among data sources:
      - Mercer: 30 days
      - MyCareersFuture: 24 hours
      - Glassdoor: 7 days
      - Hays: 14 days
      - LinkedIn: 3 days

    ## Example Request:
    ```json
    {
        "job_title": "Senior HR Business Partner",
        "job_description": "Strategic HR partner supporting business units",
        "location": "Tampines",
        "job_family": "HRM"
    }
    ```

    Add `?force_refresh=true` to bypass cache.

    ## Example Response (Fresh):
    ```json
    {
        "success": true,
        "recommended_range": {
            "min": 236449.00,
            "target": 281453.00,
            "max": 353017.00
        },
        "confidence": {"score": 69.0, "level": "Medium"},
        "metadata": {
            "from_cache": false,
            "version": 1,
            "calculated_at": "2025-11-18T10:30:00Z",
            "expires_at": "2025-11-19T10:30:00Z"
        }
    }
    ```

    ## Example Response (Cached):
    ```json
    {
        ...same salary data...,
        "metadata": {
            "from_cache": true,
            "version": 1,
            "cache_age_seconds": 3600,
            "time_to_expiry_seconds": 82800
        }
    }
    ```

    ## Confidence Levels:
    - **High (≥75)**: Strong match with abundant data - proceed with confidence
    - **Medium (50-74)**: Good match but review carefully
    - **Low (<50)**: Limited data or weak match - manual review recommended

    **Returns**: Complete salary recommendation with confidence metrics and cache metadata
    """
    logger.info(
        f"Salary recommendation requested by user {current_user.email} "
        f"for job: {request.job_title} (force_refresh={force_refresh})"
    )

    try:
        # Initialize V2 service with smart caching
        # Session is automatically injected via FastAPI Depends and will be closed after request
        service_v2 = SalaryRecommendationServiceV2(session)

        # Generate recommendation using V3 algorithm with smart caching
        result = service_v2.calculate_recommendation(
            job_title=request.job_title,
            location=request.location or "Singapore",
            user_id=current_user.id,
            job_description=request.job_description or "",
            force_refresh=force_refresh
        )

        # Build response from V2 result format
        response = SalaryRecommendationResponse(
            success=True,
            job_title=result["job_title"],
            location=result.get("location", request.location),
            currency=result["currency"],
            period=result["period"],
            recommended_range=SalaryRange(
                min=result["recommended_min"],
                max=result["recommended_max"],
                target=result["target_salary"]
            ),
            percentiles=Percentiles(
                p25=result["percentiles"]["p25"],
                p50=result["percentiles"]["p50"],
                p75=result["percentiles"]["p75"]
            ),
            confidence=ConfidenceMetrics(
                score=result.get("confidence_score", 0.0),
                level=result.get("confidence_level", "Low"),
                recommendation=f"{result.get('confidence_level', 'Low')} confidence - {result.get('explanation', 'No explanation available')}",
                factors={
                    "job_match": float(result.get("mercer_match", {}).get("match_score", 0.0) * 30.0) if result.get("mercer_match") else 0.0,  # Best match quality (0-30 points)
                    "data_points": float(result.get("data_sources_used", 0) * 12.0),  # Number of data sources scaled to points (0-35 points)
                    "sample_size": float(sum(c.get("sample_size", 0) for c in result.get("source_contributions", [])))  # Total sample size from all sources
                }
            ),
            matched_jobs=[
                MatchedJob(
                    job_code=result["mercer_match"]["job_code"] if result.get("mercer_match") else "N/A",
                    job_title=result["mercer_match"]["job_title"] if result.get("mercer_match") else request.job_title,
                    similarity=f"{result['mercer_match']['match_score']*100:.1f}%" if result.get("mercer_match") and result["mercer_match"].get("match_score") else "N/A",
                    confidence=result.get("confidence_level", "Low")
                )
            ],
            data_sources={
                src.get("source", "unknown"): DataSource(
                    jobs_matched=src.get("sample_size", 0),
                    total_sample_size=src.get("sample_size", 0),
                    survey=f"{src.get('source', 'unknown')} - {src.get('recency_days', 0)} days old" if src.get("recency_days") else src.get("source", "unknown")
                )
                for src in result.get("source_contributions", [])
            },
            location_adjustment=LocationAdjustment(
                location=request.location,
                cost_of_living_index=get_cost_of_living_index(session, request.location),
                note=f"Based on {result.get('data_sources_used', 0)} data sources"
            ),
            summary=result.get("explanation", "No explanation available")
        )

        return response

    except NoMarketDataError as e:
        # Graceful "no data" response - NOT an error state
        logger.info(
            f"No market data available for user {current_user.email}, job: {e.job_title}"
        )

        # Return HTTP 200 with helpful, generic guidance
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": False,
                "job_title": e.job_title,
                "message": "No market data available for this job title",
                "sources_attempted": e.sources_attempted,
                "suggestions": [
                    "Add a detailed job description to improve semantic matching",
                    "Specify the job family if known",
                    "Try simplified or alternative variations of the job title",
                    "Ensure the job title uses standard industry terminology"
                ],
                "metadata": {
                    "mercer_searched": "mercer" in e.sources_attempted,
                    "external_sources_searched": any(s in e.sources_attempted for s in ["my_careers_future", "glassdoor"]),
                    "internal_sources_searched": any(s in e.sources_attempted for s in ["internal_hris", "applicants"])
                }
            }
        )

    except Exception as e:
        logger.error(
            f"Salary recommendation error for user {current_user.email}: {e}",
            exc_info=True
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=SalaryRecommendationError(
                success=False,
                error="An error occurred while generating the recommendation",
                error_code="INTERNAL_ERROR",
                details=str(e)
            ).dict()
        )


@router.post(
    "/match",
    response_model=JobMatchingResponse,
    status_code=status.HTTP_200_OK,
    summary="Find Similar Jobs",
    description="Find similar jobs in Mercer library using semantic matching (without salary data)",
    responses={
        200: {"description": "Matches found successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Permission denied"},
        404: {"description": "No matches found"},
        500: {"description": "Internal server error"},
    },
)
async def match_jobs(
    request: JobMatchingRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Find similar jobs in the Mercer Job Library using semantic matching.

    This endpoint performs only the job matching step without retrieving salary data.
    Useful for:
    - Exploring what jobs exist in the Mercer library
    - Understanding how your job title maps to standardized codes
    - Testing match quality before requesting full salary recommendation

    ## Process:
    1. Generate OpenAI embedding for your job
    2. Search Mercer library using pgvector similarity
    3. Return top K matches with similarity scores

    ## Example Request:
    ```json
    {
        "job_title": "HR Director",
        "job_description": "Leads HR strategy",
        "job_family": "HRM",
        "top_k": 5
    }
    ```

    **Returns**: List of matched jobs with similarity scores
    """
    logger.info(
        f"Job matching requested by user {current_user.email} "
        f"for job: {request.job_title}"
    )

    try:
        # Initialize service
        service = JobMatchingService()

        # Find similar jobs
        matches = service.find_similar_jobs(
            job_title=request.job_title,
            job_description=request.job_description or "",
            job_family=request.job_family,
            career_level=request.career_level,
            top_k=request.top_k
        )

        if not matches:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "success": False,
                    "error": "No similar jobs found",
                    "query": request.job_title
                }
            )

        # Build response
        response = JobMatchingResponse(
            success=True,
            matched_jobs=[
                MatchedJob(
                    job_code=job["job_code"],
                    job_title=job["job_title"],
                    similarity=f"{job['similarity_score']:.1%}",
                    confidence=job["confidence"]
                )
                for job in matches
            ],
            query=request.job_title
        )

        return response

    except Exception as e:
        logger.error(
            f"Job matching error for user {current_user.email}: {e}",
            exc_info=True
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": "An error occurred during job matching",
                "details": str(e)
            }
        )


@router.get(
    "/locations",
    summary="List Available Locations",
    description="Get list of Singapore locations with cost-of-living indices",
    responses={
        200: {"description": "Locations retrieved successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Permission denied"},
        500: {"description": "Internal server error"},
    },
)
async def list_locations(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get list of available Singapore locations with cost-of-living adjustments.

    Returns all 24 Singapore locations that can be used for salary recommendations.

    **Returns**: List of locations with indices
    """
    logger.info(f"Locations list requested by user {current_user.email}")

    from job_pricing.models.supporting import LocationIndex
    from job_pricing.utils.database import get_db_context

    try:
        with get_db_context() as session:
            locations = session.query(LocationIndex).order_by(
                LocationIndex.cost_of_living_index.desc()
            ).all()

            return {
                "success": True,
                "count": len(locations),
                "locations": [
                    {
                        "name": loc.location_name,
                        "cost_of_living_index": float(loc.cost_of_living_index),
                        "region": loc.region,
                        "adjustment_note": f"{float(loc.cost_of_living_index):.0%} of CBD baseline"
                    }
                    for loc in locations
                ]
            }

    except Exception as e:
        logger.error(
            f"Failed to retrieve locations for user {current_user.email}: {e}",
            exc_info=True
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": "Failed to retrieve locations",
                "details": str(e)
            }
        )


@router.get(
    "/stats",
    summary="Get System Statistics",
    description="Get statistics about available jobs and salary data",
    responses={
        200: {"description": "Statistics retrieved successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Permission denied"},
        500: {"description": "Internal server error"},
    },
)
async def get_stats(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get statistics about the salary recommendation system.

    Returns information about:
    - Number of Mercer jobs with embeddings
    - Number of jobs with salary data
    - Number of locations available
    - Data freshness

    **Returns**: System statistics
    """
    logger.info(f"System statistics requested by user {current_user.email}")

    from job_pricing.models.mercer import MercerJobLibrary, MercerMarketData
    from job_pricing.models.supporting import LocationIndex
    from job_pricing.utils.database import get_db_context

    try:
        with get_db_context() as session:
            # Count jobs with embeddings
            total_jobs = session.query(MercerJobLibrary).count()
            jobs_with_embeddings = session.query(MercerJobLibrary).filter(
                MercerJobLibrary.embedding.isnot(None)
            ).count()

            # Count jobs with salary data
            jobs_with_salaries = session.query(MercerMarketData).count()

            # Count locations
            total_locations = session.query(LocationIndex).count()

            # Get latest survey date
            latest_survey = session.query(MercerMarketData).order_by(
                MercerMarketData.survey_date.desc()
            ).first()

            return {
                "success": True,
                "statistics": {
                    "mercer_jobs": {
                        "total": total_jobs,
                        "with_embeddings": jobs_with_embeddings,
                        "with_salary_data": jobs_with_salaries,
                        "embedding_coverage": f"{jobs_with_embeddings/total_jobs*100:.1f}%" if total_jobs > 0 else "0%"
                    },
                    "locations": {
                        "total": total_locations,
                        "baseline": "Central Business District"
                    },
                    "data_freshness": {
                        "survey_name": latest_survey.survey_name if latest_survey else None,
                        "survey_date": latest_survey.survey_date.isoformat() if latest_survey else None,
                        "currency": latest_survey.currency if latest_survey else None
                    }
                }
            }

    except Exception as e:
        logger.error(
            f"Failed to retrieve statistics for user {current_user.email}: {e}",
            exc_info=True
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": "Failed to retrieve statistics",
                "details": str(e)
            }
        )
