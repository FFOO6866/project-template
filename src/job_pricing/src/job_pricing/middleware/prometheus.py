"""
Prometheus Monitoring Middleware

Exposes application metrics for Prometheus scraping.
"""

import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

logger = logging.getLogger(__name__)


# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

REQUEST_IN_PROGRESS = Gauge(
    'http_requests_in_progress',
    'HTTP requests currently in progress',
    ['method', 'endpoint']
)

DB_CONNECTIONS = Gauge(
    'db_connections_active',
    'Active database connections'
)

CELERY_TASKS = Counter(
    'celery_tasks_total',
    'Total Celery tasks executed',
    ['task_name', 'status']
)

CELERY_TASK_DURATION = Histogram(
    'celery_task_duration_seconds',
    'Celery task duration in seconds',
    ['task_name']
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Middleware to collect and expose Prometheus metrics.

    Collects:
    - Request count by method, endpoint, status code
    - Request duration by method, endpoint
    - Requests in progress by method, endpoint
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and collect metrics.

        Args:
            request: Incoming request
            call_next: Next middleware in chain

        Returns:
            Response
        """
        # Skip metrics collection for /metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)

        method = request.method
        endpoint = request.url.path

        # Track request in progress
        REQUEST_IN_PROGRESS.labels(method=method, endpoint=endpoint).inc()

        # Start timer
        start_time = time.time()

        try:
            # Process request
            response = await call_next(request)

            # Record metrics
            status_code = response.status_code
            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).inc()

            duration = time.time() - start_time
            REQUEST_DURATION.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)

            return response

        except Exception as e:
            # Record error
            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status_code=500
            ).inc()

            duration = time.time() - start_time
            REQUEST_DURATION.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)

            raise

        finally:
            # Decrement in-progress counter
            REQUEST_IN_PROGRESS.labels(method=method, endpoint=endpoint).dec()


async def metrics_endpoint(request: Request) -> Response:
    """
    Prometheus metrics endpoint.

    Returns:
        Prometheus metrics in text format
    """
    metrics = generate_latest()
    return Response(
        content=metrics,
        media_type=CONTENT_TYPE_LATEST
    )
