"""
Pydantic Schemas for Salary Recommendation API

Request and response models for the salary recommendation endpoints.
"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


# --------------------------------------------------------------------------
# Request Schemas
# --------------------------------------------------------------------------

class SalaryRecommendationRequest(BaseModel):
    """Request model for salary recommendation."""

    job_title: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Job title to price (e.g., 'Senior HR Business Partner')",
        examples=["Senior HR Business Partner", "HR Director, Total Rewards"]
    )

    job_description: Optional[str] = Field(
        default="",
        max_length=5000,
        description="Job description for better matching (optional but recommended)",
        examples=["Responsible for strategic HR partnership with business units"]
    )

    location: str = Field(
        default="Central Business District",
        max_length=100,
        description="Singapore location for cost-of-living adjustment",
        examples=["Central Business District", "Tampines", "Woodlands", "Marina Bay"]
    )

    job_family: Optional[str] = Field(
        default=None,
        max_length=10,
        description="Mercer job family code (e.g., 'HRM', 'ICT') for filtering",
        examples=["HRM", "ICT", "FIN", "MKT"]
    )

    career_level: Optional[str] = Field(
        default=None,
        max_length=10,
        description="Mercer career level (e.g., 'M5', 'ET2', 'P3') for filtering",
        examples=["M5", "M6", "ET2", "ET3", "P3", "P4"]
    )

    @field_validator('job_title')
    @classmethod
    def validate_job_title(cls, v):
        """Validate job title is not empty."""
        if not v or not v.strip():
            raise ValueError('Job title cannot be empty')
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "job_title": "Senior HR Business Partner",
                "job_description": "Strategic HR partner supporting business units with talent management and organizational development",
                "location": "Tampines",
                "job_family": "HRM",
                "career_level": "M6"
            }
        }


class JobMatchingRequest(BaseModel):
    """Request model for job matching only (without salary)."""

    job_title: str = Field(..., min_length=3, max_length=200)
    job_description: Optional[str] = Field(default="", max_length=5000)
    job_family: Optional[str] = Field(default=None, max_length=10)
    career_level: Optional[str] = Field(default=None, max_length=10)
    top_k: int = Field(default=5, ge=1, le=10, description="Number of top matches to return")

    class Config:
        json_schema_extra = {
            "example": {
                "job_title": "HR Director",
                "job_description": "Leads HR strategy and operations",
                "job_family": "HRM",
                "top_k": 3
            }
        }


# --------------------------------------------------------------------------
# Response Schemas
# --------------------------------------------------------------------------

class MatchedJob(BaseModel):
    """Matched Mercer job details."""

    job_code: str = Field(..., description="Mercer job code")
    job_title: str = Field(..., description="Standardized Mercer job title")
    similarity: str = Field(..., description="Similarity score as percentage (e.g., '64.9%')")
    confidence: str = Field(..., description="Confidence level: high, medium, or low")


class ConfidenceMetrics(BaseModel):
    """Confidence scoring breakdown."""

    score: float = Field(..., ge=0, le=100, description="Overall confidence score (0-100)")
    level: str = Field(..., description="Confidence level: High, Medium, or Low")
    recommendation: str = Field(..., description="Recommendation based on confidence")
    factors: Dict[str, float] = Field(..., description="Breakdown of confidence factors")


class SalaryRange(BaseModel):
    """Salary range recommendation."""

    min: float = Field(..., description="Minimum recommended salary (P25)")
    max: float = Field(..., description="Maximum recommended salary (P75)")
    target: float = Field(..., description="Target salary (P50 median)")


class Percentiles(BaseModel):
    """Full salary percentile distribution."""

    p25: float = Field(..., description="25th percentile")
    p50: float = Field(..., description="50th percentile (median)")
    p75: float = Field(..., description="75th percentile")


class DataSource(BaseModel):
    """Data source information."""

    jobs_matched: int = Field(..., description="Number of Mercer jobs matched")
    total_sample_size: int = Field(..., description="Total sample size from survey")
    survey: str = Field(..., description="Survey name and year")


class LocationAdjustment(BaseModel):
    """Location cost-of-living adjustment details."""

    location: str = Field(..., description="Location name")
    cost_of_living_index: float = Field(..., description="Cost-of-living index (1.0 = CBD baseline)")
    note: str = Field(..., description="Adjustment explanation")


class SalaryRecommendationResponse(BaseModel):
    """Response model for salary recommendation."""

    success: bool = Field(..., description="Whether the recommendation was successful")

    # Recommendation details
    job_title: str = Field(..., description="Job title that was priced")
    location: str = Field(..., description="Location used for adjustment")
    currency: str = Field(..., description="Currency code (SGD)")
    period: str = Field(..., description="Salary period (annual)")

    # Salary recommendation
    recommended_range: SalaryRange = Field(..., description="Recommended salary range (P25-P75)")
    percentiles: Percentiles = Field(..., description="Full percentile distribution")

    # Confidence metrics
    confidence: ConfidenceMetrics = Field(..., description="Confidence scoring")

    # Matched jobs
    matched_jobs: List[MatchedJob] = Field(..., description="Top matched Mercer jobs")

    # Data sources
    data_sources: Dict[str, DataSource] = Field(..., description="Data source information")

    # Location adjustment
    location_adjustment: LocationAdjustment = Field(..., description="Location adjustment details")

    # Summary
    summary: str = Field(..., description="Human-readable summary of recommendation")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "job_title": "Senior HR Business Partner",
                "location": "Tampines",
                "currency": "SGD",
                "period": "annual",
                "recommended_range": {
                    "min": 236449.00,
                    "max": 353017.00,
                    "target": 281453.00
                },
                "percentiles": {
                    "p25": 236449.00,
                    "p50": 281453.00,
                    "p75": 353017.00
                },
                "confidence": {
                    "score": 69.0,
                    "level": "Medium",
                    "recommendation": "Review recommended range carefully",
                    "factors": {
                        "job_match": 19.5,
                        "data_points": 35.0,
                        "sample_size": 15.0
                    }
                },
                "matched_jobs": [
                    {
                        "job_code": "HRM.02.003.M60",
                        "job_title": "HR Business Partners - Senior Director (M6)",
                        "similarity": "64.9%",
                        "confidence": "medium"
                    }
                ],
                "data_sources": {
                    "mercer_market_data": {
                        "jobs_matched": 3,
                        "total_sample_size": 150,
                        "survey": "2024 Singapore Total Remuneration Survey"
                    }
                },
                "location_adjustment": {
                    "location": "Tampines",
                    "cost_of_living_index": 0.88,
                    "note": "Salaries adjusted by 88% for Tampines location"
                },
                "summary": "Based on analysis of 3 Mercer benchmark jobs..."
            }
        }


class SalaryRecommendationError(BaseModel):
    """Error response for failed recommendations."""

    success: bool = Field(default=False, description="Always false for errors")
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code for programmatic handling")
    details: Optional[str] = Field(default=None, description="Additional error details")
    matched_jobs: Optional[List[MatchedJob]] = Field(
        default=None,
        description="Matched jobs if available (e.g., matches found but no salary data)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "No similar jobs found in Mercer library",
                "error_code": "NO_MATCHES",
                "details": "Try adjusting the job title or removing filters"
            }
        }


class JobMatchingResponse(BaseModel):
    """Response model for job matching."""

    success: bool = Field(..., description="Whether matching was successful")
    matched_jobs: List[MatchedJob] = Field(..., description="List of matched jobs")
    query: str = Field(..., description="Original job title queried")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "matched_jobs": [
                    {
                        "job_code": "HRM.02.003.M60",
                        "job_title": "HR Business Partners - Senior Director (M6)",
                        "similarity": "64.9%",
                        "confidence": "medium"
                    }
                ],
                "query": "Senior HR Business Partner"
            }
        }
