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
import hashlib
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime, timedelta, timezone
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import func

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

    Workflow (Option 1+: Smart Caching):
    1. Generate request hash for deduplication
    2. Find or create request (reuse existing)
    3. Check cache for non-expired result
    4. If cache miss: Calculate fresh recommendation
    5. Save versioned result with smart expiry
    6. Cleanup old versions (keep last 5)
    7. Return result with cache metadata
    """

    # Cache TTL per data source (smart expiry)
    CACHE_TTL = {
        "mercer": timedelta(days=30),        # Annual survey data
        "my_careers_future": timedelta(hours=24),  # Daily job postings
        "glassdoor": timedelta(days=7),      # Weekly updates
        "hays": timedelta(days=14),          # Bi-weekly updates
        "linkedin": timedelta(days=3),       # Frequent updates
    }

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

    def _generate_request_hash(self, job_title: str, location: str, user_id: int) -> str:
        """
        Generate deterministic SHA256 hash for request deduplication.

        Hash is based on normalized key fields to handle variations:
        - "Software Engineer" == "software engineer"
        - "Singapore" == "singapore"

        Args:
            job_title: Job title
            location: Location
            user_id: User ID

        Returns:
            64-character SHA256 hex digest
        """
        normalized = f"{job_title.lower().strip()}|{location.lower().strip()}|{user_id}"
        return hashlib.sha256(normalized.encode()).hexdigest()

    def _find_or_create_request(
        self,
        request_hash: str,
        job_title: str,
        location: str,
        user_id: int,
        job_description: str = ""
    ) -> JobPricingRequest:
        """
        Find existing request by hash or create new one.

        This implements request deduplication - if same (job_title + location + user)
        combination exists, reuse it and increment request_count.

        Args:
            request_hash: Pre-calculated SHA256 hash
            job_title: Job title
            location: Location
            user_id: User ID
            job_description: Optional job description

        Returns:
            Existing or newly created JobPricingRequest
        """
        existing = self.session.query(JobPricingRequest).filter_by(
            request_hash=request_hash
        ).first()

        if existing:
            # Update tracking fields
            existing.last_requested_at = datetime.now(timezone.utc)
            existing.request_count += 1
            self.session.flush()
            logger.info(
                f"Reusing request {existing.id} "
                f"(requested {existing.request_count} times, "
                f"first: {existing.first_requested_at})"
            )
            return existing

        # Create new request
        new_request = JobPricingRequest(
            request_hash=request_hash,
            job_title=job_title,
            location_text=location,
            job_description=job_description or "",
            requested_by=str(user_id),  # Convert to string for DB field
            requestor_email=f"user_{user_id}@system.local",  # Placeholder
            request_count=1,
            first_requested_at=datetime.now(timezone.utc),
            last_requested_at=datetime.now(timezone.utc),
            status='pending',
            urgency='normal',
        )
        self.session.add(new_request)
        self.session.flush()
        logger.info(f"Created new request {new_request.id} (hash: {request_hash[:16]}...)")
        return new_request

    def _get_cached_result(self, request: JobPricingRequest) -> Optional[JobPricingResult]:
        """
        Get latest non-expired cached result for a request.

        Checks for:
        1. Result exists for this request
        2. Result is marked as latest (is_latest = TRUE)
        3. Result hasn't expired (expires_at > now)

        Args:
            request: JobPricingRequest to check

        Returns:
            JobPricingResult if valid cache exists, None otherwise
        """
        cached = self.session.query(JobPricingResult).filter(
            JobPricingResult.request_id == request.id,
            JobPricingResult.is_latest == True,
            JobPricingResult.expires_at > datetime.now(timezone.utc)
        ).first()

        if cached:
            cache_age = datetime.now(timezone.utc) - cached.calculated_at
            time_to_expiry = cached.expires_at - datetime.now(timezone.utc)
            logger.info(
                f"Cache HIT for request {request.id} "
                f"(version {cached.version}, age: {cache_age}, "
                f"expires in: {time_to_expiry})"
            )
        else:
            logger.info(f"Cache MISS for request {request.id}")

        return cached

    def _calculate_cache_expiry(self, data_sources_used: List[str]) -> datetime:
        """
        Calculate smart cache expiry based on data source freshness.

        Uses the SHORTEST TTL among all data sources to ensure result freshness.
        For example, if using Mercer (30 days) + MyCareersFuture (24 hours),
        cache expires in 24 hours.

        Args:
            data_sources_used: List of data source names

        Returns:
            Datetime when cache should expire
        """
        if not data_sources_used:
            # Default 24 hours if no sources specified
            return datetime.now(timezone.utc) + timedelta(hours=24)

        ttls = [
            self.CACHE_TTL.get(source, timedelta(hours=24))
            for source in data_sources_used
        ]
        shortest_ttl = min(ttls)

        expiry = datetime.now(timezone.utc) + shortest_ttl
        logger.debug(
            f"Cache TTL: {shortest_ttl} (sources: {data_sources_used}, "
            f"expires: {expiry})"
        )
        return expiry

    def _cleanup_old_versions(self, request: JobPricingRequest, keep_last: int = 5):
        """
        Delete old versions, keeping only the last N.

        This prevents unlimited database growth while maintaining
        recent audit trail for compliance.

        Args:
            request: JobPricingRequest to cleanup
            keep_last: Number of versions to keep (default: 5)
        """
        # Get all versions for this request, ordered by version DESC
        all_versions = self.session.query(JobPricingResult).filter(
            JobPricingResult.request_id == request.id
        ).order_by(JobPricingResult.version.desc()).all()

        # Delete versions beyond keep_last
        if len(all_versions) > keep_last:
            versions_to_delete = all_versions[keep_last:]
            count = len(versions_to_delete)

            for old_result in versions_to_delete:
                logger.debug(f"Deleting old version {old_result.version} (id: {old_result.id})")
                self.session.delete(old_result)

            logger.info(
                f"Cleaned up {count} old versions for request {request.id}, "
                f"kept last {keep_last}"
            )

    def calculate_recommendation(
        self,
        job_title: str,
        location: str,
        user_id: int,
        job_description: str = "",
        force_refresh: bool = False
    ) -> Dict:
        """
        Calculate comprehensive salary recommendation with smart caching.

        This is the main entry point implementing Option 1+ architecture:
        1. Generate request hash for deduplication
        2. Find or create request (reuse existing)
        3. Check cache for non-expired result (unless force_refresh)
        4. If cache miss: Calculate fresh recommendation
        5. Save versioned result with smart expiry
        6. Cleanup old versions (keep last 5)
        7. Return result with cache metadata

        Args:
            job_title: Job title to price
            location: Location (e.g., "Singapore")
            user_id: User ID making the request
            job_description: Optional job description
            force_refresh: If True, bypass cache and recalculate

        Returns:
            Dictionary with recommendation details, percentiles, confidence, and cache metadata

        Example:
            >>> service = SalaryRecommendationServiceV2(session)
            >>> result = service.calculate_recommendation(
            ...     job_title="Software Engineer",
            ...     location="Singapore",
            ...     user_id=1,
            ...     force_refresh=False
            ... )
            >>> print(f"Target: ${result['target_salary']:,.0f}")
            >>> print(f"Cache hit: {result['metadata']['from_cache']}")
        """
        logger.info(f"Calculating salary recommendation for: {job_title} in {location}")

        try:
            # Step 1: Generate request hash for deduplication
            request_hash = self._generate_request_hash(job_title, location, user_id)

            # Step 2: Find or create request (reuse existing)
            request = self._find_or_create_request(
                request_hash=request_hash,
                job_title=job_title,
                location=location,
                user_id=user_id,
                job_description=job_description
            )

            # Step 3: Check cache for non-expired result (unless force_refresh)
            if not force_refresh:
                cached_result = self._get_cached_result(request)
                if cached_result:
                    # Cache HIT - mark and return
                    cached_result.cache_hit = True
                    self.session.commit()

                    # Format cached result for response
                    response = self._format_cached_response(cached_result)
                    logger.info(
                        f"Returning cached result (version {cached_result.version}, "
                        f"age: {datetime.now(timezone.utc) - cached_result.calculated_at})"
                    )
                    return response

            # Step 4: Cache MISS or force refresh - calculate fresh recommendation
            logger.info("Cache miss or force refresh - calculating fresh recommendation")
            request.status = 'processing'
            request.processing_started_at = datetime.now(timezone.utc)
            self.session.flush()

            # Extract skills from job description
            extracted_skills = []
            if request.job_description:
                logger.debug("Extracting skills from job description...")
                extracted_skills = self.skill_service.extract_skills(
                    job_description=request.job_description,
                    job_title=request.job_title
                )
                logger.info(f"Extracted {len(extracted_skills)} skills")

            # Match to Mercer job code (if available)
            mercer_match = None
            if request.job_title:
                logger.debug("Matching to Mercer job library...")
                mercer_match = self.matching_service.find_best_match(
                    job_title=request.job_title,
                    job_description=request.job_description
                )
                if mercer_match:
                    logger.info(f"Matched to Mercer code: {mercer_match.get('job_code')}")

            # Calculate pricing using V3 algorithm with Mercer match for job family filtering
            logger.debug("Calculating pricing with multi-source aggregation...")
            pricing_result: PricingResult = self.pricing_service.calculate_pricing(request, mercer_match)

            # Step 5: Save versioned result with smart expiry
            job_result = self._save_result(request, pricing_result, mercer_match)

            # Step 6: Cleanup old versions (keep last 5)
            self._cleanup_old_versions(request, keep_last=5)

            # Mark request as completed
            request.status = 'completed'
            request.processing_completed_at = datetime.now(timezone.utc)
            self.session.commit()

            # Step 7: Format response with cache metadata
            response = self._format_response(pricing_result, job_result, mercer_match, extracted_skills)

            logger.info(
                f"Fresh calculation complete: ${pricing_result.target_salary:,.0f} "
                f"(confidence: {pricing_result.confidence_score:.0f}%, "
                f"version: {job_result.version})"
            )

            return response

        except Exception as e:
            request.status = 'failed'
            request.error_message = str(e)
            self.session.rollback()
            logger.error(f"Error calculating recommendation: {e}", exc_info=True)
            raise

    def _save_result(
        self,
        request: JobPricingRequest,
        pricing_result: PricingResult,
        mercer_match: Optional[Dict] = None
    ) -> JobPricingResult:
        """
        Save versioned pricing result to database with smart cache expiry.

        Implements Option 1+ versioning:
        1. Mark all existing results as not latest (is_latest = FALSE)
        2. Get next version number (max version + 1)
        3. Calculate smart cache expiry based on data sources
        4. Save new result with version, is_latest=TRUE, expires_at

        Args:
            request: Original pricing request
            pricing_result: Calculated pricing result
            mercer_match: Matched Mercer job (if any)

        Returns:
            Saved JobPricingResult model with version and expiry
        """
        try:
            # Step 1: Mark all existing results as not latest
            self.session.query(JobPricingResult).filter(
                JobPricingResult.request_id == request.id,
                JobPricingResult.is_latest == True
            ).update({"is_latest": False})
            self.session.flush()

            # Step 2: Get next version number
            max_version = self.session.query(
                func.max(JobPricingResult.version)
            ).filter(
                JobPricingResult.request_id == request.id
            ).scalar()

            next_version = (max_version or 0) + 1
            logger.info(f"Saving result as version {next_version} for request {request.id}")

            # Step 3: Calculate smart cache expiry based on data sources
            data_sources_used = [c.source_name for c in pricing_result.source_contributions]
            expires_at = self._calculate_cache_expiry(data_sources_used)

            # Prepare confidence factors with Mercer match
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

            # Step 4: Create new versioned result
            job_result = JobPricingResult(
                request_id=request.id,
                # Versioning fields
                version=next_version,
                is_latest=True,
                calculated_at=datetime.now(timezone.utc),
                expires_at=expires_at,
                cache_hit=False,
                # Salary data
                recommended_min=pricing_result.recommended_min,
                recommended_max=pricing_result.recommended_max,
                target_salary=pricing_result.target_salary,
                p10=pricing_result.p10,
                p25=pricing_result.p25,
                p50=pricing_result.p50,
                p75=pricing_result.p75,
                p90=pricing_result.p90,
                # Confidence and metadata
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
            logger.info(
                f"Saved result version {next_version} (expires: {expires_at}, "
                f"id: {job_result.id})"
            )

            return job_result

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error saving result: {e}", exc_info=True)
            raise

    def _format_cached_response(self, job_result: JobPricingResult) -> Dict:
        """
        Format cached JobPricingResult from database as API response.

        Used when returning cached results to maintain consistent response format.

        Args:
            job_result: Cached JobPricingResult from database

        Returns:
            Formatted response dictionary with cache metadata
        """
        # Extract mercer match from confidence_factors if available
        mercer_match = None
        if job_result.confidence_factors and "mercer_match" in job_result.confidence_factors:
            mercer_match = job_result.confidence_factors["mercer_match"]

        # Extract source contributions from confidence_factors
        source_contributions = job_result.confidence_factors.get("data_sources", []) if job_result.confidence_factors else []

        return {
            "result_id": str(job_result.id),
            "job_title": job_result.request.job_title,

            # Main recommendation
            "recommended_min": float(job_result.recommended_min),
            "recommended_max": float(job_result.recommended_max),
            "target_salary": float(job_result.target_salary),

            # Percentiles
            "percentiles": {
                "p10": float(job_result.p10),
                "p25": float(job_result.p25),
                "p50": float(job_result.p50),
                "p75": float(job_result.p75),
                "p90": float(job_result.p90),
            },

            # Confidence and quality
            "confidence_score": float(job_result.confidence_score),
            "confidence_level": job_result.confidence_level,

            # Data sources
            "data_sources_used": job_result.data_sources_used,
            "source_contributions": [
                {
                    "source": contrib["source"],
                    "weight": f"{contrib['weight'] * 100:.0f}%",
                    "sample_size": contrib["sample_size"],
                    "recency_days": contrib.get("recency_days"),
                    "match_quality": f"{contrib['match_quality'] * 100:.0f}%",
                }
                for contrib in source_contributions
            ],

            # Alternative scenarios
            "scenarios": {
                name: {
                    "min": float(scenario["min"]),
                    "max": float(scenario["max"]),
                    "use_case": scenario.get("use_case", ""),
                }
                for name, scenario in (job_result.alternative_scenarios or {}).items()
            },

            # Mercer match (if available)
            "mercer_match": mercer_match,

            # Skills - empty for cached response (not stored)
            "skills_extracted": 0,
            "top_skills": [],

            # Explanation
            "explanation": job_result.summary_text,

            # Metadata - includes cache info
            "created_at": job_result.created_at.isoformat(),
            "currency": "SGD",
            "period": "Annual",
            "metadata": {
                "from_cache": True,
                "version": job_result.version,
                "calculated_at": job_result.calculated_at.isoformat(),
                "expires_at": job_result.expires_at.isoformat(),
                "cache_age_seconds": int((datetime.now(timezone.utc) - job_result.calculated_at).total_seconds()),
                "time_to_expiry_seconds": int((job_result.expires_at - datetime.now(timezone.utc)).total_seconds()),
            }
        }

    def _format_response(
        self,
        pricing_result: PricingResult,
        job_result: JobPricingResult,
        mercer_match: Optional[Dict],
        extracted_skills: List
    ) -> Dict:
        """
        Format fresh pricing result as API response.

        Args:
            pricing_result: Calculated pricing result
            job_result: Saved database result
            mercer_match: Matched Mercer job
            extracted_skills: Extracted skills

        Returns:
            Formatted response dictionary with fresh calculation metadata
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
                    "skill_name": skill.skill_name,
                    "category": getattr(skill, 'skill_category', None),
                    "confidence": getattr(skill, 'match_confidence', None),
                }
                for skill in extracted_skills[:10]  # Top 10 skills
            ],

            # Explanation
            "explanation": pricing_result.explanation,

            # Metadata - includes cache info
            "created_at": job_result.created_at.isoformat(),
            "currency": "SGD",
            "period": "Annual",
            "metadata": {
                "from_cache": False,
                "version": job_result.version,
                "calculated_at": job_result.calculated_at.isoformat(),
                "expires_at": job_result.expires_at.isoformat(),
            }
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
