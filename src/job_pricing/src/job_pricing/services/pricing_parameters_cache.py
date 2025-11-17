"""
Pricing Parameters Cache Service

Redis-backed caching for pricing parameters to avoid repeated database queries.
Implements cache warming, invalidation, and automatic expiration.
"""

import json
import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from functools import wraps

import redis
from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..repositories.pricing_parameters_repository import (
    SalaryBandRepository,
    IndustryAdjustmentRepository,
    CompanySizeFactorRepository,
    SkillPremiumRepository,
)

logger = logging.getLogger(__name__)
settings = get_settings()


class PricingParametersCache:
    """
    Redis cache for pricing parameters.

    Caches database-driven pricing parameters to reduce database load.
    Implements automatic cache warming on startup and invalidation on updates.
    """

    # Cache key prefixes
    KEY_PREFIX = "pricing_params"
    KEY_SALARY_BAND = f"{KEY_PREFIX}:salary_band"
    KEY_INDUSTRY_ADJ = f"{KEY_PREFIX}:industry_adj"
    KEY_COMPANY_SIZE = f"{KEY_PREFIX}:company_size"
    KEY_SKILL_PREMIUM = f"{KEY_PREFIX}:skill_premium"
    KEY_ALL_SALARY_BANDS = f"{KEY_PREFIX}:all_salary_bands"
    KEY_ALL_INDUSTRY_ADJ = f"{KEY_PREFIX}:all_industry_adj"
    KEY_ALL_COMPANY_SIZE = f"{KEY_PREFIX}:all_company_size"
    KEY_ALL_SKILL_PREMIUMS = f"{KEY_PREFIX}:all_skill_premiums"

    # Cache TTL (Time To Live) in seconds
    CACHE_TTL = settings.CACHE_TTL_MEDIUM  # Default: 1800 seconds (30 minutes)

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        Initialize pricing parameters cache.

        Args:
            redis_client: Redis client instance (creates new if not provided)
        """
        if redis_client:
            self.redis = redis_client
        else:
            # Parse Redis URL from settings
            self.redis = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                encoding="utf-8"
            )

    # -------------------------------------------------------------------------
    # Salary Bands
    # -------------------------------------------------------------------------

    def get_salary_band(
        self,
        experience_level: str,
        session: Session,
        as_of_date: Optional[date] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get salary band from cache or database.

        Args:
            experience_level: Experience level
            session: Database session (for cache miss)
            as_of_date: Date to check active status

        Returns:
            Salary band dictionary or None
        """
        cache_key = f"{self.KEY_SALARY_BAND}:{experience_level}"

        # Try cache first
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached

        # Cache miss - query database
        repo = SalaryBandRepository(session)
        band = repo.get_by_experience_level(experience_level, as_of_date)

        if band:
            band_dict = {
                'experience_level': band.experience_level,
                'min_years': band.min_years,
                'max_years': band.max_years,
                'salary_min_sgd': float(band.salary_min_sgd),
                'salary_max_sgd': float(band.salary_max_sgd),
                'currency': band.currency,
            }
            self._set_in_cache(cache_key, band_dict, self.CACHE_TTL)
            return band_dict

        return None

    def get_all_salary_bands(self, session: Session) -> List[Dict[str, Any]]:
        """
        Get all active salary bands from cache or database.

        Args:
            session: Database session (for cache miss)

        Returns:
            List of salary band dictionaries
        """
        cache_key = self.KEY_ALL_SALARY_BANDS

        # Try cache first
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached

        # Cache miss - query database
        repo = SalaryBandRepository(session)
        bands = repo.get_active_bands()

        bands_list = [
            {
                'experience_level': b.experience_level,
                'min_years': b.min_years,
                'max_years': b.max_years,
                'salary_min_sgd': float(b.salary_min_sgd),
                'salary_max_sgd': float(b.salary_max_sgd),
                'currency': b.currency,
            }
            for b in bands
        ]

        self._set_in_cache(cache_key, bands_list, self.CACHE_TTL)
        return bands_list

    # -------------------------------------------------------------------------
    # Industry Adjustments
    # -------------------------------------------------------------------------

    def get_industry_adjustment(
        self,
        industry_name: str,
        session: Session,
        as_of_date: Optional[date] = None
    ) -> Decimal:
        """
        Get industry adjustment factor from cache or database.

        Args:
            industry_name: Industry name
            session: Database session (for cache miss)
            as_of_date: Date to check active status

        Returns:
            Adjustment factor (Decimal)
        """
        cache_key = f"{self.KEY_INDUSTRY_ADJ}:{industry_name}"

        # Try cache first
        cached = self._get_from_cache(cache_key)
        if cached:
            return Decimal(str(cached))

        # Cache miss - query database
        repo = IndustryAdjustmentRepository(session)
        factor = repo.get_adjustment_factor(industry_name, as_of_date)

        self._set_in_cache(cache_key, float(factor), self.CACHE_TTL)
        return factor

    # -------------------------------------------------------------------------
    # Company Size Factors
    # -------------------------------------------------------------------------

    def get_company_size_factor(
        self,
        size_category: str,
        session: Session,
        as_of_date: Optional[date] = None
    ) -> Decimal:
        """
        Get company size adjustment factor from cache or database.

        Args:
            size_category: Size category
            session: Database session (for cache miss)
            as_of_date: Date to check active status

        Returns:
            Adjustment factor (Decimal)
        """
        cache_key = f"{self.KEY_COMPANY_SIZE}:{size_category}"

        # Try cache first
        cached = self._get_from_cache(cache_key)
        if cached:
            return Decimal(str(cached))

        # Cache miss - query database
        repo = CompanySizeFactorRepository(session)
        factor = repo.get_adjustment_factor(size_category, as_of_date)

        self._set_in_cache(cache_key, float(factor), self.CACHE_TTL)
        return factor

    # -------------------------------------------------------------------------
    # Skill Premiums
    # -------------------------------------------------------------------------

    def get_skill_premiums(
        self,
        skill_names: List[str],
        session: Session,
        as_of_date: Optional[date] = None
    ) -> Dict[str, Decimal]:
        """
        Get skill premiums from cache or database.

        Args:
            skill_names: List of skill names
            session: Database session (for cache miss)
            as_of_date: Date to check active status

        Returns:
            Dictionary mapping skill_name -> premium_percentage
        """
        # Normalize skill names to lowercase
        skill_names_lower = [s.lower() for s in skill_names]

        # Try to get each skill from cache
        premiums = {}
        missing_skills = []

        for skill in skill_names_lower:
            cache_key = f"{self.KEY_SKILL_PREMIUM}:{skill}"
            cached = self._get_from_cache(cache_key)

            if cached is not None:
                premiums[skill] = Decimal(str(cached))
            else:
                missing_skills.append(skill)

        # If all skills found in cache, return
        if not missing_skills:
            return premiums

        # Cache miss - query database for missing skills
        repo = SkillPremiumRepository(session)
        db_premiums = repo.get_premiums_for_skills(missing_skills, as_of_date)

        # Cache the database results
        for skill, premium in db_premiums.items():
            cache_key = f"{self.KEY_SKILL_PREMIUM}:{skill}"
            self._set_in_cache(cache_key, float(premium), self.CACHE_TTL)
            premiums[skill] = premium

        return premiums

    def calculate_total_skill_premium(
        self,
        skill_names: List[str],
        session: Session,
        max_premium: Decimal = Decimal('0.50'),
        as_of_date: Optional[date] = None
    ) -> Decimal:
        """
        Calculate total skill premium (capped at max_premium).

        Args:
            skill_names: List of skill names
            session: Database session (for cache miss)
            max_premium: Maximum total premium (default 50%)
            as_of_date: Date to check active status

        Returns:
            Total premium percentage
        """
        premiums = self.get_skill_premiums(skill_names, session, as_of_date)
        total = sum(premiums.values())
        return min(total, max_premium)

    # -------------------------------------------------------------------------
    # Cache Management
    # -------------------------------------------------------------------------

    def invalidate_all(self):
        """Invalidate all pricing parameter caches."""
        pattern = f"{self.KEY_PREFIX}:*"
        keys = self.redis.keys(pattern)

        if keys:
            self.redis.delete(*keys)
            logger.info(f"Invalidated {len(keys)} pricing parameter cache keys")
        else:
            logger.info("No pricing parameter cache keys to invalidate")

    def invalidate_salary_bands(self):
        """Invalidate salary band caches."""
        pattern = f"{self.KEY_SALARY_BAND}:*"
        keys = self.redis.keys(pattern)
        keys.append(self.KEY_ALL_SALARY_BANDS)

        if keys:
            self.redis.delete(*keys)
            logger.info(f"Invalidated {len(keys)} salary band cache keys")

    def invalidate_industry_adjustments(self):
        """Invalidate industry adjustment caches."""
        pattern = f"{self.KEY_INDUSTRY_ADJ}:*"
        keys = self.redis.keys(pattern)
        keys.append(self.KEY_ALL_INDUSTRY_ADJ)

        if keys:
            self.redis.delete(*keys)
            logger.info(f"Invalidated {len(keys)} industry adjustment cache keys")

    def invalidate_company_size_factors(self):
        """Invalidate company size factor caches."""
        pattern = f"{self.KEY_COMPANY_SIZE}:*"
        keys = self.redis.keys(pattern)
        keys.append(self.KEY_ALL_COMPANY_SIZE)

        if keys:
            self.redis.delete(*keys)
            logger.info(f"Invalidated {len(keys)} company size factor cache keys")

    def invalidate_skill_premiums(self):
        """Invalidate skill premium caches."""
        pattern = f"{self.KEY_SKILL_PREMIUM}:*"
        keys = self.redis.keys(pattern)
        keys.append(self.KEY_ALL_SKILL_PREMIUMS)

        if keys:
            self.redis.delete(*keys)
            logger.info(f"Invalidated {len(keys)} skill premium cache keys")

    def warm_cache(self, session: Session):
        """
        Warm cache by loading all active pricing parameters.

        Args:
            session: Database session
        """
        logger.info("Warming pricing parameters cache...")

        # Warm salary bands
        self.get_all_salary_bands(session)

        # Warm industry adjustments
        repo_industry = IndustryAdjustmentRepository(session)
        industries = repo_industry.get_active_adjustments()
        for industry in industries:
            cache_key = f"{self.KEY_INDUSTRY_ADJ}:{industry.industry_name}"
            self._set_in_cache(cache_key, float(industry.adjustment_factor), self.CACHE_TTL)

        # Warm company size factors
        repo_size = CompanySizeFactorRepository(session)
        sizes = repo_size.get_active_factors()
        for size in sizes:
            cache_key = f"{self.KEY_COMPANY_SIZE}:{size.size_category}"
            self._set_in_cache(cache_key, float(size.adjustment_factor), self.CACHE_TTL)

        # Warm skill premiums (top 100 most common)
        repo_skills = SkillPremiumRepository(session)
        skills = repo_skills.get_active_premiums()[:100]  # Limit to top 100
        for skill in skills:
            cache_key = f"{self.KEY_SKILL_PREMIUM}:{skill.skill_name}"
            self._set_in_cache(cache_key, float(skill.premium_percentage), self.CACHE_TTL)

        logger.info("Cache warming complete")

    # -------------------------------------------------------------------------
    # Private Helper Methods
    # -------------------------------------------------------------------------

    def _get_from_cache(self, key: str) -> Any:
        """
        Get value from Redis cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        try:
            value = self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning(f"Cache read error for key '{key}': {e}")
            return None

    def _set_in_cache(self, key: str, value: Any, ttl: int):
        """
        Set value in Redis cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        try:
            self.redis.setex(key, ttl, json.dumps(value))
        except Exception as e:
            logger.warning(f"Cache write error for key '{key}': {e}")

    def health_check(self) -> bool:
        """
        Check if Redis cache is healthy.

        Returns:
            True if cache is accessible, False otherwise
        """
        try:
            self.redis.ping()
            return True
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return False


# Global cache instance
_cache_instance: Optional[PricingParametersCache] = None


def get_pricing_cache() -> PricingParametersCache:
    """
    Get global pricing parameters cache instance.

    Returns:
        PricingParametersCache instance
    """
    global _cache_instance

    if _cache_instance is None:
        _cache_instance = PricingParametersCache()

    return _cache_instance
