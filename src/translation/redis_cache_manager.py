"""
Redis Translation Cache Manager
================================

Production-ready caching layer for translations:
- 7-day TTL for cached translations
- Hash-based cache keys for efficient lookups
- Cache hit rate tracking
- Target: >80% cache hit rate

No mock data - real Redis integration using config from .env.production
"""

import logging
import hashlib
import json
from typing import Optional, Dict, Any
from datetime import timedelta
import redis
from src.core.config import config

logger = logging.getLogger(__name__)


class TranslationCacheManager:
    """
    Redis-based translation cache manager

    Cache key format: translation:{source_lang}:{target_lang}:{text_hash}
    TTL: 7 days (604800 seconds)
    """

    CACHE_PREFIX = "translation"
    DEFAULT_TTL = 7 * 24 * 60 * 60  # 7 days in seconds

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        Initialize cache manager

        Args:
            redis_client: Optional Redis client (creates one if not provided)
        """
        if redis_client:
            self.redis_client = redis_client
        else:
            # Create Redis client from config
            self.redis_client = redis.from_url(
                config.REDIS_URL,
                max_connections=config.REDIS_MAX_CONNECTIONS,
                socket_timeout=config.REDIS_SOCKET_TIMEOUT,
                socket_connect_timeout=5,
                decode_responses=True  # Auto-decode bytes to strings
            )

        self._cache_hits = 0
        self._cache_misses = 0

        # Test connection
        try:
            self.redis_client.ping()
            logger.info("✅ Redis translation cache connected")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            raise

    def _generate_cache_key(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        context: Optional[str] = None
    ) -> str:
        """
        Generate cache key for translation

        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            context: Optional context (e.g., "technical", "product")

        Returns:
            Cache key string
        """
        # Create hash of text for efficient storage
        text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]

        # Include context in key if provided
        if context:
            return f"{self.CACHE_PREFIX}:{source_lang}:{target_lang}:{context}:{text_hash}"
        else:
            return f"{self.CACHE_PREFIX}:{source_lang}:{target_lang}:{text_hash}"

    def get_translation(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        context: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached translation

        Args:
            text: Original text
            source_lang: Source language code
            target_lang: Target language code
            context: Optional context

        Returns:
            Cached translation data or None if not found
        """
        cache_key = self._generate_cache_key(text, source_lang, target_lang, context)

        try:
            cached_data = self.redis_client.get(cache_key)

            if cached_data:
                self._cache_hits += 1
                logger.debug(f"Cache HIT: {cache_key[:50]}...")
                return json.loads(cached_data)
            else:
                self._cache_misses += 1
                logger.debug(f"Cache MISS: {cache_key[:50]}...")
                return None

        except Exception as e:
            logger.error(f"Cache get failed: {e}")
            self._cache_misses += 1
            return None

    def set_translation(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        translation_data: Dict[str, Any],
        context: Optional[str] = None,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache translation result

        Args:
            text: Original text
            source_lang: Source language code
            target_lang: Target language code
            translation_data: Translation result to cache
            context: Optional context
            ttl: Optional TTL in seconds (default: 7 days)

        Returns:
            True if cached successfully
        """
        cache_key = self._generate_cache_key(text, source_lang, target_lang, context)
        ttl = ttl or self.DEFAULT_TTL

        try:
            # Store as JSON with TTL
            self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(translation_data, ensure_ascii=False)
            )
            logger.debug(f"Cached translation: {cache_key[:50]}... (TTL: {ttl}s)")
            return True

        except Exception as e:
            logger.error(f"Cache set failed: {e}")
            return False

    def invalidate_translation(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        context: Optional[str] = None
    ) -> bool:
        """
        Invalidate cached translation

        Args:
            text: Original text
            source_lang: Source language code
            target_lang: Target language code
            context: Optional context

        Returns:
            True if invalidated successfully
        """
        cache_key = self._generate_cache_key(text, source_lang, target_lang, context)

        try:
            deleted = self.redis_client.delete(cache_key)
            if deleted:
                logger.debug(f"Invalidated cache: {cache_key[:50]}...")
                return True
            return False

        except Exception as e:
            logger.error(f"Cache invalidation failed: {e}")
            return False

    def clear_all_translations(self) -> int:
        """
        Clear all translation caches

        Returns:
            Number of keys deleted
        """
        try:
            # Find all translation cache keys
            pattern = f"{self.CACHE_PREFIX}:*"
            keys = list(self.redis_client.scan_iter(match=pattern, count=100))

            if not keys:
                logger.info("No translation cache keys to clear")
                return 0

            # Delete in batches
            deleted = self.redis_client.delete(*keys)
            logger.info(f"Cleared {deleted} translation cache entries")
            return deleted

        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return 0

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache performance statistics

        Returns:
            Dictionary with cache statistics
        """
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total_requests * 100) if total_requests > 0 else 0.0

        try:
            # Count translation cache keys
            pattern = f"{self.CACHE_PREFIX}:*"
            cache_size = sum(1 for _ in self.redis_client.scan_iter(match=pattern, count=100))
        except Exception as e:
            logger.error(f"Failed to get cache size: {e}")
            cache_size = -1

        return {
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'total_requests': total_requests,
            'hit_rate_percent': round(hit_rate, 2),
            'cache_size': cache_size,
            'target_hit_rate': 80.0,
            'performance_status': 'excellent' if hit_rate >= 80 else ('good' if hit_rate >= 60 else 'needs_improvement')
        }

    def reset_stats(self):
        """Reset cache statistics"""
        self._cache_hits = 0
        self._cache_misses = 0
        logger.info("Cache statistics reset")

    def health_check(self) -> bool:
        """
        Check if Redis cache is healthy

        Returns:
            True if healthy
        """
        try:
            return self.redis_client.ping()
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return False

    def close(self):
        """Close Redis connection"""
        try:
            self.redis_client.close()
            logger.info("Redis translation cache closed")
        except Exception as e:
            logger.error(f"Failed to close cache: {e}")


# Global cache instance (singleton pattern)
_cache_instance = None


def get_translation_cache() -> TranslationCacheManager:
    """Get global translation cache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = TranslationCacheManager()
    return _cache_instance


def close_translation_cache():
    """Close global translation cache"""
    global _cache_instance
    if _cache_instance:
        _cache_instance.close()
        _cache_instance = None
