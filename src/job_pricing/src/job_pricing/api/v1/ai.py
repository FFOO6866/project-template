"""
AI Generation Endpoints

Endpoints for AI-powered job analysis features:
- Skills extraction
- Job description generation
- Mercer code mapping
- Alternative title generation

SECURITY: All endpoints require authentication with USE_AI_GENERATION permission.
Rate limited to prevent excessive OpenAI API costs.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from openai import OpenAI
import os
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from job_pricing.core.database import get_session
from job_pricing.models.auth import User
from job_pricing.api.dependencies.auth import get_current_active_user, get_optional_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

# Rate limiter for AI endpoints (cost control)
limiter = Limiter(key_func=get_remote_address)

# Initialize OpenAI client lazily
_openai_client = None

def get_openai_client():
    """Get OpenAI client, initialized lazily"""
    global _openai_client
    if _openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OpenAI API key not configured"
            )
        _openai_client = OpenAI(api_key=api_key)
    return _openai_client


# --------------------------------------------------------------------------
# Request/Response Schemas
# --------------------------------------------------------------------------

class SkillExtractionRequest(BaseModel):
    """Request for extracting skills from job title/description."""
    job_title: str = Field(..., min_length=1, description="Job title")
    job_description: Optional[str] = Field(None, description="Job description")

    class Config:
        json_schema_extra = {
            "example": {
                "job_title": "Senior Data Scientist",
                "job_description": "Responsible for building ML models and analyzing data..."
            }
        }


class ExtractedSkill(BaseModel):
    """Individual extracted skill."""
    skill_name: str
    skill_category: Optional[str] = None
    proficiency_level: Optional[str] = None  # e.g., "Expert", "Intermediate"

    class Config:
        json_schema_extra = {
            "example": {
                "skill_name": "Python",
                "skill_category": "Programming Language",
                "proficiency_level": "Expert"
            }
        }


class SkillExtractionResponse(BaseModel):
    """Response with extracted skills."""
    skills: List[ExtractedSkill]
    total_count: int

    class Config:
        json_schema_extra = {
            "example": {
                "skills": [
                    {
                        "skill_name": "Python",
                        "skill_category": "Programming Language",
                        "proficiency_level": "Expert"
                    },
                    {
                        "skill_name": "Machine Learning",
                        "skill_category": "Technical Skill",
                        "proficiency_level": "Expert"
                    }
                ],
                "total_count": 2
            }
        }


class JobDescriptionGenerationRequest(BaseModel):
    """Request for generating job description."""
    job_title: str = Field(..., min_length=1)
    department: Optional[str] = None
    job_family: Optional[str] = None
    key_responsibilities: Optional[List[str]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "job_title": "Senior Data Scientist",
                "department": "Analytics",
                "job_family": "Data Science",
                "key_responsibilities": ["Build ML models", "Analyze data"]
            }
        }


class JobDescriptionGenerationResponse(BaseModel):
    """Response with generated job description."""
    job_description: str
    word_count: int

    class Config:
        json_schema_extra = {
            "example": {
                "job_description": "We are seeking an experienced Senior Data Scientist...",
                "word_count": 250
            }
        }


class MercerMappingRequest(BaseModel):
    """Request for mapping to Mercer job code."""
    job_title: str = Field(..., min_length=1)
    job_description: Optional[str] = None
    job_family: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "job_title": "Senior Data Scientist",
                "job_family": "Data Science"
            }
        }


class MercerMatch(BaseModel):
    """Single Mercer job match with similarity score."""
    mercer_job_code: str
    mercer_job_title: str
    mercer_job_description: str
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Semantic similarity score (0-1)")
    job_family: Optional[str] = Field(None, description="Mercer job family code")


class MercerMappingResponse(BaseModel):
    """Response with top 3 Mercer job matches."""
    # Top match (for backward compatibility and quick access)
    mercer_job_code: str
    mercer_job_title: str
    mercer_job_description: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)

    # All top 3 matches (new field)
    matches: List[MercerMatch] = Field(..., min_items=1, max_items=3, description="Top 3 matching Mercer jobs")

    class Config:
        json_schema_extra = {
            "example": {
                "mercer_job_code": "ICT.04.005.M50",
                "mercer_job_title": "Data Scientist - Senior",
                "mercer_job_description": "Applies advanced analytics...",
                "confidence_score": 0.85,
                "matches": [
                    {
                        "mercer_job_code": "ICT.04.005.M50",
                        "mercer_job_title": "Data Scientist - Senior",
                        "mercer_job_description": "Applies advanced analytics...",
                        "similarity_score": 0.85,
                        "job_family": "ICT"
                    },
                    {
                        "mercer_job_code": "ICT.04.004.ET2",
                        "mercer_job_title": "Data Scientist",
                        "mercer_job_description": "Develops data models...",
                        "similarity_score": 0.78,
                        "job_family": "ICT"
                    },
                    {
                        "mercer_job_code": "ICT.05.002.M50",
                        "mercer_job_title": "Analytics Manager",
                        "mercer_job_description": "Leads analytics team...",
                        "similarity_score": 0.72,
                        "job_family": "ICT"
                    }
                ]
            }
        }


class AlternativeTitlesRequest(BaseModel):
    """Request for generating alternative job titles."""
    job_title: str = Field(..., min_length=1)
    job_family: Optional[str] = None
    industry: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "job_title": "Senior Data Scientist",
                "job_family": "Data Science",
                "industry": "Technology"
            }
        }


class AlternativeTitlesResponse(BaseModel):
    """Response with alternative titles."""
    alternative_titles: List[str]
    total_count: int

    class Config:
        json_schema_extra = {
            "example": {
                "alternative_titles": [
                    "Data Scientist",
                    "Senior Data Analyst",
                    "Machine Learning Engineer",
                    "AI Engineer"
                ],
                "total_count": 4
            }
        }


# --------------------------------------------------------------------------
# AI Helper Functions
# --------------------------------------------------------------------------

def call_openai_chat(system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
    """
    Call OpenAI Chat Completion API.

    Args:
        system_prompt: System instructions
        user_prompt: User message
        temperature: Sampling temperature (0.0-1.0)

    Returns:
        AI-generated response text
    """
    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL_DEFAULT", "gpt-4"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
            max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "2000"))
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OpenAI API error: {str(e)}"
        )


def parse_skills_from_text(text: str) -> List[ExtractedSkill]:
    """
    Parse skills from AI-generated text.

    Expected format:
    - Python (Programming Language) - Expert
    - Machine Learning (Technical Skill) - Expert
    """
    skills = []
    lines = [line.strip() for line in text.split('\n') if line.strip()]

    for line in lines:
        if line.startswith('-') or line.startswith('•'):
            line = line[1:].strip()

        # Try to parse: "Skill (Category) - Level"
        parts = line.split('-')
        if len(parts) >= 1:
            skill_part = parts[0].strip()
            level = parts[1].strip() if len(parts) > 1 else None

            # Extract category if present
            if '(' in skill_part and ')' in skill_part:
                skill_name = skill_part[:skill_part.index('(')].strip()
                category = skill_part[skill_part.index('(')+1:skill_part.index(')')].strip()
            else:
                skill_name = skill_part
                category = None

            if skill_name:
                skills.append(ExtractedSkill(
                    skill_name=skill_name,
                    skill_category=category,
                    proficiency_level=level
                ))

    return skills


# --------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------

@router.post(
    "/extract-skills",
    response_model=SkillExtractionResponse,
    summary="Extract Skills from Job Title/Description",
    description="Use AI to extract required skills from job information",
    responses={
        200: {"description": "Skills extracted successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Permission denied"},
        429: {"description": "Rate limit exceeded"},
        503: {"description": "OpenAI API unavailable"},
    },
)
@limiter.limit("10/minute")
async def extract_skills(
    request: Request,
    data: SkillExtractionRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Extract skills from job title and description using OpenAI.

    This endpoint analyzes the job information and identifies:
    - Required technical skills
    - Soft skills
    - Domain knowledge
    - Proficiency levels

    **Rate Limit**: 10 requests per minute per user
    **Permission Required**: USE_AI_GENERATION

    **Example Use Case**:
    - User enters job title: "Senior Data Scientist"
    - AI extracts: Python, SQL, Machine Learning, Statistics, etc.
    """
    logger.info(
        f"AI skill extraction requested by user {current_user.email} "
        f"for job: {data.job_title}"
    )

    system_prompt = """You are an expert HR analyst specializing in job skill extraction.
Given a job title and description, extract all required skills.

Format each skill as:
- Skill Name (Category) - Proficiency Level

Categories: Programming Language, Framework, Tool, Soft Skill, Domain Knowledge, Technical Skill
Proficiency Levels: Expert, Intermediate, Basic

Example:
- Python (Programming Language) - Expert
- Communication (Soft Skill) - Intermediate
- Machine Learning (Technical Skill) - Expert"""

    user_prompt = f"""Extract skills from this job:

Job Title: {data.job_title}
"""

    if data.job_description:
        user_prompt += f"\nJob Description: {data.job_description}"

    user_prompt += "\n\nList 5-15 most important skills in the specified format."

    # Call OpenAI
    try:
        ai_response = call_openai_chat(system_prompt, user_prompt)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OpenAI API error for user {current_user.email if current_user else 'anonymous'}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service temporarily unavailable"
        )

    # Parse response
    skills = parse_skills_from_text(ai_response)

    return SkillExtractionResponse(
        skills=skills,
        total_count=len(skills)
    )


@router.post(
    "/generate-job-description",
    response_model=JobDescriptionGenerationResponse,
    summary="Generate Job Description",
    description="Use AI to generate a professional job description",
    responses={
        200: {"description": "Job description generated successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Permission denied"},
        429: {"description": "Rate limit exceeded"},
        503: {"description": "OpenAI API unavailable"},
    },
)
@limiter.limit("10/minute")
async def generate_job_description(
    request: Request,
    data: JobDescriptionGenerationRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Generate a professional job description using OpenAI.

    Creates a comprehensive job description including:
    - Overview
    - Key responsibilities
    - Required qualifications
    - Preferred qualifications

    **Rate Limit**: 10 requests per minute per user
    **Permission Required**: USE_AI_GENERATION
    """
    logger.info(
        f"AI job description generation requested by user {current_user.email} "
        f"for job: {data.job_title}"
    )

    system_prompt = """You are an expert HR professional who writes compelling job descriptions.
Create professional, detailed job descriptions that attract top talent.

Format:
1. Overview (2-3 sentences)
2. Key Responsibilities (5-7 bullet points)
3. Required Qualifications (4-5 bullet points)
4. Preferred Qualifications (2-3 bullet points)

Keep tone professional but engaging. Be specific about skills and experience."""

    user_prompt = f"""Create a job description for:

Job Title: {data.job_title}
"""

    if data.department:
        user_prompt += f"\nDepartment: {data.department}"
    if data.job_family:
        user_prompt += f"\nJob Family: {data.job_family}"
    if data.key_responsibilities:
        user_prompt += f"\nKey Responsibilities: {', '.join(data.key_responsibilities)}"

    # Call OpenAI
    try:
        description = call_openai_chat(system_prompt, user_prompt, temperature=0.7)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OpenAI API error for user {current_user.email if current_user else 'anonymous'}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service temporarily unavailable"
        )

    word_count = len(description.split())

    return JobDescriptionGenerationResponse(
        job_description=description,
        word_count=word_count
    )


@router.post(
    "/map-mercer-code",
    response_model=MercerMappingResponse,
    summary="Map to Mercer Job Code",
    description="Use AI to map job to Mercer job classification",
    responses={
        200: {"description": "Mercer code mapped successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Permission denied"},
        429: {"description": "Rate limit exceeded"},
        503: {"description": "OpenAI API unavailable"},
    },
)
@limiter.limit("10/minute")
async def map_mercer_code(
    request: Request,
    data: MercerMappingRequest,
    db: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """
    Map job title to Mercer job code using semantic search against the Mercer database.

    **Rate Limit**: 10 requests per minute
    **Authentication**: Optional (but recommended for tracking)

    **How it works**:
    - Uses vector embeddings to find the most similar Mercer job
    - Searches across 18,000+ standardized Mercer jobs
    - Returns REAL job codes with official descriptions
    - Confidence score based on semantic similarity

    **Note**: This uses the same proven semantic search as the salary recommendation engine.
    """
    logger.info(
        f"Mercer mapping requested by user {current_user.email if current_user else 'anonymous'} "
        f"for job: {data.job_title}"
    )

    # ✅ USE REAL SEMANTIC SEARCH AGAINST MERCER DATABASE
    # Instead of having AI guess codes, use the same semantic search as salary recommendation
    from job_pricing.services.job_matching_service import JobMatchingService
    from job_pricing.models.mercer import MercerJobLibrary

    try:
        # Use JobMatchingService for semantic search against Mercer database
        matching_service = JobMatchingService(db)

        # Find similar jobs using vector embeddings
        # NOTE: For Mercer mapping, we search across ALL families to find the best semantic match
        # The job_family is intentionally set to None to avoid overly restrictive filtering
        logger.info(f"[MERCER SEARCH] Searching Mercer database for:")
        logger.info(f"  job_title: '{data.job_title}'")
        logger.info(f"  job_description: '{data.job_description}'")
        logger.info(f"  job_family: None (searching ALL families for best semantic match)")
        logger.info(f"  requested_family_hint: '{data.job_family}' (not used as filter)")
        logger.info(f"  top_k: 3")

        try:
            matches = matching_service.find_similar_jobs(
                job_title=data.job_title,
                job_description=data.job_description or "",
                job_family=None,  # Search ALL families - don't filter
                top_k=3  # Get top 3 to log them
            )
        except Exception as search_error:
            logger.error(f"[MERCER SEARCH] ❌ Exception during find_similar_jobs: {search_error}", exc_info=True)
            raise

        logger.info(f"[MERCER SEARCH] find_similar_jobs() returned: {len(matches) if matches else 0} matches")

        if not matches or len(matches) == 0:
            logger.warning(f"[MERCER SEARCH] ❌ No Mercer matches found for: {data.job_title}")
            logger.warning(f"[MERCER SEARCH] This should NOT happen - database has 18,000+ jobs with embeddings")
            logger.warning(f"[MERCER SEARCH] Possible causes:")
            logger.warning(f"  1. OpenAI embedding generation failed silently")
            logger.warning(f"  2. Database connection issue")
            logger.warning(f"  3. All embeddings are NULL in database")

            # Check if we can query the database at all
            try:
                job_count = db.query(MercerJobLibrary).count()
                logger.warning(f"[MERCER SEARCH] Database has {job_count} total Mercer jobs")

                embedding_count = db.query(MercerJobLibrary).filter(
                    MercerJobLibrary.embedding.isnot(None)
                ).count()
                logger.warning(f"[MERCER SEARCH] Database has {embedding_count} jobs with embeddings")
            except Exception as db_check_error:
                logger.error(f"[MERCER SEARCH] Failed to check database: {db_check_error}")

            raise HTTPException(
                status_code=404,
                detail="No matching Mercer job found. The semantic search returned zero results, which is unexpected. Please check the server logs for details."
            )

        # Log all matches for debugging
        logger.info(f"[MERCER SEARCH] ✅ Found {len(matches)} matches for '{data.job_title}':")
        for i, match in enumerate(matches[:3], 1):
            logger.info(f"  {i}. {match['job_code']} - {match['job_title']} (similarity: {match['similarity_score']:.2%}, family: {match.get('family', 'N/A')})")

        # Get full details for all top 3 matches from database
        top_matches = matches[:3]  # Limit to top 3
        match_details = []

        for match in top_matches:
            mercer_job = db.query(MercerJobLibrary).filter(
                MercerJobLibrary.job_code == match["job_code"]
            ).first()

            if mercer_job:
                match_details.append(MercerMatch(
                    mercer_job_code=mercer_job.job_code,
                    mercer_job_title=mercer_job.job_title,
                    mercer_job_description=mercer_job.job_description or "No description available.",
                    similarity_score=match["similarity_score"],
                    job_family=match.get("family")
                ))
            else:
                logger.warning(f"Matched job code {match['job_code']} not found in database, skipping")

        if not match_details:
            logger.error("No matched jobs found in database")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal error: No matched jobs found in database"
            )

        # Best match is the first one
        best_match_detail = match_details[0]

        logger.info(
            f"✅ Matched '{data.job_title}' to {best_match_detail.mercer_job_code} - {best_match_detail.mercer_job_title} "
            f"(similarity: {best_match_detail.similarity_score:.2%}), with {len(match_details)-1} alternatives"
        )

        return MercerMappingResponse(
            # Top match fields (for backward compatibility)
            mercer_job_code=best_match_detail.mercer_job_code,
            mercer_job_title=best_match_detail.mercer_job_title,
            mercer_job_description=best_match_detail.mercer_job_description,
            confidence_score=best_match_detail.similarity_score,
            # All matches (new field)
            matches=match_details
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during Mercer job matching: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to map to Mercer job code: {str(e)}"
        )


@router.post(
    "/generate-alternative-titles",
    response_model=AlternativeTitlesResponse,
    summary="Generate Alternative Job Titles",
    description="Use AI to generate alternative/similar job titles",
    responses={
        200: {"description": "Alternative titles generated successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Permission denied"},
        429: {"description": "Rate limit exceeded"},
        503: {"description": "OpenAI API unavailable"},
    },
)
@limiter.limit("10/minute")
async def generate_alternative_titles(
    request: Request,
    data: AlternativeTitlesRequest,
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """
    Generate alternative job titles for broader market matching.

    Helps identify similar roles across different companies and industries.

    **Rate Limit**: 10 requests per minute
    **Authentication**: Optional (but recommended for tracking)
    """
    logger.info(
        f"AI alternative titles requested by user {current_user.email if current_user else 'anonymous'} "
        f"for job: {data.job_title}"
    )
    system_prompt = """You are an expert in job market terminology and job title standardization.
Generate alternative job titles that represent similar roles.

Consider:
- Industry variations (e.g., "Engineer" vs "Developer")
- Seniority levels
- Regional differences
- Company-specific titles

Provide 5-10 alternative titles, ranked by similarity."""

    user_prompt = f"""Generate alternative titles for:

Job Title: {data.job_title}
"""

    if data.job_family:
        user_prompt += f"\nJob Family: {data.job_family}"
    if data.industry:
        user_prompt += f"\nIndustry: {data.industry}"

    user_prompt += "\n\nList alternative titles (one per line, no numbering):"

    # Call OpenAI
    try:
        ai_response = call_openai_chat(system_prompt, user_prompt)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"OpenAI API error for user {current_user.email}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service temporarily unavailable"
        )

    # Parse titles
    titles = []
    lines = [line.strip() for line in ai_response.split('\n') if line.strip()]

    for line in lines:
        # Remove bullets, numbers, etc.
        cleaned = line.lstrip('-•*0123456789. ').strip()
        if cleaned and len(cleaned) > 3:
            titles.append(cleaned)

    # Remove duplicates while preserving order
    seen = set()
    unique_titles = []
    for title in titles:
        if title.lower() not in seen:
            seen.add(title.lower())
            unique_titles.append(title)

    return AlternativeTitlesResponse(
        alternative_titles=unique_titles[:10],  # Limit to 10
        total_count=len(unique_titles)
    )


@router.get(
    "/health",
    summary="AI Service Health Check",
    description="Check if AI service and OpenAI connection are working",
)
async def ai_health_check():
    """Health check for AI endpoints."""
    api_key_configured = bool(os.getenv("OPENAI_API_KEY"))

    status_value = "healthy" if api_key_configured else "degraded"
    logger.info(f"AI health check performed: status={status_value}")

    return {
        "status": status_value,
        "openai_api_key_configured": api_key_configured,
        "model": os.getenv("OPENAI_MODEL_DEFAULT", "gpt-4"),
        "message": "AI endpoints ready" if api_key_configured else "OpenAI API key not configured"
    }
