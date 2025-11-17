"""
Salary Recommendation Service V2 - Integrated with V3 Pricing Algorithm

Updates the salary recommendation service to use the new multi-source
weighted aggregation algorithm from pricing_calculation_service_v3.

Key Changes from V1:
- Uses PricingCalculationServiceV3 for multi-source aggregation
- Returns percentiles (P10, P25, P50, P75, P90)
- Includes confidence scores
- Provides alternative scenarios
- Source contribution breakdown

NO MOCK DATA - Production-ready implementation.
"""

import logging
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime
import uuid

from sqlalchemy.orm import Session

from job_pricing.models import (
    JobPricingRequest,
    JobPricingResult,
    DataSourceContribution as DataSourceContributionModel,
)
from job_pricing.services.pricing_calculation_service_v3 import (
    PricingCalculationServiceV3,
    PricingResult,
    DataSourceContribution,
)
from job_pricing.services.skill_extraction_service import SkillExtractionService
from job_pricing.services.job_matching_service import JobMatchingService
from job_pricing.repositories.job_pricing_repository import JobPricingRepository

logger = logging.getLogger(__name__)


class SalaryRecommendationServiceV2:
    """
    Production-ready salary recommendation service using V3 pricing algorithm.

    Workflow:
    1. Extract skills from job description (using OpenAI)
    2. Match job to Mercer code (using vector similarity)
    3. Aggregate data from 5 sources with weights
    4. Calculate percentiles and confidence
    5. Generate recommendations with scenarios
    """

    def __init__(self, session: Session):
        """
        Initialize service.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session
        self.pricing_service = PricingCalculationServiceV3(session)
        self.skill_service = SkillExtractionService()
        self.matching_service = JobMatchingService(session)
        self.repository = JobPricingRepository(session)

    def calculate_recommendation(
        self,
        request: JobPricingRequest
    ) -> Dict:
        """
        Calculate comprehensive salary recommendation.

        This is the main entry point that orchestrates the complete workflow.

        Args:
            request: Job pricing request with job details

        Returns:
            Dictionary with recommendation details, percentiles, and confidence

        Example:
            >>> service = SalaryRecommendationServiceV2(session)
            >>> recommendation = service.calculate_recommendation(request)
            >>> print(f"Target: ${recommendation['target_salary']:,.0f}")
            >>> print(f"Range: ${recommendation['recommended_min']:,.0f} - "
            ...       f"${recommendation['recommended_max']:,.0f}")
            >>> print(f"Confidence: {recommendation['confidence_score']:.0f}%")
        """
        logger.info(f"Calculating salary recommendation for: {request.job_title}")

        try:
            # Save request to database first (if not already saved)
            if not request.id:
                self.session.add(request)
                self.session.flush()  # Get the ID
                logger.debug(f"Saved request to database with ID: {request.id}")
            # Step 1: Extract skills from job description
            extracted_skills = []
            if request.job_description:
                logger.debug("Extracting skills from job description...")
                extracted_skills = self.skill_service.extract_skills(
                    job_description=request.job_description,
                    job_title=request.job_title
                )
                logger.info(f"Extracted {len(extracted_skills)} skills")

            # Step 2: Match to Mercer job code (if available)
            mercer_match = None
            if request.job_title:
                logger.debug("Matching to Mercer job library...")
                mercer_match = self.matching_service.find_best_match(
                    job_title=request.job_title,
                    job_description=request.job_description
                )
                if mercer_match:
                    logger.info(f"Matched to Mercer code: {mercer_match.job_code}")

            # Step 3: Calculate pricing using V3 algorithm
            logger.debug("Calculating pricing with multi-source aggregation...")
            pricing_result: PricingResult = self.pricing_service.calculate_pricing(request)

            # Step 4: Save result to database
            job_result = self._save_result(request, pricing_result, mercer_match)

            # Step 5: Format response
            response = self._format_response(pricing_result, job_result, mercer_match, extracted_skills)

            logger.info(f"Recommendation complete: ${pricing_result.target_salary:,.0f} "
                       f"(confidence: {pricing_result.confidence_score:.0f}%)")

            return response

        except Exception as e:
            logger.error(f"Error calculating recommendation: {e}", exc_info=True)
            raise

    def _save_result(
        self,
        request: JobPricingRequest,
        pricing_result: PricingResult,
        mercer_match: Optional[Dict] = None
    ) -> JobPricingResult:
        """
        Save pricing result to database.

        Args:
            request: Original pricing request
            pricing_result: Calculated pricing result
            mercer_match: Matched Mercer job (if any)

        Returns:
            Saved JobPricingResult model
        """
        try:
            # Create main result with confidence factors including Mercer match
            # Convert all Decimal values to float for JSON serialization
            confidence_factors = {
                "data_sources": [
                    {
                        "source": c.source_name,
                        "weight": float(c.weight),
                        "sample_size": int(c.sample_size),
                        "recency_days": int(c.recency_days) if c.recency_days else None,
                        "match_quality": float(c.match_quality),
                    }
                    for c in pricing_result.source_contributions
                ],
                "total_sample": int(sum(c.sample_size for c in pricing_result.source_contributions)),
            }
            if mercer_match:
                confidence_factors["mercer_match"] = {
                    "job_code": str(mercer_match.get("job_code")) if mercer_match.get("job_code") else None,
                    "job_title": str(mercer_match.get("job_title")) if mercer_match.get("job_title") else None,
                    "match_score": float(mercer_match.get("match_score")) if mercer_match.get("match_score") else None,
                }

            # Convert alternative_scenarios Decimal values to float for JSON
            alternative_scenarios_serializable = {}
            for scenario_name, scenario_data in pricing_result.alternative_scenarios.items():
                alternative_scenarios_serializable[scenario_name] = {
                    k: float(v) if isinstance(v, Decimal) else v
                    for k, v in scenario_data.items()
                }

            job_result = JobPricingResult(
                request_id=request.id,
                recommended_min=pricing_result.recommended_min,
                recommended_max=pricing_result.recommended_max,
                target_salary=pricing_result.target_salary,
                p10=pricing_result.p10,
                p25=pricing_result.p25,
                p50=pricing_result.p50,
                p75=pricing_result.p75,
                p90=pricing_result.p90,
                confidence_score=Decimal(str(pricing_result.confidence_score)),
                confidence_level=self._get_confidence_level(pricing_result.confidence_score),
                confidence_factors=confidence_factors,
                summary_text=pricing_result.explanation,
                alternative_scenarios=alternative_scenarios_serializable,
                total_data_points=int(sum(c.sample_size for c in pricing_result.source_contributions)),
                data_sources_used=len(pricing_result.source_contributions),
            )

            self.session.add(job_result)
            self.session.flush()  # Get ID

            # Save source contributions
            for contrib in pricing_result.source_contributions:
                source_contrib = DataSourceContributionModel(
                    result_id=job_result.id,
                    source_name=contrib.source_name,
                    weight_applied=Decimal(str(contrib.weight)),
                    sample_size=contrib.sample_size,
                    quality_score=Decimal(str(contrib.match_quality)),
                    recency_weight=Decimal(str(1.0 - (contrib.recency_days / 365.0))) if contrib.recency_days else None,
                )
                self.session.add(source_contrib)

            self.session.commit()
            logger.debug(f"Saved result to database: {job_result.id}")

            return job_result

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error saving result: {e}")
            raise

    def _format_response(
        self,
        pricing_result: PricingResult,
        job_result: JobPricingResult,
        mercer_match: Optional[Dict],
        extracted_skills: List
    ) -> Dict:
        """
        Format pricing result as API response.

        Args:
            pricing_result: Calculated pricing result
            job_result: Saved database result
            mercer_match: Matched Mercer job
            extracted_skills: Extracted skills

        Returns:
            Formatted response dictionary
        """
        return {
            "result_id": str(job_result.id),
            "job_title": job_result.request.job_title,

            # Main recommendation
            "recommended_min": float(pricing_result.recommended_min),
            "recommended_max": float(pricing_result.recommended_max),
            "target_salary": float(pricing_result.target_salary),

            # Percentiles
            "percentiles": {
                "p10": float(pricing_result.p10),
                "p25": float(pricing_result.p25),
                "p50": float(pricing_result.p50),
                "p75": float(pricing_result.p75),
                "p90": float(pricing_result.p90),
            },

            # Confidence and quality
            "confidence_score": pricing_result.confidence_score,
            "confidence_level": self._get_confidence_level(pricing_result.confidence_score),

            # Data sources
            "data_sources_used": len(pricing_result.source_contributions),
            "source_contributions": [
                {
                    "source": contrib.source_name,
                    "weight": f"{contrib.weight * 100:.0f}%",
                    "sample_size": contrib.sample_size,
                    "recency_days": contrib.recency_days,
                    "match_quality": f"{contrib.match_quality * 100:.0f}%",
                }
                for contrib in pricing_result.source_contributions
            ],

            # Alternative scenarios
            "scenarios": {
                name: {
                    "min": float(scenario["min"]),
                    "max": float(scenario["max"]),
                    "use_case": scenario.get("use_case", ""),
                }
                for name, scenario in pricing_result.alternative_scenarios.items()
            },

            # Mercer match (if available)
            "mercer_match": {
                "job_code": mercer_match.get("job_code"),
                "job_title": mercer_match.get("job_title"),
                "match_score": mercer_match.get("match_score"),
                "career_level": mercer_match.get("career_level"),
            } if mercer_match else None,

            # Skills
            "skills_extracted": len(extracted_skills),
            "top_skills": [
                {
                    "skill_name": skill.get("skill_name"),
                    "category": skill.get("category"),
                    "confidence": skill.get("confidence"),
                }
                for skill in extracted_skills[:10]  # Top 10 skills
            ],

            # Explanation
            "explanation": pricing_result.explanation,

            # Metadata
            "created_at": job_result.created_at.isoformat(),
            "currency": "SGD",
            "period": "Annual",
        }

    def _get_confidence_level(self, score: float) -> str:
        """
        Convert confidence score to human-readable level.

        Args:
            score: Confidence score (0-100)

        Returns:
            Confidence level string (High, Medium, or Low per DB constraint)
        """
        if score >= 75:
            return "High"
        elif score >= 50:
            return "Medium"
        else:
            return "Low"

    def get_recommendation_history(
        self,
        limit: int = 10,
        skip: int = 0
    ) -> List[Dict]:
        """
        Get recent salary recommendations.

        Args:
            limit: Maximum results to return
            skip: Number of results to skip

        Returns:
            List of recommendation summaries
        """
        results = self.repository.get_recent_results(limit=limit, skip=skip)

        return [
            {
                "result_id": str(result.id),
                "job_title": result.request.job_title,
                "target_salary": float(result.target_salary),
                "recommended_range": f"${result.recommended_min:,.0f} - ${result.recommended_max:,.0f}",
                "confidence_score": float(result.confidence_score),
                "created_at": result.created_at.isoformat(),
            }
            for result in results
        ]

    def get_recommendation_by_id(self, result_id: uuid.UUID) -> Optional[Dict]:
        """
        Get detailed recommendation by ID.

        Args:
            result_id: Result UUID

        Returns:
            Detailed recommendation or None
        """
        result = self.repository.get_result_by_id(result_id)

        if not result:
            return None

        # Reconstruct pricing result from database
        source_contribs = [
            DataSourceContribution(
                source_name=contrib.source_name,
                weight=float(contrib.weight_applied) if contrib.weight_applied else 0.0,
                sample_size=contrib.sample_size,
                data_points=[],  # Not stored in DB
                recency_days=int((1.0 - float(contrib.recency_weight)) * 365) if contrib.recency_weight else 0,
                match_quality=float(contrib.quality_score) if contrib.quality_score else 0.0,
            )
            for contrib in result.source_contributions
        ]

        pricing_result = PricingResult(
            recommended_min=result.recommended_min,
            recommended_max=result.recommended_max,
            target_salary=result.target_salary,
            p10=result.p10,
            p25=result.p25,
            p50=result.p50,
            p75=result.p75,
            p90=result.p90,
            confidence_score=float(result.confidence_score),
            source_contributions=source_contribs,
            alternative_scenarios=result.alternative_scenarios or {},
            explanation=result.summary_text,
        )

        # Extract Mercer match from confidence_factors if present
        mercer_match = None
        if result.confidence_factors and "mercer_match" in result.confidence_factors:
            mercer_match = result.confidence_factors["mercer_match"]

        return self._format_response(
            pricing_result=pricing_result,
            job_result=result,
            mercer_match=mercer_match,
            extracted_skills=[],  # Not stored in DB
        )
