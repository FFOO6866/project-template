"""
Job Processing Service

Orchestrates the complete job pricing workflow:
1. Extract skills from job description (OpenAI)
2. Match skills to SSG TSC taxonomy
3. Find matching job roles
4. Calculate salary pricing
5. Generate final results
"""

import logging
from typing import Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session

from job_pricing.repositories.job_pricing_repository import JobPricingRepository
from job_pricing.models import JobPricingRequest, JobPricingResult, DataSourceContribution as DBContribution
from job_pricing.exceptions import NoMarketDataError
from .skill_extraction_service import SkillExtractionService
from .skill_matching_service import SkillMatchingService
from .pricing_calculation_service_v3 import PricingCalculationServiceV3
from .job_matching_service import JobMatchingService

logger = logging.getLogger(__name__)


class JobProcessingService:
    """
    Service for processing job pricing requests end-to-end.

    Coordinates skill extraction, matching, and pricing calculation.
    Updates request status and stores results in database.
    """

    def __init__(self, session: Session):
        """
        Initialize job processing service.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session
        self.repository = JobPricingRepository(session)
        self.extraction_service = SkillExtractionService()
        self.matching_service = SkillMatchingService(session)
        self.job_matching_service = JobMatchingService(session)
        self.pricing_service = PricingCalculationServiceV3(session)

    def process_request(self, request_id: UUID) -> JobPricingRequest:
        """
        Process a job pricing request end-to-end.

        Steps:
        1. Mark request as processing
        2. Extract skills from job description
        3. Match skills to SSG TSC taxonomy
        4. Find matching job roles
        5. Calculate salary pricing
        6. Save results and mark as completed

        Args:
            request_id: UUID of the job pricing request

        Returns:
            Updated JobPricingRequest with results

        Raises:
            ValueError: If request not found
            Exception: If processing fails

        Example:
            >>> service = JobProcessingService(session)
            >>> request = service.process_request(request_id)
            >>> print(f"Status: {request.status}")
            >>> print(f"Skills found: {len(request.extracted_skills)}")
        """
        # Get the request
        request = self.repository.get_by_id(request_id)
        if not request:
            raise ValueError(f"Job pricing request not found: {request_id}")

        try:
            # Mark as processing
            self.repository.mark_as_processing(request_id)
            self.session.commit()

            # Step 1: Extract skills from job description
            logger.info(f"[{request_id}] Step 1: Extracting skills...")
            extracted_skills = self.extraction_service.extract_skills_simple(
                request.job_title, request.job_description
            )
            logger.info(f"[{request_id}] Extracted {len(extracted_skills)} skills")

            # Step 2: Match skills to SSG TSC
            logger.info(f"[{request_id}] Step 2: Matching skills to SSG TSC...")
            skill_matches = self.matching_service.match_skills_batch(extracted_skills)
            logger.info(
                f"[{request_id}] Matched {sum(1 for m in skill_matches if m.matched_tsc)} skills"
            )

            # Step 3: Save matched skills
            logger.info(f"[{request_id}] Step 3: Saving matched skills...")
            saved_skills = self.matching_service.save_matched_skills(
                request_id, skill_matches
            )
            logger.info(f"[{request_id}] Saved {len(saved_skills)} skills to database")

            # Step 4: Calculate pricing using V3 multi-source aggregation
            logger.info(f"[{request_id}] Step 4: Calculating pricing...")
            pricing_result = self._calculate_pricing(request, skill_matches)

            # Step 5: Commit pricing result and contributions (already added to session in _calculate_pricing)
            if pricing_result:
                logger.info(f"[{request_id}] Step 5: Committing pricing result...")
                self.session.commit()

            # Mark as completed
            self.repository.mark_as_completed(request_id, duration_seconds=0)
            self.session.commit()

            # Refresh request to get updated data
            self.session.refresh(request)

            logger.info(f"[{request_id}] Processing completed successfully")
            return request

        except Exception as e:
            # Rollback transaction first
            self.session.rollback()

            # Mark as failed
            logger.error(f"[{request_id}] Error: {e}", exc_info=True)
            try:
                request.status = "failed"
                request.error_message = str(e)[:500]  # Limit error message length
                self.session.commit()
            except Exception as commit_error:
                logger.error(f"[{request_id}] Failed to mark as failed: {commit_error}")
                self.session.rollback()
            raise

    def _calculate_pricing(
        self, request: JobPricingRequest, skill_matches
    ) -> Optional[JobPricingResult]:
        """
        Calculate salary pricing using V3 multi-source weighted aggregation.

        Uses PricingCalculationServiceV3 (production-ready) which:
        1. Finds best Mercer job match using semantic search
        2. Aggregates data from 5 sources (Mercer, MCF, Glassdoor, HRIS, Applicants)
        3. Calculates weighted percentiles (P10-P90)
        4. Generates confidence scores based on data quality
        5. Returns production-ready salary recommendation

        Args:
            request: Job pricing request
            skill_matches: List of matched skills (used for logging, V3 uses Mercer match)

        Returns:
            JobPricingResult or None if pricing cannot be calculated
        """
        try:
            logger.info(f"    Calculating pricing for: {request.job_title}")
            logger.info(f"    - Location: {request.location_text or 'Not specified'}")
            logger.info(f"    - Using V3 multi-source weighted aggregation")

            # Step 1: Find best Mercer job match
            mercer_match = self.job_matching_service.find_best_match(
                job_title=request.job_title,
                job_description=request.job_description or "",
                use_llm_reasoning=False  # Faster, deterministic matching
            )

            if mercer_match:
                logger.info(f"    - Mercer match: {mercer_match.get('job_code')} "
                           f"(similarity: {mercer_match.get('similarity_score', 0):.2%})")
            else:
                logger.info(f"    - No Mercer match found, using external sources only")

            # Step 2: Calculate pricing using V3 multi-source aggregation
            pricing_result = self.pricing_service.calculate_pricing(request, mercer_match)

            # Step 3: Convert PricingResult dataclass to JobPricingResult model
            # Determine confidence level from score
            if pricing_result.confidence_score >= 75:
                confidence_level = 'High'
            elif pricing_result.confidence_score >= 50:
                confidence_level = 'Medium'
            else:
                confidence_level = 'Low'

            # Convert alternative_scenarios Decimals to floats for JSON storage
            from decimal import Decimal
            def decimal_to_float(obj):
                if isinstance(obj, dict):
                    return {k: decimal_to_float(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [decimal_to_float(item) for item in obj]
                elif isinstance(obj, Decimal):
                    return float(obj)
                return obj

            scenarios_json = decimal_to_float(pricing_result.alternative_scenarios)

            db_result = JobPricingResult(
                request_id=request.id,
                currency='SGD',
                period='annual',
                recommended_min=pricing_result.recommended_min,
                recommended_max=pricing_result.recommended_max,
                target_salary=pricing_result.target_salary,
                p10=pricing_result.p10,
                p25=pricing_result.p25,
                p50=pricing_result.p50,
                p75=pricing_result.p75,
                p90=pricing_result.p90,
                confidence_score=pricing_result.confidence_score,
                confidence_level=confidence_level,
                summary_text=pricing_result.explanation,
                alternative_scenarios=scenarios_json,
                total_data_points=sum(c.sample_size for c in pricing_result.source_contributions),
                data_sources_used=len(pricing_result.source_contributions),
                data_consistency_score=pricing_result.confidence_score,  # Use confidence as proxy
            )

            # Add to session and flush to get ID for contributions
            self.session.add(db_result)
            self.session.flush()

            # Step 4: Save data source contributions for audit trail
            for contrib in pricing_result.source_contributions:
                recency_days = contrib.recency_days if contrib.recency_days is not None else 180
                recency_weight = max(0.0, 1.0 - (recency_days / 365))

                db_contrib = DBContribution(
                    result_id=db_result.id,
                    source_name=contrib.source_name,
                    weight_applied=contrib.weight,
                    sample_size=contrib.sample_size,
                    quality_score=contrib.match_quality,
                    recency_weight=recency_weight,
                    p10=contrib.p10,
                    p25=contrib.p25,
                    p50=contrib.p50,
                    p75=contrib.p75,
                    p90=contrib.p90,
                )
                self.session.add(db_contrib)

            logger.info(f"    Target salary: SGD {db_result.target_salary:,.2f}")
            logger.info(f"    Range: SGD {db_result.recommended_min:,.2f} - {db_result.recommended_max:,.2f}")
            logger.info(f"    Confidence: {db_result.confidence_level} ({db_result.confidence_score:.0f}%)")
            logger.info(f"    Data sources: {len(pricing_result.source_contributions)}")

            return db_result

        except NoMarketDataError as e:
            # Specific handling for no market data available
            logger.warning(f"    No market data available for '{request.job_title}': {e}")
            return None

        except Exception as e:
            logger.error(f"    Error calculating pricing: {e}", exc_info=True)
            return None

    def get_processing_status(self, request_id: UUID) -> dict:
        """
        Get current processing status of a request.

        Args:
            request_id: UUID of the job pricing request

        Returns:
            Dictionary with status information

        Example:
            >>> status = service.get_processing_status(request_id)
            >>> print(f"Status: {status['status']}")
        """
        request = self.repository.get_by_id(request_id)
        if not request:
            return {"error": "Request not found"}

        return {
            "request_id": str(request.id),
            "status": request.status,
            "job_title": request.job_title,
            "created_at": request.created_at.isoformat(),
            "processing_started_at": (
                request.processing_started_at.isoformat()
                if request.processing_started_at
                else None
            ),
            "processing_completed_at": (
                request.processing_completed_at.isoformat()
                if request.processing_completed_at
                else None
            ),
            "error_message": request.error_message,
        }

    def reprocess_request(self, request_id: UUID) -> JobPricingRequest:
        """
        Reprocess a failed or completed request.

        Useful for:
        - Retrying failed requests
        - Updating results with improved algorithms
        - Testing changes

        Args:
            request_id: UUID of the job pricing request

        Returns:
            Updated JobPricingRequest

        Example:
            >>> request = service.reprocess_request(request_id)
        """
        request = self.repository.get_by_id(request_id)
        if not request:
            raise ValueError(f"Job pricing request not found: {request_id}")

        # Reset status to pending
        request.status = "pending"
        request.error_message = None
        request.processing_started_at = None
        request.processing_completed_at = None
        self.session.commit()

        # Process again
        return self.process_request(request_id)


# Convenience function for quick processing
def process_job_request(session: Session, request_id: UUID) -> JobPricingRequest:
    """
    Convenience function to process a job pricing request.

    Args:
        session: Database session
        request_id: UUID of the job pricing request

    Returns:
        Processed JobPricingRequest

    Example:
        >>> from job_pricing.services.job_processing_service import process_job_request
        >>> from job_pricing.core.database import get_session
        >>> session = get_session()
        >>> request = process_job_request(session, request_id)
        >>> print(f"Processed: {request.job_title}")
    """
    service = JobProcessingService(session)
    return service.process_request(request_id)
