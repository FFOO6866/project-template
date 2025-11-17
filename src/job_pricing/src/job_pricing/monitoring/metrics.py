"""
Monitoring and Metrics for Job Pricing Engine

Provides real-time performance monitoring, error tracking, and business metrics.
"""

import time
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict
from threading import Lock

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Collects and aggregates metrics for monitoring system health and performance.

    Tracks:
    - Request latencies (p50, p95, p99)
    - Error rates by type
    - Data source contribution rates
    - Cache hit rates
    - API call counts
    """

    def __init__(self):
        self._lock = Lock()

        # Latency tracking (in milliseconds)
        self.latencies = []
        self.max_latency_samples = 10000

        # Error tracking
        self.errors = defaultdict(int)  # error_type -> count
        self.total_requests = 0
        self.failed_requests = 0

        # Data source metrics
        self.source_usage = defaultdict(int)  # source_name -> count
        self.source_contribution_weights = defaultdict(list)  # source_name -> [weights]

        # Mercer-specific metrics
        self.mercer_matches = 0
        self.mercer_no_match = 0
        self.mercer_similarity_scores = []

        # Cache metrics
        self.cache_hits = 0
        self.cache_misses = 0

        # API call tracking
        self.openai_api_calls = 0
        self.openai_api_errors = 0

        # Start time
        self.start_time = datetime.now()

    def record_request_latency(self, latency_ms: float):
        """Record request latency in milliseconds."""
        with self._lock:
            self.total_requests += 1
            self.latencies.append(latency_ms)

            # Keep only recent samples
            if len(self.latencies) > self.max_latency_samples:
                self.latencies = self.latencies[-self.max_latency_samples:]

    def record_error(self, error_type: str):
        """Record an error occurrence."""
        with self._lock:
            self.errors[error_type] += 1
            self.failed_requests += 1

    def record_source_usage(self, source_name: str, weight: float):
        """Record data source usage and contribution weight."""
        with self._lock:
            self.source_usage[source_name] += 1
            self.source_contribution_weights[source_name].append(weight)

    def record_mercer_match(self, matched: bool, similarity_score: Optional[float] = None):
        """Record Mercer matching result."""
        with self._lock:
            if matched:
                self.mercer_matches += 1
                if similarity_score is not None:
                    self.mercer_similarity_scores.append(similarity_score)
            else:
                self.mercer_no_match += 1

    def record_cache_access(self, hit: bool):
        """Record cache hit or miss."""
        with self._lock:
            if hit:
                self.cache_hits += 1
            else:
                self.cache_misses += 1

    def record_openai_call(self, success: bool = True):
        """Record OpenAI API call."""
        with self._lock:
            self.openai_api_calls += 1
            if not success:
                self.openai_api_errors += 1

    def get_percentile_latency(self, percentile: int) -> Optional[float]:
        """Get percentile latency (p50, p95, p99)."""
        with self._lock:
            if not self.latencies:
                return None

            sorted_latencies = sorted(self.latencies)
            index = int(len(sorted_latencies) * (percentile / 100.0))
            return sorted_latencies[min(index, len(sorted_latencies) - 1)]

    def get_error_rate(self) -> float:
        """Get overall error rate (0.0 to 1.0)."""
        with self._lock:
            if self.total_requests == 0:
                return 0.0
            return self.failed_requests / self.total_requests

    def get_cache_hit_rate(self) -> float:
        """Get cache hit rate (0.0 to 1.0)."""
        with self._lock:
            total = self.cache_hits + self.cache_misses
            if total == 0:
                return 0.0
            return self.cache_hits / total

    def get_mercer_match_rate(self) -> float:
        """Get Mercer match success rate (0.0 to 1.0)."""
        with self._lock:
            total = self.mercer_matches + self.mercer_no_match
            if total == 0:
                return 0.0
            return self.mercer_matches / total

    def get_average_mercer_similarity(self) -> Optional[float]:
        """Get average Mercer similarity score."""
        with self._lock:
            if not self.mercer_similarity_scores:
                return None
            return sum(self.mercer_similarity_scores) / len(self.mercer_similarity_scores)

    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary."""
        uptime = datetime.now() - self.start_time

        with self._lock:
            return {
                "uptime_seconds": uptime.total_seconds(),
                "total_requests": self.total_requests,
                "failed_requests": self.failed_requests,
                "error_rate": self.get_error_rate(),
                "latency": {
                    "p50_ms": self.get_percentile_latency(50),
                    "p95_ms": self.get_percentile_latency(95),
                    "p99_ms": self.get_percentile_latency(99),
                    "samples": len(self.latencies)
                },
                "errors_by_type": dict(self.errors),
                "data_sources": {
                    "usage_count": dict(self.source_usage),
                    "mercer_match_rate": self.get_mercer_match_rate(),
                    "mercer_avg_similarity": self.get_average_mercer_similarity()
                },
                "cache": {
                    "hits": self.cache_hits,
                    "misses": self.cache_misses,
                    "hit_rate": self.get_cache_hit_rate()
                },
                "openai": {
                    "total_calls": self.openai_api_calls,
                    "errors": self.openai_api_errors,
                    "error_rate": self.openai_api_errors / max(self.openai_api_calls, 1)
                }
            }

    def log_summary(self):
        """Log metrics summary at INFO level."""
        summary = self.get_summary()

        logger.info("=" * 80)
        logger.info("METRICS SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Uptime: {summary['uptime_seconds']:.0f}s")
        logger.info(f"Total Requests: {summary['total_requests']}")
        logger.info(f"Error Rate: {summary['error_rate']:.1%}")
        logger.info(f"")
        logger.info(f"Latency:")
        logger.info(f"  P50: {summary['latency']['p50_ms']:.0f}ms")
        logger.info(f"  P95: {summary['latency']['p95_ms']:.0f}ms")
        logger.info(f"  P99: {summary['latency']['p99_ms']:.0f}ms")
        logger.info(f"")
        logger.info(f"Mercer:")
        logger.info(f"  Match Rate: {summary['data_sources']['mercer_match_rate']:.1%}")
        logger.info(f"  Avg Similarity: {summary['data_sources']['mercer_avg_similarity']:.1%}" if summary['data_sources']['mercer_avg_similarity'] else "  Avg Similarity: N/A")
        logger.info(f"")
        logger.info(f"Cache:")
        logger.info(f"  Hit Rate: {summary['cache']['hit_rate']:.1%}")
        logger.info(f"  Hits: {summary['cache']['hits']}, Misses: {summary['cache']['misses']}")
        logger.info(f"")
        logger.info(f"OpenAI:")
        logger.info(f"  Calls: {summary['openai']['total_calls']}")
        logger.info(f"  Errors: {summary['openai']['errors']} ({summary['openai']['error_rate']:.1%})")
        logger.info("=" * 80)


# Global metrics collector instance
_metrics = MetricsCollector()


def get_metrics() -> MetricsCollector:
    """Get the global metrics collector instance."""
    return _metrics


class RequestTimer:
    """Context manager for timing requests."""

    def __init__(self, metrics: MetricsCollector):
        self.metrics = metrics
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            latency_ms = (time.time() - self.start_time) * 1000
            self.metrics.record_request_latency(latency_ms)

            if exc_type is not None:
                # Record error
                error_type = exc_type.__name__ if exc_type else "UnknownError"
                self.metrics.record_error(error_type)

        return False  # Don't suppress exceptions
