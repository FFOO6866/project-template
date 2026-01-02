"""
Pricing Calculation Service V3 - Multi-Source Weighted Aggregation

Implements the complete Dynamic Pricing Algorithm as specified in:
docs/architecture/dynamic_pricing_algorithm.md

Key Features:
1. Multi-source data aggregation with weights:
   - Mercer IPE: 40%
   - MyCareersFuture: 25%
   - Glassdoor: 15%
   - Internal HRIS: 15%
   - Applicants: 5%

2. Statistical percentile calculation (P10, P25, P50, P75, P90)

3. Confidence scoring based on:
   - Data availability
   - Sample size
   - Data recency
   - Match quality

4. Alternative scenario generation

NO MOCK DATA - All calculations use real data sources.
"""

import logging
from typing import List, Dict, Optional
from decimal import Decimal
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone, date
import statistics

from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from job_pricing.models import (
    JobPricingRequest,
    JobPricingResult,
    MercerJobLibrary,
    MercerMarketData,
    ScrapedJobListing,
    InternalEmployee,
    Applicant,
    DataSourceContribution as DBContribution,
)
from job_pricing.repositories.mercer_repository import MercerRepository
from job_pricing.repositories.scraping_repository import ScrapingRepository
from job_pricing.repositories.hris_repository import HRISRepository
from job_pricing.exceptions import NoMarketDataError

logger = logging.getLogger(__name__)


@dataclass
class DataSourceContribution:
    """
    Represents contribution from a single data source.

    Attributes:
        source_name: Data source identifier (mercer, my_careers_future, etc.)
        weight: Base weight for this source (0.0-1.0), from WEIGHTS constant
        sample_size: Number of data points from this source
        data_points: Raw salary data points from this source
        p10-p90: Pre-calculated percentiles (for Mercer data)
        recency_days: Age of data in days (0 = current)
        match_quality: How well the data matches the query (0.0-1.0)
            - Used for filtering (MIN_MATCH_QUALITY_THRESHOLD)
            - Used for weighted aggregation (effective_weight = weight * match_quality)
        confidence: DEPRECATED - Not used. Use match_quality instead.
            - Kept for backwards compatibility with any serialized data.
            - Will be removed in future version.
    """
    source_name: str
    weight: float  # 0.0 to 1.0
    sample_size: int
    data_points: List[Decimal]  # All salary data points from this source
    p10: Optional[Decimal] = None
    p25: Optional[Decimal] = None
    p50: Optional[Decimal] = None
    p75: Optional[Decimal] = None
    p90: Optional[Decimal] = None
    recency_days: Optional[int] = None  # Age of data in days
    match_quality: float = 1.0  # 0.0 to 1.0, used for filtering and weighting
    confidence: float = 0.0  # DEPRECATED: Use match_quality instead


@dataclass
class PricingResult:
    """Complete pricing result with percentiles and confidence."""
    recommended_min: Decimal  # P25
    recommended_max: Decimal  # P75
    target_salary: Decimal  # P50
    p10: Decimal
    p25: Decimal
    p50: Decimal
    p75: Decimal
    p90: Decimal
    confidence_score: float  # 0 to 100
    source_contributions: List[DataSourceContribution]
    alternative_scenarios: Dict[str, Dict[str, Decimal]]
    explanation: str


class PricingCalculationServiceV3:
    """
    Production-ready pricing calculation service.

    Implements multi-source weighted aggregation with confidence scoring
    as specified in dynamic_pricing_algorithm.md
    """

    # Data source weights (must sum to 1.0)
    # Validated in __init__ to ensure consistency
    WEIGHTS = {
        "mercer": 0.40,
        "my_careers_future": 0.25,
        "glassdoor": 0.15,
        "internal_hris": 0.15,
        "applicants": 0.05,
    }

    # Confidence scoring thresholds
    MIN_SAMPLE_SIZE_EXCELLENT = 50
    MIN_SAMPLE_SIZE_GOOD = 20
    MIN_SAMPLE_SIZE_FAIR = 10

    MAX_DATA_AGE_EXCELLENT = 90  # days
    MAX_DATA_AGE_GOOD = 180
    MAX_DATA_AGE_FAIR = 365

    # Minimum match quality to include a data source
    # Below this threshold, the source is excluded to avoid
    # diluting results with unrelated job data
    MIN_MATCH_QUALITY_THRESHOLD = 0.7

    # Similarity thresholds for job title matching
    # Using PostgreSQL pg_trgm extension's similarity function
    SIMILARITY_THRESHOLD_STRICT = 0.4   # HRIS, Applicants (internal data, need closer match)
    SIMILARITY_THRESHOLD_RELAXED = 0.3  # MCF, Glassdoor (external data, allow broader match)

    # Query limits to prevent excessive data retrieval
    QUERY_LIMIT_EXTERNAL = 100  # MCF, Glassdoor, Applicants (more data available)
    QUERY_LIMIT_INTERNAL = 50   # HRIS only (current employees, less data)
    QUERY_LIMIT_MERCER_FAMILY = 10  # Max related titles to use in family matching

    # Default recency when scraped_at is missing (days)
    DEFAULT_RECENCY_DAYS = 30

    def __init__(self, session: Session):
        """
        Initialize service.

        Args:
            session: SQLAlchemy database session

        Note on Repositories:
            The repositories (mercer_repo, scraping_repo, hris_repo) are initialized
            but NOT YET USED in this service. This is TECHNICAL DEBT.

            Current state: Direct SQLAlchemy queries are used throughout.
            Target state: Should use repository methods for cleaner architecture.

            Repositories ARE used elsewhere in the codebase (API endpoints like
            internal_hris.py and external.py). Keeping them initialized here for:
            1. Architectural consistency with other services
            2. Future refactoring to repository pattern (see ADR-002)
            3. Avoiding breaking changes when refactoring

            TODO: Refactor data access methods to use repositories instead of
            direct session queries. This would improve:
            - Testability (can mock repositories)
            - Maintainability (centralized query logic)
            - Consistency (same queries across endpoints)
        """
        self.session = session

        # Validate weights sum to 1.0 (within floating point tolerance)
        weights_sum = sum(self.WEIGHTS.values())
        if not (0.99 <= weights_sum <= 1.01):
            raise ValueError(f"WEIGHTS must sum to 1.0, got {weights_sum}")

        # NOTE: Repositories initialized for future refactoring - see docstring above
        self.mercer_repo = MercerRepository(session)
        self.scraping_repo = ScrapingRepository(session)
        self.hris_repo = HRISRepository(session)

    def calculate_pricing(
        self,
        request: JobPricingRequest,
        mercer_match: Optional[Dict] = None
    ) -> PricingResult:
        """
        Calculate comprehensive pricing using multi-source weighted aggregation.

        This is the main entry point implementing the full algorithm.

        Args:
            request: Job pricing request with job details
            mercer_match: Optional Mercer job match with job_code and family info

        Returns:
            Complete pricing result with percentiles and confidence
        """
        logger.info(f"Calculating pricing for: {request.job_title}")

        # Step 1: Gather data from all sources (with Mercer match for job family filtering)
        contributions = self._gather_all_sources(request, mercer_match)

        if not contributions:
            logger.error("❌ NO DATA SOURCES AVAILABLE - Cannot provide salary recommendation")
            # NO FALLBACK DATA - Raise exception to be handled by API layer
            raise NoMarketDataError(
                job_title=request.job_title,
                sources_attempted=["mercer", "my_careers_future", "glassdoor", "internal_hris", "applicants"]
            )

        # Step 2: Check if we have high-quality Mercer data with COMPLETE percentiles
        # If so, use it as primary source (no aggregation needed)
        # IMPORTANT: Must have P25, P50, and P75 to avoid DB constraint violations
        mercer_contrib = next((c for c in contributions if c.source_name == "mercer"), None)
        if (mercer_contrib and mercer_contrib.match_quality >= 0.6
                and mercer_contrib.p25 and mercer_contrib.p50 and mercer_contrib.p75):
            logger.info(
                f"Using Mercer data directly (quality={mercer_contrib.match_quality:.2f}, "
                f"P50={mercer_contrib.p50:,.0f})"
            )
            # Use Mercer percentiles directly as they're authoritative for this match
            percentiles = {
                "p10": mercer_contrib.p10 or mercer_contrib.p25,
                "p25": mercer_contrib.p25,
                "p50": mercer_contrib.p50,
                "p75": mercer_contrib.p75,
                "p90": mercer_contrib.p90 or mercer_contrib.p75,
            }
            # Only include Mercer in confidence calculation
            confidence = self._calculate_confidence_score([mercer_contrib])
            scenarios = self._generate_scenarios(percentiles)
            explanation = self._generate_explanation([mercer_contrib], confidence)

            return PricingResult(
                recommended_min=percentiles["p25"],
                recommended_max=percentiles["p75"],
                target_salary=percentiles["p50"],
                p10=percentiles["p10"],
                p25=percentiles["p25"],
                p50=percentiles["p50"],
                p75=percentiles["p75"],
                p90=percentiles["p90"],
                confidence_score=confidence,
                source_contributions=[mercer_contrib],  # Only Mercer
                alternative_scenarios=scenarios,
                explanation=explanation,
            )

        # Step 2b: Fallback to weighted aggregation if no strong Mercer match
        weighted_data_points = self._apply_weights_and_aggregate(contributions)

        # Check if all sources were filtered out due to low match quality
        if not weighted_data_points:
            logger.warning(
                "All data sources filtered out due to low match quality. "
                "Sources attempted: mercer, my_careers_future, glassdoor, internal_hris, applicants. "
                "All sources had match quality below threshold."
            )
            raise NoMarketDataError(
                job_title=request.job_title,
                sources_attempted=["mercer", "my_careers_future", "glassdoor", "internal_hris", "applicants"]
            )

        # Step 3: Calculate percentiles from aggregated data
        percentiles = self._calculate_percentiles(weighted_data_points)

        # Step 4: Calculate overall confidence score
        confidence = self._calculate_confidence_score(contributions)

        # Step 5: Generate alternative scenarios
        scenarios = self._generate_scenarios(percentiles)

        # Step 6: Generate explanation
        explanation = self._generate_explanation(contributions, confidence)

        result = PricingResult(
            recommended_min=percentiles["p25"],
            recommended_max=percentiles["p75"],
            target_salary=percentiles["p50"],
            p10=percentiles["p10"],
            p25=percentiles["p25"],
            p50=percentiles["p50"],
            p75=percentiles["p75"],
            p90=percentiles["p90"],
            confidence_score=confidence,
            source_contributions=contributions,
            alternative_scenarios=scenarios,
            explanation=explanation,
        )

        logger.info(f"Pricing calculated: ${result.target_salary:,.0f} (confidence: {confidence:.0f}%)")

        # NOTE: Result persistence is handled by SalaryRecommendationServiceV2._save_result()
        # to avoid duplicate save conflicts (unique constraint on request_id + version)
        # Removed: self._persist_result(request, result)

        return result

    def _gather_all_sources(
        self,
        request: JobPricingRequest,
        mercer_match: Optional[Dict] = None
    ) -> List[DataSourceContribution]:
        """
        Gather salary data from all 5 sources.

        Args:
            request: Job pricing request
            mercer_match: Optional Mercer job match with job_code and family info

        Returns:
            List of data source contributions
        """
        contributions = []

        # Source 1: Mercer IPE (40% weight)
        mercer_data = self._get_mercer_data(request, mercer_match)
        if mercer_data:
            contributions.append(mercer_data)

        # Source 2: MyCareersFuture (25% weight) - Uses job family from Mercer match
        mcf_data = self._get_mycareersfuture_data(request, mercer_match)
        if mcf_data:
            contributions.append(mcf_data)

        # Source 3: Glassdoor (15% weight) - Uses job family from Mercer match
        glassdoor_data = self._get_glassdoor_data(request, mercer_match)
        if glassdoor_data:
            contributions.append(glassdoor_data)

        # Source 4: Internal HRIS (15% weight)
        hris_data = self._get_internal_hris_data(request)
        if hris_data:
            contributions.append(hris_data)

        # Source 5: Applicants (5% weight)
        applicants_data = self._get_applicants_data(request)
        if applicants_data:
            contributions.append(applicants_data)

        logger.info(f"Gathered data from {len(contributions)}/5 sources")

        return contributions

    def _get_mercer_data(
        self,
        request: JobPricingRequest,
        mercer_match: Optional[Dict] = None
    ) -> Optional[DataSourceContribution]:
        """
        Get salary data from Mercer IPE.

        Uses vector similarity search to find matching jobs.

        Args:
            request: Job pricing request
            mercer_match: Optional pre-computed Mercer match (avoids re-matching)

        Returns:
            Mercer data contribution or None
        """
        logger.debug("Querying Mercer data...")

        try:
            # Import JobMatchingService here to avoid circular dependency
            from job_pricing.services.job_matching_service import JobMatchingService

            # Use pre-computed match if available, otherwise find match
            if not mercer_match:
                matching_service = JobMatchingService(self.session)
                mercer_match = matching_service.find_best_match(
                    job_title=request.job_title,
                    job_description=request.job_description,
                    use_llm_reasoning=False  # Disable LLM to work around OpenAI embedding non-determinism
                )

            if not mercer_match or not mercer_match.get("job_code"):
                logger.debug("No Mercer job match found")
                return None

            job_code = mercer_match["job_code"]
            # Support both LLM-enhanced (match_score) and embedding-only (similarity_score)
            match_score = mercer_match.get("match_score") or mercer_match.get("similarity_score", 0.0)

            logger.debug(f"Found Mercer match: {job_code} (score: {match_score:.2f})")

            # Query market data for this job code (Singapore data)
            market_data = self.session.query(MercerMarketData).filter(
                MercerMarketData.job_code == job_code,
                MercerMarketData.country_code == "SG",
                MercerMarketData.p50.isnot(None)
            ).first()

            if not market_data:
                logger.debug(f"No Singapore market data for job code: {job_code}")
                return None

            logger.info(f"Found Mercer market data for {job_code}")

            # Extract salary percentiles
            # Mercer data is already in percentiles, so we can use them directly
            data_points = []
            if market_data.p10:
                data_points.append(market_data.p10)
            if market_data.p25:
                data_points.append(market_data.p25)
            if market_data.p50:
                data_points.append(market_data.p50)
            if market_data.p75:
                data_points.append(market_data.p75)
            if market_data.p90:
                data_points.append(market_data.p90)

            if not data_points:
                logger.debug("No percentile data available")
                return None

            # Calculate recency (age of survey data)
            now = datetime.now(timezone.utc)
            if market_data.survey_date:
                survey_datetime = datetime.combine(market_data.survey_date, datetime.min.time(), tzinfo=timezone.utc)
                recency_days = (now - survey_datetime).days
            else:
                recency_days = 365  # Default to 1 year old

            return DataSourceContribution(
                source_name="mercer",
                weight=self.WEIGHTS["mercer"],
                sample_size=market_data.sample_size or 5,  # Default if not available
                data_points=data_points,
                p10=market_data.p10,
                p25=market_data.p25,
                p50=market_data.p50,
                p75=market_data.p75,
                p90=market_data.p90,
                recency_days=recency_days,
                match_quality=match_score,
            )

        except Exception as e:
            logger.error(f"Error querying Mercer data: {e}")
            return None

    def _get_mycareersfuture_data(
        self,
        request: JobPricingRequest,
        mercer_match: Optional[Dict] = None
    ) -> Optional[DataSourceContribution]:
        """
        Get salary data from MyCareersFuture scraped listings using job family filtering.

        Uses Mercer job family to find related roles for more accurate matching.

        Args:
            request: Job pricing request
            mercer_match: Optional Mercer match with job_code and family info

        Returns:
            MCF data contribution or None
        """
        logger.debug("Querying MyCareersFuture data...")

        try:
            # If we have a Mercer match, use job family to find related roles
            related_titles = []
            if mercer_match and mercer_match.get("job_code"):
                # Get the matched Mercer job to extract family
                mercer_job = self.session.query(MercerJobLibrary).filter(
                    MercerJobLibrary.job_code == mercer_match["job_code"]
                ).first()

                if mercer_job and mercer_job.family:
                    logger.debug(f"Using Mercer family '{mercer_job.family}' for MCF filtering")

                    # Get all job titles from the same Mercer family
                    family_jobs = self.session.query(MercerJobLibrary).filter(
                        MercerJobLibrary.family == mercer_job.family
                    ).all()

                    # Extract keywords from related job titles (remove parenthetical suffixes)
                    for job in family_jobs:
                        # Extract base title (e.g., "HR Business Partners" from "HR Business Partners - Director (M5)")
                        title = job.job_title.split(" - ")[0].strip()
                        related_titles.append(title)

                    logger.debug(f"Found {len(related_titles)} related job titles in {mercer_job.family} family")

            # Query scraped job listings from MCF
            listings = []
            match_quality = 0.5  # Default - will be updated based on matching strategy

            # Strategy 1: If we have family-based titles, match against those (highest quality)
            if related_titles:
                # Use OR condition to match any of the related titles
                title_conditions = [
                    func.similarity(ScrapedJobListing.job_title, title) > self.SIMILARITY_THRESHOLD_RELAXED
                    for title in related_titles[:self.QUERY_LIMIT_MERCER_FAMILY]
                ]

                try:
                    listings = self.session.query(ScrapedJobListing).filter(
                        ScrapedJobListing.source == "my_careers_future",
                        ScrapedJobListing.salary_min.isnot(None),
                        ScrapedJobListing.salary_max.isnot(None),
                        or_(*title_conditions)
                    ).limit(self.QUERY_LIMIT_EXTERNAL).all()

                    logger.info(f"Family-based matching found {len(listings)} MCF listings")
                    match_quality = 0.9  # High quality: matched by Mercer job family
                except Exception as e:
                    logger.warning(f"Family-based matching failed, trying alternative: {e}")
                    listings = []

            # Strategy 2: Alternative - fuzzy match on job title if no family match (medium quality)
            if not listings:
                try:
                    listings = self.session.query(ScrapedJobListing).filter(
                        ScrapedJobListing.source == "my_careers_future",
                        ScrapedJobListing.salary_min.isnot(None),
                        ScrapedJobListing.salary_max.isnot(None),
                    ).filter(
                        func.similarity(
                            ScrapedJobListing.job_title,
                            request.job_title
                        ) > self.SIMILARITY_THRESHOLD_RELAXED
                    ).limit(self.QUERY_LIMIT_EXTERNAL).all()
                    match_quality = 0.75  # Medium-high quality: fuzzy trigram match
                except Exception as e:
                    logger.warning(f"Trigram similarity not available, using basic LIKE match: {e}")
                    # Strategy 3: Basic LIKE match when trigram extension unavailable (lower quality)
                    listings = self.session.query(ScrapedJobListing).filter(
                        ScrapedJobListing.source == "my_careers_future",
                        ScrapedJobListing.salary_min.isnot(None),
                        ScrapedJobListing.salary_max.isnot(None),
                        ScrapedJobListing.job_title.ilike(f"%{request.job_title}%")
                    ).limit(self.QUERY_LIMIT_EXTERNAL).all()
                    match_quality = 0.6  # Lower quality: basic string match

            if not listings:
                logger.debug("No MCF listings found matching criteria")
                return None

            logger.info(f"Found {len(listings)} MCF listings total")

            # Extract salary midpoints and normalize to ANNUAL
            # MCF API provides salary_type (Monthly, Annual, Hourly, etc.)
            data_points = []
            for listing in listings:
                if listing.salary_min and listing.salary_max:
                    midpoint = (Decimal(listing.salary_min) + Decimal(listing.salary_max)) / 2

                    # Check salary_type to determine conversion factor
                    # MCF stores salary_type like "Monthly", "Annual", "Hourly"
                    salary_type = (listing.salary_type or "").lower()

                    if "month" in salary_type:
                        annual_salary = midpoint * 12  # Monthly to annual
                    elif "hour" in salary_type:
                        annual_salary = midpoint * 40 * 52  # Hourly to annual (40hr/wk * 52wk)
                    elif "annual" in salary_type or "year" in salary_type:
                        annual_salary = midpoint  # Already annual, no conversion
                    else:
                        # Default: assume monthly for MCF (Singapore standard)
                        # Log warning for transparency
                        logger.debug(f"Unknown salary_type '{listing.salary_type}' for MCF listing, assuming monthly")
                        annual_salary = midpoint * 12

                    data_points.append(annual_salary)

            if not data_points:
                return None

            # Calculate recency (average age) with timezone handling
            now = datetime.now(timezone.utc)
            valid_recency_values = []
            for listing in listings:
                if listing.scraped_at:
                    # Handle both timezone-aware and naive datetimes
                    if listing.scraped_at.tzinfo:
                        days = (now - listing.scraped_at).days
                    else:
                        days = (now.replace(tzinfo=None) - listing.scraped_at).days
                    valid_recency_values.append(days)
            recency_days = int(statistics.mean(valid_recency_values)) if valid_recency_values else self.DEFAULT_RECENCY_DAYS

            return DataSourceContribution(
                source_name="my_careers_future",
                weight=self.WEIGHTS["my_careers_future"],
                sample_size=len(data_points),
                data_points=data_points,
                recency_days=recency_days,
                match_quality=match_quality,  # Calculated based on matching strategy used
            )

        except Exception as e:
            logger.error(f"Error querying MCF data: {e}")
            return None

    def _get_glassdoor_data(
        self,
        request: JobPricingRequest,
        mercer_match: Optional[Dict] = None
    ) -> Optional[DataSourceContribution]:
        """
        Get salary data from Glassdoor scraped listings using job family filtering.

        Uses Mercer job family to find related roles for more accurate matching.
        Same approach as _get_mycareersfuture_data() for consistency.

        Args:
            request: Job pricing request
            mercer_match: Optional Mercer match with job_code and family info

        Returns:
            Glassdoor data contribution or None
        """
        logger.debug("Querying Glassdoor data...")

        try:
            # If we have a Mercer match, use job family to find related roles
            related_titles = []
            if mercer_match and mercer_match.get("job_code"):
                # Get the matched Mercer job to extract family
                mercer_job = self.session.query(MercerJobLibrary).filter(
                    MercerJobLibrary.job_code == mercer_match["job_code"]
                ).first()

                if mercer_job and mercer_job.family:
                    logger.debug(f"Using Mercer family '{mercer_job.family}' for Glassdoor filtering")

                    # Get all job titles from the same Mercer family
                    family_jobs = self.session.query(MercerJobLibrary).filter(
                        MercerJobLibrary.family == mercer_job.family
                    ).all()

                    # Extract keywords from related job titles
                    for job in family_jobs:
                        title = job.job_title.split(" - ")[0].strip()
                        related_titles.append(title)

                    logger.debug(f"Found {len(related_titles)} related job titles in {mercer_job.family} family")

            # Query scraped job listings from Glassdoor
            listings = []
            match_quality = 0.5  # Default

            # Strategy 1: Family-based matching (highest quality)
            if related_titles:
                title_conditions = [
                    func.similarity(ScrapedJobListing.job_title, title) > self.SIMILARITY_THRESHOLD_RELAXED
                    for title in related_titles[:self.QUERY_LIMIT_MERCER_FAMILY]
                ]

                try:
                    listings = self.session.query(ScrapedJobListing).filter(
                        ScrapedJobListing.source == "glassdoor",
                        ScrapedJobListing.salary_min.isnot(None),
                        ScrapedJobListing.salary_max.isnot(None),
                        or_(*title_conditions)
                    ).limit(self.QUERY_LIMIT_EXTERNAL).all()

                    logger.info(f"Family-based matching found {len(listings)} Glassdoor listings")
                    match_quality = 0.85  # High quality: matched by Mercer job family
                except Exception as e:
                    logger.warning(f"Family-based Glassdoor matching failed: {e}")
                    listings = []

            # Strategy 2: Fuzzy match on job title (fallback)
            if not listings:
                listings = self.session.query(ScrapedJobListing).filter(
                    ScrapedJobListing.source == "glassdoor",
                    ScrapedJobListing.salary_min.isnot(None),
                    ScrapedJobListing.salary_max.isnot(None),
                ).filter(
                    func.similarity(
                        ScrapedJobListing.job_title,
                        request.job_title
                    ) > self.SIMILARITY_THRESHOLD_RELAXED
                ).limit(self.QUERY_LIMIT_EXTERNAL).all()
                match_quality = 0.75  # Medium quality: fuzzy title match

            if not listings:
                return None

            # Extract salary midpoints and normalize to ANNUAL
            # Glassdoor typically displays annual salaries
            # salary_type field is "estimated" (data quality indicator), not period
            data_points = []
            for listing in listings:
                if listing.salary_min and listing.salary_max:
                    midpoint = (Decimal(listing.salary_min) + Decimal(listing.salary_max)) / 2

                    # Glassdoor Singapore shows annual salaries (typically $50K-$300K range)
                    # If salary looks like monthly (< $15K), convert to annual
                    # This heuristic catches edge cases where data might be monthly
                    if midpoint < 15000:
                        # Likely monthly - convert to annual
                        logger.debug(f"Glassdoor salary {midpoint} appears monthly, converting to annual")
                        annual_salary = midpoint * 12
                    else:
                        # Already annual
                        annual_salary = midpoint

                    data_points.append(annual_salary)

            if not data_points:
                return None

            # Calculate recency with timezone handling and None safety
            now = datetime.now(timezone.utc)
            valid_recency_values = []
            for listing in listings:
                if listing.scraped_at:
                    if listing.scraped_at.tzinfo:
                        days = (now - listing.scraped_at).days
                    else:
                        days = (now.replace(tzinfo=None) - listing.scraped_at).days
                    valid_recency_values.append(days)
            recency_days = int(statistics.mean(valid_recency_values)) if valid_recency_values else self.DEFAULT_RECENCY_DAYS

            return DataSourceContribution(
                source_name="glassdoor",
                weight=self.WEIGHTS["glassdoor"],
                sample_size=len(data_points),
                data_points=data_points,
                recency_days=recency_days,
                match_quality=match_quality,  # Calculated based on matching strategy
            )

        except Exception as e:
            logger.error(f"Error querying Glassdoor data: {e}")
            return None

    def _get_internal_hris_data(
        self,
        request: JobPricingRequest
    ) -> Optional[DataSourceContribution]:
        """
        Get salary data from internal HRIS.

        Args:
            request: Job pricing request

        Returns:
            HRIS data contribution or None
        """
        logger.debug("Querying internal HRIS data...")

        try:
            employees = self.session.query(InternalEmployee).filter(
                InternalEmployee.employment_status == "Active",
                InternalEmployee.current_salary.isnot(None),
            ).filter(
                func.similarity(
                    InternalEmployee.job_title,
                    request.job_title
                ) > self.SIMILARITY_THRESHOLD_STRICT
            ).limit(self.QUERY_LIMIT_INTERNAL).all()

            if not employees:
                return None

            data_points = [Decimal(emp.current_salary) for emp in employees]

            return DataSourceContribution(
                source_name="internal_hris",
                weight=self.WEIGHTS["internal_hris"],
                sample_size=len(data_points),
                data_points=data_points,
                recency_days=0,  # Internal data is always current
                match_quality=0.9,  # High quality - exact job titles
            )

        except Exception as e:
            logger.error(f"Error querying HRIS data: {e}")
            return None

    def _get_applicants_data(
        self,
        request: JobPricingRequest
    ) -> Optional[DataSourceContribution]:
        """
        Get salary expectations from applicant data.

        Args:
            request: Job pricing request

        Returns:
            Applicants data contribution or None
        """
        logger.debug("Querying applicants data...")

        try:
            # Query recent applicants (last 2 years)
            cutoff_date = datetime.now() - timedelta(days=730)

            applicants = self.session.query(Applicant).filter(
                Applicant.application_date >= cutoff_date,
                Applicant.expected_salary.isnot(None),
            ).filter(
                func.similarity(
                    Applicant.applied_job_title,
                    request.job_title
                ) > self.SIMILARITY_THRESHOLD_STRICT
            ).limit(self.QUERY_LIMIT_EXTERNAL).all()

            if not applicants:
                return None

            # Convert monthly to annual salaries (Applicant model stores monthly)
            data_points = [
                Decimal(app.expected_salary) * 12  # Monthly to annual
                for app in applicants
            ]

            # Calculate recency - application_date is Date type (not DateTime)
            # Need to use date.today() for comparison, not datetime.now()
            today = date.today()
            valid_recency_values = [
                (today - app.application_date).days
                for app in applicants
                if app.application_date is not None
            ]
            recency_days = int(statistics.mean(valid_recency_values)) if valid_recency_values else self.DEFAULT_RECENCY_DAYS

            return DataSourceContribution(
                source_name="applicants",
                weight=self.WEIGHTS["applicants"],
                sample_size=len(data_points),
                data_points=data_points,
                recency_days=recency_days,
                match_quality=0.7,
            )

        except Exception as e:
            logger.error(f"Error querying applicants data: {e}")
            return None

    def _apply_weights_and_aggregate(
        self,
        contributions: List[DataSourceContribution]
    ) -> List[Decimal]:
        """
        Apply weights to each source and aggregate all data points.

        Weighted sampling approach: each data point is repeated
        proportionally to its source weight AND match quality.
        This ensures high-quality matches (e.g., exact Mercer job matches)
        have more influence than low-quality matches (e.g., generic MCF listings).

        Args:
            contributions: List of data source contributions

        Returns:
            Aggregated weighted data points
        """
        weighted_points = []

        for contrib in contributions:
            # Skip sources with match quality below threshold
            # This prevents diluting results with unrelated job data
            if contrib.match_quality < self.MIN_MATCH_QUALITY_THRESHOLD:
                logger.info(
                    f"Excluding {contrib.source_name} due to low match quality "
                    f"({contrib.match_quality:.2f} < {self.MIN_MATCH_QUALITY_THRESHOLD})"
                )
                continue

            # Calculate repeat factor based on weight AND match quality
            # E.g., Mercer (40% weight, 85% match) = 0.4 * 0.85 * 100 = 34 repeats
            #       MCF (25% weight, 60% match) = 0.25 * 0.6 * 100 = 15 repeats
            # This ensures high-quality matches have more influence
            effective_weight = contrib.weight * contrib.match_quality
            repeat_factor = max(1, int(effective_weight * 100))  # At least 1 repeat

            logger.debug(
                f"Source {contrib.source_name}: weight={contrib.weight:.2f}, "
                f"quality={contrib.match_quality:.2f}, effective={effective_weight:.3f}, "
                f"repeats={repeat_factor}, points={len(contrib.data_points)}"
            )

            # Add each data point N times based on effective weight
            for point in contrib.data_points:
                for _ in range(repeat_factor):
                    weighted_points.append(point)

        logger.info(f"Aggregated {len(weighted_points)} weighted data points")

        return weighted_points

    def _calculate_percentiles(
        self,
        data_points: List[Decimal]
    ) -> Dict[str, Decimal]:
        """
        Calculate statistical percentiles from data points.

        Args:
            data_points: List of salary data points

        Returns:
            Dictionary with P10, P25, P50, P75, P90
        """
        if not data_points:
            raise ValueError("No data points available for percentile calculation")

        sorted_data = sorted(data_points)
        n = len(sorted_data)

        # Handle edge case: single data point
        # statistics.quantiles requires at least 2 data points
        if n == 1:
            single_value = sorted_data[0]
            logger.warning(f"Only 1 data point available ({single_value}), using same value for all percentiles")
            return {
                "p10": single_value,
                "p25": single_value,
                "p50": single_value,
                "p75": single_value,
                "p90": single_value,
            }

        # Handle edge case: 2-3 data points (quantiles needs at least n+1 for n-tile)
        if n < 4:
            logger.warning(f"Only {n} data points available, using linear interpolation")
            # Use median for p50, min for lower, max for upper
            median_val = Decimal(str(statistics.median(sorted_data)))
            return {
                "p10": sorted_data[0],
                "p25": sorted_data[0],
                "p50": median_val,
                "p75": sorted_data[-1],
                "p90": sorted_data[-1],
            }

        # Normal case: enough data points for proper percentile calculation
        percentiles = {
            "p10": Decimal(str(statistics.quantiles(sorted_data, n=10)[0])),
            "p25": Decimal(str(statistics.quantiles(sorted_data, n=4)[0])),
            "p50": Decimal(str(statistics.median(sorted_data))),
            "p75": Decimal(str(statistics.quantiles(sorted_data, n=4)[2])),
            "p90": Decimal(str(statistics.quantiles(sorted_data, n=10)[8])),
        }

        logger.debug(f"Calculated percentiles: {percentiles}")

        return percentiles

    def _calculate_confidence_score(
        self,
        contributions: List[DataSourceContribution]
    ) -> float:
        """
        Calculate overall confidence score (0-100).

        Based on:
        - Number of data sources (more is better, but high-quality Mercer alone is valuable)
        - Total sample size
        - Data recency
        - Match quality

        Args:
            contributions: List of data source contributions

        Returns:
            Confidence score (0-100)
        """
        if not contributions:
            return 0.0

        # Factor 1: Data source coverage (0-30 points)
        # High-quality Mercer alone gets 20 points, other sources add to it
        mercer_contrib = next((c for c in contributions if c.source_name == "mercer"), None)
        if mercer_contrib and mercer_contrib.match_quality >= 0.6 and mercer_contrib.p50:
            # High-quality Mercer with percentile data is authoritative
            source_coverage = 20 + min(10, (len(contributions) - 1) * 5)  # 20 for Mercer + 5 for each additional
        else:
            source_coverage = min(30, len(contributions) * 6)  # 6 points per source

        # Factor 2: Sample size (0-30 points)
        total_sample = sum(c.sample_size for c in contributions)
        if total_sample >= self.MIN_SAMPLE_SIZE_EXCELLENT:
            sample_score = 30
        elif total_sample >= self.MIN_SAMPLE_SIZE_GOOD:
            sample_score = 20
        elif total_sample >= self.MIN_SAMPLE_SIZE_FAIR:
            sample_score = 10
        else:
            sample_score = 5

        # Factor 3: Data recency (0-20 points)
        avg_recency = statistics.mean([
            c.recency_days for c in contributions if c.recency_days is not None
        ]) if any(c.recency_days for c in contributions) else 180

        if avg_recency <= self.MAX_DATA_AGE_EXCELLENT:
            recency_score = 20
        elif avg_recency <= self.MAX_DATA_AGE_GOOD:
            recency_score = 15
        elif avg_recency <= self.MAX_DATA_AGE_FAIR:
            recency_score = 10
        else:
            recency_score = 5

        # Factor 4: Match quality (0-20 points)
        avg_match = statistics.mean([c.match_quality for c in contributions])
        match_score = avg_match * 20

        total_score = source_coverage + sample_score + recency_score + match_score

        logger.info(f"Confidence breakdown: sources={source_coverage}, sample={sample_score}, "
                   f"recency={recency_score}, match={match_score} -> total={total_score}")

        return min(100.0, total_score)

    def _generate_scenarios(
        self,
        percentiles: Dict[str, Decimal]
    ) -> Dict[str, Dict[str, Decimal]]:
        """
        Generate alternative pricing scenarios.

        Args:
            percentiles: Calculated percentiles

        Returns:
            Dictionary of scenarios with min/max ranges and use cases.

        Note on P40/P60:
            The "market" scenario checks for "p40" and "p60" keys which are NOT
            currently calculated by _calculate_percentiles(). This is INTENTIONAL
            forward-compatible design.

            Current behavior: Falls back to interpolation (P25+P50)/2 and (P50+P75)/2
            Future enhancement: When P40/P60 are calculated, they will be used directly.

            This pattern is documented in:
            - COMPLETION_SUMMARY_2025-11-16.md: "Market (P40-P60)"
            - PROJECT_STATUS.md: "Market (P40-P60)"
            - dynamic_pricing_algorithm.md: Scenario generation

            DO NOT REMOVE the p40/p60 checks - they enable future enhancement
            without code changes.
        """
        return {
            "conservative": {
                "min": percentiles["p25"],
                "max": percentiles["p50"],
                "use_case": "Budget-conscious hiring, junior candidates"
            },
            "market": {
                # Forward-compatible: uses P40/P60 if available, else interpolates
                "min": percentiles["p40"] if "p40" in percentiles else (percentiles["p25"] + percentiles["p50"]) / 2,
                "max": percentiles["p60"] if "p60" in percentiles else (percentiles["p50"] + percentiles["p75"]) / 2,
                "use_case": "Standard market positioning"
            },
            "competitive": {
                "min": percentiles["p50"],
                "max": percentiles["p75"],
                "use_case": "Attract strong candidates, critical roles"
            },
            "premium": {
                "min": percentiles["p75"],
                "max": percentiles["p90"],
                "use_case": "Top talent acquisition, leadership roles"
            }
        }

    def _generate_explanation(
        self,
        contributions: List[DataSourceContribution],
        confidence: float
    ) -> str:
        """
        Generate human-readable explanation of pricing.

        Args:
            contributions: Data source contributions
            confidence: Confidence score

        Returns:
            Explanation string
        """
        sources = [c.source_name for c in contributions]
        total_sample = sum(c.sample_size for c in contributions)

        explanation = (
            f"This recommendation is based on {len(contributions)} data source(s): "
            f"{', '.join(sources)}. "
            f"Total sample size: {total_sample} data points. "
            f"Confidence level: {confidence:.0f}%."
        )

        return explanation

    # ❌ DELETED: _fallback_calculation() method
    # REASON: Violates ZERO TOLERANCE FOR MOCK DATA policy
    # All pricing MUST be based on real market data from actual sources
    # If no data available, raise NoMarketDataError instead

    def _persist_result(self, request: JobPricingRequest, result: PricingResult) -> None:
        """
        Persist pricing result to database for audit trail and historical analysis.

        Args:
            request: The job pricing request
            result: The calculated pricing result
        """
        try:
            # Determine confidence level (must match database constraint: 'High', 'Medium', 'Low')
            if result.confidence_score >= 75:
                confidence_level = 'High'
            elif result.confidence_score >= 50:
                confidence_level = 'Medium'
            else:
                confidence_level = 'Low'

            # Calculate total data points
            total_data_points = sum(c.sample_size for c in result.source_contributions)

            # Convert alternative_scenarios Decimals to floats for JSON storage
            def decimal_to_float(obj):
                """Convert Decimals to floats for JSON serialization."""
                if isinstance(obj, dict):
                    return {k: decimal_to_float(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [decimal_to_float(item) for item in obj]
                elif isinstance(obj, Decimal):
                    return float(obj)
                return obj

            scenarios_json = decimal_to_float(result.alternative_scenarios)

            # Create database record
            db_result = JobPricingResult(
                request_id=request.id,
                currency='SGD',
                period='annual',
                recommended_min=result.recommended_min,
                recommended_max=result.recommended_max,
                target_salary=result.target_salary,
                p10=result.p10,
                p25=result.p25,
                p50=result.p50,
                p75=result.p75,
                p90=result.p90,
                confidence_score=result.confidence_score,
                confidence_level=confidence_level,
                summary_text=result.explanation,
                alternative_scenarios=scenarios_json,
                total_data_points=total_data_points,
                data_sources_used=len(result.source_contributions),
                data_consistency_score=result.confidence_score  # Use confidence as proxy for consistency
            )

            self.session.add(db_result)
            self.session.flush()  # Get ID without full commit

            # Save data source contributions
            for contrib in result.source_contributions:
                # Calculate recency_weight safely (handle None recency_days)
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
                    p90=contrib.p90
                )
                self.session.add(db_contrib)

            logger.info(f"Persisted result (ID: {db_result.id}) for request {request.id}")

        except Exception as e:
            logger.error(f"Failed to persist result: {e}", exc_info=True)
            # Don't fail the whole request if persistence fails
