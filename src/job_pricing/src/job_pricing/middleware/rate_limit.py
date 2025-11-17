"""
Per-User Rate Limiting Middleware

Implements rate limiting based on authenticated user ID rather than IP address.
"""

import logging
from typing import Optional
from datetime import datetime, timedelta

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import redis

from job_pricing.core.config import get_settings
from job_pricing.models.auth import User, UserRole
from job_pricing.utils.auth import decode_token

logger = logging.getLogger(__name__)
settings = get_settings()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Per-user rate limiting middleware.

    Rate limits are based on user ID from JWT token, falling back to IP address
    for unauthenticated requests.

    Rate limits by user role:
    - ADMIN: No limit (bypass)
    - HR_MANAGER: 1000 requests/hour
    - HR_ANALYST: 500 requests/hour
    - VIEWER: 100 requests/hour
    - Unauthenticated: 50 requests/hour (by IP)
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

        # Rate limits by role (requests per hour)
        self.rate_limits = {
            UserRole.ADMIN.value: None,  # No limit for admins
            UserRole.HR_MANAGER.value: settings.RATE_LIMIT_STANDARD_TIER,  # 1000/hour
            UserRole.HR_ANALYST.value: 500,  # 500/hour
            UserRole.VIEWER.value: settings.RATE_LIMIT_FREE_TIER,  # 100/hour
            "unauthenticated": 50,  # 50/hour for unauthenticated
        }

    async def dispatch(self, request: Request, call_next):
        """
        Process request and apply rate limiting.

        Args:
            request: Incoming request
            call_next: Next middleware in chain

        Returns:
            Response

        Raises:
            HTTPException: If rate limit exceeded
        """
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/ready", "/docs", "/openapi.json"]:
            return await call_next(request)

        # Get user info from token
        user_id, user_role = self._get_user_info(request)

        # Get rate limit for user role
        rate_limit = self.rate_limits.get(user_role, self.rate_limits["unauthenticated"])

        # Admin users bypass rate limiting
        if rate_limit is None:
            response = await call_next(request)
            return response

        # Check rate limit
        key = f"rate_limit:{user_id if user_id else request.client.host}:{user_role}"
        current_count = self._increment_request_count(key)

        # Add rate limit headers
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, rate_limit - current_count))
        response.headers["X-RateLimit-Reset"] = str(self._get_reset_time())

        # Check if limit exceeded
        if current_count > rate_limit:
            logger.warning(
                f"Rate limit exceeded for user_id={user_id}, role={user_role}, "
                f"count={current_count}, limit={rate_limit}"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "limit": rate_limit,
                    "reset_at": self._get_reset_time(),
                },
                headers={
                    "Retry-After": str(self._get_retry_after_seconds()),
                    "X-RateLimit-Limit": str(rate_limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(self._get_reset_time()),
                }
            )

        return response

    def _get_user_info(self, request: Request) -> tuple[Optional[int], str]:
        """
        Extract user ID and role from JWT token.

        Args:
            request: Incoming request

        Returns:
            Tuple of (user_id, user_role)
        """
        try:
            # Get Authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return None, "unauthenticated"

            # Extract token
            token = auth_header.split(" ")[1]

            # Decode token
            payload = decode_token(token)

            # JWT 'sub' claim is string (user ID)
            user_id = payload.get("sub")  # Keep as string for rate limit key
            user_role = payload.get("role", "viewer")

            return user_id, user_role

        except Exception as e:
            logger.debug(f"Could not extract user info from token: {e}")
            return None, "unauthenticated"

    def _increment_request_count(self, key: str) -> int:
        """
        Increment request count in Redis.

        Args:
            key: Redis key for rate limiting

        Returns:
            Current request count
        """
        try:
            # Increment counter
            count = self.redis_client.incr(key)

            # Set expiration on first request (1 hour)
            if count == 1:
                self.redis_client.expire(key, 3600)

            return count

        except Exception as e:
            logger.error(f"Redis error in rate limiting: {e}")
            # Fail open - allow request if Redis is down
            return 0

    def _get_reset_time(self) -> int:
        """
        Get Unix timestamp when rate limit will reset.

        Returns:
            Unix timestamp (1 hour from now)
        """
        reset_time = datetime.utcnow() + timedelta(hours=1)
        return int(reset_time.timestamp())

    def _get_retry_after_seconds(self) -> int:
        """
        Get number of seconds until rate limit resets.

        Returns:
            Seconds until reset
        """
        # Calculate seconds until next hour
        now = datetime.utcnow()
        next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        return int((next_hour - now).total_seconds())
