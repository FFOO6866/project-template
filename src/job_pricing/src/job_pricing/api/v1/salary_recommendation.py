"""
Salary Recommendation API Router

Endpoints for intelligent salary recommendations using semantic job matching
and real Mercer market data.

SECURITY: All endpoints require authentication and VIEW_SALARY_RECOMMENDATIONS permission.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

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
from job_pricing.models.auth import User, Permission
from job_pricing.models import JobPricingRequest
from job_pricing.api.dependencies.auth import get_current_active_user, PermissionChecker
from job_pricing.core.database import get_session

logger = logging.getLogger(__name__)

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
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(PermissionChecker([Permission.VIEW_SALARY_RECOMMENDATIONS])),
):
    """
    Generate an intelligent salary recommendation for a given job.

    This endpoint uses:
    - **OpenAI embeddings** for semantic job matching
    - **pgvector similarity search** to find similar Mercer jobs
    - **Real Mercer salary benchmarks** from 2024 Singapore survey
    - **Location-based cost-of-living adjustments**
    - **Multi-factor confidence scoring**

    ## Process Flow:
    1. Generate embedding for your job title/description
    2. Search 174+ Mercer jobs for best semantic matches
    3. Retrieve salary data (P25/P50/P75) for matched jobs
    4. Calculate weighted salary based on match quality
    5. Apply location cost-of-living adjustment
    6. Score confidence based on data quality

    ## Example Request:
    ```json
    {
        "job_title": "Senior HR Business Partner",
        "job_description": "Strategic HR partner supporting business units",
        "location": "Tampines",
        "job_family": "HRM"
    }
    ```

    ## Example Response:
    ```json
    {
        "success": true,
        "recommended_range": {
            "min": 236449.00,
            "target": 281453.00,
            "max": 353017.00
        },
        "confidence": {
            "score": 69.0,
            "level": "Medium"
        }
    }
    ```

    ## Confidence Levels:
    - **High (≥75)**: Strong match with abundant data - proceed with confidence
    - **Medium (50-74)**: Good match but review carefully
    - **Low (<50)**: Limited data or weak match - manual review recommended

    ## Location Options:
    Available Singapore locations with cost-of-living indices:
    - Central Business District (1.0 baseline)
    - Marina Bay (1.02)
    - Orchard Road (0.98)
    - Tampines (0.88)
    - Woodlands (0.82)
    - Punggol (0.83)
    - Jurong (0.85)
    - And 17 more...

    **Returns**: Complete salary recommendation with confidence metrics
    """
    logger.info(
        f"Salary recommendation requested by user {current_user.email} "
        f"for job: {request.job_title}"
    )

    try:
        # Initialize V2 service with multi-source aggregation
        session = get_session()
        service_v2 = SalaryRecommendationServiceV2(session)

        # Create pricing request
        pricing_request = JobPricingRequest(
            job_title=request.job_title,
            job_description=request.job_description or "",
            location_text=request.location,
            requested_by=current_user.id,  # Set the user who requested this
            requestor_email=current_user.email,  # Set the requestor email
            status='pending',  # Set initial status
            urgency='normal',  # Set default urgency
        )

        # Generate recommendation using V3 algorithm with multi-source aggregation
        result = service_v2.calculate_recommendation(pricing_request)

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
                score=result["confidence_score"],
                level=result["confidence_level"],
                recommendation=f"{result['confidence_level']} confidence - {result['explanation']}",
                factors={
                    "data_sources": result["data_sources_used"],
                    "total_sample": sum(c["sample_size"] for c in result["source_contributions"]),
                    "explanation": result["explanation"]
                }
            ),
            matched_jobs=[
                MatchedJob(
                    job_code=result["mercer_match"]["job_code"] if result.get("mercer_match") else "N/A",
                    job_title=result["mercer_match"]["job_title"] if result.get("mercer_match") else request.job_title,
                    similarity=f"{result['mercer_match']['match_score']*100:.1f}%" if result.get("mercer_match") and result["mercer_match"].get("match_score") else "N/A",
                    confidence=result["confidence_level"]
                )
            ],
            data_sources={
                src["source"]: DataSource(
                    jobs_matched=src["sample_size"],
                    total_sample_size=src["sample_size"],
                    survey=f"{src['source']} - {src['recency_days']} days old" if src.get("recency_days") else src["source"]
                )
                for src in result["source_contributions"]
            },
            location_adjustment=LocationAdjustment(
                location=request.location,
                cost_of_living_index=1.0,  # TODO: Get from location table
                note=f"Based on {result['data_sources_used']} data sources"
            ),
            summary=result["explanation"]
        )

        session.close()
        return response

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
    _: None = Depends(PermissionChecker([Permission.VIEW_SALARY_RECOMMENDATIONS])),
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
    _: None = Depends(PermissionChecker([Permission.VIEW_SALARY_RECOMMENDATIONS])),
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
    _: None = Depends(PermissionChecker([Permission.VIEW_SALARY_RECOMMENDATIONS])),
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
