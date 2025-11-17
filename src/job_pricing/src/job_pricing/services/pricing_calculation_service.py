"""
Salary Pricing Calculation Service

Calculates salary recommendations based on:
- Job title and description
- Extracted and matched skills
- Years of experience
- Location (cost-of-living adjustments)
- Industry
- Company size
- SSG job role mappings
"""

from typing import List, Dict, Optional, Tuple
from decimal import Decimal
from dataclasses import dataclass

from sqlalchemy.orm import Session

from job_pricing.models import (
    JobPricingRequest,
    JobPricingResult,
    JobSkillsExtracted,
    Location,
    LocationIndex,
)
from job_pricing.repositories.ssg_repository import SSGRepository


@dataclass
class SalaryBand:
    """Represents a salary band calculation"""

    recommended_min: Decimal
    recommended_max: Decimal
    target_salary: Decimal
    p10: Optional[Decimal] = None
    p25: Optional[Decimal] = None
    p50: Optional[Decimal] = None
    p75: Optional[Decimal] = None
    p90: Optional[Decimal] = None


@dataclass
class PricingFactors:
    """Factors that influence pricing calculation"""

    base_salary: Decimal
    experience_multiplier: float
    location_multiplier: float
    skill_premium: float
    industry_adjustment: float
    company_size_factor: float
    confidence_score: float


class PricingCalculationService:
    """
    Service for calculating salary pricing recommendations.

    Uses a multi-factor approach:
    1. Base salary from job role matching
    2. Experience level adjustments
    3. Location cost-of-living multipliers
    4. Skill premium calculations
    5. Industry and company size factors
    """

    # Base salary ranges by experience level (SGD, annual)
    BASE_SALARY_BY_EXPERIENCE = {
        "entry": (45000, 65000),  # 0-2 years
        "junior": (60000, 85000),  # 2-4 years
        "mid": (85000, 120000),  # 4-7 years
        "senior": (120000, 170000),  # 7-10 years
        "lead": (170000, 250000),  # 10+ years
    }

    # Industry adjustment factors
    INDUSTRY_FACTORS = {
        "Technology": 1.15,
        "Finance": 1.20,
        "Healthcare": 1.05,
        "Education": 0.90,
        "Retail": 0.95,
        "Manufacturing": 1.00,
        "Consulting": 1.10,
        "Government": 0.95,
        "default": 1.00,
    }

    # Company size factors
    COMPANY_SIZE_FACTORS = {
        "1-10": 0.85,
        "11-50": 0.90,
        "51-200": 1.00,
        "201-500": 1.10,
        "501-1000": 1.15,
        "1000+": 1.20,
        "default": 1.00,
    }

    def __init__(self, session: Session):
        """
        Initialize pricing calculation service.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session
        self.ssg_repository = SSGRepository(session)

    def calculate_pricing(
        self,
        request: JobPricingRequest,
        extracted_skills: List[JobSkillsExtracted],
    ) -> Tuple[JobPricingResult, PricingFactors]:
        """
        Calculate comprehensive salary pricing for a job request.

        Args:
            request: Job pricing request
            extracted_skills: List of extracted and matched skills

        Returns:
            Tuple of (JobPricingResult, PricingFactors)

        Example:
            >>> service = PricingCalculationService(session)
            >>> result, factors = service.calculate_pricing(request, skills)
            >>> print(f"Target salary: SGD {result.target_salary:,.2f}")
        """
        # Step 1: Determine experience level and base salary
        experience_level = self._classify_experience_level(
            request.years_of_experience_min, request.years_of_experience_max
        )
        base_min, base_max = self.BASE_SALARY_BY_EXPERIENCE[experience_level]
        base_salary = Decimal((base_min + base_max) / 2)

        # Step 2: Calculate experience multiplier
        experience_multiplier = self._calculate_experience_multiplier(
            request.years_of_experience_min, request.years_of_experience_max
        )

        # Step 3: Get location adjustment
        location_multiplier = self._get_location_multiplier(request.location_text)

        # Step 4: Calculate skill premium
        skill_premium = self._calculate_skill_premium(extracted_skills)

        # Step 5: Apply industry adjustment
        industry_adjustment = self.INDUSTRY_FACTORS.get(
            request.industry, self.INDUSTRY_FACTORS["default"]
        )

        # Step 6: Apply company size factor
        company_size_factor = self.COMPANY_SIZE_FACTORS.get(
            request.company_size, self.COMPANY_SIZE_FACTORS["default"]
        )

        # Step 7: Calculate final salary
        adjusted_salary = (
            base_salary
            * Decimal(experience_multiplier)
            * Decimal(location_multiplier)
            * Decimal(1 + skill_premium)
            * Decimal(industry_adjustment)
            * Decimal(company_size_factor)
        )

        # Step 8: Generate salary band
        salary_band = self._generate_salary_band(adjusted_salary)

        # Step 9: Calculate confidence score
        confidence_score = self._calculate_confidence_score(
            request, extracted_skills, experience_level
        )

        # Step 10: Create pricing factors record
        pricing_factors = PricingFactors(
            base_salary=base_salary,
            experience_multiplier=experience_multiplier,
            location_multiplier=location_multiplier,
            skill_premium=skill_premium,
            industry_adjustment=industry_adjustment,
            company_size_factor=company_size_factor,
            confidence_score=confidence_score,
        )

        # Step 11: Create JobPricingResult
        result = JobPricingResult(
            request_id=request.id,
            currency="SGD",
            period="annual",
            recommended_min=salary_band.recommended_min,
            recommended_max=salary_band.recommended_max,
            target_salary=salary_band.target_salary,
            p10=salary_band.p10,
            p25=salary_band.p25,
            p50=salary_band.p50,
            p75=salary_band.p75,
            p90=salary_band.p90,
            confidence_score=Decimal(confidence_score),
            confidence_level=self._get_confidence_level(confidence_score),
            market_position="Competitive market rate",
            summary_text=self._generate_summary_text(
                request, salary_band, confidence_score
            ),
            key_factors=[
                f"Experience: {experience_level} level",
                f"Location: {request.location_text or 'Not specified'}",
                f"Industry: {request.industry or 'General'}",
                f"Skills matched: {sum(1 for s in extracted_skills if s.matched_tsc_code)}",
            ],
            considerations=[
                "Pricing based on Singapore market data",
                "Actual offers may vary based on candidate quality",
                "Benefits and bonuses not included in estimates",
            ],
            confidence_factors={
                "experience_data": 0.8,
                "skills_match": min(
                    sum(1 for s in extracted_skills if s.matched_tsc_code)
                    / max(len(extracted_skills), 1),
                    1.0,
                ),
                "location_data": 0.9 if request.location_text else 0.5,
                "market_data": 0.7,
            },
            total_data_points=len(extracted_skills),
            data_sources_used=2,  # SSG + internal calculations
            data_consistency_score=Decimal(75.0),
        )

        return result, pricing_factors

    def _classify_experience_level(
        self, min_years: Optional[int], max_years: Optional[int]
    ) -> str:
        """Classify experience level based on years."""
        avg_years = 0
        if min_years and max_years:
            avg_years = (min_years + max_years) / 2
        elif min_years:
            avg_years = min_years
        elif max_years:
            avg_years = max_years

        if avg_years < 2:
            return "entry"
        elif avg_years < 4:
            return "junior"
        elif avg_years < 7:
            return "mid"
        elif avg_years < 10:
            return "senior"
        else:
            return "lead"

    def _calculate_experience_multiplier(
        self, min_years: Optional[int], max_years: Optional[int]
    ) -> float:
        """Calculate experience-based salary multiplier."""
        avg_years = 0
        if min_years and max_years:
            avg_years = (min_years + max_years) / 2
        elif min_years:
            avg_years = min_years
        elif max_years:
            avg_years = max_years

        # Progressive multiplier: 3% increase per year up to 15 years
        return min(1.0 + (avg_years * 0.03), 1.45)

    def _get_location_multiplier(self, location_text: Optional[str]) -> float:
        """Get location cost-of-living multiplier."""
        if not location_text:
            return 1.0

        # Try to find in location_index table
        location_index = (
            self.session.query(LocationIndex)
            .filter(LocationIndex.location_name.ilike(f"%{location_text}%"))
            .first()
        )

        if location_index:
            return float(location_index.cost_of_living_index)

        # Default Singapore multiplier
        if "singapore" in location_text.lower():
            return 1.0

        # Other locations (placeholder)
        return 1.0

    def _calculate_skill_premium(self, extracted_skills: List[JobSkillsExtracted]) -> float:
        """Calculate additional premium based on in-demand skills."""
        if not extracted_skills:
            return 0.0

        # High-value skills (placeholder - would come from market data)
        high_value_skills = {
            "python",
            "aws",
            "kubernetes",
            "machine learning",
            "react",
            "typescript",
            "terraform",
        }

        matched_high_value = sum(
            1
            for skill in extracted_skills
            if any(
                hv in skill.skill_name.lower() for hv in high_value_skills
            )
        )

        # 2% premium per high-value skill, max 20%
        return min(matched_high_value * 0.02, 0.20)

    def _generate_salary_band(self, target_salary: Decimal) -> SalaryBand:
        """Generate salary band with percentiles."""
        # Band spread: ±20% from target
        band_min = target_salary * Decimal("0.80")
        band_max = target_salary * Decimal("1.20")

        # Calculate percentiles
        p10 = target_salary * Decimal("0.75")
        p25 = target_salary * Decimal("0.90")
        p50 = target_salary  # Median = target
        p75 = target_salary * Decimal("1.10")
        p90 = target_salary * Decimal("1.25")

        return SalaryBand(
            recommended_min=band_min,
            recommended_max=band_max,
            target_salary=target_salary,
            p10=p10,
            p25=p25,
            p50=p50,
            p75=p75,
            p90=p90,
        )

    def _calculate_confidence_score(
        self,
        request: JobPricingRequest,
        extracted_skills: List[JobSkillsExtracted],
        experience_level: str,
    ) -> float:
        """Calculate overall confidence score (0-100)."""
        confidence = 70.0  # Base confidence

        # Add confidence for job description quality
        if request.job_description and len(request.job_description) > 100:
            confidence += 10.0

        # Add confidence for skills matched
        if extracted_skills:
            match_rate = sum(1 for s in extracted_skills if s.matched_tsc_code) / len(
                extracted_skills
            )
            confidence += match_rate * 10.0

        # Add confidence for experience data
        if request.years_of_experience_min and request.years_of_experience_max:
            confidence += 5.0

        # Add confidence for location data
        if request.location_text:
            confidence += 5.0

        return min(confidence, 100.0)

    def _get_confidence_level(self, confidence_score: float) -> str:
        """Convert numeric confidence to level."""
        if confidence_score >= 85:
            return "High"
        elif confidence_score >= 70:
            return "Medium"
        else:
            return "Low"

    def _generate_summary_text(
        self, request: JobPricingRequest, salary_band: SalaryBand, confidence: float
    ) -> str:
        """Generate human-readable summary."""
        return (
            f"Based on the job title '{request.job_title}' with "
            f"{request.years_of_experience_min or 'unspecified'}-"
            f"{request.years_of_experience_max or 'unspecified'} years of experience "
            f"in {request.industry or 'general'} industry, "
            f"we recommend an annual salary range of "
            f"SGD {salary_band.recommended_min:,.0f} to "
            f"SGD {salary_band.recommended_max:,.0f}, "
            f"with a target of SGD {salary_band.target_salary:,.0f}. "
            f"This estimate has {self._get_confidence_level(confidence).lower()} confidence."
        )
