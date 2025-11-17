"""
Job Pricing Request and Response Schemas

Pydantic models for API request/response validation.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr, validator


# --------------------------------------------------------------------------
# Request Schemas
# --------------------------------------------------------------------------

class JobPricingRequestCreate(BaseModel):
    """
    Schema for creating a new job pricing request.

    Required fields:
    - job_title: The job title to price

    Optional fields:
    - job_description: Full job description with responsibilities and requirements
    - location_id: ID from locations table (preferred)
    - location_text: Free-text location if location_id not available
    - years_of_experience_min: Minimum years of experience
    - years_of_experience_max: Maximum years of experience
    - industry: Industry classification
    - company_size: Company size category
    - urgency: Request priority (low, normal, high, critical)
    - requestor_email: Email for notifications
    """
    job_title: str = Field(..., min_length=1, max_length=255, description="Job title")
    job_description: Optional[str] = Field(None, description="Full job description")
    location_id: Optional[int] = Field(None, ge=1, description="Location ID from locations table")
    location_text: Optional[str] = Field(None, max_length=255, description="Free-text location")
    years_of_experience_min: Optional[int] = Field(None, ge=0, le=50, description="Minimum years of experience")
    years_of_experience_max: Optional[int] = Field(None, ge=0, le=50, description="Maximum years of experience")
    industry: Optional[str] = Field(None, max_length=100, description="Industry classification")
    company_size: Optional[str] = Field(None, max_length=50, description="Company size (e.g., '1-10', '11-50', '51-200', '201-500', '500+')")
    urgency: str = Field(default="normal", description="Request urgency: low, normal, high, critical")
    requestor_email: Optional[EmailStr] = Field(None, description="Email for notifications")

    # TPC-Specific Fields
    portfolio: Optional[str] = Field(None, max_length=255, description="Portfolio/Entity")
    department: Optional[str] = Field(None, max_length=255, description="Department")
    employment_type: Optional[str] = Field(None, max_length=50, description="Employment type (permanent, contract, fixed-term, secondment)")
    job_family: Optional[str] = Field(None, max_length=255, description="Job family")
    internal_grade: Optional[str] = Field(None, max_length=50, description="Internal company grade")
    skills_required: Optional[List[str]] = Field(None, description="Array of required skills")
    alternative_titles: Optional[List[str]] = Field(None, description="Alternative market titles")
    mercer_job_code: Optional[str] = Field(None, max_length=100, description="Mercer job code")
    mercer_job_description: Optional[str] = Field(None, description="Mercer job description")

    @validator("employment_type")
    def validate_employment_type(cls, v):
        """Validate employment type is one of allowed values."""
        if v is not None:
            allowed = ["permanent", "contract", "fixed-term", "secondment"]
            if v.lower() not in allowed:
                raise ValueError(f"employment_type must be one of: {', '.join(allowed)}")
            return v.lower()
        return v

    @validator("skills_required", "alternative_titles")
    def validate_string_arrays(cls, v):
        """Validate array fields don't exceed reasonable limits."""
        if v is not None:
            if len(v) > 50:
                raise ValueError("Array cannot contain more than 50 items")
            # Remove empty strings and duplicates
            v = list(dict.fromkeys([s.strip() for s in v if s and s.strip()]))
        return v

    @validator("internal_grade")
    def validate_internal_grade(cls, v):
        """Validate internal grade format."""
        if v is not None:
            # Remove whitespace
            v = v.strip()
            # Check if it's numeric or alphanumeric
            if not v.replace("-", "").replace(".", "").isalnum():
                raise ValueError("internal_grade must be alphanumeric (e.g., '10', 'M5', 'L3-A')")
        return v

    @validator("urgency")
    def validate_urgency(cls, v):
        """Validate urgency is one of allowed values."""
        allowed = ["low", "normal", "high", "critical"]
        if v not in allowed:
            raise ValueError(f"urgency must be one of: {', '.join(allowed)}")
        return v

    @validator("years_of_experience_max")
    def validate_experience_range(cls, v, values):
        """Ensure max experience >= min experience."""
        if v is not None and "years_of_experience_min" in values:
            min_exp = values["years_of_experience_min"]
            if min_exp is not None and v < min_exp:
                raise ValueError("years_of_experience_max must be >= years_of_experience_min")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "job_title": "Senior Data Scientist",
                "job_description": "We are seeking an experienced Data Scientist to lead our analytics team...",
                "location_text": "Singapore",
                "years_of_experience_min": 5,
                "years_of_experience_max": 10,
                "industry": "Technology",
                "company_size": "51-200",
                "urgency": "normal",
                "requestor_email": "hr@example.com"
            }
        }


# --------------------------------------------------------------------------
# Response Schemas
# --------------------------------------------------------------------------

class JobPricingRequestResponse(BaseModel):
    """
    Response schema for job pricing request.

    Returned immediately after creating a request.
    """
    id: UUID = Field(..., description="Unique request ID")
    status: str = Field(..., description="Request status: pending, processing, completed, failed")
    job_title: str = Field(..., description="Job title")
    location_text: Optional[str] = Field(None, description="Location")
    urgency: str = Field(..., description="Request urgency")
    created_at: datetime = Field(..., description="Request creation timestamp")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "8bd79f97-efb3-4b5a-bf43-639b345a1a34",
                "status": "pending",
                "job_title": "Senior Data Scientist",
                "location_text": "Singapore",
                "urgency": "normal",
                "created_at": "2025-01-15T10:30:00Z"
            }
        }


class SkillExtracted(BaseModel):
    """Individual extracted skill."""
    skill_name: str = Field(..., description="Skill name")
    skill_category: Optional[str] = Field(None, description="Skill category")
    matched_tsc_code: Optional[str] = Field(None, description="Matched SSG TSC code")
    match_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Match confidence (0.0-1.0)")
    is_core_skill: bool = Field(default=False, description="Whether this is a core skill")

    class Config:
        from_attributes = True


class PricingResult(BaseModel):
    """Pricing calculation result."""
    currency: str = Field(default="SGD", description="Currency code (ISO 4217)")
    period: str = Field(default="annual", description="Salary period (annual, monthly)")
    recommended_min: Optional[float] = Field(None, ge=0, description="Recommended minimum salary")
    recommended_max: Optional[float] = Field(None, ge=0, description="Recommended maximum salary")
    target_salary: Optional[float] = Field(None, ge=0, description="Target/mid-point salary")
    p10: Optional[float] = Field(None, ge=0, description="10th percentile salary")
    p25: Optional[float] = Field(None, ge=0, description="25th percentile salary")
    p50: Optional[float] = Field(None, ge=0, description="50th percentile salary (median)")
    p75: Optional[float] = Field(None, ge=0, description="75th percentile salary")
    p90: Optional[float] = Field(None, ge=0, description="90th percentile salary")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=100.0, description="Pricing confidence (0-100)")
    confidence_level: Optional[str] = Field(None, description="High, Medium, or Low")
    market_position: Optional[str] = Field(None, description="Market position description")
    summary_text: Optional[str] = Field(None, description="Human-readable summary")
    key_factors: Optional[list[str]] = Field(default_factory=list, description="Key factors influencing result")
    considerations: Optional[list[str]] = Field(default_factory=list, description="Considerations/caveats")
    confidence_factors: Optional[dict] = Field(None, description="Breakdown of confidence components")
    total_data_points: Optional[int] = Field(None, description="Total number of data points used")
    data_sources_used: Optional[int] = Field(None, description="Number of data sources used")
    data_consistency_score: Optional[float] = Field(None, description="Data consistency score (0-100)")

    @validator("recommended_max")
    def validate_salary_range(cls, v, values):
        """Ensure recommended_max >= recommended_min and salaries are positive."""
        if v is not None and "recommended_min" in values:
            min_salary = values["recommended_min"]
            if min_salary is not None:
                if v < min_salary:
                    raise ValueError("recommended_max must be >= recommended_min")
        return v

    class Config:
        from_attributes = True


class JobPricingResultResponse(BaseModel):
    """
    Complete job pricing result response.

    Returned when request is completed.
    """
    # Request info
    id: UUID = Field(..., description="Request ID")
    status: str = Field(..., description="Request status")
    job_title: str = Field(..., description="Job title")
    job_description: Optional[str] = Field(None, description="Job description")
    location_text: Optional[str] = Field(None, description="Location")
    years_of_experience_min: Optional[int] = Field(None, description="Minimum years of experience")
    years_of_experience_max: Optional[int] = Field(None, description="Maximum years of experience")
    industry: Optional[str] = Field(None, description="Industry")
    company_size: Optional[str] = Field(None, description="Company size")
    urgency: str = Field(..., description="Request urgency")

    # TPC-Specific Fields
    portfolio: Optional[str] = Field(None, description="Portfolio/Entity")
    department: Optional[str] = Field(None, description="Department")
    employment_type: Optional[str] = Field(None, description="Employment type")
    job_family: Optional[str] = Field(None, description="Job family")
    internal_grade: Optional[str] = Field(None, description="Internal company grade")
    skills_required: Optional[List[str]] = Field(None, description="Skills required")
    alternative_titles: Optional[List[str]] = Field(None, description="Alternative market titles")
    mercer_job_code: Optional[str] = Field(None, description="Mercer job code")
    mercer_job_description: Optional[str] = Field(None, description="Mercer job description")

    # Timing
    created_at: datetime = Field(..., description="Request creation timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")

    # Results
    extracted_skills: List[SkillExtracted] = Field(default_factory=list, description="Extracted skills")
    pricing_result: Optional[PricingResult] = Field(None, description="Pricing calculation result")

    # Error handling
    error_message: Optional[str] = Field(None, description="Error message if failed")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "8bd79f97-efb3-4b5a-bf43-639b345a1a34",
                "status": "completed",
                "job_title": "Senior Data Scientist",
                "job_description": "We are seeking an experienced Data Scientist...",
                "location_text": "Singapore",
                "years_of_experience_min": 5,
                "years_of_experience_max": 10,
                "industry": "Technology",
                "company_size": "51-200",
                "urgency": "normal",
                "created_at": "2025-01-15T10:30:00Z",
                "completed_at": "2025-01-15T10:31:30Z",
                "extracted_skills": [
                    {
                        "skill_name": "Python",
                        "skill_category": "Programming",
                        "matched_tsc_code": "TSC-PRG-001",
                        "match_confidence": 0.95,
                        "is_core_skill": True
                    }
                ],
                "pricing_result": {
                    "base_salary_sgd": 120000.0,
                    "adjusted_salary_sgd": 120000.0,
                    "salary_band_min_sgd": 100000.0,
                    "salary_band_max_sgd": 140000.0,
                    "confidence_score": 0.85,
                    "matched_mercer_code": "MER-DS-001",
                    "matched_ssg_code": "ICT-DA-DSC-1a2b3c",
                    "pricing_factors": {
                        "experience_multiplier": 1.2,
                        "location_adjustment": 1.0,
                        "skill_premium": 0.15
                    }
                },
                "error_message": None
            }
        }


class JobPricingStatusResponse(BaseModel):
    """
    Quick status check response.

    Lightweight response for checking request status.
    """
    id: UUID = Field(..., description="Request ID")
    status: str = Field(..., description="Request status")
    created_at: datetime = Field(..., description="Creation timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    error_message: Optional[str] = Field(None, description="Error message if failed")

    class Config:
        from_attributes = True


# --------------------------------------------------------------------------
# Error Response Schema
# --------------------------------------------------------------------------

class ErrorResponse(BaseModel):
    """Standard error response."""
    success: bool = Field(default=False, description="Always false for errors")
    error: dict = Field(..., description="Error details")

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Job pricing request not found",
                    "details": "No request found with ID: 8bd79f97-efb3-4b5a-bf43-639b345a1a34"
                }
            }
        }
