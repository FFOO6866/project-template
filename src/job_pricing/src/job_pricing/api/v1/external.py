"""
External Data Integration API Router

Endpoints for accessing scraped job data from MyCareersFuture and Glassdoor.
Production-ready with caching, rate limiting, comprehensive error handling, and logging.

SECURITY: All endpoints require authentication and VIEW_EXTERNAL_DATA permission.
"""

import json
import logging
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import DatabaseError, OperationalError
from pydantic import BaseModel, Field, validator
from slowapi import Limiter
from slowapi.util import get_remote_address

from job_pricing.core.database import get_session
from job_pricing.core.config import get_settings
from job_pricing.core.constants import DataSource, APIConfig, ErrorMessages
from job_pricing.repositories.scraping_repository import ScrapingRepository
from job_pricing.models.auth import User
from job_pricing.api.dependencies.auth import get_current_active_user

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Get settings for Redis connection
settings = get_settings()

router = APIRouter()


# --------------------------------------------------------------------------
# Redis Cache Helper
# --------------------------------------------------------------------------

class CacheHelper:
    """Helper for Redis caching operations."""

    def __init__(self):
        try:
            import redis
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True
            )
            self.enabled = True
            logger.info("Redis cache initialized successfully")
        except Exception as e:
            logger.warning(f"Redis cache unavailable, caching disabled: {e}")
            self.redis_client = None
            self.enabled = False

    def get(self, key: str) -> Optional[dict]:
        """Get value from cache."""
        if not self.enabled:
            return None

        try:
            cached = self.redis_client.get(key)
            if cached:
                logger.debug(f"Cache HIT: {key}")
                return json.loads(cached)
            logger.debug(f"Cache MISS: {key}")
            return None
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None

    def set(self, key: str, value: dict, ttl: int = APIConfig.CACHE_TTL_SECONDS):
        """Set value in cache with TTL."""
        if not self.enabled:
            return

        try:
            self.redis_client.setex(
                key,
                ttl,
                json.dumps(value, default=str)  # default=str handles datetime
            )
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
        except Exception as e:
            logger.warning(f"Cache set error: {e}")


# Initialize cache helper
cache = CacheHelper()


# --------------------------------------------------------------------------
# Response Models (Pydantic Schemas)
# --------------------------------------------------------------------------

class MyCareersFutureJob(BaseModel):
    """MyCareersFuture job listing response model."""
    id: str = Field(..., description="Unique job identifier")
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    location: str = Field(..., description="Job location")
    salary_min: Optional[float] = Field(None, description="Minimum salary (SGD)")
    salary_max: Optional[float] = Field(None, description="Maximum salary (SGD)")
    posted_date: Optional[str] = Field(None, description="Posted date (ISO format)")
    employment_type: Optional[str] = Field(None, description="Employment type (Full-time, Contract, etc.)")
    description: Optional[str] = Field(None, description="Job description")

    @validator('salary_min', 'salary_max', pre=True)
    def validate_salary(cls, v):
        """Validate salary values."""
        if v is None:
            return None
        try:
            return float(v)
        except (ValueError, TypeError):
            logger.warning(f"Invalid salary value: {v}")
            return None

    class Config:
        from_attributes = True


class SalaryEstimate(BaseModel):
    """Salary estimate nested model."""
    min: float = Field(..., description="Minimum salary")
    max: float = Field(..., description="Maximum salary")
    currency: str = Field(default="SGD", description="Currency code")


class GlassdoorSalaryData(BaseModel):
    """Glassdoor salary insight response model."""
    id: str = Field(..., description="Unique identifier")
    job_title: str = Field(..., description="Job title")
    company: Optional[str] = Field(None, description="Company name")
    location: str = Field(..., description="Location")
    salary_estimate: Optional[SalaryEstimate] = Field(None, description="Salary estimate")
    rating: Optional[float] = Field(None, description="Company rating (1-5)")
    reviews_count: Optional[int] = Field(None, description="Number of reviews")
    data_source: str = Field(default="glassdoor", description="Data source identifier")

    @validator('rating', pre=True)
    def validate_rating(cls, v):
        """Validate rating is between 1-5."""
        if v is None:
            return None
        try:
            rating = float(v)
            return min(max(rating, 1.0), 5.0)  # Clamp to 1-5
        except (ValueError, TypeError):
            logger.warning(f"Invalid rating value: {v}")
            return None

    class Config:
        from_attributes = True


class MyCareersFutureResponse(BaseModel):
    """Response wrapper for MyCareersFuture job listings."""
    jobs: List[MyCareersFutureJob] = Field(..., description="List of job listings")
    count: int = Field(..., description="Number of jobs returned")
    cached: bool = Field(False, description="Whether response was served from cache")


class GlassdoorResponse(BaseModel):
    """Response wrapper for Glassdoor salary data."""
    salary_data: List[GlassdoorSalaryData] = Field(..., description="List of salary insights")
    count: int = Field(..., description="Number of salary records returned")
    cached: bool = Field(False, description="Whether response was served from cache")


class ErrorResponse(BaseModel):
    """Error response model."""
    detail: str = Field(..., description="Error message")
    timestamp: str = Field(..., description="Error timestamp (ISO format)")


# --------------------------------------------------------------------------
# Dependency Injection
# --------------------------------------------------------------------------

def get_scraping_repository(session: Session = Depends(get_session)) -> ScrapingRepository:
    """Get scraping repository instance."""
    return ScrapingRepository(session)


# --------------------------------------------------------------------------
# Helper Functions
# --------------------------------------------------------------------------

def transform_to_mcf_job(listing) -> Optional[MyCareersFutureJob]:
    """
    Transform database model to MyCareersFuture job response.

    Returns None if transformation fails (invalid data).
    """
    try:
        return MyCareersFutureJob(
            id=str(listing.id),
            title=listing.job_title,
            company=listing.company_name,
            location=listing.location or "Singapore",
            salary_min=float(listing.salary_min) if listing.salary_min else None,
            salary_max=float(listing.salary_max) if listing.salary_max else None,
            posted_date=listing.posted_date.isoformat() if listing.posted_date else None,
            employment_type=listing.employment_type,
            description=listing.job_description,
        )
    except Exception as e:
        logger.error(f"Failed to transform MCF job listing {listing.id}: {e}")
        return None


def transform_to_glassdoor_data(listing) -> Optional[GlassdoorSalaryData]:
    """
    Transform database model to Glassdoor salary data response.

    Returns None if transformation fails (invalid data).
    """
    try:
        # Create salary estimate if salary data exists
        salary_estimate = None
        if listing.salary_min and listing.salary_max:
            salary_estimate = SalaryEstimate(
                min=float(listing.salary_min),
                max=float(listing.salary_max),
                currency=listing.salary_currency or "SGD"
            )

        return GlassdoorSalaryData(
            id=str(listing.id),
            job_title=listing.job_title,
            company=listing.company_name,
            location=listing.location or "Singapore",
            salary_estimate=salary_estimate,
            rating=float(listing.company_rating) if listing.company_rating else None,
            reviews_count=None,  # Not currently scraped
            data_source="glassdoor"
        )
    except Exception as e:
        logger.error(f"Failed to transform Glassdoor listing {listing.id}: {e}")
        return None


# --------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------

@router.get(
    "/mycareersfuture",
    response_model=MyCareersFutureResponse,
    summary="Get MyCareersFuture Job Listings",
    description="Fetch scraped job listings from MyCareersFuture (Singapore government job portal)",
    responses={
        200: {"description": "Successfully retrieved job listings"},
        400: {"model": ErrorResponse, "description": "Invalid request parameters"},
        401: {"description": "Authentication required"},
        403: {"description": "Permission denied"},
        503: {"model": ErrorResponse, "description": "Database unavailable"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
        429: {"description": "Rate limit exceeded"},
    },
)
@limiter.limit(f"{APIConfig.RATE_LIMIT_PER_MINUTE}/minute")
async def get_mycareersfuture_jobs(
    request: Request,
    job_title: str = Query(
        ...,
        description="Job title to search for (case-insensitive partial match)",
        min_length=2,
        max_length=200,
        example="HR Director"
    ),
    location: Optional[str] = Query(
        None,
        description="Location filter (optional, defaults to all Singapore locations)",
        max_length=100,
        example="Singapore"
    ),
    limit: int = Query(
        APIConfig.DEFAULT_PAGE_SIZE,
        description="Maximum number of results to return",
        ge=1,
        le=APIConfig.MAX_PAGE_SIZE
    ),
    current_user: User = Depends(get_current_active_user),
    repository: ScrapingRepository = Depends(get_scraping_repository),
):
    """
    Get job listings from MyCareersFuture.

    Searches the database for scraped MyCareersFuture job listings matching the
    specified job title and location. Results are cached for 30 minutes.

    **Query Parameters:**
    - `job_title` (required): Job title to search for (e.g., "HR Director", "Software Engineer")
    - `location` (optional): Location filter (e.g., "Singapore", "Central")
    - `limit` (optional): Maximum results to return (default: 20, max: 100)

    **Returns:**
    - `jobs`: Array of job listing objects
    - `count`: Number of jobs returned
    - `cached`: Whether response was served from cache

    **Rate Limit:** 60 requests/minute per IP

    **Example:**
    ```
    GET /api/v1/external/mycareersfuture?job_title=HR%20Director&location=Singapore&limit=10
    ```
    """
    # Generate cache key
    cache_key = f"mcf:{job_title}:{location or 'all'}:{limit}"

    # Log request
    logger.info(
        f"MCF job search request by user {current_user.email}",
        extra={
            "user_email": current_user.email,
            "job_title": job_title,
            "location": location,
            "limit": limit,
            "ip": get_remote_address(request)
        }
    )

    # Try cache first
    cached_response = cache.get(cache_key)
    if cached_response:
        cached_response['cached'] = True
        return MyCareersFutureResponse(**cached_response)

    try:
        # Query database with efficient filtering
        listings = repository.search_by_title(
            search_term=job_title,
            source=DataSource.MY_CAREERS_FUTURE,
            location=location,
            limit=limit
        )

        # Transform database models to response models
        jobs = []
        for listing in listings:
            job = transform_to_mcf_job(listing)
            if job:  # Only include successfully transformed jobs
                jobs.append(job)

        response_data = {
            "jobs": [job.dict() for job in jobs],
            "count": len(jobs),
            "cached": False
        }

        # Cache the response
        cache.set(cache_key, response_data)

        logger.info(
            "MCF job search completed",
            extra={
                "job_title": job_title,
                "results_count": len(jobs),
                "cached": False
            }
        )

        return MyCareersFutureResponse(**response_data)

    except (DatabaseError, OperationalError) as e:
        logger.error(f"Database error in MCF endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=ErrorMessages.DATABASE_ERROR
        )
    except ValueError as e:
        logger.warning(f"Invalid parameter in MCF endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorMessages.INVALID_REQUEST
        )
    except Exception as e:
        logger.error(f"Unexpected error in MCF endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorMessages.INTERNAL_ERROR
        )


@router.get(
    "/glassdoor",
    response_model=GlassdoorResponse,
    summary="Get Glassdoor Salary Insights",
    description="Fetch scraped salary data and company ratings from Glassdoor",
    responses={
        200: {"description": "Successfully retrieved salary insights"},
        400: {"model": ErrorResponse, "description": "Invalid request parameters"},
        401: {"description": "Authentication required"},
        403: {"description": "Permission denied"},
        503: {"model": ErrorResponse, "description": "Database unavailable"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
        429: {"description": "Rate limit exceeded"},
    },
)
@limiter.limit(f"{APIConfig.RATE_LIMIT_PER_MINUTE}/minute")
async def get_glassdoor_data(
    request: Request,
    job_title: str = Query(
        ...,
        description="Job title to search for (case-insensitive partial match)",
        min_length=2,
        max_length=200,
        example="HR Director"
    ),
    location: Optional[str] = Query(
        None,
        description="Location filter (optional, defaults to all locations)",
        max_length=100,
        example="Singapore"
    ),
    limit: int = Query(
        APIConfig.DEFAULT_PAGE_SIZE,
        description="Maximum number of results to return",
        ge=1,
        le=APIConfig.MAX_PAGE_SIZE
    ),
    current_user: User = Depends(get_current_active_user),
    repository: ScrapingRepository = Depends(get_scraping_repository),
):
    """
    Get salary insights from Glassdoor.

    Searches the database for scraped Glassdoor salary estimates and company ratings
    matching the specified job title and location. Results are cached for 30 minutes.

    **Query Parameters:**
    - `job_title` (required): Job title to search for (e.g., "HR Director", "Data Analyst")
    - `location` (optional): Location filter (e.g., "Singapore")
    - `limit` (optional): Maximum results to return (default: 20, max: 100)

    **Returns:**
    - `salary_data`: Array of salary insight objects with company ratings
    - `count`: Number of salary records returned
    - `cached`: Whether response was served from cache

    **Rate Limit:** 60 requests/minute per IP

    **Note:** Glassdoor data includes salary estimates (not actual posted salaries)
    and company ratings aggregated from employee reviews.

    **Example:**
    ```
    GET /api/v1/external/glassdoor?job_title=Data%20Analyst&location=Singapore&limit=15
    ```
    """
    # Generate cache key
    cache_key = f"glassdoor:{job_title}:{location or 'all'}:{limit}"

    # Log request
    logger.info(
        f"Glassdoor salary search request by user {current_user.email}",
        extra={
            "user_email": current_user.email,
            "job_title": job_title,
            "location": location,
            "limit": limit,
            "ip": get_remote_address(request)
        }
    )

    # Try cache first
    cached_response = cache.get(cache_key)
    if cached_response:
        cached_response['cached'] = True
        return GlassdoorResponse(**cached_response)

    try:
        # Query database with efficient filtering
        listings = repository.search_by_title(
            search_term=job_title,
            source=DataSource.GLASSDOOR,
            location=location,
            limit=limit
        )

        # Transform database models to response models
        salary_data = []
        for listing in listings:
            data = transform_to_glassdoor_data(listing)
            if data:  # Only include successfully transformed data
                salary_data.append(data)

        response_data = {
            "salary_data": [data.dict() for data in salary_data],
            "count": len(salary_data),
            "cached": False
        }

        # Cache the response
        cache.set(cache_key, response_data)

        logger.info(
            "Glassdoor salary search completed",
            extra={
                "job_title": job_title,
                "results_count": len(salary_data),
                "cached": False
            }
        )

        return GlassdoorResponse(**response_data)

    except (DatabaseError, OperationalError) as e:
        logger.error(f"Database error in Glassdoor endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=ErrorMessages.DATABASE_ERROR
        )
    except ValueError as e:
        logger.warning(f"Invalid parameter in Glassdoor endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorMessages.INVALID_REQUEST
        )
    except Exception as e:
        logger.error(f"Unexpected error in Glassdoor endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorMessages.INTERNAL_ERROR
        )
