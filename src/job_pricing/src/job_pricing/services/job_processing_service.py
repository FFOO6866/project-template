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
from job_pricing.models import JobPricingRequest, JobPricingResult
from .skill_extraction_service import SkillExtractionService
from .skill_matching_service import SkillMatchingService
from .pricing_calculation_service import PricingCalculationService

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

            # Step 4: Calculate pricing (placeholder for now)
            logger.info(f"[{request_id}] Step 4: Calculating pricing...")
            pricing_result = self._calculate_pricing(request, skill_matches)

            # Step 5: Save pricing result (if calculated)
            if pricing_result:
                logger.info(f"[{request_id}] Step 5: Saving pricing result...")
                self.session.add(pricing_result)
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
        Calculate salary pricing based on job details and matched skills.

        Uses PricingCalculationService to:
        1. Determine base salary from experience level
        2. Apply experience multiplier
        3. Apply location cost-of-living adjustments
        4. Calculate skill premium for high-value skills
        5. Apply industry and company size factors
        6. Generate salary bands with percentiles
        7. Calculate confidence scores

        Args:
            request: Job pricing request
            skill_matches: List of matched skills

        Returns:
            JobPricingResult or None if pricing cannot be calculated
        """
        try:
            # Get extracted skills from database
            from job_pricing.models import JobSkillsExtracted
            extracted_skills = (
                self.session.query(JobSkillsExtracted)
                .filter_by(request_id=request.id)
                .all()
            )

            if not extracted_skills:
                logger.debug(f"    No extracted skills found, using empty list")
                extracted_skills = []

            # Initialize pricing service
            pricing_service = PricingCalculationService(self.session)

            # Calculate pricing
            logger.info(f"    Calculating pricing for: {request.job_title}")
            logger.info(f"    - Location: {request.location_text or 'Not specified'}")
            logger.info(f"    - Experience: {request.years_of_experience_min or 0}-{request.years_of_experience_max or 0} years")
            logger.info(f"    - Industry: {request.industry or 'General'}")
            logger.info(f"    - Company size: {request.company_size or 'Not specified'}")
            logger.info(f"    - Skills: {len(extracted_skills)} extracted, {sum(1 for s in extracted_skills if s.matched_tsc_code)} matched")

            pricing_result, pricing_factors = pricing_service.calculate_pricing(
                request, extracted_skills
            )

            logger.info(f"    Target salary: SGD {pricing_result.target_salary:,.2f}")
            logger.info(f"    Range: SGD {pricing_result.recommended_min:,.2f} - {pricing_result.recommended_max:,.2f}")
            logger.info(f"    Confidence: {pricing_result.confidence_level} ({pricing_result.confidence_score}%)")

            return pricing_result

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
